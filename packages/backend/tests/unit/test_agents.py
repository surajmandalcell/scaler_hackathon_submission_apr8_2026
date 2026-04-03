"""Unit tests for agents — random, FIFO, and assessment."""

from agents.eval import run_assessment
from agents.fifo_agent import FIFOAgent
from agents.random_agent import RandomAgent
from env.fridge_env import FridgeEnv
from env.models import Action


def _get_obs_dict(difficulty: str = "easy", seed: int = 42) -> dict:
    env = FridgeEnv()
    obs = env.reset(difficulty, seed=seed)
    return obs.model_dump(mode="json")


def test_fifo_returns_valid_action():
    obs = _get_obs_dict()
    agent = FIFOAgent()
    result = agent.act(obs)
    action = Action(**result)
    assert len(action.meal_plan) > 0


def test_random_returns_valid_action():
    obs = _get_obs_dict()
    agent = RandomAgent(seed=0)
    result = agent.act(obs)
    action = Action(**result)
    assert len(action.meal_plan) > 0


def test_fifo_uses_soonest_first():
    obs = _get_obs_dict()
    agent = FIFOAgent()
    result = agent.act(obs)
    if result["meal_plan"]:
        first_day = result["meal_plan"][0]
        used_names = {i["name"] for i in first_day["ingredients"]}
        # The soonest-expiring items should be prioritized
        sorted_inv = sorted(obs["inventory"], key=lambda x: x["expiry_date"])
        soonest_names = {i["name"] for i in sorted_inv[:5]}
        # At least one of the first-day ingredients should be among soonest
        assert used_names & soonest_names, "FIFO should use soonest-expiring items"


def test_fifo_covers_horizon():
    obs = _get_obs_dict()
    agent = FIFOAgent()
    result = agent.act(obs)
    days_covered = {m["day"] for m in result["meal_plan"]}
    # Should cover most days in the horizon
    assert len(days_covered) >= obs["horizon"] - 1


def test_random_covers_horizon():
    obs = _get_obs_dict()
    agent = RandomAgent(seed=0)
    result = agent.act(obs)
    days_covered = {m["day"] for m in result["meal_plan"]}
    assert len(days_covered) >= 1


def test_fifo_scores_higher_than_random_easy():
    """FIFO should statistically outperform random on easy difficulty."""
    fifo_scores = []
    random_scores = []
    env = FridgeEnv()

    for seed in range(20):
        obs = env.reset("easy", seed=seed)
        obs_dict = obs.model_dump(mode="json")

        fifo_action = Action(**FIFOAgent().act(obs_dict))
        env.reset("easy", seed=seed)
        _, fifo_reward, _, _ = env.step(fifo_action)
        fifo_scores.append(fifo_reward.score)

        env.reset("easy", seed=seed)
        random_action = Action(**RandomAgent(seed=seed).act(obs_dict))
        env.reset("easy", seed=seed)
        _, random_reward, _, _ = env.step(random_action)
        random_scores.append(random_reward.score)

    fifo_mean = sum(fifo_scores) / len(fifo_scores)
    random_mean = sum(random_scores) / len(random_scores)
    assert fifo_mean > random_mean, f"FIFO ({fifo_mean:.3f}) should beat Random ({random_mean:.3f})"


def test_assessment_runs_without_error():
    agent = FIFOAgent()
    result = run_assessment(agent, "easy", num_episodes=10)
    assert result["episodes"] == 10
    assert 0.0 <= result["mean_score"] <= 1.0


def test_assessment_output_format():
    agent = RandomAgent(seed=0)
    result = run_assessment(agent, "easy", num_episodes=5)
    assert "agent" in result
    assert "difficulty" in result
    assert "mean_score" in result
    assert "mean_waste_rate" in result
    assert "mean_nutrition_score" in result
    assert "results" in result
    assert len(result["results"]) == 5
