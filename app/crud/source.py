# app/crud/source.py
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Source, OperatorSourceWeight


def get_sources(db: Session) -> List[Source]:
    stmt = select(Source).order_by(Source.id)
    return list(db.scalars(stmt).all())


def get_source(db: Session, source_id: int) -> Optional[Source]:
    return db.get(Source, source_id)


def get_source_by_code(db: Session, code: str) -> Optional[Source]:
    stmt = select(Source).where(Source.code == code)
    return db.scalars(stmt).first()


def create_source(db: Session, *, name: str, code: str) -> Source:
    source = Source(name=name, code=code)
    db.add(source)
    db.flush()
    return source


def update_source(
    db: Session,
    source: Source,
    *,
    name: str | None = None,
    code: str | None = None,
) -> Source:
    if name is not None:
        source.name = name
    if code is not None:
        source.code = code

    db.flush()
    return source


def set_source_operator_weights(
    db: Session,
    source: Source,
    weights: Iterable[Tuple[int, int]],
) -> Source:
    """
    Replace the complete operator and weight configuration for a source.
    """
    db.execute(
        delete(OperatorSourceWeight).where(
            OperatorSourceWeight.source_id == source.id
        )
    )

    for operator_id, weight in weights:
        row = OperatorSourceWeight(
            operator_id=operator_id,
            source_id=source.id,
            weight=weight,
        )
        db.add(row)

    db.flush()
    return source


def get_weights_for_source(db: Session, source_id: int) -> List[OperatorSourceWeight]:
    stmt = (
        select(OperatorSourceWeight)
        .where(OperatorSourceWeight.source_id == source_id)
        .order_by(OperatorSourceWeight.id)
    )
    return list(db.scalars(stmt).all())
