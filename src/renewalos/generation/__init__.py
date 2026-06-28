"""Synthetic source-data generation for RenewalOS."""

from renewalos.generation.config import DEFAULT_GENERATION_CONFIG, SyntheticDataConfig
from renewalos.generation.validate_generation import generate_raw_data

__all__ = [
    "DEFAULT_GENERATION_CONFIG",
    "SyntheticDataConfig",
    "generate_raw_data",
]
