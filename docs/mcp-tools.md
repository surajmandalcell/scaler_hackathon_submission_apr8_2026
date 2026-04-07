# MCP Tools

FundLens registers **15 MCP tools** via FastMCP. Agents call these by name through `POST /step` with a `CallToolAction` payload.

## Computation tools

These are what agents primarily use to compute the NAV bridge and metrics.

| Tool                       | Arguments                                | Returns                                          |
|----------------------------|------------------------------------------|--------------------------------------------------|
| `get_available_filters`    | -                                        | `{fund_ids, deal_ids, sectors, cf_types}`        |
| `get_nav_bridge`           | `fund_id: str`                           | 8-line bridge dict for one fund                  |
| `get_cashflow_summary`     | `fund_id: str, deal_id?: str`            | Pre-aggregated totals + IRR schedule (use this for computation, not raw rows) |
| `get_deal_info`            | `fund_id: str`                           | Per-deal: sector, ownership_pct, appraiser_nav, deal_beginning_nav |
| `get_irr`                  | `fund_id: str`                           | `{irr: float}`                                   |
| `submit_report`            | `nav_bridge: dict, metrics?: dict`       | `{reward, bridge_score, metrics_score, ...}`     |

## Exploration tools

Optional tools for agents that want richer context.

| Tool                       | Arguments                                | Returns                                          |
|----------------------------|------------------------------------------|--------------------------------------------------|
| `get_portfolio_summary`    | `funds?: list[str]`                      | Fund-level NAV, MOIC, IRR                        |
| `get_portfolio_bridge`     | -                                        | NAV bridge across all loaded funds               |
| `get_portfolio_metrics`    | -                                        | MOIC and IRR pooled across all funds             |
| `get_deal_bridge`          | `fund_id: str, deal_id: str`             | Single-deal NAV bridge                           |
| `get_deal_metrics`         | `fund_id: str, deal_id: str`             | Single-deal MOIC and IRR                         |
| `get_deal_exposure`        | `deal_id: str`                           | Cross-fund consolidation for shared deals        |
| `compare_funds`            | `funds?: list[str], metrics?: list[str]` | Side-by-side comparison                          |
| `get_sector_report`        | `sector?: str, funds?: list[str]`        | Breakdown by property sector                     |
| `get_raw_cashflows`        | `fund_id: str, deal_id?: str, limit, offset` | Paginated raw cashflow rows (large datasets) |

## Recommended call sequence

For an agent solving a task:

### Easy
```
1. get_available_filters         -> get fund_ids
2. get_nav_bridge(fund_id)       -> get the 8-line bridge directly
3. submit_report(nav_bridge=...)
```

### Medium
```
1. get_available_filters         -> get fund_ids
2. get_nav_bridge(fund_id)       -> bridge
3. get_portfolio_summary(...)    -> MOIC
4. submit_report(nav_bridge=..., metrics={"moic": ...})
```

### Hard
```
1. get_available_filters         -> get fund_ids (multiple!)
2. get_nav_bridge(primary)       -> bridge for primary fund
3. get_portfolio_summary(funds)  -> MOIC and IRR for primary fund
4. submit_report(nav_bridge=..., metrics={"moic": ..., "irr": ...})
```

A clever agent could compute the bridge from `get_cashflow_summary` and `get_deal_info` instead of taking the pre-computed `get_nav_bridge`. This is what `inference.py` demonstrates.

## Why so many tools?

Different agents have different strategies. A pass-through baseline calls `get_nav_bridge` and submits the result directly. A more sophisticated agent might call `get_raw_cashflows`, compute the bridge from scratch, and use `get_deal_info` to handle ownership percentages for the hard task. The tool surface supports both extremes without forcing the agent into one pattern.
