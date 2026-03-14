"""In-memory session store for document data."""

from __future__ import annotations

import uuid

sessions: dict[str, dict] = {}


def generate_session_id() -> str:
    return str(uuid.uuid4())
