from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from .db import Base, engine, get_session
from .models import Medicine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed_sample_data() -> None:
    sample_medicines = [
        # name, requires_prescription, controlled_level, max_daily_dosage (mg)
        ("Paracetamol", False, 0, 4000),
        ("Ibuprofen", False, 0, 2400),
        ("Amoxicillin", True, 0, 1500),
        ("Morphine", True, 2, 200),
        ("Diazepam", True, 2, 40),
    ]

    with get_session() as session:
        for name, requires_prescription, controlled_level, max_daily_dosage in sample_medicines:
            med = Medicine(
                name=name,
                requires_prescription=requires_prescription,
                controlled_level=controlled_level,
                max_daily_dosage=max_daily_dosage,
            )
            session.add(med)
        try:
            session.flush()
        except IntegrityError:
            # If already seeded, ignore duplicates
            session.rollback()


def main() -> None:
    init_db()
    seed_sample_data()
    print("Database initialized and sample medicines seeded.")


if __name__ == "__main__":
    main()

