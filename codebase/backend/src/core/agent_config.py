"""ReAct agent step limits (env-tunable)."""

from __future__ import annotations

import os

DEFAULT_MAX_STEPS = max(2, int(os.getenv("AGENT_DEFAULT_MAX_STEPS", "8")))
MAX_MAX_STEPS = max(DEFAULT_MAX_STEPS, int(os.getenv("AGENT_MAX_MAX_STEPS", "12")))
