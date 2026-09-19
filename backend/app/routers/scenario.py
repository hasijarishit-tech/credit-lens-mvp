from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Company, User, UserRole
from app.routers.companies import get_owned_company
from app.schemas import ScenarioRequest, ScenarioResponse, ScenarioResult
from app.scoring.preset_scenarios import PRESET_SCENARIOS, apply_preset_scenario

router = APIRouter(prefix="/companies", tags=["scenario"])


def _to_result(pipeline_result: dict) -> ScenarioResult:
    if pipeline_result["status"] != "scored":
        return ScenarioResult(status=pipeline_result["status"])
    return ScenarioResult(
        status="scored",
        composite_score=pipeline_result["composite_score"],
        letter_grade=pipeline_result["letter_grade"],
        ratios=pipeline_result["ratios"],
    )


@router.post("/{company_id}/scenario", response_model=ScenarioResponse)
def run_scenario(
    company_id: str,
    payload: ScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.lender:
        raise HTTPException(status_code=403, detail="Scenario Q&A is a lender-view feature")

    company: Company = get_owned_company(company_id, db, current_user)
    if not company.financial_records:
        raise HTTPException(status_code=400, detail="This company has no financial data yet")

    if payload.preset not in PRESET_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown preset. Choose one of: {', '.join(PRESET_SCENARIOS.keys())}",
        )

    latest_record = max(company.financial_records, key=lambda r: r.created_at)
    result = apply_preset_scenario(latest_record.extracted_data, company.sector.value, payload.preset)

    return ScenarioResponse(
        preset=result["preset"],
        label=result["label"],
        explanation=result["explanation"],
        before=_to_result(result["before"]),
        after=_to_result(result["after"]),
    )
