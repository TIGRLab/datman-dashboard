"""Add XNAT settings columns to StudySite table.

Revision ID: 5dc31b2f9fb4
Revises: 4a842feae63a
Create Date: 2021-12-03 18:47:00.540128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5dc31b2f9fb4'
down_revision = '4a842feae63a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'study_sites',
        sa.Column('xnat_archive', sa.String(length=32), nullable=True)
    )
    op.add_column(
        'study_sites',
        sa.Column(
            'xnat_convention',
            sa.String(length=10),
            nullable=True,
            server_default='KCNI'
        )
    )
    op.add_column(
        'study_sites',
        sa.Column('xnat_credentials', sa.String(length=128), nullable=True)
    )
    op.add_column(
        'study_sites',
        sa.Column('xnat_url', sa.String(length=128), nullable=True)
    )


def downgrade():
    op.drop_column('study_sites', 'xnat_url')
    op.drop_column('study_sites', 'xnat_credentials')
    op.drop_column('study_sites', 'xnat_convention')
    op.drop_column('study_sites', 'xnat_archive')
