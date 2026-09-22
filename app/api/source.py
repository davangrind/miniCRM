# app/api/source.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app import crud
from app.schemas import (
    SourceCreate,
    SourceUpdate,
    SourceOut,
    SourceWithOperators,
    SourceOperatorWeightSet,
    SourceOperatorWeightOut,
)
from app.models import Source

router = APIRouter()


def _build_source_with_operators(source: Source) -> SourceWithOperators:
    operators = [
        SourceOperatorWeightOut.model_validate(w)
        for w in source.operator_weights
    ]
    return SourceWithOperators(
        id=source.id,
        name=source.name,
        code=source.code,
        created_at=source.created_at,
        operators=operators,
    )


@router.post(
    "/",
    response_model=SourceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    data: SourceCreate,
    db: Session = Depends(get_db),
) -> SourceOut:
    source = crud.create_source(db, name=data.name, code=data.code)
    db.commit()
    db.refresh(source)
    return SourceOut.model_validate(source)


@router.get(
    "/",
    response_model=List[SourceWithOperators],
)
def list_sources(
    db: Session = Depends(get_db),
) -> List[SourceWithOperators]:
    sources = crud.get_sources(db)
    return [_build_source_with_operators(src) for src in sources]


@router.put(
    "/{source_id}/operators",
    response_model=SourceWithOperators,
)
def set_source_operators(
    source_id: int,
    data: SourceOperatorWeightSet,
    db: Session = Depends(get_db),
) -> SourceWithOperators:
    source = crud.get_source(db, source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )

    # Verify that every configured operator exists.
    for item in data.operators:
        op = crud.get_operator(db, item.operator_id)
        if op is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operator {item.operator_id} not found",
            )

    weights = [(item.operator_id, item.weight) for item in data.operators]
    source = crud.set_source_operator_weights(db, source, weights=weights)
    db.commit()
    db.refresh(source)
    # Reload the source and its relationships.
    source = crud.get_source(db, source_id) or source
    return _build_source_with_operators(source)


@router.patch(
    "/{source_id}",
    response_model=SourceOut,
)
def update_source(
    source_id: int,
    data: SourceUpdate,
    db: Session = Depends(get_db),
) -> SourceOut:
    source = crud.get_source(db, source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )

    source = crud.update_source(
        db,
        source,
        name=data.name,
        code=data.code,
    )
    db.commit()
    db.refresh(source)
    return SourceOut.model_validate(source)
