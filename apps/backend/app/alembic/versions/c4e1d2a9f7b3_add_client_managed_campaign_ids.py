"""add client managed_campaign_ids

Revision ID: c4e1d2a9f7b3
Revises: 18fc44068ccd
Create Date: 2026-06-21 10:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e1d2a9f7b3'
down_revision: str | None = '18fc44068ccd'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Allowlist d'ids de campagnes gérées par l'agence (incluses dans le rapport).
    # Nullable pour ne pas casser les lignes existantes ; l'ORM applique [] par défaut.
    op.add_column('clients', sa.Column('managed_campaign_ids', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('clients', 'managed_campaign_ids')
