from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, validates
from app.database import Base
import phonenumbers
import validate_email

study_site_table = Table('study_site',
                         Base.metadata,
                         Column('study_id', Integer, ForeignKey('studies.id')),
                         Column('site_id', Integer, ForeignKey('sites.id')))

class Study(Base):
    __tablename__ = 'studies'

    id = Column(Integer, primary_key = True)
    nickname = Column(String(12), index = True, unique = True)
    name = Column(String(64))
    sites = relationship('Site', secondary = study_site_table, back_populates = 'studies')
    sessions = relationship('Session')

    def __repr__(self):
        return ('<Study {}>'.format(self.nickname))

class Site(Base):
    __tablename__ = 'sites'

    id = Column(Integer, primary_key = True)
    name = Column(String(64), index = True, unique = True)
    studies = relationship('Study', secondary = study_site_table, back_populates = 'sites')
    sessions = relationship('Session')

    def __repr__(self):
        return ('<Site {}>'.format(self.name))

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key = True)
    name = Column(String(64), unique=True)
    study_id = Column(Integer, ForeignKey('studies.id'))
    study = relationship('Study', back_populates='sessions')
    site_id = Column(Integer, ForeignKey('sites.id'))
    site = relationship('Site', back_populates='sites')
    scans = relationship('Scan')

    def __repr__(self):
        return('<Session {} from Study {} at Site {}'.format(self.name,
                                                             self.study.nickname,
                                                             self.site.name))

class ScanType(Base):
    __tablename__ = 'scantypes'

    id = Column(Integer, primary_key = True)
    name = Column(String(64), index = True, unique = True)
    metrics = relationship('Metric')
    scans = relationship("Scan", back_populates = 'scantype')

    def __repr__(self):
        return('<ScanType {}>'.format(self.name))

class Metric(Base):
    __tablename__ = 'metrics'

    id = Column(Integer, primary_key = True)
    name = Column(String(12), index = True, unique = True)
    scantype_id = Column(Integer, ForeignKey('scantypes.id'))
    scantype = relationship('ScanType', back_populates = 'metrics')
    metricvalues = relationship('MetricValue')

    def __repr__(self):
        return('<Metric {}>'.format(self.name))

class Person(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key = True)
    name = Column(String(64))
    role = Column(String(64))
    email = Column(String(255))
    phone1 = Column(String(20))
    phone2 = Column(String(20))

    def __repr__(self):
        return('<Contact {}>'.format(self.name))

    @validates('email')
    def validate_email(self, key, value):
        if not validate_email.validate_email(value):
            raise AssertionError

    @validates('phone1','phone2')
    def validate_phone(self, key, value):
        p = phonenumbers.parse(value, 'CA')
        if not phonenumbers.is_valid_number(p):
            raise AssertionError

class Scan(Base):
    __tablename__ = 'scans'

    id = Column(Integer, primary_key = True)
    name = Column(String(128), index = True, unique = True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    session = relationship('Session', back_populates='scans')

    scantype_id = Column(Integer, ForeignKey('scantypes.id'))
    scantype = relationship('ScanType', back_populates= "scans")
    metricvalues = relationship('MetricValue')

    def __repr__(self):
        return('<Scan {}>'.format(self.name))

class MetricValue(Base):
    __tablename__ = 'scanmetrics'

    id = Column(Integer, primary_key = True)
    value = Column(Float)
    scan_id = Column(Integer, ForeignKey('scans.id'))
    scan = relationship('Scan', back_populates = "metricvalues")
    metrictype_id = Column(Integer, ForeignKey('metrics.id'))
    metrictype = relationship('Metric', back_populates = "metricvalues")

    def __repr__(self):
        return('<Scan {}: Metric {}: Value {}>'.format(self.scan.name,
                                                     self.metrictype.name,
                                                     self.value))
