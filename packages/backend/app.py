"""FastAPI server implementing OpenEnv /reset, /step, /state, /health endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from env.fridge_env import FridgeEnv
from env.models import Action

app = FastAPI(title="FridgeEnv", version="1.0.0", description="Food waste reduction RL benchmark")
env = FridgeEnv()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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


# Serve React frontend build if it exists
frontend_build = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
