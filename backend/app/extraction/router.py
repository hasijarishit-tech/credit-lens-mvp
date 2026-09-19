"""Single entry point the API calls for extraction. Picks the Claude-powered
extractor when a key is configured, and falls back to rule-based keyword
matching otherwise — callers don't need to know which one ran; the result's
extraction_notes always says so.
"""
from typing import Any, Dict

from app.config import settings
from app.extraction.rule_based import extract_financials_rule_based


def is_llm_configured() -> bool:
    return bool(settings.anthropic_api_key)


def extract_financials(
    text: str, source_type: str, source_reference: str, sector_hint: str = ""
) -> Dict[str, Any]:
    if is_llm_configured():
        from app.llm.extraction import extract_financials as extract_with_claude

        result = extract_with_claude(text, source_type, source_reference, sector_hint)
        result["extraction_notes"]["method"] = "claude"
        return result

    return extract_financials_rule_based(text, source_type, source_reference)
