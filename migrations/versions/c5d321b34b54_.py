"""Add KCNI identifiers columns to timepoints and sessions

Revision ID: c5d321b34b54
Revises: 2cb6998f5e9c
Create Date: 2020-03-05 17:11:45.958726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5d321b34b54'
down_revision = '2cb6998f5e9c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sessions', sa.Column('kcni_name', sa.String(length=48), nullable=True))
    op.add_column('timepoints', sa.Column('kcni_name', sa.String(length=48), nullable=True))


def downgrade():
    op.drop_column('timepoints', 'kcni_name')
    op.drop_column('sessions', 'kcni_name')
