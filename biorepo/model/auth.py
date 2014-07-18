# -*- coding: utf-8 -*-
"""
Auth* related model.

This is where the models used by :mod:`repoze.who` and :mod:`repoze.what` are
defined.

It's perfectly fine to re-use this definition in the biorepo application,
though.

"""
import uuid

from datetime import datetime
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relationship, synonym
from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils.types import TSVectorType

from biorepo.model import DeclarativeBase, metadata, DBSession
date_format = "%A %d. %B %Y %H.%M.%S"

__all__ = ['User', 'Group', 'Permission', 'Labs']


#
# Association tables
#
# This is the association table for the many-to-many relationship between
# groups and permissions. This is required by repoze.what.
group_permission_table = Table('GroupPermissions', metadata,
    Column('group_id', Integer, ForeignKey('Group.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('Permission.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships. It's required by repoze.what.
user_group_table = Table('UserGroup', metadata,
    Column('user_id', Integer, ForeignKey('User.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('group_id', Integer, ForeignKey('Group.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

user_lab_table = Table('Cross_user_lab', metadata,
    Column('user_id', Integer, ForeignKey('User.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('lab_id', Integer, ForeignKey('Labs.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

projects_lab_table = Table('Cross_projects_lab', metadata,
    Column('project_id', Integer, ForeignKey('Projects.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('lab_id', Integer, ForeignKey('Labs.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)
#
# *The auth* model itself
#
#Full Text Search with SQLAlchemy-Searchable
make_searchable()


class Group(DeclarativeBase):
    """
    Group definition for :mod:`repoze.what`.
    Only the ``group_name`` column is required by :mod:`repoze.what`.
    """
    __tablename__ = 'Group'
    # columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(255))
    _created = Column(DateTime, default=datetime.now)
    # relations
    users = relationship('User', secondary=user_group_table, backref='groups')
    # special methods

    def __repr__(self):
        return '<Group: name=%r>' % self.name

    def __unicode__(self):
        return self.name

    @property
    def get_users(self):
        return self.users

    @property
    def get_permissions(self):
        return self.permissions

    def _get_date(self):
        return self._created.strftime(date_format)

    def _set_date(self, date):
        self._created = date

    created = synonym('_created', descriptor=property(_get_date, _set_date))

    def has_permission(self, tag):
        '''
        Return true if the group has the permission specified
        '''
        for perm in self.permissions:
            if perm.name == tag:
                return True
            return False
# The 'info' argument we're passing to the email_address and password columns
# contain metadata that Rum (http://python-rum.org/) can use generate an
# admin interface for your models.


class User(DeclarativeBase):
    """
    User definition.
    This is the user definition used by :mod:`repoze.who`, which requires at
    least the ``user_name`` column.
    """
    __tablename__ = 'User'

    def setdefaultkey(self):
        uid = str(uuid.uuid4())
        while DBSession.query(User).filter(User.key == uid).first():
            uid = str(uuid.uuid4())
        return uid
    # columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    firstname = Column(Unicode(255))
    name = Column(Unicode(255))
    _email = Column(Unicode(255), unique=True, info={'rum': {'field': 'Email'}})
    _created = Column(DateTime, default=datetime.now)
    key = Column(Unicode(255), unique=True, default=setdefaultkey)
    #search vector for FTS
    search_vector = Column(TSVectorType('firstname', 'name'))

    def _get_date(self):
        return self._created.strftime(date_format)

    def _set_date(self, date):
        self._created = date

    created = synonym('_created', descriptor=property(_get_date, _set_date))

    # email and user_name properties
    def _get_email(self):
        return self._email

    def _set_email(self, email):
        self._email = email.lower()

    email = synonym('_email', descriptor=property(_get_email, _set_email))

    def get_path_perso(self):
        tmp_mail = self._get_email().replace("@", "AT")
        path_perso = "/" + tmp_mail + "/"
        return path_perso

    # class methods
    @classmethod
    def by_email_address(cls, email):
        """Return the user object whose email address is ``email``."""
        return DBSession.query(cls).filter(cls.email == email).first()

    # non-column properties
    def validate_login(self, password):
        print 'validate_login'
        print password

    @property
    def permissions(self):
        """Return a set with all permissions granted to the user."""
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    def permissions_for_group(self, group_id):
        '''
        Return permissions granted for the group.
        '''
        for g in self.groups:
            if g.id == group_id:
                return g.permissions
        return []

    def has_access(self, permission, group_id):
        '''
        Return True if the user has the desired access.
        (Alway true if the user is the creator).
        @param permission: which permission
        @type permission: the string representing the permission
        @param group_id : the identifier of the group
        @type group_id: an integer
        '''
        group_id = int(group_id)
        for g in self.groups:
            if g.id == group_id:
                if g.creator_id == self.id:
                    return True
                for p in permission:
                    if p.name == permission:
                        return True
        return False

    def __repr__(self):
        return '<User: id=%r, name=%r, email=%r, key=%r>' % (self.id, self.name, self.email, self.key)

    def __unicode__(self):
        return self.name


class Permission(DeclarativeBase):
    """
    Permission definition for :mod:`repoze.what`.
    Only the ``permission_name`` column is required by :mod:`repoze.what`.
    """

    __tablename__ = 'Permission'

    # columns

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(63), unique=True, nullable=False)

    # relations

    groups = relationship(Group, secondary=group_permission_table, backref='permissions')

    # special methods

    def __repr__(self):
        return '<Permission: name=%r>' % self.name

    def __unicode__(self):
        return self.name


## Add to TurboTequila
class Labs(DeclarativeBase):

    __tablename__ = 'Labs'
    # columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(255))
    path_raw = Column(Unicode(255))
    path_processed = Column(Unicode(255))
    path_tmp = Column(Unicode(255))

        # relations
    users = relationship('User', secondary=user_lab_table, backref='labs')
    projects = relationship('Projects', secondary=projects_lab_table, backref='labs')

    # special methods

    def __repr__(self):
        return '<Lab: id=%r, name=%r, path_raw=%r, path_processed=%r, path_tmp=%r>' % (self.id,
        self.name, self.path_raw, self.path_processed, self.path_tmp)

    def __unicode__(self):
        return self.name
