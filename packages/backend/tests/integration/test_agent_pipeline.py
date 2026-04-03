"""Integration tests for the agent->env->score pipeline."""

from agents.eval import run_assessment
from agents.fifo_agent import FIFOAgent
from agents.random_agent import RandomAgent
from env.fridge_env import FridgeEnv
from env.models import Action


def test_fifo_agent_easy_pipeline():
    env = FridgeEnv()
    obs = env.reset("easy", seed=42)
    agent = FIFOAgent()
    action_dict = agent.act(obs.model_dump(mode="json"))
    action = Action(**action_dict)
    _, reward, _, _ = env.step(action)
    assert reward.score > 0.5, f"FIFO easy score {reward.score} should be > 0.5"


def test_fifo_agent_medium_pipeline():
    env = FridgeEnv()
    obs = env.reset("medium", seed=42)
    agent = FIFOAgent()
    action_dict = agent.act(obs.model_dump(mode="json"))
    action = Action(**action_dict)
    _, reward, _, _ = env.step(action)
    assert reward.score > 0.2, f"FIFO medium score {reward.score} should be > 0.2"


def test_random_agent_produces_valid_score():
    env = FridgeEnv()
    obs = env.reset("easy", seed=0)
    agent = RandomAgent(seed=0)
    action_dict = agent.act(obs.model_dump(mode="json"))
    action = Action(**action_dict)
    _, reward, _, _ = env.step(action)
    assert 0.0 <= reward.score <= 1.0


def test_assessment_100_episodes_easy():
    result = run_assessment(FIFOAgent(), "easy", num_episodes=100)
    assert result["episodes"] == 100
    assert all(0.0 <= r["score"] <= 1.0 for r in result["results"])


def test_assessment_results_format():
    result = run_assessment(RandomAgent(seed=0), "medium", num_episodes=5)
    assert "agent" in result
    assert "difficulty" in result
    assert "mean_score" in result
    assert "mean_waste_rate" in result
    assert "mean_nutrition_score" in result
    assert isinstance(result["results"], list)
    assert len(result["results"]) == 5
    for r in result["results"]:
        assert "seed" in r
        assert "score" in r
        assert "waste_rate" in r
