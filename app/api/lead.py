# app/api/lead.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app import crud
from app.schemas import LeadOut, LeadWithContacts

router = APIRouter()


@router.get(
    "/",
    response_model=List[LeadOut],
)
def list_leads(
    db: Session = Depends(get_db),
) -> List[LeadOut]:
    leads = crud.get_leads(db)
    return [LeadOut.model_validate(lead) for lead in leads]


@router.get(
    "/{lead_id}",
    response_model=LeadWithContacts,
)
def get_lead_with_contacts(
    lead_id: int,
    db: Session = Depends(get_db),
) -> LeadWithContacts:
    lead = crud.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    contacts = crud.get_contacts_for_lead(db, lead.id)

    return LeadWithContacts(
        id=lead.id,
        external_id=lead.external_id,
        created_at=lead.created_at,
        contacts=contacts,
    )
