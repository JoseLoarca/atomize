"""seed default categories

Revision ID: seed_categories
Revises: 575b68b0f294
"""

from collections.abc import Sequence

from sqlalchemy import MetaData, Table, delete

from alembic import op
from atomize_api.seed.categories import DEFAULT_CATEGORY_NAMES, seed_categories

revision: str = "seed_categories"
down_revision: str | Sequence[str] | None = "575b68b0f294"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    seed_categories(op.get_bind())


def downgrade() -> None:
    bind = op.get_bind()
    category = Table("category", MetaData(), autoload_with=bind)
    bind.execute(delete(category).where(category.c.name.in_(DEFAULT_CATEGORY_NAMES)))
