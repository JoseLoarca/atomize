"""Canonical category list (SPEC.md §4 / Overview.pdf §4), seeded once by migration."""

import uuid
from typing import cast

from sqlalchemy import Connection, Table, insert, select

from atomize_api.models.categories import Category

# Order here defines `sort_order`. Gaps of 10 leave room to slot a category in later.
DEFAULT_CATEGORY_NAMES: tuple[str, ...] = (
    "Groceries",
    "Restaurants & Dining",
    "Coffee & Snacks",
    "Alcohol & Bars",
    "Transportation",
    "Gas",
    "Travel",
    "Accommodation",
    "Entertainment & Fun",
    "Shopping (General)",
    "Clothing & Accessories",
    "Electronics",
    "Health & Medical",
    "Personal Care",
    "Pets",
    "Home & Household",
    "Utilities",
    "Insurance",
    "Subscriptions",
    "Education",
    "Gifts & Donations",
    "Childcare",
    "Miscellaneous",
)

_SORT_STEP = 10
_NAMESPACE = uuid.UUID("6f1c1c1e-7a52-4a52-9d0e-5a1f0c0a7a11")


def category_id(name: str) -> uuid.UUID:
    """Deterministic id so every environment shares the same category primary keys."""
    return uuid.uuid5(_NAMESPACE, name)


def seed_categories(connection: Connection) -> int:
    """Insert any missing default categories; safe to re-run. Returns rows inserted."""
    table = cast(Table, Category.__table__)
    existing = set(connection.execute(select(table.c.name)).scalars())
    rows = [
        {"id": category_id(name), "name": name, "sort_order": (i + 1) * _SORT_STEP, "is_active": True}
        for i, name in enumerate(DEFAULT_CATEGORY_NAMES)
        if name not in existing
    ]
    if rows:
        connection.execute(insert(table), rows)
    return len(rows)
