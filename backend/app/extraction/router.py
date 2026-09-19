"""Single entry point the API calls for extraction. Picks the Claude-powered
extractor when a key is configured, and falls back to rule-based keyword
matching otherwise — callers don't need to know which one ran; the result's
extraction_notes always says so.
"""
from typing import Any, Dict

from app.config import settings
from app.extraction.rule_based import extract_financials_rule_based
from app.extraction.screener_parser import extract_financials_screener, is_screener_url


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

    # Screener.in reports aggregated line items the generic keyword matcher
    # can't find at all (it never uses words like "sundry debtors") — try
    # the site-specific parser first for those pages.
    if source_type in ("source_link", "name_search") and is_screener_url(source_reference):
        result = extract_financials_screener(text, source_reference)
        result["source_type"] = source_type
        result["source_reference"] = source_reference
        return result

    return extract_financials_rule_based(text, source_type, source_reference)
