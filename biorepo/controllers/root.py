# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, request, tmpl_context, validate, session, redirect

from biorepo.lib.base import BaseController
from biorepo.model import DBSession, User, Labs, Attributs, Attributs_values
from repoze.what.predicates import has_permission

from biorepo.controllers import ErrorController, LoginController, GroupController
from biorepo.controllers import PermissionController, UserController, ProjectController,\
                                SampleController, MeasurementController
from sqlalchemy import distinct
#from tgext.crud import CrudRestController

try:
    import simplejson as json
except ImportError:
    import json

import inspect
from sqlalchemy.orm import class_mapper

import biorepo.model.auth
import biorepo.model.database
models = {}
for m in biorepo.model.auth.__all__:
    m = getattr(biorepo.model.auth, m)
    if not inspect.isclass(m):
        continue
    try:
        mapper = class_mapper(m)
        models[m.__name__.lower()] = m
    except:
        pass
from biorepo.model import Projects
from biorepo.model import Samples
from biorepo.model import Measurements
from tg import app_globals as gl
from repoze.what.predicates import has_any_permission
from biorepo.lib import util
from sqlalchemy.sql.expression import cast
from sqlalchemy import String, and_
from biorepo.lib.util import SearchWrapper as SW
from biorepo.widgets.datagrids import build_search_grid
from scripts.multi_upload import run_script as MU
from biorepo.handler.user import get_user

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the biorepo application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """

    error = ErrorController()
    login = LoginController()

    # admin controllers
    groups = GroupController(DBSession, menu_items=models)
    projects = ProjectController()
    samples = SampleController()
    measurements = MeasurementController()
    permissions = PermissionController(DBSession, menu_items=models)
    users = UserController(DBSession, menu_items=models)

    @expose('biorepo.templates.index')
    def index(self, *args, **kw):
        return dict(page='index')

    @expose('biorepo.templates.index')
    def login_needed(self):
        flash('You need to login')
        return dict(page='index')

    @expose('biorepo.templates.about')
    def about(self):
        """Handle the 'about' page."""
        return dict(page='about')

    @expose('biorepo.templates.UCSC')
    def UCSC(self):
        return dict(page='UCSC')

    ## DEVELOPMENT PAGES ##
    @require(has_permission('admin', msg='Only for admins'))
    @expose('biorepo.templates.environ')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(page='environ', environment=request.environ)

    @require(has_permission('admin', msg='Only for admins'))
    @expose('biorepo.templates.data')
    @expose('json')
    def data(self, **kw):
        """This method showcases how you can use the same controller for a data page and a display page"""
        return dict(page='data', params=kw)

    #SEARCH PAGE
    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('biorepo.templates.search')
    def search(self, *args, **kw):
        """
        Handle the searching page
        """

        user_lab = session.get("current_lab", None)
        if user_lab:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
            attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).all()
            measurements = []
            for a in attributs:
                for m in a.measurements:
                    if m not in measurements:
                        measurements.append(m)
            searching = [SW(meas) for meas in measurements]
            search_grid, hidden_positions, positions_not_searchable = build_search_grid(measurements)

            items = [util.to_datagrid(search_grid, searching, '', grid_display=len(searching) > 0)]

            #tmpl_context.users = list(set([mes.get_user for mes in searching]))
            #tmpl_context.samples = DBSession.query(Samples).all()

            return dict(
                page='search',
                items=items,
                searchlists=json.dumps([hidden_positions, positions_not_searchable]),
                value=kw,
        )
        else:
            flash("Your lab is not registred, contact the administrator please", "error")
            raise redirect("./")

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose()
    def create_with_tgz(self, path_tgz, mail, key):
        try:
            print "working on : ", path_tgz
        except:
            print "error, bad path_tgz"
        MU(self, path_tgz)
