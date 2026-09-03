"""Convenient ASGI entry point for ``uvicorn api:app``."""

from knowledge_assistant.api.app import app, create_app

__all__ = ["app", "create_app"]
