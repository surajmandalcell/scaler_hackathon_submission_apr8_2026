"""Shared runtime singletons for FundLens.

Owns the in-process `_demo_env` and the `_unwrap_tool_result` helper that the
REST routes in `app.py`, `session_routes.py`, and `admin/routes.py` all need
to reach. Centralising these here avoids:

1. Circular imports between `app.py` and the other route modules.
2. Multiple divergent copies of the "unwrap an MCP observation" helper.
3. Any risk of two REST paths accidentally creating two different environments
   (and therefore two different in-memory stores).

The singleton `_demo_env` is deliberately stateful across HTTP requests. This
is a hard workaround for openenv-core's stateless `/reset` + `/step` lifecycle
(`http_server.py:582,617` instantiates a fresh env per request and closes it
afterwards) -- the Playground UI needs a persistent env that spans many
requests, and `/api/run-agent` already relied on this pattern.
"""
from __future__ import annotations

from typing import Any

from fundlens.server.data_store import store as shared_store
from fundlens.server.environment import FundLensEnvironment

# Singleton env -- shares the SQLite-backed `store` module singleton so that
# Analyst/Admin/Investor REST endpoints and the Playground all see the same
# data. Any `/api/session/*` call mutates this instance in place.
demo_env: FundLensEnvironment = FundLensEnvironment(store=shared_store)


def unwrap_tool_result(observation: Any) -> Any:
    """Pull the structured tool result out of an MCP observation envelope.

    FastMCP tool returns arrive wrapped in an MCP result object; we want the
    inner dict (either `data` or `structured_content` depending on the version).
    """
    if observation is None:
        return None
    result = getattr(observation, "result", None)
    if result is None:
        return None
    data = getattr(result, "data", None) or getattr(result, "structured_content", None)
    return data
