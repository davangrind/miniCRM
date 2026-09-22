# app/api/operator.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app import crud
from app.schemas import (
    OperatorCreate,
    OperatorUpdate,
    OperatorOut,
)

router = APIRouter()


@router.post(
    "/",
    response_model=OperatorOut,
    status_code=status.HTTP_201_CREATED,
)
def create_operator(
    data: OperatorCreate,
    db: Session = Depends(get_db),
) -> OperatorOut:
    operator = crud.create_operator(
        db,
        name=data.name,
        is_active=data.is_active,
        max_active_contacts=data.max_active_contacts,
    )
    db.commit()
    db.refresh(operator)
    return OperatorOut.model_validate(operator)


@router.get(
    "/",
    response_model=List[OperatorOut],
)
def list_operators(
    db: Session = Depends(get_db),
) -> List[OperatorOut]:
    operators = crud.get_operators(db)
    return [OperatorOut.model_validate(op) for op in operators]


@router.patch(
    "/{operator_id}",
    response_model=OperatorOut,
)
def update_operator(
    operator_id: int,
    data: OperatorUpdate,
    db: Session = Depends(get_db),
) -> OperatorOut:
    operator = crud.get_operator(db, operator_id)
    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found",
        )

    operator = crud.update_operator(
        db,
        operator,
        name=data.name,
        is_active=data.is_active,
        max_active_contacts=data.max_active_contacts,
    )
    db.commit()
    db.refresh(operator)
    return OperatorOut.model_validate(operator)
