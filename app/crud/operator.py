# app/crud/operator.py
from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Operator, Contact, ContactStatus


def get_operators(db: Session) -> List[Operator]:
    stmt = select(Operator).order_by(Operator.id)
    return list(db.scalars(stmt).all())


def get_operator(db: Session, operator_id: int) -> Optional[Operator]:
    return db.get(Operator, operator_id)


def create_operator(
    db: Session,
    *,
    name: str,
    is_active: bool,
    max_active_contacts: int,
) -> Operator:
    operator = Operator(
        name=name,
        is_active=is_active,
        max_active_contacts=max_active_contacts,
    )
    db.add(operator)
    db.flush()
    return operator


def update_operator(
    db: Session,
    operator: Operator,
    *,
    name: str | None = None,
    is_active: bool | None = None,
    max_active_contacts: int | None = None,
) -> Operator:
    if name is not None:
        operator.name = name
    if is_active is not None:
        operator.is_active = is_active
    if max_active_contacts is not None:
        operator.max_active_contacts = max_active_contacts

    db.flush()
    return operator


def get_operator_active_contacts_count(db: Session, operator_id: int) -> int:
    """
    An operator's workload is the number of open contacts.
    """
    stmt = (
        select(func.count(Contact.id))
        .where(
            Contact.operator_id == operator_id,
            Contact.status == ContactStatus.OPEN,
        )
    )
    return db.scalar(stmt) or 0


def get_operator_stats_rows(db: Session) -> List[Tuple[int, str, int, int]]:
    """
    Return raw operator statistics rows:
    (operator_id, operator_name, total_contacts, open_contacts)
    """
    total_contacts_subq = (
        select(
            Contact.operator_id.label("op_id"),
            func.count(Contact.id).label("total_contacts"),
        )
        .group_by(Contact.operator_id)
        .subquery()
    )

    open_contacts_subq = (
        select(
            Contact.operator_id.label("op_id"),
            func.count(Contact.id).label("open_contacts"),
        )
        .where(Contact.status == ContactStatus.OPEN)
        .group_by(Contact.operator_id)
        .subquery()
    )

    stmt = (
        select(
            Operator.id,
            Operator.name,
            func.coalesce(total_contacts_subq.c.total_contacts, 0),
            func.coalesce(open_contacts_subq.c.open_contacts, 0),
        )
        .outerjoin(
            total_contacts_subq,
            total_contacts_subq.c.op_id == Operator.id,
        )
        .outerjoin(
            open_contacts_subq,
            open_contacts_subq.c.op_id == Operator.id,
        )
        .order_by(Operator.id)
    )

    rows = db.execute(stmt).all()
    # each row: (operator_id, operator_name, total_contacts, open_contacts)
    return rows
