"""add audit_logs.changes

Diff champ par champ (avant/après) pour les modifications d'entités clés.

Revision ID: b7d3f1928c4a
Revises: a1b2c3d4e5f6
Create Date: 2026-06-22 19:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d3f1928c4a'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('audit_logs', sa.Column('changes', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('audit_logs', 'changes')
