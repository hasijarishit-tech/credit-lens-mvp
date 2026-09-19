"""Small shared helpers used by every financial-record intake path
(manual entry, PDF, source link, name search)."""
from typing import Any, Dict, Optional

from app.models import TrustLabel, User, UserRole


def trust_label_for(current_user: User) -> TrustLabel:
    return TrustLabel.self_reported if current_user.role == UserRole.msme else TrustLabel.verified


def extracted_data_shape(
    balance_sheet: Dict[str, Any],
    income_statement: Dict[str, Any],
    prior_year: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "balance_sheet": balance_sheet,
        "income_statement": income_statement,
        "prior_year": prior_year,
    }


def extraction_found_nothing(balance_sheet: Dict[str, Any], income_statement: Dict[str, Any]) -> bool:
    """True when extraction defaulted every single field to 0 — i.e. found no
    recognizable financial line items at all. This is the exact case the spec
    calls out: fail loudly and point to PDF upload / manual entry, rather than
    silently creating a record full of zeroes that would produce a
    meaningless score."""
    total = sum(abs(v) for v in balance_sheet.values()) + sum(abs(v) for v in income_statement.values())
    return total == 0
