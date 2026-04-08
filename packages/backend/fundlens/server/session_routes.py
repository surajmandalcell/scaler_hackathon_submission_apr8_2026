"""Stateful MCP playground routes -- /api/session/*.

These routes let a human drive the same MCP tool surface that AI agents use
through `/step`, but with state that spans requests. They're the direct
workaround for openenv-core's stateless `/reset` + `/step` lifecycle: every
call here hits the long-lived `demo_env` singleton in `runtime.py` instead of
the per-request env the framework creates for `/reset` and `/step`.

Route map:
    GET  /api/session/state   -> current task_id, funds, step_count, is_done
    GET  /api/session/tools   -> introspected FastMCP tool list (name, desc, schema)
    POST /api/session/reset   -> reset demo_env onto a task, return observation
    POST /api/session/step    -> call an MCP tool by name with JSON arguments
    POST /api/session/submit  -> thin wrapper around the submit_report tool
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from openenv.core.env_server import CallToolAction
from pydantic import BaseModel, Field

from fundlens.server.runtime import demo_env, unwrap_tool_result

router = APIRouter(prefix="/api/session", tags=["session"])


# ── Request models ────────────────────────────────────────────────────────────


class ResetRequest(BaseModel):
    task_id: str = Field(default="easy")


class StepRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class SubmitRequest(BaseModel):
    nav_bridge: dict[str, float]
    metrics: dict[str, float] | None = None


# ── Helpers ──────────────────────────────────────────────────────────────────


def _observation_to_dict(obs: Any) -> dict[str, Any]:
    """Best-effort serialization of a FundLensObservation to a plain dict."""
    if obs is None:
        return {}
    dump = getattr(obs, "model_dump", None)
    if callable(dump):
        return dump()
    return {k: v for k, v in vars(obs).items() if not k.startswith("_")}


def _session_state_dict() -> dict[str, Any]:
    st = demo_env.state
    return {
        "task_id": getattr(st, "task_id", ""),
        "is_done": bool(getattr(st, "is_done", False)),
        "step_count": int(getattr(st, "step_count", 0) or 0),
        "funds_loaded": list(demo_env._store.funds.keys()),
        "deals_loaded": list(demo_env._store.deals.keys()),
    }


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/state")
async def get_state() -> dict[str, Any]:
    """Current playground session state."""
    return _session_state_dict()


@router.get("/tools")
async def list_tools() -> dict[str, Any]:
    """Introspect the FastMCP server and return the tool catalogue.

    Each tool entry contains:
        name:         string (e.g. "get_nav_bridge")
        description:  string (first line is a short summary)
        parameters:   JSON Schema object for arguments

    The frontend uses `parameters` to render an input form for every tool.
    """
    tools = demo_env._get_server_tools(demo_env.mcp_server)
    result: list[dict[str, Any]] = []
    for name, tool in tools.items():
        description = (tool.description or "").strip()
        parameters = getattr(tool, "parameters", None) or {
            "type": "object",
            "properties": {},
            "required": [],
        }
        result.append({
            "name": name,
            "description": description,
            "parameters": parameters,
        })
    result.sort(key=lambda t: t["name"])
    return {"tools": result}


@router.post("/reset")
async def reset_session(req: ResetRequest) -> dict[str, Any]:
    """Reset demo_env onto a task. Returns the initial observation."""
    observation = demo_env.reset(task_id=req.task_id)
    return {
        "state": _session_state_dict(),
        "observation": _observation_to_dict(observation),
    }


@router.post("/step")
async def step_session(req: StepRequest) -> dict[str, Any]:
    """Call an MCP tool by name with JSON arguments on the shared demo_env.

    Returns:
        tool_name:   echo of the request
        arguments:   echo of the request
        result:      unwrapped tool result (or error dict)
        state:       updated session state after the call
    """
    action = CallToolAction(tool_name=req.tool_name, arguments=req.arguments)
    observation = demo_env.step(action)
    result = unwrap_tool_result(observation)
    if result is None:
        # Some tool errors surface as a raw message on the observation envelope.
        result = {"error": getattr(observation, "message", "tool returned no data")}
    return {
        "tool_name": req.tool_name,
        "arguments": req.arguments,
        "result": result,
        "state": _session_state_dict(),
    }


@router.post("/submit")
async def submit_session(req: SubmitRequest) -> dict[str, Any]:
    """Convenience wrapper around `submit_report` for the grading view.

    Equivalent to POST /api/session/step with tool_name=submit_report and the
    bridge/metrics already wrapped, but saves the frontend from having to know
    the tool's payload shape.
    """
    args: dict[str, Any] = {"nav_bridge": req.nav_bridge}
    if req.metrics is not None:
        args["metrics"] = req.metrics
    action = CallToolAction(tool_name="submit_report", arguments=args)
    observation = demo_env.step(action)
    grading = unwrap_tool_result(observation) or {}
    return {
        "grading": grading,
        "state": _session_state_dict(),
    }
