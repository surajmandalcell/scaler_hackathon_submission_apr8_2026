"""FastAPI server implementing OpenEnv spec endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from env.fridge_env import FridgeEnv
from env.models import Action, Observation

app = FastAPI(
    title="FridgeEnv",
    version="1.0.0",
    description="Food waste reduction RL benchmark — OpenEnv-compliant environment",
)
env = FridgeEnv()


# ── OpenEnv Required Endpoints ───────────────────────────────────────


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.get("/metadata")
def metadata() -> dict:
    return {
        "name": "FridgeEnv",
        "description": (
            "Food waste reduction RL benchmark. Agent receives a fridge inventory "
            "with expiring items and must plan meals to minimize waste while "
            "respecting dietary restrictions and nutritional balance."
        ),
        "version": "1.0.0",
        "tasks": ["easy", "medium", "hard"],
    }


@app.get("/schema")
def schema() -> dict:
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "seed": {"type": "integer"},
                "done": {"type": "boolean"},
                "inventory": {"type": "array"},
                "reward": {"type": ["object", "null"]},
            },
        },
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> JSONResponse:
    """Minimal MCP JSON-RPC endpoint for OpenEnv compatibility."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    method = body.get("method", "")
    req_id = body.get("id", 1)

    if method == "initialize":
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "FridgeEnv", "version": "1.0.0"},
                },
            }
        )

    if method == "tools/list":
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "reset",
                            "description": "Reset environment with task_id and seed",
                            "inputSchema": Action.model_json_schema(),
                        },
                        {
                            "name": "step",
                            "description": "Submit a meal plan action",
                            "inputSchema": Action.model_json_schema(),
                        },
                    ]
                },
            }
        )

    # Default: return empty result
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {},
        }
    )


# ── Core Environment Endpoints ───────────────────────────────────────


@app.post("/reset")
def reset(body: dict) -> dict:
    task_id = body.get("task_id", "easy")
    seed = body.get("seed", 0)
    try:
        obs = env.reset(task_id=task_id, seed=seed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return obs.model_dump(mode="json")


@app.post("/step")
def step(action: Action) -> dict:
    try:
        obs, reward, done, info = env.step(action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return {
        "observation": obs.model_dump(mode="json"),
        "reward": reward.model_dump(mode="json"),
        "done": done,
        "info": info,
    }


@app.get("/state")
def get_state() -> dict:
    try:
        return env.state()
    except ValueError:
        raise HTTPException(
            status_code=409, detail="No active episode. Call /reset first."
        ) from None


# ── Frontend Static Files ────────────────────────────────────────────

frontend_build = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
