"""E2E tests for Docker build and deployment.

These tests are marked with @pytest.mark.e2e and require Docker to be available.
Run with: npm run test:e2e
"""

import subprocess

import pytest

CONTAINER_NAME = "fridgeenv-test-run"
IMAGE_NAME = "fridgeenv-test"
HOST_PORT = 27860


@pytest.mark.e2e
def test_docker_build():
    """Docker image should build successfully."""
    result = subprocess.run(
        ["docker", "build", "-t", IMAGE_NAME, "."],
        cwd=str(__import__("pathlib").Path(__file__).parent.parent.parent.parent.parent),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"Docker build failed: {result.stderr}"


@pytest.mark.e2e
def test_docker_run_health():
    """Container should start and respond to /health."""
    import time

    import httpx

    cmd = [
        "docker",
        "run",
        "--rm",
        "-p",
        f"{HOST_PORT}:7860",
        "--name",
        CONTAINER_NAME,
        IMAGE_NAME,
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        time.sleep(3)
        resp = httpx.get(f"http://localhost:{HOST_PORT}/health", timeout=10)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    finally:
        subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True)
        proc.wait(timeout=10)


@pytest.mark.e2e
def test_docker_reset_step():
    """Full API roundtrip against Docker container."""
    import httpx

    base = f"http://localhost:{HOST_PORT}"
    obs = httpx.post(
        f"{base}/reset",
        json={"task_id": "easy", "seed": 0},
        timeout=10,
    ).json()
    item = obs["inventory"][0]
    action = {
        "meal_plan": [
            {
                "day": 1,
                "meal_name": "test",
                "ingredients": [{"name": item["name"], "quantity": 10}],
            }
        ]
    }
    result = httpx.post(f"{base}/step", json=action, timeout=10).json()
    assert result["done"] is True
    assert 0.0 <= result["reward"]["score"] <= 1.0


@pytest.mark.e2e
def test_docker_port_7860():
    """Container should expose port 7860 internally."""
    result = subprocess.run(
        [
            "docker",
            "inspect",
            "--format",
            "{{.Config.ExposedPorts}}",
            IMAGE_NAME,
        ],
        capture_output=True,
        text=True,
    )
    assert "7860" in result.stdout
