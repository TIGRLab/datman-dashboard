"""Move redcap configuration into the database.

Revision ID: 4a842feae63a
Revises: 442e3abe5587
Create Date: 2020-12-30 17:52:57.592157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a842feae63a'
down_revision = '442e3abe5587'
branch_labels = None
depends_on = None


def upgrade():
    redcap_config = op.create_table(
        'redcap_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('instrument', sa.String(length=1024), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('redcap_version', sa.String(length=10), nullable=True),
        sa.Column('date_field', sa.String(length=128), nullable=True),
        sa.Column('comment_field', sa.String(length=128), nullable=True),
        sa.Column('user_id_field', sa.String(length=128), nullable=True),
        sa.Column('session_id_field', sa.String(length=128), nullable=True),
        sa.Column('access_token', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column(
        'redcap_records',
        sa.Column('config', sa.Integer(), nullable=False)
    )

    # Transfer existing config to new table
    conn = op.get_bind()
    records = conn.execute(
        'select project_id, instrument, url, redcap_version '
        '  from redcap_records '
        '  group by project_id, instrument, url, redcap_version;'
    )
    op.bulk_insert(
        redcap_config,
        [{'project_id': record[0],
          'instrument': record[1],
          'url': record[2],
          'redcap_version': record[3]}
          for record in records]
    )

    # Set config column to entry in new table
    op.execute(
        'update redcap_records '
        '  set redcap_records.config = cfg.id '
        '  from redcap_config as cfg'
        '  where cfg.project_id = redcap_records.project_id and '
        '    cfg.instrument = redcap_records.instrument and '
        '    cfg.url = redcap_records.url and '
        '    cfg.redcap_version = redcap_records.redcap_version;'
    )

    op.drop_constraint(
        'redcap_records_unique_record',
        'redcap_records',
        type_='unique'
    )
    op.create_unique_constraint(
        'redcap_records_unique_record',
        'redcap_records',
        ['record', 'config', 'event_id', 'entry_date']
    )
    op.create_foreign_key(
        None,
        'redcap_records',
        'redcap_config',
        ['config'],
        ['id']
    )
    op.drop_column('redcap_records', 'project_id')
    op.drop_column('redcap_records', 'instrument')
    op.drop_column('redcap_records', 'redcap_version')
    op.drop_column('redcap_records', 'url')


def downgrade():
    op.add_column(
        'redcap_records',
        sa.Column(
            'url',
            sa.VARCHAR(length=1024),
            autoincrement=False,
            nullable=False
        )
    )
    op.add_column(
        'redcap_records',
        sa.Column(
            'redcap_version',
            sa.VARCHAR(length=10),
            server_default=sa.text("'7.4.2'::character varying"),
            autoincrement=False,
            nullable=True
        )
    )
    op.add_column(
        'redcap_records',
        sa.Column(
            'instrument',
            sa.VARCHAR(length=1024),
            autoincrement=False,
            nullable=False
        )
    )
    op.add_column(
        'redcap_records',
        sa.Column(
            'project_id',
            sa.INTEGER(),
            autoincrement=False,
            nullable=False
        )
    )

    # Migrate config back to redcap_records
    op.execute(
        'update redcap_records '
        '  set redcap_records.project_id = cfg.project_id, '
        '      redcap_records.instrument = cfg.instrument, '
        '      redcap_records.url = cfg.url, '
        '      redcap_records.redcap_version = cfg.redcap_version '
        '  from redcap_config as cfg '
        '  where redcap_records.config = cfg.id;'
    )

    op.drop_constraint(None, 'redcap_records', type_='foreignkey')
    op.drop_constraint(
        'redcap_records_unique_record',
        'redcap_records',
        type_='unique'
    )
    op.create_unique_constraint(
        'redcap_records_unique_record',
        'redcap_records',
        ['record', 'project_id', 'url', 'event_id', 'entry_date']
    )
    op.drop_column('redcap_records', 'config')
    op.drop_table('redcap_config')
