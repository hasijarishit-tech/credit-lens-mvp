from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.extraction.router import extract_financials
from app.models import (
    Company,
    FinancialRecord,
    Score,
    SourceType,
    TrustLabel,
    User,
    UserRole,
)
from app.narrative.router import generate_lender_summary, generate_msme_narrative
from app.routers.companies import get_owned_company
from app.schemas import (
    FinancialRecordOut,
    FinancialRecordUpdate,
    LinkIntakeRequest,
    ManualEntryRequest,
    ScoreOut,
    ScoreWithIssues,
)
from app.scoring.pipeline import run_pipeline
from app.utils.pdf_text import PdfTextExtractionError, extract_text_from_pdf
from app.utils.records import extracted_data_shape, extraction_found_nothing, trust_label_for
from app.utils.web_fetch import WebFetchError, fetch_page_text

router = APIRouter(tags=["financial-records"])


def get_owned_financial_record(record_id: str, db: Session, current_user: User) -> FinancialRecord:
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    if not record or record.company.owner_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Financial record not found")
    return record


@router.get("/companies/{company_id}/financial-records", response_model=list[FinancialRecordOut])
def list_financial_records(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = get_owned_company(company_id, db, current_user)
    return (
        db.query(FinancialRecord)
        .filter(FinancialRecord.company_id == company.id)
        .order_by(FinancialRecord.created_at.desc())
        .all()
    )


@router.post(
    "/companies/{company_id}/financial-records/manual",
    response_model=FinancialRecordOut,
    status_code=201,
)
def create_manual_entry(
    company_id: str,
    payload: ManualEntryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = get_owned_company(company_id, db, current_user)

    extracted_data = extracted_data_shape(
        payload.balance_sheet.model_dump(),
        payload.income_statement.model_dump(),
        payload.prior_year.model_dump() if payload.prior_year else None,
    )

    record = FinancialRecord(
        company_id=company.id,
        financial_year=payload.financial_year,
        source_type=SourceType.manual_entry,
        source_reference=None,
        trust_label=trust_label_for(current_user),
        extracted_data=extracted_data,
        extraction_confidence={"method": "manual_entry", "overall_confidence": "high", "warnings": []},
        created_by_user_id=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/companies/{company_id}/financial-records/pdf",
    response_model=FinancialRecordOut,
    status_code=201,
)
def create_from_pdf(
    company_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = get_owned_company(company_id, db, current_user)

    file_bytes = file.file.read()
    try:
        text = extract_text_from_pdf(file_bytes)
    except PdfTextExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = extract_financials(text, source_type="pdf_upload", source_reference=file.filename or "uploaded.pdf")

    extracted_data = extracted_data_shape(
        result["balance_sheet"], result["income_statement"], result.get("prior_year")
    )
    if extraction_found_nothing(result["balance_sheet"], result["income_statement"]):
        raise HTTPException(
            status_code=422,
            detail="Couldn't find any recognizable financial figures in this PDF. "
            "Please try manual entry instead.",
        )

    record = FinancialRecord(
        company_id=company.id,
        financial_year=result.get("financial_year") or "Unknown",
        source_type=SourceType.pdf_upload,
        source_reference=file.filename,
        trust_label=trust_label_for(current_user),
        extracted_data=extracted_data,
        extraction_confidence=result["extraction_notes"],
        created_by_user_id=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/companies/{company_id}/financial-records/link",
    response_model=FinancialRecordOut,
    status_code=201,
)
def create_from_link(
    company_id: str,
    payload: LinkIntakeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = get_owned_company(company_id, db, current_user)

    cached = (
        db.query(FinancialRecord)
        .filter(
            FinancialRecord.company_id == company.id,
            FinancialRecord.source_reference == payload.url,
        )
        .first()
    )
    if cached:
        return cached

    try:
        text = fetch_page_text(payload.url)
    except WebFetchError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = extract_financials(text, source_type="source_link", source_reference=payload.url)

    extracted_data = extracted_data_shape(
        result["balance_sheet"], result["income_statement"], result.get("prior_year")
    )
    if extraction_found_nothing(result["balance_sheet"], result["income_statement"]):
        raise HTTPException(
            status_code=422,
            detail="Couldn't find clean financial line items on this page — its layout "
            "may not match what this tool knows how to read. Please try uploading a "
            "PDF or manual entry instead.",
        )

    record = FinancialRecord(
        company_id=company.id,
        financial_year=payload.financial_year_hint or result.get("financial_year") or "Unknown",
        source_type=SourceType.source_link,
        source_reference=payload.url,
        trust_label=trust_label_for(current_user),
        extracted_data=extracted_data,
        extraction_confidence=result["extraction_notes"],
        created_by_user_id=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/financial-records/{record_id}", response_model=FinancialRecordOut)
def update_financial_record(
    record_id: str,
    payload: FinancialRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = get_owned_financial_record(record_id, db, current_user)

    if payload.financial_year is not None:
        record.financial_year = payload.financial_year
    if payload.balance_sheet is not None:
        record.extracted_data["balance_sheet"] = payload.balance_sheet.model_dump()
    if payload.income_statement is not None:
        record.extracted_data["income_statement"] = payload.income_statement.model_dump()
    if payload.prior_year is not None:
        record.extracted_data["prior_year"] = payload.prior_year.model_dump()

    # SQLAlchemy doesn't auto-detect in-place mutation of a JSON column's dict
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(record, "extracted_data")
    db.commit()
    db.refresh(record)
    return record


@router.get("/financial-records/{record_id}", response_model=FinancialRecordOut)
def get_financial_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_financial_record(record_id, db, current_user)


@router.get("/financial-records/{record_id}/score", response_model=Optional[ScoreOut])
def get_score(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the already-computed score, or null if this record hasn't
    been scored yet (POST /score to compute it)."""
    record = get_owned_financial_record(record_id, db, current_user)
    return record.score


@router.post("/financial-records/{record_id}/score", response_model=ScoreWithIssues)
def score_financial_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = get_owned_financial_record(record_id, db, current_user)
    company = record.company

    result = run_pipeline(record.extracted_data, sector=company.sector.value)

    if result["status"] == "needs_review":
        return ScoreWithIssues(status="needs_review", issues=result["issues"])

    msme_narrative = generate_msme_narrative(company.name, company.sector.value, result)
    lender_summary = generate_lender_summary(company.name, company.sector.value, result)

    score = record.score
    if score is None:
        score = Score(financial_record_id=record.id)
        db.add(score)

    score.composite_score = result["composite_score"]
    score.letter_grade = result["letter_grade"]
    score.ratios = result["ratios"]
    score.bucket_scores = result["bucket_scores"]
    score.anomaly_flags = result["anomaly_flags"]
    score.derived_cash_flow = result.get("cash_flow")
    score.narrative_text = msme_narrative
    score.lender_summary_text = lender_summary

    db.commit()
    db.refresh(score)

    return ScoreWithIssues(status="scored", issues=result.get("issues", []), score=ScoreOut.model_validate(score))
