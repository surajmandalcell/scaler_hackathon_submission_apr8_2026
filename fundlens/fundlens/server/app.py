"""FastAPI application — OpenEnv API + Gradio dashboards."""
import gradio as gr
from openenv.core.env_server import create_app, CallToolAction
from fundlens.models import FundLensObservation
from fundlens.server.environment import FundLensEnvironment
from fundlens.admin.ui import build_admin_ui
from fundlens.investor.ui import build_investor_ui

# OpenEnv HTTP API (reset / step / state endpoints)
app = create_app(
    env=FundLensEnvironment,
    action_cls=CallToolAction,
    observation_cls=FundLensObservation,
    env_name="fundlens",
)

# Admin dashboard — data entry, answer key export
admin_demo = build_admin_ui()
gr.mount_gradio_app(app, admin_demo, path="/admin")

# Investor portal — read-only, plain English
investor_demo = build_investor_ui()
gr.mount_gradio_app(app, investor_demo, path="/investor")


@app.get("/health")
async def health() -> dict:
    """Health check for container orchestration / HuggingFace Space."""
    return {"status": "ok"}
