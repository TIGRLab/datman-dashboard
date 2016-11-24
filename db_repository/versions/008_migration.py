from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
sessions = Table('sessions', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=64)),
    Column('date', DateTime),
    Column('study_id', Integer, nullable=False),
    Column('site_id', Integer, nullable=False),
    Column('is_phantom', Boolean),
    Column('cl_comment', String(length=1024)),
    Column('gh_issue', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['sessions'].columns['gh_issue'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['sessions'].columns['gh_issue'].drop()
