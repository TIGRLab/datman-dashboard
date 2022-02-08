"""Add a column to RedcapConfig to track event name to event ID mappings.

Revision ID: b68a8193acad
Revises: 77bce5fefcf4
Create Date: 2022-02-08 21:40:46.276639

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b68a8193acad'
down_revision = '77bce5fefcf4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'redcap_config',
        sa.Column(
            'event_ids',
            postgresql.JSONB(astext_type=sa.Text()), nullable=True
        )
    )


def downgrade():
    op.drop_column('redcap_config', 'event_ids')
