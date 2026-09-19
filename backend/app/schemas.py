from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import Sector, SourceType, TrustLabel, UserRole


class SignupRequest(BaseModel):
    name: str
    org_name: str = Field(..., description="Business name (MSME) or institution name (lender)")
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    org_name: str
    email: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Companies ----


class CompanyCreate(BaseModel):
    name: str
    sector: Sector


class CompanyOut(BaseModel):
    id: str
    name: str
    sector: Sector
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Financial records ----


class BalanceSheetData(BaseModel):
    cash_and_equivalents: float = 0
    receivables: float = 0
    inventory: float = 0
    other_current_assets: float = 0
    fixed_assets: float = 0
    current_liabilities: float = 0
    payables: float = 0
    long_term_debt: float = 0
    equity: float = 0


class IncomeStatementData(BaseModel):
    revenue: float = 0
    cogs: float = 0
    operating_expenses: float = 0
    depreciation: float = 0
    interest_expense: float = 0
    net_income: float = 0


class FinancialYearData(BaseModel):
    balance_sheet: BalanceSheetData
    income_statement: IncomeStatementData


class ManualEntryRequest(BaseModel):
    financial_year: str
    balance_sheet: BalanceSheetData
    income_statement: IncomeStatementData
    prior_year: Optional[FinancialYearData] = None


class LinkIntakeRequest(BaseModel):
    url: str
    financial_year_hint: Optional[str] = None


class FinancialRecordUpdate(BaseModel):
    """Corrections from the Extraction Review screen — any subset of fields."""

    financial_year: Optional[str] = None
    balance_sheet: Optional[BalanceSheetData] = None
    income_statement: Optional[IncomeStatementData] = None
    prior_year: Optional[FinancialYearData] = None


class FinancialRecordOut(BaseModel):
    id: str
    company_id: str
    financial_year: str
    source_type: SourceType
    source_reference: Optional[str]
    trust_label: TrustLabel
    extracted_data: Dict[str, Any]
    extraction_confidence: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class ScoreOut(BaseModel):
    id: str
    financial_record_id: str
    composite_score: float
    letter_grade: str
    ratios: Dict[str, Any]
    bucket_scores: Dict[str, Any]
    anomaly_flags: List[Dict[str, Any]]
    derived_cash_flow: Optional[Dict[str, Any]]
    narrative_text: Optional[str]
    lender_summary_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScoreWithIssues(BaseModel):
    status: str  # "scored" | "needs_review"
    issues: List[Dict[str, str]] = []
    score: Optional[ScoreOut] = None


# ---- Scenario Q&A ----


class ScenarioRequest(BaseModel):
    preset: str


class ScenarioResult(BaseModel):
    status: str
    composite_score: Optional[float] = None
    letter_grade: Optional[str] = None
    ratios: Optional[Dict[str, Any]] = None


class ScenarioResponse(BaseModel):
    preset: str
    label: str
    explanation: str
    before: ScenarioResult
    after: ScenarioResult


# ---- Name search ----


class NameSearchRequest(BaseModel):
    query: str


class NameSearchCandidate(BaseModel):
    name: str
    sector: str
    location: str
    listing: str
    source_reference: str


class NameSearchResponse(BaseModel):
    candidates: List[NameSearchCandidate]


class NameSearchConfirmRequest(BaseModel):
    company_id: str
    source_reference: str
    financial_year_hint: Optional[str] = None
