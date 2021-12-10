"""Add a few more columns to hold Datman config settings.

Revision ID: 77bce5fefcf4
Revises: 5dc31b2f9fb4
Create Date: 2021-12-10 19:25:50.213883

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77bce5fefcf4'
down_revision = '5dc31b2f9fb4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'scantypes',
        sa.Column('qc_type', sa.String(length=64), nullable=True)
    )
    op.add_column(
        'scantypes',
        sa.Column('pha_type', sa.String(length=64), nullable=True)
    )
    op.alter_column(
        'studies',
        'is_open',
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default=sa.text('true')
    )
    op.add_column(
        'study_sites',
        sa.Column('uses_tech_notes', sa.Boolean(), nullable=True)
    )


def downgrade():
    op.drop_column('study_sites', 'uses_tech_notes')
    op.alter_column(
        'studies',
        'is_open',
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default=sa.text('true')
    )
    op.drop_column('scantypes', 'pha_type')
    op.drop_column('scantypes', 'qc_type')
