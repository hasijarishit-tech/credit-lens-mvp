import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    msme = "msme"
    lender = "lender"


class SourceType(str, enum.Enum):
    pdf_upload = "pdf_upload"
    manual_entry = "manual_entry"
    source_link = "source_link"
    name_search = "name_search"


class TrustLabel(str, enum.Enum):
    self_reported = "self_reported"
    verified = "verified"


class Sector(str, enum.Enum):
    manufacturing = "Manufacturing"
    trading = "Trading"
    services = "Services"
    construction = "Construction"
    agriculture_adjacent = "Agriculture-adjacent"


class User(Base):
    """An MSME owner or a lender analyst. `org_name` holds the business name
    for MSME users and the institution name for lender users."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    org_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    companies = relationship("Company", back_populates="owner")


class Company(Base):
    """One MSME being scored. For an MSME user this is their own business;
    for a lender user this is one of the applicants in their portfolio."""

    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    sector = Column(Enum(Sector), nullable=False)
    owner_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="companies")
    financial_records = relationship(
        "FinancialRecord", back_populates="company", cascade="all, delete-orphan"
    )


class FinancialRecord(Base):
    """One year of extracted balance sheet + income statement data for a
    company, tagged with how it was collected and how trustworthy it is."""

    __tablename__ = "financial_records"

    id = Column(String, primary_key=True, default=gen_id)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    financial_year = Column(String, nullable=False)

    source_type = Column(Enum(SourceType), nullable=False)
    source_reference = Column(String, nullable=True)
    trust_label = Column(Enum(TrustLabel), nullable=False)

    # Full extracted JSON payload matching the schema in the project spec:
    # balance_sheet, income_statement, prior_year, extraction confidence notes.
    extracted_data = Column(JSON, nullable=True)
    extraction_confidence = Column(JSON, nullable=True)

    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="financial_records")
    score = relationship(
        "Score", back_populates="financial_record", uselist=False, cascade="all, delete-orphan"
    )


class Score(Base):
    """The computed result for one financial record: ratios, composite
    score, letter grade, anomaly flags, and cached AI narrative."""

    __tablename__ = "scores"

    id = Column(String, primary_key=True, default=gen_id)
    financial_record_id = Column(
        String, ForeignKey("financial_records.id"), unique=True, nullable=False
    )

    composite_score = Column(Float, nullable=False)
    letter_grade = Column(String, nullable=False)

    ratios = Column(JSON, nullable=False)  # bucket -> {ratio_name: value}
    bucket_scores = Column(JSON, nullable=False)  # bucket -> normalized score
    anomaly_flags = Column(JSON, nullable=False)  # list of {flag, detail}
    derived_cash_flow = Column(JSON, nullable=True)

    narrative_text = Column(Text, nullable=True)  # MSME-facing plain-English coaching
    lender_summary_text = Column(Text, nullable=True)  # lender-facing analyst note

    created_at = Column(DateTime, default=datetime.utcnow)

    financial_record = relationship("FinancialRecord", back_populates="score")
