"""drop client conversion_goal

Le « résultat » suit désormais l'objectif de chaque campagne (rapport par campagne),
donc l'objectif de conversion global par client n'a plus de raison d'être.

Revision ID: d7b2f1a3c9e4
Revises: c4e1d2a9f7b3
Create Date: 2026-06-21 11:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7b2f1a3c9e4'
down_revision: str | None = 'c4e1d2a9f7b3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column('clients', 'conversion_goal')


def downgrade() -> None:
    op.add_column(
        'clients',
        sa.Column('conversion_goal', sa.String(length=50), server_default='purchase', nullable=False),
    )
