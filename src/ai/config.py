"""
config.py

Groq / LLM configuration and client factory for GarmentsPay AI query layer.
Strictly avoids logging or exposing the API key.
"""

from __future__ import annotations

import os
from typing import Any
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
if _ENV_PATH.exists():
    load_dotenv(dotenv_path=_ENV_PATH)
else:
    load_dotenv()

# Active Groq model configured and verified
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"

_OVERRIDDEN_CLIENT: Any = None


def get_groq_api_key() -> str:
    """
    Retrieve the configured Groq API key from environment.
    Never logs or exposes the key value.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError("GROQ_API_KEY environment variable is not set or is empty.")
    return api_key.strip()


def get_groq_model() -> str:
    """
    Returns the configured Groq model identifier.
    Defaults to 'qwen/qwen3.8-27b', overridable via GROQ_MODEL environment variable.
    """
    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()


def set_groq_client(client: Any) -> None:
    """
    Allows injecting a mock or custom client for testing without network dependency.
    Pass None to reset to default client.
    """
    global _OVERRIDDEN_CLIENT
    _OVERRIDDEN_CLIENT = client


def get_groq_client() -> Any:
    """
    Returns an initialized Groq client using the configured API key,
    or the overridden mock client if set.
    """
    global _OVERRIDDEN_CLIENT
    if _OVERRIDDEN_CLIENT is not None:
        return _OVERRIDDEN_CLIENT

    import groq

    api_key = get_groq_api_key()
    return groq.Groq(api_key=api_key)
