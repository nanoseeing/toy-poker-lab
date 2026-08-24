"""Configuration-driven experiment execution."""

from toy_poker.experiments.config import ExperimentConfig
from toy_poker.experiments.runner import RunResult, run_experiment

__all__ = ["ExperimentConfig", "RunResult", "run_experiment"]
