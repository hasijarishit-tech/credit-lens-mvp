from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Company, User
from app.schemas import CompanyCreate, CompanyOut

router = APIRouter(prefix="/companies", tags=["companies"])


def get_owned_company(company_id: str, db: Session, current_user: User) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or company.owner_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("", response_model=CompanyOut, status_code=201)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = Company(name=payload.name, sector=payload.sector, owner_user_id=current_user.id)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(Company)
        .filter(Company.owner_user_id == current_user.id)
        .order_by(Company.created_at.desc())
        .all()
    )


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_company(company_id, db, current_user)
