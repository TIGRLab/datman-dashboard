from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
studies = Table('studies', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String(length=12)),
    Column('name', String(length=64)),
    Column('description', String(length=1024)),
    Column('fullname', String(length=1024)),
    Column('primary_contact_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['studies'].columns['description'].create()
    post_meta.tables['studies'].columns['fullname'].create()
    post_meta.tables['studies'].columns['primary_contact_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['studies'].columns['description'].drop()
    post_meta.tables['studies'].columns['fullname'].drop()
    post_meta.tables['studies'].columns['primary_contact_id'].drop()
