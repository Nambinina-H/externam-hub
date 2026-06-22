"""add email_templates signature

Bloc signature libre du modèle d'email (séparateur « -- » ajouté au rendu).

Revision ID: f3a9d27c5b18
Revises: e8c1a4f6b2d9
Create Date: 2026-06-22 16:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a9d27c5b18'
down_revision: str | None = 'e8c1a4f6b2d9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'email_templates',
        sa.Column('signature', sa.Text(), nullable=False, server_default=''),
    )


def downgrade() -> None:
    op.drop_column('email_templates', 'signature')
