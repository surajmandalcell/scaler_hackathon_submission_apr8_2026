"""Shared test fixtures for FridgeEnv."""

import pytest


@pytest.fixture
def env():
    from env.fridge_env import FridgeEnv

    return FridgeEnv()


@pytest.fixture
def easy_obs(env):
    return env.reset(task_id="easy", seed=42)


@pytest.fixture
def medium_obs(env):
    return env.reset(task_id="medium", seed=42)


@pytest.fixture
def hard_obs(env):
    return env.reset(task_id="hard", seed=42)
