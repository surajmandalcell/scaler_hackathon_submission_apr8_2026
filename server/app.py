"""
Root-level server entry point for OpenEnv CLI validators.

This stub exists so that `openenv validate` (which expects a flat
`server/app.py` + `pyproject.toml` layout) recognises the repo as a
valid OpenEnv environment. The real FastAPI application lives in
`packages/backend/fundlens/server/app.py`; this file simply re-exports
it and provides a `main()` entry point that uvicorn can launch.

The Dockerfile (the canonical deployment path for this env, per
README.md frontmatter `sdk: docker`) does NOT use this file -- it
runs `uvicorn fundlens.server.app:app` directly against the installed
package inside the container.
"""
from __future__ import annotations

import os

# Re-export the FastAPI app so `uvicorn server.app:app` also works
# if someone invokes it that way.
from fundlens.server.app import app  # noqa: F401


def main() -> None:
    """Launch the FundLens server. Used by `[project.scripts] server`."""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "fundlens.server.app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
