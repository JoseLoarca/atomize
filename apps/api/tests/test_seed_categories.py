import uuid
from collections.abc import Iterator
from typing import cast

import pytest
from sqlalchemy import Connection, Table, create_engine, func, select

from atomize_api.models.categories import Category
from atomize_api.seed.categories import (
    DEFAULT_CATEGORY_NAMES,
    category_id,
    seed_categories,
)

CATEGORY_TABLE = cast(Table, Category.__table__)


@pytest.fixture
def conn() -> Iterator[Connection]:
    engine = create_engine("sqlite://")
    CATEGORY_TABLE.create(engine)
    with engine.begin() as connection:
        yield connection


def _count(conn: Connection) -> int:
    return conn.execute(select(func.count()).select_from(CATEGORY_TABLE)).scalar_one()


def test_has_23_unique_categories() -> None:
    assert len(DEFAULT_CATEGORY_NAMES) == 23
    assert len(set(DEFAULT_CATEGORY_NAMES)) == 23


def test_seed_inserts_all_in_order(conn: Connection) -> None:
    assert seed_categories(conn) == 23
    t = CATEGORY_TABLE
    names = list(conn.execute(select(t.c.name).order_by(t.c.sort_order)).scalars())
    assert names == list(DEFAULT_CATEGORY_NAMES)
    orders = list(conn.execute(select(t.c.sort_order)).scalars())
    assert len(set(orders)) == 23


def test_seed_is_idempotent(conn: Connection) -> None:
    seed_categories(conn)
    assert seed_categories(conn) == 0
    assert _count(conn) == 23


def test_seed_fills_only_missing(conn: Connection) -> None:
    seed_categories(conn)
    t = CATEGORY_TABLE
    conn.execute(t.delete().where(t.c.name == "Pets"))
    assert seed_categories(conn) == 1
    assert _count(conn) == 23


def test_ids_are_stable() -> None:
    assert category_id("Groceries") == category_id("Groceries")
    assert isinstance(category_id("Gas"), uuid.UUID)
    assert category_id("Gas") != category_id("Pets")
