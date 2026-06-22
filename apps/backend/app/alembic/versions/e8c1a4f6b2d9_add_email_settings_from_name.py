"""add email_settings from_name

Nom d'expéditeur (réutilisable comme variable {{expediteur}} dans les modèles).

Revision ID: e8c1a4f6b2d9
Revises: d7b2f1a3c9e4
Create Date: 2026-06-22 14:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8c1a4f6b2d9'
down_revision: str | None = 'd7b2f1a3c9e4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('email_settings', sa.Column('from_name', sa.String(length=150), nullable=True))


def downgrade() -> None:
    op.drop_column('email_settings', 'from_name')
