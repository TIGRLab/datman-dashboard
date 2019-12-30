"""Initialize the dashboard schema from a blank database

This version will go from a totally empty database (e.g. one just made with
createdb dashboard) to one containing the full dashboard schema.

Revision ID: 2cb6998f5e9c
Revises:
Create Date: 2019-12-19 13:39:12.312265

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2cb6998f5e9c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('analyses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('description', sa.String(length=4096), nullable=False),
    sa.Column('software', sa.String(length=4096), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('redcap_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('record', sa.String(length=256), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=1024), nullable=False),
    sa.Column('instrument', sa.String(length=1024), nullable=False),
    sa.Column('entry_date', sa.Date(), nullable=False),
    sa.Column('redcap_user', sa.Integer(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('redcap_version', sa.String(length=10), nullable=True, server_default='7.4.2'),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('record', 'project_id', 'url', 'event_id', 'entry_date', name='redcap_records_unique_record_idx')
    )
    op.create_table('scantypes',
    sa.Column('tag', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('tag')
    )
    op.create_table('sites',
    sa.Column('name', sa.String(length=32), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('studies',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=1024), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('read_me', sa.Text(), nullable=True),
    sa.Column('is_open', sa.Boolean(), nullable=True, server_default='true'),
    sa.Column('email_on_trigger', sa.Boolean(), nullable=True, server_default='False')
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(length=64), nullable=False),
    sa.Column('last_name', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=256), nullable=True),
    sa.Column('position', sa.String(length=64), nullable=True),
    sa.Column('institution', sa.String(length=128), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('ext', sa.String(length=10), nullable=True),
    sa.Column('alt_phone', sa.String(length=20), nullable=True),
    sa.Column('alt_ext', sa.String(length=10), nullable=True),
    sa.Column('username', sa.String(length=70), nullable=True),
    sa.Column('picture', sa.String(length=2048), nullable=True),
    sa.Column('dashboard_admin', sa.Boolean(), nullable=True, server_default='false'),
    sa.Column('account_active', sa.Boolean(), nullable=True, server_default='false'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('account_requests',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('metrictypes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('scantype', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['scantype'], ['scantypes.tag'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('study_scantypes',
    sa.Column('study', sa.String(length=32), nullable=False),
    sa.Column('scantype', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['scantype'], ['scantypes.tag'], ),
    sa.ForeignKeyConstraint(['study'], ['studies.id'], ),
    sa.UniqueConstraint('study', 'scantype')
    )
    op.create_table('study_sites',
    sa.Column('study', sa.String(length=32), nullable=False),
    sa.Column('site', sa.String(length=32), nullable=False),
    sa.Column('uses_redcap', sa.Boolean(), nullable=True, server_default='false'),
    sa.Column('code', sa.String(length=32), nullable=True),
    sa.ForeignKeyConstraint(['site'], ['sites.name'], ),
    sa.ForeignKeyConstraint(['study'], ['studies.id'], ),
    sa.UniqueConstraint('study', 'site')
    )
    op.create_table('study_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('study', sa.String(length=32), nullable=False),
    sa.Column('site', sa.String(length=32), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='false'),
    sa.Column('primary_contact', sa.Boolean(), nullable=True, server_default='false'),
    sa.Column('kimel_contact', sa.Boolean(), nullable=True, server_default='false'),
    sa.Column('study_ra', sa.Boolean(), nullable=True, server_default='false'),
    sa.Column('does_qc', sa.Boolean(), nullable=True, server_default='false'),
    sa.ForeignKeyConstraint(['study', 'site'], ['study_sites.study', 'study_sites.site'],),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'],),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('study', 'site', 'user_id')
    )
    op.create_table('timepoints',
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('site', sa.String(length=32), nullable=False),
    sa.Column('is_phantom', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('last_qc_generated', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('static_page', sa.String(length=1028), nullable=True),
    sa.Column('bids_name', sa.Text(), nullable=True),
    sa.Column('bids_sess', sa.String(length=48), nullable=True),
    sa.Column('header_diffs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['site'], ['sites.name'], ),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('alt_study_codes',
    sa.Column('study', sa.String(length=32), nullable=False),
    sa.Column('site', sa.String(length=32), nullable=False),
    sa.Column('code', sa.String(length=32), nullable=False),
    sa.ForeignKeyConstraint(['study', 'site'], ['study_sites.study', 'study_sites.site'], ),
    )
    op.create_table('gold_standards',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('study', sa.String(length=32), nullable=False),
    sa.Column('site', sa.String(length=32), nullable=False),
    sa.Column('scantype', sa.String(length=64), nullable=False),
    sa.Column('added', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    sa.Column('json_path', sa.String(length=1028), nullable=True),
    sa.Column('contents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['study', 'scantype'], ['study_scantypes.study', 'study_scantypes.scantype'], ),
    sa.ForeignKeyConstraint(['study', 'site'], ['study_sites.study', 'study_sites.site'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('json_path', 'contents')
    )
    op.create_table('incidental_findings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('timepoint_id', sa.String(length=64), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('date_reported', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    sa.ForeignKeyConstraint(['timepoint_id'], ['timepoints.name'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sessions',
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('num', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('signed_off', sa.Boolean(), nullable=True, server_default='false'),
    sa.Column('reviewer', sa.Integer(), nullable=True),
    sa.Column('review_date', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    sa.ForeignKeyConstraint(['name'], ['timepoints.name'], ),
    sa.ForeignKeyConstraint(['reviewer'], ['users.id'], ),
    sa.PrimaryKeyConstraint('name', 'num')
    )
    op.create_table('study_timepoints',
    sa.Column('study', sa.String(length=32), nullable=False),
    sa.Column('timepoint', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['study'], ['studies.id'], ),
    sa.ForeignKeyConstraint(['timepoint'], ['timepoints.name'], ),
    sa.UniqueConstraint('study', 'timepoint')
    )
    op.create_table('timepoint_comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timepoint', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('comment_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    sa.Column('comment', sa.Text(), nullable=False),
    sa.Column('modified', sa.Boolean(), nullable=False, server_default='false'),
    sa.ForeignKeyConstraint(['timepoint'], ['timepoints.name'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('empty_sessions',
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('num', sa.Integer(), nullable=False),
    sa.Column('comment', sa.String(length=2048), nullable=False),
    sa.Column('reviewer', sa.Integer(), nullable=False),
    sa.Column('date_added', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    sa.ForeignKeyConstraint(['name', 'num'], ['sessions.name', 'sessions.num'], ),
    sa.ForeignKeyConstraint(['reviewer'], ['users.id'], ),
    sa.PrimaryKeyConstraint('name', 'num')
    )
    op.create_table('scans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('timepoint', sa.String(length=64), nullable=False),
    sa.Column('session', sa.Integer(), nullable=False),
    sa.Column('series', sa.Integer(), nullable=False),
    sa.Column('tag', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=128), nullable=True),
    sa.Column('bids_name', sa.Text(), nullable=True),
    sa.Column('conversion_errors', sa.Text(), nullable=True),
    sa.Column('json_path', sa.String(length=1028), nullable=True),
    sa.Column('json_contents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('json_created', sa.DateTime(timezone=True), nullable=True),
    sa.Column('source_data', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['source_data'], ['scans.id'], ),
    sa.ForeignKeyConstraint(['tag'], ['scantypes.tag'], ),
    sa.ForeignKeyConstraint(['timepoint', 'session'], ['sessions.name', 'sessions.num'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('session_redcap',
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('num', sa.Integer(), nullable=False),
    sa.Column('record_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['name', 'num'], ['sessions.name', 'sessions.num'], ),
    sa.ForeignKeyConstraint(['record_id'], ['redcap_records.id'], ),
    sa.PrimaryKeyConstraint('name', 'num')
    )
    op.create_table('session_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timepoint', sa.String(length=64), nullable=False),
    sa.Column('repeat', sa.Integer(), nullable=False),
    sa.Column('task_fname', sa.String(length=256), nullable=False),
    sa.Column('task_file_path', sa.String(length=2048), nullable=False),
    sa.ForeignKeyConstraint(['timepoint', 'repeat'], ['sessions.name', 'sessions.num'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('task_file_path')
    )
    op.create_table('analysis_comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scan_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('analysis_id', sa.Integer(), nullable=False),
    sa.Column('excluded', sa.Boolean(), nullable=True, server_default='false'),
    sa.Column('comment', sa.String(length=4096), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
    sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('scan_checklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scan_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('review_timestamp', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    sa.Column('comment', sa.String(length=1028), nullable=True),
    sa.Column('signed_off', sa.Boolean(), nullable=False, server_default='false'),
    sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('scan_id')
    )
    op.create_table('scan_gold_standard',
    sa.Column('scan', sa.Integer(), nullable=False),
    sa.Column('gold_standard', sa.Integer(), nullable=False),
    sa.Column('date_added', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('gold_version', sa.String(length=128), nullable=True),
    sa.Column('scan_version', sa.String(length=128), nullable=True),
    sa.Column('header_diffs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['gold_standard'], ['gold_standards.id'], ),
    sa.ForeignKeyConstraint(['scan'], ['scans.id'], ),
    sa.PrimaryKeyConstraint('scan', 'gold_standard')
    )
    op.create_table('scan_metrics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scan_id', sa.Integer(), nullable=False),
    sa.Column('metric_type', sa.Integer(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['metric_type'], ['metrictypes.id'], ),
    sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('scan_metrics')
    op.drop_table('scan_gold_standard')
    op.drop_table('scan_checklist')
    op.drop_table('analysis_comments')
    op.drop_table('session_tasks')
    op.drop_table('session_redcap')
    op.drop_table('scans')
    op.drop_table('empty_sessions')
    op.drop_table('timepoint_comments')
    op.drop_table('study_timepoints')
    op.drop_table('sessions')
    op.drop_table('incidental_findings')
    op.drop_table('gold_standards')
    op.drop_table('alt_study_codes')
    op.drop_table('timepoints')
    op.drop_table('study_users')
    op.drop_table('study_sites')
    op.drop_table('study_scantypes')
    op.drop_table('metrictypes')
    op.drop_table('account_requests')
    op.drop_table('users')
    op.drop_table('studies')
    op.drop_table('sites')
    op.drop_table('scantypes')
    op.drop_table('redcap_records')
    op.drop_table('analyses')
