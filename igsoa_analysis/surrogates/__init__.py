"""Surrogate modelling utilities for IGSOA acceleration experiments."""

from .base import SurrogateConfig, SurrogateModelBase, SurrogateTrainingArtifact
from .pytorch_surrogate import FeedForwardSurrogate

__all__ = [
    "SurrogateConfig",
    "SurrogateModelBase",
    "SurrogateTrainingArtifact",
    "FeedForwardSurrogate",
]
