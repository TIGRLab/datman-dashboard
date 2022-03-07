"""Update models to allow dynamic QC page generation.

Revision ID: 4ab18b9516c9
Revises: b68a8193acad
Create Date: 2022-03-07 14:26:24.512674

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ab18b9516c9'
down_revision = 'b68a8193acad'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scans', sa.Column('length', sa.String(length=10), nullable=True))
    op.add_column('sessions', sa.Column('tech_notes', sa.String(length=1028), nullable=True))
    op.drop_column('timepoints', 'static_page')
    op.drop_column('timepoints', 'last_qc_generated')


def downgrade():
    op.add_column('timepoints', sa.Column('last_qc_generated', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('timepoints', sa.Column('static_page', sa.VARCHAR(length=1028), autoincrement=False, nullable=True))
    op.drop_column('sessions', 'tech_notes')
    op.drop_column('scans', 'length')
