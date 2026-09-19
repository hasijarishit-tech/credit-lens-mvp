"""Single entry point the API calls for narrative generation. Picks Claude
when a key is configured, templated sentences otherwise."""
from typing import Any, Dict

from app.extraction.router import is_llm_configured
from app.narrative.template_narrative import (
    generate_lender_summary_template,
    generate_msme_narrative_template,
)


def generate_msme_narrative(company_name: str, sector: str, pipeline_result: Dict[str, Any]) -> str:
    if is_llm_configured():
        from app.llm.narrative import generate_msme_narrative as generate_with_claude

        return generate_with_claude(company_name, sector, pipeline_result)
    return generate_msme_narrative_template(company_name, sector, pipeline_result)


def generate_lender_summary(company_name: str, sector: str, pipeline_result: Dict[str, Any]) -> str:
    if is_llm_configured():
        from app.llm.narrative import generate_lender_summary as generate_with_claude

        return generate_with_claude(company_name, sector, pipeline_result)
    return generate_lender_summary_template(company_name, sector, pipeline_result)
