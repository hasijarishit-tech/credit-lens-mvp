from functools import lru_cache

from anthropic import Anthropic

from app.config import settings


class ClaudeNotConfigured(Exception):
    """Raised when an LLM feature is called but no API key is set."""


@lru_cache
def get_client() -> Anthropic:
    if not settings.anthropic_api_key:
        raise ClaudeNotConfigured(
            "ANTHROPIC_API_KEY is not set. Add it to backend/.env to enable "
            "extraction and AI narrative features."
        )
    return Anthropic(api_key=settings.anthropic_api_key)


MODEL = settings.claude_model
