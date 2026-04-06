"""IT Head — owns app.py, inference.py, environment.py, requirements.txt."""
from __future__ import annotations
from agents.base_specialist import run_specialist

_SYSTEM = """You are the IT Head / DevOps lead for a Python FastAPI + OpenEnv hackathon project.
You own the server, inference baseline, and deployment config. Your expertise:
- FastAPI + uvicorn server setup, OpenEnv MCPEnvironment lifecycle (reset/step/state)
- Dockerfile (python:3.11-slim, port 8000, uvicorn entrypoint)
- inference.py: OpenAI-compatible client, tool-use loop, auto-submit on max steps
- requirements.txt: openenv-core, fastmcp, pydantic>=2, fastapi, uvicorn, openai, gradio
When reviewing: check server correctness, Docker build hygiene, inference loop reliability.
When executing: fix infra issues, optimise server config, update dependencies as needed."""


def review(owned_files: list[str]) -> dict:
    return run_specialist(
        role_name="IT Head",
        system_prompt=_SYSTEM,
        task="Review the FastAPI server, inference baseline, and deployment config. "
             "Report on reliability, missing error handling, and deployment readiness.",
        owned_files=owned_files,
        mode="review",
    )


def execute(task: str, owned_files: list[str]) -> dict:
    return run_specialist(
        role_name="IT Head",
        system_prompt=_SYSTEM,
        task=task,
        owned_files=owned_files,
        mode="execute",
    )
