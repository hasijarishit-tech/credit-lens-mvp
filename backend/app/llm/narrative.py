"""Turns already-computed ratios, scores, and anomaly flags into plain
language. Claude never sees raw statements here and never computes a
number itself — it only explains numbers the deterministic engine
(app/scoring/pipeline.py) already produced, which are passed in verbatim
so the narrative can't drift from the math.
"""
import json
from typing import Any, Dict

from app.config import settings
from app.llm.client import get_client

MSME_SYSTEM_PROMPT = """You are a plain-English credit coach for a small Indian \
business owner (MSME) who is not a finance professional. You will be given the \
company's computed credit score, ratio values, sector benchmarks, and anomaly \
flags — all already calculated by a separate ratio engine. Your only job is to \
explain them clearly and suggest concrete, specific next steps.

Rules:
- Use simple language, short sentences, no jargon without explaining it once.
- Every claim must cite an actual number from the data given — never invent or \
  round in a way that changes the meaning.
- Be specific about WHAT to do (e.g. "reduce inventory by roughly X to bring \
  inventory days closer to the sector norm of Y days"), not generic advice like \
  "improve your finances."
- Keep it to about 150-250 words.
- Do not repeat the raw JSON back at the user; write prose."""

LENDER_SYSTEM_PROMPT = """You are a credit analyst writing a short internal note \
for a lending officer at an NBFC/bank, about one MSME loan applicant. You will \
be given the company's computed credit score, ratio values, sector benchmarks, \
and anomaly flags — already calculated by a separate ratio engine.

Rules:
- Write like an analyst memo: direct, no hand-holding, no coaching tone.
- Every claim must cite an actual number from the data given.
- Lead with the headline risk view, then the 2-3 factors driving it, then any \
  anomaly flags worth underwriting attention.
- Keep it to about 120-180 words."""


def _build_data_block(
    company_name: str, sector: str, pipeline_result: Dict[str, Any]
) -> str:
    payload = {
        "company_name": company_name,
        "sector": sector,
        "composite_score": pipeline_result["composite_score"],
        "letter_grade": pipeline_result["letter_grade"],
        "bucket_scores": pipeline_result["bucket_scores"],
        "ratios": pipeline_result["ratios"],
        "sector_benchmark": pipeline_result["sector_benchmark_used"],
        "anomaly_flags": pipeline_result["anomaly_flags"],
        "non_critical_data_warnings": pipeline_result.get("issues", []),
    }
    return json.dumps(payload, indent=2, default=str)


def generate_msme_narrative(
    company_name: str, sector: str, pipeline_result: Dict[str, Any]
) -> str:
    client = get_client()
    data_block = _build_data_block(company_name, sector, pipeline_result)

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=MSME_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": data_block}],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()


def generate_lender_summary(
    company_name: str, sector: str, pipeline_result: Dict[str, Any]
) -> str:
    client = get_client()
    data_block = _build_data_block(company_name, sector, pipeline_result)

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=768,
        system=LENDER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": data_block}],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()
