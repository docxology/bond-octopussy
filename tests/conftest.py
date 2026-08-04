"""Shared pytest fixtures for the FABERGÉ suite.

Forces the non-interactive matplotlib backend so figure tests never open a
display window or hang (mirrors the template's known-issue #4). Project
``src/`` is already on ``sys.path`` via ``pyproject.toml`` (``pythonpath``).
"""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")
