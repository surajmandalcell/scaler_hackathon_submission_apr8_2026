"""Tests for DataStore operations."""
import pytest
from fundlens.server.data_store import DataStore
from fundlens.models import Fund, Deal, Ownership, Cashflow


def test_add_and_get_fund():
    s = DataStore()
    s.add_fund(Fund(fund_id="f1", fund_name="Test", reporting_date="2024-12-31",
                    beginning_nav=10.0, ending_nav=15.0))
    assert "f1" in s.funds
    assert s.funds["f1"].fund_name == "Test"


def test_add_and_get_deal():
    s = DataStore()
    s.add_deal(Deal(deal_id="d1", property_name="Prop", sector="Office", location="NYC"))
    assert "d1" in s.deals


def test_add_ownership():
    s = DataStore()
    s.add_fund(Fund(fund_id="f1", fund_name="T", reporting_date="2024-12-31",
                    beginning_nav=10.0, ending_nav=15.0))
    s.add_deal(Deal(deal_id="d1", property_name="P", sector="Office", location="NYC"))
    s.add_ownership(Ownership(deal_id="d1", fund_id="f1", ownership_pct=0.65, entry_date="2022-01-01"))
    own = s.get_ownership("f1", "d1")
    assert own is not None
    assert own.ownership_pct == 0.65


def test_get_cashflows_by_fund():
    s = DataStore()
    s.add_cashflow(Cashflow(cashflow_id="c1", deal_id="d1", fund_id="f1",
                            cash_date="2024-01-01", cf_type="contribution", fund_amt=-5.0))
    s.add_cashflow(Cashflow(cashflow_id="c2", deal_id="d1", fund_id="f2",
                            cash_date="2024-01-01", cf_type="contribution", fund_amt=-3.0))
    cfs = s.get_cashflows(fund_id="f1")
    assert len(cfs) == 1
    assert cfs[0].fund_amt == -5.0


def test_get_cashflows_by_deal():
    s = DataStore()
    s.add_cashflow(Cashflow(cashflow_id="c1", deal_id="d1", fund_id="f1",
                            cash_date="2024-01-01", cf_type="contribution", fund_amt=-5.0))
    s.add_cashflow(Cashflow(cashflow_id="c2", deal_id="d2", fund_id="f1",
                            cash_date="2024-01-01", cf_type="contribution", fund_amt=-3.0))
    cfs = s.get_cashflows(fund_id="f1", deal_id="d1")
    assert len(cfs) == 1


def test_get_deals_for_fund():
    s = DataStore()
    s.add_fund(Fund(fund_id="f1", fund_name="T", reporting_date="2024-12-31",
                    beginning_nav=10.0, ending_nav=15.0))
    s.add_deal(Deal(deal_id="d1", property_name="P1", sector="Office", location="NYC"))
    s.add_deal(Deal(deal_id="d2", property_name="P2", sector="Residential", location="LA"))
    s.add_ownership(Ownership(deal_id="d1", fund_id="f1", ownership_pct=1.0, entry_date="2022-01-01"))
    s.add_ownership(Ownership(deal_id="d2", fund_id="f1", ownership_pct=0.5, entry_date="2022-01-01"))
    deals = s.get_deals_for_fund("f1")
    assert len(deals) == 2
