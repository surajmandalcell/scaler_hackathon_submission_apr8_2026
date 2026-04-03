"""Run agents across episodes and aggregate scores."""

from __future__ import annotations

import json

from agents.base import BaseAgent
from env.fridge_env import FridgeEnv
from env.models import Action


def run_assessment(
    agent: BaseAgent,
    difficulty: str,
    num_episodes: int = 100,
) -> dict:
    """Run agent over multiple episodes and return aggregated results."""
    env = FridgeEnv()
    results: list[dict] = []

    for seed in range(num_episodes):
        obs = env.reset(task_id=difficulty, seed=seed)
        action_dict = agent.act(obs.model_dump(mode="json"))
        action = Action(**action_dict)
        _, reward, _, info = env.step(action)

        results.append(
            {
                "seed": seed,
                "score": reward.score,
                "waste_rate": reward.waste_rate,
                "nutrition_score": reward.nutrition_score,
                "items_used": reward.items_used,
                "items_expired": reward.items_expired,
                "num_violations": len(reward.violations),
            }
        )

    scores = [r["score"] for r in results]
    waste_rates = [r["waste_rate"] for r in results]
    nutrition_scores = [r["nutrition_score"] for r in results]

    return {
        "agent": agent.__class__.__name__,
        "difficulty": difficulty,
        "episodes": num_episodes,
        "mean_score": sum(scores) / len(scores),
        "min_score": min(scores),
        "max_score": max(scores),
        "mean_waste_rate": sum(waste_rates) / len(waste_rates),
        "mean_nutrition_score": sum(nutrition_scores) / len(nutrition_scores),
        "results": results,
    }


def main() -> None:
    """Run assessment for all agents and difficulties."""
    from agents.fifo_agent import FIFOAgent
    from agents.random_agent import RandomAgent

    agents = [RandomAgent(seed=0), FIFOAgent()]
    difficulties = ["easy", "medium", "hard"]

    all_results = {}
    for agent in agents:
        for difficulty in difficulties:
            key = f"{agent.__class__.__name__}_{difficulty}"
            result = run_assessment(agent, difficulty, num_episodes=100)
            all_results[key] = {k: v for k, v in result.items() if k != "results"}
            print(
                f"{agent.__class__.__name__:15s} | {difficulty:6s} | "
                f"score={result['mean_score']:.3f} | "
                f"waste={result['mean_waste_rate']:.3f} | "
                f"nutrition={result['mean_nutrition_score']:.3f}"
            )

    with open("assessment_results.json", "w") as f:
        json.dump(all_results, f, indent=2)


if __name__ == "__main__":
    main()
