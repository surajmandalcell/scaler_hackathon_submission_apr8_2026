"""FridgeEnv baseline agents."""

from agents.base import BaseAgent
from agents.fifo_agent import FIFOAgent
from agents.random_agent import RandomAgent

__all__ = ["BaseAgent", "FIFOAgent", "RandomAgent"]
