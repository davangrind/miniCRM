# app/services.py
from __future__ import annotations

import random
from typing import List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.models import Operator, Contact
from app.schemas import ContactCreate
from app.crud import (
    get_or_create_lead,
    get_source,
    get_weights_for_source,
    get_operator_active_contacts_count,
    create_contact,
)


def _choose_operator_weighted(
    candidates: Sequence[Tuple[Operator, int]],
) -> Optional[Operator]:
    """
    Choose an operator at random using the configured weights.

    candidates: a sequence of (operator, weight) tuples
    """
    if not candidates:
        return None

    operators, weights = zip(*candidates)
    # Use the weighted random implementation from the standard library.
    chosen = random.choices(list(operators), weights=list(weights), k=1)[0]
    return chosen


def assign_operator_for_source(
    db: Session,
    *,
    source_id: int,
) -> Optional[Operator]:
    """
    Choose an operator for a source based on:
      operator availability (is_active)
      the active-contact limit (max_active_contacts)
      source-specific weights

    Return None when no operator is eligible.
    """
    weights = get_weights_for_source(db, source_id=source_id)

    candidates: List[Tuple[Operator, int]] = []

    for w in weights:
        operator = w.operator  # Lazy loading is acceptable for this small set.
        if operator is None:
            continue

        if not operator.is_active:
            continue

        active_count = get_operator_active_contacts_count(db, operator.id)
        if active_count >= operator.max_active_contacts:
            # The operator has reached the configured workload limit.
            continue

        candidates.append((operator, w.weight))

    if not candidates:
        return None

    return _choose_operator_weighted(candidates)


def register_contact(
    db: Session,
    data: ContactCreate,
) -> Contact:
    """
    Register an incoming contact:

    1) Find or create a lead by external_lead_id.
    2) Verify that the source exists.
    3) Select an operator according to the assignment rules.
    4) Create the contact.

    If no operator is eligible, create the contact with operator_id = None.
    """
    # 1. Lead
    lead = get_or_create_lead(db, external_id=data.external_lead_id)

    # 2. Source
    source = get_source(db, data.source_id)
    if source is None:
        # The API layer converts this into an HTTP 404 response.
        raise ValueError(f"Source {data.source_id} not found")

    # 3. Operator assignment
    operator = assign_operator_for_source(db, source_id=source.id)
    operator_id: Optional[int] = operator.id if operator is not None else None

    # 4. Contact creation
    contact = create_contact(
        db,
        lead_id=lead.id,
        source_id=source.id,
        operator_id=operator_id,
        payload=data.payload,
    )

    return contact
