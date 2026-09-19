from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.extraction.router import extract_financials
from app.known_companies import search_known_companies
from app.models import FinancialRecord, SourceType, User
from app.routers.companies import get_owned_company
from app.utils.records import extracted_data_shape, extraction_found_nothing, trust_label_for
from app.schemas import (
    FinancialRecordOut,
    NameSearchCandidate,
    NameSearchConfirmRequest,
    NameSearchRequest,
    NameSearchResponse,
)
from app.utils.web_fetch import WebFetchError, fetch_page_text

router = APIRouter(prefix="/name-search", tags=["name-search"])


@router.post("", response_model=NameSearchResponse)
def search(payload: NameSearchRequest):
    matches = search_known_companies(payload.query)
    return NameSearchResponse(candidates=[NameSearchCandidate(**m) for m in matches])


@router.post("/confirm", response_model=FinancialRecordOut, status_code=201)
def confirm(
    payload: NameSearchConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = get_owned_company(payload.company_id, db, current_user)

    cached = (
        db.query(FinancialRecord)
        .filter(
            FinancialRecord.company_id == company.id,
            FinancialRecord.source_reference == payload.source_reference,
        )
        .first()
    )
    if cached:
        return cached

    try:
        text = fetch_page_text(payload.source_reference)
    except WebFetchError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = extract_financials(text, source_type="name_search", source_reference=payload.source_reference)

    extracted_data = extracted_data_shape(
        result["balance_sheet"], result["income_statement"], result.get("prior_year")
    )
    if extraction_found_nothing(result["balance_sheet"], result["income_statement"]):
        raise HTTPException(
            status_code=422,
            detail="Couldn't find clean financial line items on this company's page — its "
            "layout may not match what this tool knows how to read. Please try uploading "
            "a PDF or manual entry instead.",
        )

    record = FinancialRecord(
        company_id=company.id,
        financial_year=payload.financial_year_hint or result.get("financial_year") or "Unknown",
        source_type=SourceType.name_search,
        source_reference=payload.source_reference,
        trust_label=trust_label_for(current_user),
        extracted_data=extracted_data,
        extraction_confidence=result["extraction_notes"],
        created_by_user_id=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
