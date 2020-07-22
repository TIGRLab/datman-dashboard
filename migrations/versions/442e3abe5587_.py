"""Add a column to indicate that sessions should be downloaded as soon as
a redcap form comes in (and indicate there may be further pipelines to run).

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
            'auto_download',
            sa.Boolean(),
            server_default='False',
        )
    )


def downgrade():
    op.drop_column('study_sites', 'auto_download')
