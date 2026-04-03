"""E2E tests for full server workflow via HTTP.

These tests use FastAPI TestClient (no Docker needed).
"""

from fastapi.testclient import TestClient

from app import app


def _step_json(name: str, qty: float = 10, meal: str = "m") -> dict:
    return {
        "meal_plan": [
            {
                "day": 1,
                "meal_name": meal,
                "ingredients": [{"name": name, "quantity": qty}],
            }
        ]
    }


def test_server_reset_step_state():
    """Full workflow: reset -> step -> state."""
    client = TestClient(app)

    obs = client.post("/reset", json={"task_id": "easy", "seed": 42}).json()
    assert obs["done"] is False

    item = obs["inventory"][0]
    result = client.post("/step", json=_step_json(item["name"])).json()
    assert result["done"] is True

    state = client.get("/state").json()
    assert state["done"] is True
    assert state["reward"] is not None


def test_server_multiple_episodes():
    """Server should handle multiple sequential episodes."""
    client = TestClient(app)
    for seed in range(5):
        obs = client.post("/reset", json={"task_id": "easy", "seed": seed}).json()
        item = obs["inventory"][0]
        result = client.post("/step", json=_step_json(item["name"], meal=f"ep{seed}")).json()
        assert result["done"] is True


def test_server_concurrent_safety():
    """Rapid sequential requests should not crash."""
    client = TestClient(app)
    for _ in range(10):
        obs = client.post("/reset", json={"task_id": "easy", "seed": 0}).json()
        item = obs["inventory"][0]
        client.post("/step", json=_step_json(item["name"], qty=1))
    obs = client.post("/reset", json={"task_id": "hard", "seed": 99}).json()
    assert len(obs["inventory"]) >= 20
