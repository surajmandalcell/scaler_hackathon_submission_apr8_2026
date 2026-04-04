"""Integration tests for FastAPI server endpoints."""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def _step_json(item_name: str, qty: float = 1) -> dict:
    """Build a minimal step action JSON."""
    return {
        "meal_plan": [
            {
                "day": 1,
                "meal_name": "m",
                "ingredients": [{"name": item_name, "quantity": qty}],
            }
        ]
    }


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_reset_returns_observation(client):
    resp = client.post("/reset", json={"task_id": "easy", "seed": 42})
    assert resp.status_code == 200
    data = resp.json()
    assert "inventory" in data
    assert "horizon" in data
    assert data["done"] is False


def test_reset_different_tasks(client):
    for task_id in ["easy", "medium", "hard"]:
        resp = client.post("/reset", json={"task_id": task_id, "seed": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["inventory"]) > 0


def test_step_returns_reward(client):
    obs = client.post("/reset", json={"task_id": "easy", "seed": 42}).json()
    item = obs["inventory"][0]
    resp = client.post("/step", json=_step_json(item["name"], 10))
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert "reward" in data
    assert 0.0 <= data["reward"]["score"] <= 1.0


def test_step_before_reset_returns_400(client):
    obs = client.post("/reset", json={"task_id": "easy", "seed": 0}).json()
    item = obs["inventory"][0]
    client.post("/step", json=_step_json(item["name"]))
    resp = client.post("/step", json=_step_json(item["name"]))
    assert resp.status_code == 400


def test_state_before_reset_returns_409(client):
    from fastapi import FastAPI, HTTPException

    from env.fridge_env import FridgeEnv

    test_app = FastAPI()
    test_env = FridgeEnv()

    @test_app.get("/state")
    def get_state():
        try:
            return test_env.state()
        except ValueError:
            raise HTTPException(status_code=409, detail="No active episode.") from None

    test_client = TestClient(test_app)
    resp = test_client.get("/state")
    assert resp.status_code == 409


def test_state_after_reset(client):
    client.post("/reset", json={"task_id": "easy", "seed": 42})
    resp = client.get("/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "easy"
    assert data["done"] is False
    assert len(data["inventory"]) > 0


def test_state_after_step(client):
    obs = client.post("/reset", json={"task_id": "easy", "seed": 42}).json()
    item = obs["inventory"][0]
    client.post("/step", json=_step_json(item["name"], 10))
    resp = client.get("/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert data["reward"] is not None


def test_full_roundtrip(client):
    obs = client.post("/reset", json={"task_id": "medium", "seed": 7}).json()
    assert len(obs["inventory"]) >= 10

    meals = []
    for day in range(1, obs["horizon"] + 1):
        ingredients = [
            {
                "name": item["name"],
                "quantity": item["quantity"] / obs["horizon"],
            }
            for item in obs["inventory"]
        ]
        meals.append(
            {
                "day": day,
                "meal_name": f"day{day}",
                "ingredients": ingredients,
            }
        )

    resp = client.post("/step", json={"meal_plan": meals})
    assert resp.status_code == 200
    data = resp.json()
    assert data["done"] is True
    assert 0.0 <= data["reward"]["score"] <= 1.0

    state = client.get("/state").json()
    assert state["done"] is True


def test_reset_clears_previous_episode(client):
    obs1 = client.post("/reset", json={"task_id": "easy", "seed": 0}).json()
    item = obs1["inventory"][0]
    client.post("/step", json=_step_json(item["name"]))
    obs2 = client.post("/reset", json={"task_id": "hard", "seed": 5}).json()
    assert obs2["done"] is False
    assert len(obs2["inventory"]) >= 20
