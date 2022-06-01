"""Add tables for managing installed QC Pipelines.

Revision ID: 94813db21f13
Revises: b68a8193acad
Create Date: 2022-06-01 22:17:51.632942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94813db21f13'
down_revision = 'b68a8193acad'
branch_labels = None
depends_on = None


def upgrade():
    scope = op.create_table(
        'pipeline_scope',
        sa.Column('scope', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('scope')
    )

    conn = op.get_bind()
    op.bulk_insert(
        scope,
        [{'scope': item}
         for item in ['study', 'timepoint', 'scan']]
    )

    op.create_table('study_pipeline',
    sa.Column('study', sa.String(length=32), nullable=False),
    sa.Column('pipeline_key', sa.String(), nullable=False),
    sa.Column('view', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('scope', sa.String(length=32), nullable=False),
    sa.ForeignKeyConstraint(['scope'], ['pipeline_scope.scope'], ),
    sa.ForeignKeyConstraint(['study'], ['studies.id'], ),
    sa.PrimaryKeyConstraint('study', 'pipeline_key'),
    sa.UniqueConstraint('study', 'pipeline_key')
    )


def downgrade():
    op.drop_table('study_pipeline')
    op.drop_table('pipeline_scope')
