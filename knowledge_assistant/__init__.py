"""Production-oriented, multi-tenant knowledge assistant."""

from knowledge_assistant.config import Settings
from knowledge_assistant.services.knowledge import KnowledgeAssistant

__all__ = ["KnowledgeAssistant", "Settings"]
