"""Offline τ²-bench reference-task evaluation (imports are lazy)."""

from .adapter import SUPPORTED_REVISION, load_dataset
from .evaluator import evaluate

__all__ = ["SUPPORTED_REVISION", "load_dataset", "evaluate"]
