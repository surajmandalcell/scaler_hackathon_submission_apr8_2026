"""In-memory data store for FundLens — with optional SQLite persistence."""
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional
from fundlens.models import Fund, Deal, Ownership, Cashflow


class DataStore:
    """
    Single store with an in-memory cache.
    Pass db_path to enable SQLite persistence — data survives server restarts.
    Omit db_path (default) for a pure in-memory store (used by the environment).
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.funds: Dict[str, Fund] = {}
        self.deals: Dict[str, Deal] = {}
        self.ownerships: List[Ownership] = []
        self.cashflows: List[Cashflow] = []
        self.fx_rates: List = []

        self._db_path = db_path
        if db_path:
            self._init_db()
            self._load_from_db()

    # ── SQLite helpers ────────────────────────────────────────────────────

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS funds (
                    fund_id          TEXT PRIMARY KEY,
                    fund_name        TEXT,
                    fund_currency    TEXT,
                    reporting_date   TEXT,
                    beginning_nav    REAL,
                    ending_nav       REAL,
                    nav_period_start TEXT
                );
                CREATE TABLE IF NOT EXISTS deals (
                    deal_id       TEXT PRIMARY KEY,
                    property_name TEXT,
                    sector        TEXT,
                    location      TEXT,
                    appraiser_nav REAL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS ownerships (
                    fund_id       TEXT,
                    deal_id       TEXT,
                    ownership_pct REAL,
                    entry_date    TEXT,
                    PRIMARY KEY (fund_id, deal_id)
                );
                CREATE TABLE IF NOT EXISTS cashflows (
                    cashflow_id TEXT PRIMARY KEY,
                    deal_id     TEXT,
                    fund_id     TEXT,
                    cash_date   TEXT,
                    cf_type     TEXT,
                    fund_amt    REAL
                );
            """)
            # Migrate: add appraiser_nav to deals if missing
            deal_cols = [r[1] for r in conn.execute("PRAGMA table_info(deals)").fetchall()]
            if "appraiser_nav" not in deal_cols:
                conn.execute("ALTER TABLE deals ADD COLUMN appraiser_nav REAL DEFAULT 0")
            # Migrate: drop appraiser_nav from ownerships if it crept in (old schema)
            own_cols = [r[1] for r in conn.execute("PRAGMA table_info(ownerships)").fetchall()]
            if "appraiser_nav" in own_cols:
                conn.executescript("""
                    CREATE TABLE ownerships_new (
                        fund_id       TEXT,
                        deal_id       TEXT,
                        ownership_pct REAL,
                        entry_date    TEXT,
                        PRIMARY KEY (fund_id, deal_id)
                    );
                    INSERT INTO ownerships_new SELECT fund_id, deal_id, ownership_pct, entry_date
                        FROM ownerships;
                    DROP TABLE ownerships;
                    ALTER TABLE ownerships_new RENAME TO ownerships;
                """)

    def _load_from_db(self) -> None:
        with self._db() as conn:
            for row in conn.execute("SELECT * FROM funds"):
                self.funds[row["fund_id"]] = Fund(**dict(row))
            for row in conn.execute("SELECT * FROM deals"):
                self.deals[row["deal_id"]] = Deal(**dict(row))
            for row in conn.execute("SELECT * FROM ownerships"):
                self.ownerships.append(Ownership(**dict(row)))
            for row in conn.execute("SELECT * FROM cashflows"):
                self.cashflows.append(Cashflow(**dict(row)))

    # ── CRUD ──────────────────────────────────────────────────────────────

    def add_fund(self, fund: Fund) -> None:
        self.funds[fund.fund_id] = fund
        if self._db_path:
            with self._db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO funds VALUES (?,?,?,?,?,?,?)",
                    (fund.fund_id, fund.fund_name, fund.fund_currency,
                     fund.reporting_date, fund.beginning_nav, fund.ending_nav,
                     fund.nav_period_start),
                )

    def add_deal(self, deal: Deal) -> None:
        self.deals[deal.deal_id] = deal
        if self._db_path:
            with self._db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO deals VALUES (?,?,?,?,?)",
                    (deal.deal_id, deal.property_name, deal.sector,
                     deal.location, deal.appraiser_nav),
                )

    def add_ownership(self, o: Ownership) -> None:
        self.ownerships = [x for x in self.ownerships
                           if not (x.fund_id == o.fund_id and x.deal_id == o.deal_id)]
        self.ownerships.append(o)
        if self._db_path:
            with self._db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO ownerships VALUES (?,?,?,?)",
                    (o.fund_id, o.deal_id, o.ownership_pct, o.entry_date),
                )

    def compute_fund_ending_nav(self, fund_id: str) -> float:
        """Sum of (deal.appraiser_nav × ownership_pct) for all deals in a fund."""
        total = 0.0
        for o in self.ownerships:
            if o.fund_id == fund_id:
                deal = self.deals.get(o.deal_id)
                if deal:
                    total += deal.appraiser_nav * o.ownership_pct
        return total

    def sync_all_fund_navs(self) -> None:
        """Recompute ending_nav for every fund from deal-level appraiser NAVs."""
        for fund_id in self.funds:
            nav = self.compute_fund_ending_nav(fund_id)
            if nav > 0:
                f = self.funds[fund_id]
                self.add_fund(f.model_copy(update={"ending_nav": round(nav, 4)}))

    def add_cashflow(self, cf: Cashflow) -> None:
        self.cashflows.append(cf)
        if self._db_path:
            with self._db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cashflows VALUES (?,?,?,?,?,?)",
                    (cf.cashflow_id, cf.deal_id, cf.fund_id,
                     cf.cash_date, cf.cf_type, cf.fund_amt),
                )

    def add_fx_rate(self, fx) -> None:
        self.fx_rates.append(fx)

    def clear(self) -> None:
        """Clears in-memory cache AND SQLite (if persistent). Used by seed loaders."""
        self.funds.clear()
        self.deals.clear()
        self.ownerships.clear()
        self.cashflows.clear()
        self.fx_rates.clear()
        if self._db_path:
            with self._db() as conn:
                conn.executescript("""
                    DELETE FROM funds;
                    DELETE FROM deals;
                    DELETE FROM ownerships;
                    DELETE FROM cashflows;
                """)

    # ── Queries ───────────────────────────────────────────────────────────

    def get_cashflows(
        self,
        fund_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        cf_types: Optional[List[str]] = None,
    ) -> List[Cashflow]:
        result = self.cashflows
        if fund_id:
            result = [c for c in result if c.fund_id == fund_id]
        if deal_id:
            result = [c for c in result if c.deal_id == deal_id]
        if cf_types:
            result = [c for c in result if c.cf_type in cf_types]
        return result

    def get_ownership(self, fund_id: str, deal_id: str) -> Optional[Ownership]:
        for o in self.ownerships:
            if o.fund_id == fund_id and o.deal_id == deal_id:
                return o
        return None

    def get_deals_for_fund(self, fund_id: str) -> List[Deal]:
        deal_ids = {o.deal_id for o in self.ownerships if o.fund_id == fund_id}
        return [self.deals[did] for did in deal_ids if did in self.deals]

    def get_funds_for_deal(self, deal_id: str) -> List[str]:
        return [o.fund_id for o in self.ownerships if o.deal_id == deal_id]


# ── Global singleton — persistent, used by the admin UI ───────────────────
_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fundlens.db")
store = DataStore(db_path=os.path.normpath(_DB_FILE))
