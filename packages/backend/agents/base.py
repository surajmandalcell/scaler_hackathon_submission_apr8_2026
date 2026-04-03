"""Abstract base agent for FridgeEnv."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    @abstractmethod
    def act(self, observation: dict) -> dict:
        """Take a serialized Observation, return a serialized Action."""
        raise NotImplementedError
