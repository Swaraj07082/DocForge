"""Load the NeMo Guardrails YAML config from guardrails/config/."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from nemoguardrails import RailsConfig

_CONFIG_DIR = Path(__file__).resolve().parent / "config"


@lru_cache(maxsize=1)
def load_rails_config() -> RailsConfig:
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is not set in the environment")
    return RailsConfig.from_path(str(_CONFIG_DIR))
