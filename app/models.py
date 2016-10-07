"""Object definition file for dashboard app"""

from app import db

study_site_table = db.Table('study_site',
                            db.Column('study_id', db.Integer,
                                      db.ForeignKey('studies.id')),
                            db.Column('site_id', db.Integer,
                                      db.ForeignKey('sites.id')))

study_scantype_table = db.Table('study_scantypes',
                                db.Column('study_id', db.Integer,
                                          db.ForeignKey('studies.id')),
                                db.Column('scantype_id', db.Integer,
                                          db.ForeignKey('scantypes.id')))

study_people_table = db.Table('study_people',
                              db.Column('study_id', db.Integer,
                                        db.ForeignKey('studies.id')),
                              db.Column('person_id', db.Integer,
                                        db.ForeignKey('people.id')))

class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(12), index=True, unique=True)
    name = db.Column(db.String(64))
    scantypes = db.relationship('ScanType', secondary=study_scantype_table,
                                back_populates='studies')
    sites = db.relationship('Site', secondary=study_site_table,
                            back_populates='studies')
    sessions = db.relationship('Session')
    description = db.Column(db.String(1024))
    fullname = db.Column(db.String(1024))
    primary_contact_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    primary_contact = db.relationship('Person')
    #people = db.relationship('Person', secondary=study_people_table,
    #                         back_populates='studies')

    def __repr__(self):
        return ('<Study {}>'.format(self.nickname))


class Site(db.Model):
    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    studies = db.relationship('Study', secondary=study_site_table,
                              back_populates='sites')
    sessions = db.relationship('Session')

    def __repr__(self):
        return ('<Site {}>'.format(self.name))


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    date = db.Column(db.DateTime)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id'))
    study = db.relationship('Study', back_populates='sessions')
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'))
    site = db.relationship('Site', back_populates='sessions')
    scans = db.relationship('Scan')

    def __repr__(self):
        return('<Session {} from Study {} at Site {}>'.format(self.name,
                                                              self.study.nickname,
                                                              self.site.name))


class ScanType(db.Model):
    __tablename__ = 'scantypes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    metrictypes = db.relationship('MetricType', back_populates="scantype")
    scans = db.relationship("Scan", back_populates='scantype')
    studies = db.relationship("Study", secondary=study_scantype_table,
                              back_populates="scantypes")

    def __repr__(self):
        return('<ScanType {}>'.format(self.name))


class MetricType(db.Model):
    __tablename__ = 'metrictypes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(12))
    scantype_id = db.Column(db.Integer, db.ForeignKey('scantypes.id'))
    scantype = db.relationship('ScanType', back_populates='metrictypes')
    metricvalues = db.relationship('MetricValue')

    db.UniqueConstraint('name', 'scantype_id')

    def __repr__(self):
        return('<MetricType {}>'.format(self.name))


class Person(db.Model):
    __tablename__ = 'people'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    role = db.Column(db.String(64))
    email = db.Column(db.String(255))
    phone1 = db.Column(db.String(20))
    phone2 = db.Column(db.String(20))

    def __repr__(self):
        return('<Contact {}>'.format(self.name))


class Scan(db.Model):
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'))
    session = db.relationship('Session', back_populates='scans')

    scantype_id = db.Column(db.Integer, db.ForeignKey('scantypes.id'))
    scantype = db.relationship('ScanType', back_populates="scans")
    metricvalues = db.relationship('MetricValue')

    def __repr__(self):
        return('<Scan {}>'.format(self.name))


class MetricValue(db.Model):
    __tablename__ = 'scanmetrics'

    id = db.Column(db.Integer, primary_key=True)
    _value = db.Column('value', db.String)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'))
    scan = db.relationship('Scan', back_populates="metricvalues")
    metrictype_id = db.Column(db.Integer, db.ForeignKey('metrictypes.id'))
    metrictype = db.relationship('MetricType', back_populates="metricvalues")

    @property
    def value(self):
        """Returns the value field from the database.
        The value is stored as a string.
        If the value contains '::' character this will convert it to a list,
        otherwise it will attempt to cast to Float.
        Failing that the value is returned as a string.
        """
        if self._value is None:
            return(None)
        value = self._value.split('::')
        try:
            value = [float(v) for v in value]
        except ValueError:
            return(''.join(value))
        if len(value) == 1:
            return(value[0])
        else:
            return(value)

    @value.setter
    def value(self, value, delimiter=None):
        """Stores the value in the database as a string.
        If the delimiter is specified any characters matching delimiter are
        replaced with '::' for storage.

        Keyword arguments:
        [delimiter] -- optional character string that is replaced by '::' for
            database storage.
        """
        if delimiter is not None:
            try:
                value = value.replace(delimiter, '::')
            except AttributeError:
                pass
        self._value = str(value)

    def __repr__(self):
        return('<Scan {}: Metric {}: Value {}>'.format(self.scan.name,
                                                       self.metrictype.name,
                                                       self.value))
