# -*- coding: utf-8 -*-
'''
Database model. Put here the rest of the database.
'''

from datetime import datetime

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import relationship, synonym

from biorepo.model import DeclarativeBase, metadata
from biorepo.model.auth import User
from tg.controllers import redirect
from tg import flash

date_format = "%d/%m/%Y"

__all__ = ['Projects', 'Samples', 'Measurements', 'Files_up', 'Attributs', 'Attributs_values']

#
#Associations tables
#

#This is the association table for the many-to-many relationship between
# samples and data. This is required by repoze.what.
sample_data_table = Table('Cross_sample_measurement', metadata,
     Column('sample_id', Integer, ForeignKey('Samples.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     Column('measurement_id', Integer, ForeignKey('Measurements.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

#This is the association table for the many-to-many relationship between
# parents data and child data. This is required by repoze.what.
meas_meas_table = Table('Cross_measurements', metadata,
     Column('parent_id', Integer, ForeignKey('Measurements.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     Column('child_id', Integer, ForeignKey('Measurements.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)


#This is the association table for the many-to-many relationship between
# measurements and files uploaded. This is required by repoze.what.
meas_fu_table = Table('Cross_meas_fu', metadata,
    Column('measurement_id', Integer, ForeignKey('Measurements.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('fu_id', Integer, ForeignKey('Files_up.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

#This is the association table for the many-to-many relationship between
# measurements and attributs. This is required by repoze.what.
meas_attribut_table = Table('Cross_measurement_attribut', metadata,
    Column('measurement_id', Integer, ForeignKey('Measurements.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('attribut_id', Integer, ForeignKey('Attributs.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

#This is the association table for the many-to-many relationship between
# samples and attributs. This is required by repoze.what.
sample_attribut_table = Table('Cross_sample_attribut', metadata,
    Column('sample_id', Integer, ForeignKey('Samples.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('attribut_id', Integer, ForeignKey('Attributs.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

#This is the association table for the many-to-many relationship between
# samples and attributs values. This is required by repoze.what.
sample_attributvalues_table = Table('Cross_sample_attributvalues', metadata,
    Column('sample_id', Integer, ForeignKey('Samples.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('attributvalues_id', Integer, ForeignKey('Attributs_values.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

#This is the association table for the many-to-many relationship between
# measurements and attributs values. This is required by repoze.what.
meas_attributvalues_table = Table('Cross_meas_attributvalues', metadata,
    Column('measurement_id', Integer, ForeignKey('Measurements.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('attributvalues_id', Integer, ForeignKey('Attributs_values.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)
#
# *The database* model itself
#


class Projects(DeclarativeBase):
    """
    Projects definition
    """
    __tablename__ = 'Projects'
    #columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    #RELATION A CHECKER
    user_id = Column(Integer, ForeignKey('User.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user = relationship('User', foreign_keys=user_id, backref="projects")
    #DELETE THE SAMPLE(S) IF THE PROJECT IS DELETED
    samples = relationship('Samples', backref="project", cascade="all, delete, delete-orphan")

    project_name = Column(Unicode(255))
    date = Column(DateTime, default=datetime.now)
    description = Column(Text)

    def __repr__(self):
        return (u"<Project('%s','%s','%s')>" % (
            self.project_name, self.date, self.description
        )).encode('utf-8')

    def _get_date(self):
        return self.date.strftime(date_format)

    def _set_date(self, date):
        self.date = date

    created = synonym('date', descriptor=property(_get_date, _set_date))

    @property
    def get_username(self):
        if self.user is None:
            return "No user"

        return self.user.name

    @property
    def get_userid(self):
        return self.user.id

    @property
    def samples_display(self):
        """
        for a nice sample display on projects page
        """
        return '<br/>'.join(['%s' % (sample.name) for sample in self.samples])


class Files_up(DeclarativeBase):
    """
    Files upload definition
    """
    __tablename__ = 'Files_up'
    #columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    filename = Column(Unicode(255))
    sha1 = Column(Unicode(255))
    path = Column(Unicode(255))
    url_path = Column(Unicode(255))
    extension = Column(Unicode(255))
    vitalit_path = Column(Unicode(255))


class Measurements(DeclarativeBase):
    """
    Data definition
    """
    __tablename__ = 'Measurements'
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id',
         onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    #user relationship
    user = relationship('User', foreign_keys=user_id, backref="measurements")

    name = Column(Unicode(255))
    description = Column(Text)
    status_type = Column(Boolean)  # A METTRE PUBLIC/PRIVATE
    type = Column(Boolean)  # A METTRE RAW/PROCESSED
    date = Column(DateTime, default=datetime.now)

    #files up relationship
    fus = relationship('Files_up', secondary=meas_fu_table, backref='measurements')
    #atttributs relationship
    attributs = relationship('Attributs', secondary=meas_attribut_table, backref='measurements')

    #attributs values relationship
    a_values = relationship('Attributs_values', secondary=meas_attributvalues_table, backref='measurements')

    #filiation
    children = relationship('Measurements', secondary=meas_meas_table,
                      primaryjoin=id == meas_meas_table.c.child_id,
                      secondaryjoin=id == meas_meas_table.c.parent_id,
                      backref='parents')

    def __repr__(self):
        return (u"<Data('%s','%s','%s','%s','%s')>" % (
            self.name, self.description, self.status_type, self.type, self.date)).encode('utf-8')

    def _get_date(self):
        return self.date.strftime(date_format)

    def _set_date(self, date):
        self.date = date

    created = synonym('date', descriptor=property(_get_date, _set_date))

    @property
    def get_username(self):
        return self.user.name

    @property
    def get_user(self):
        return self.user

    @property
    def get_userid(self):
        return self.user.id

    @property
    def get_status_type(self):
        if self.status_type:
            return "public"
        else:
            return "private"

    @property
    def get_type(self):
        if self.type:
            return "raw data"
        else:
            return "processed data"

    #################################
    ######## for search page ########
    #################################

    @property
    def samples_display(self):
        """
        for a nice sample display on search page
        """

        return ' ; '.join(['%s' % (sample.name) for sample in self.samples])

    @property
    def projects_display(self):
        """
        for a nice project display on search page
        """
        return ' ; '.join(['%s' % (sample.get_projectname) for sample in self.samples])

    @property
    def measurement_type(self):
        """
        for a nice raw/processed type on search page
        """
        if self.type == False:
            return "Processed"
        else:
            return "Raw"

    @property
    def sample_type(self):
        #return ' ; '.join( ['%s'% (sample.type) for sample in self.samples ] )
        list_type = []
        for sample in self.samples:
            if sample.type is not None:
                list_type.append(sample.type)
        return ' ; '.join(list_type)

    @property
    def sample_cell_type(self):
        #return ' ; '.join( [ '%s' % (sample.cell_type) for sample in self.samples ] )
        list_cell_type = []
        for sample in self.samples:
            if sample.cell_type is not None:
                list_cell_type.append(sample.cell_type)
        return ' ; '.join(list_cell_type)

    @property
    def sample_cell_type_test(self):
        return [s.cell_type for s in self.samples]

    @property
    def sample_ab_target(self):
        #return ' ; '.join( [ '%s' % (sample.target) for sample in self.samples ] )
        list_target = []
        for sample in self.samples:
            if sample.target is not None:
                list_target.append(sample.target)
        return ' ; '.join(list_target)

    @property
    def sample_bio_bg(self):
        #return ' ; '.join( [ '%s' % (sample.bio_background) for sample in self.samples ] )
        list_biobg = []
        for sample in self.samples:
            if sample.bio_background is not None:
                list_biobg.append(sample.bio_background)
        return ' ; '.join(list_biobg)

    @property
    def sample_stage(self):
        #return ' ; '.join( [ '%s' % (sample.stage) for sample in self.samples ] )
        list_stage = []
        for sample in self.samples:
            if sample.stage is not None:
                list_stage.append(sample.stage)
        return ' ; '.join(list_stage)

    @property
    def sample_species(self):
        #return ' ; '.join( ['%s' % (sample.organism) for sample in self.samples ] )
        list_orga = []
        for sample in self.samples:
            if sample.organism is not None:
                list_orga.append(sample.organism)
        return ' ; '.join(list_orga)

    @property
    def get_extension(self):
        list_fus = self.fus
        if len(list_fus) > 0:
            for f in list_fus:
                extension = f.extension
                return extension
        else:
            return "URL"

    #dynamicity part
    @property
    def attributs_keys(self):
        return ' ; '.join(['%s' % (att.key) for att in self.attributs])


class Samples(DeclarativeBase):
    """
    Sample definition
    """
    __tablename__ = 'Samples'
    #columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    #RELATION A CHECKER
    project_id = Column(Integer, ForeignKey('Projects.id',
         onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    name = Column(Unicode(255))
    type = Column(Unicode(255))
    date = Column(DateTime, default=datetime.now)
    protocole = Column(Text)

    #measurements relationship
    measurements = relationship('Measurements', secondary=sample_data_table, backref='samples')
    #atttributs relationship
    attributs = relationship('Attributs', secondary=sample_attribut_table, backref='samples')
    #attributs values relationship
    a_values = relationship('Attributs_values', secondary=sample_attributvalues_table, backref='samples')

    def __repr__(self):
        return (u"<Sample('%s','%s','%s','%s','%s','%s')>" % (
               self.id, self.project_id, self.name, self.type,
               self.date, self.protocole)).encode('utf-8')

    def _get_date(self):
        return self.date.strftime(date_format)

    def _set_date(self, date):
        self.date = date

    created = synonym('date', descriptor=property(_get_date, _set_date))

    @property
    def get_username(self):
        if self.project is None:
            return "No project bug - database.py l320"

        return self.project.get_username

    @property
    def get_userid(self):
        if self.project is None:
            return None

        return self.project.get_userid

    @property
    def get_projectname(self):
        if self.project is None:
            return "No project"

        return self.project.project_name


class Attributs(DeclarativeBase):
    """
    Attributs definition
    """
    __tablename__ = 'Attributs'
    #columns

    id = Column(Integer, autoincrement=True, primary_key=True)
    #relation
    lab_id = Column(Integer, ForeignKey('Labs.id',
         onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    #others
    key = Column(Unicode(255))
    fixed_value = Column(Boolean)
    searchable = Column(Boolean)
    deprecated = Column(Boolean)
    widget = Column(Unicode(255))
    owner = Column(Unicode(255))


class Attributs_values(DeclarativeBase):
    """
    Attributs_values definition
    """
    __tablename__ = 'Attributs_values'

    #columns

    id = Column(Integer, autoincrement=True, primary_key=True)
    #relation
    attribut_id = Column(Integer, ForeignKey('Attributs.id',
        onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    value = Column(Unicode(255))
    deprecated = Column(Boolean)

    #relationship
    att = relationship('Attributs', backref='values')
