"""Add a columns to configure on demand downloading + post download processing.

Revision ID: 442e3abe5587
Revises: c5d321b34b54
Create Date: 2020-07-20 16:43:57.435851

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '442e3abe5587'
down_revision = 'c5d321b34b54'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'study_sites',
        sa.Column(
            'download_script',
            sa.String(length=128),
            nullable=True
        )
    )
    op.add_column(
        'study_sites',
        sa.Column(
            'post_download_script',
            sa.String(length=128),
            nullable=True
        )
    )


def downgrade():
    op.drop_column('study_sites', 'post_download_script')
    op.drop_column('study_sites', 'download_script')
