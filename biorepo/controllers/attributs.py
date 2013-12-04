# -*- coding: utf-8 -*-
"""Attributs Controller"""



from tgext.crud import CrudRestController
from tg import expose, flash, request, tmpl_context, validate
from repoze.what.predicates import has_any_permission
from tg.controllers import redirect
from biorepo.widgets.attribut import attribut_table, attribut_table_filler, \
    new_attribut_form, attribut_edit_filler, attribut_edit_form, attribut_grid
from biorepo.model import DBSession, User, Attributs, Samples, Measurements, Projects
from tg import app_globals as gl
from tg.decorators import paginate, with_trailing_slash
from biorepo import handler
from biorepo.lib import util, constant
import pylons
from biorepo.lib.util import isAdmin, list_lower
from biorepo.lib.constant import list_ab_targets, list_cell_lines, list_cell_types,\
    list_dataType, list_organisms, list_types


__all__ = ['AttributController']


class AttributController(CrudRestController):
    allow_only = has_any_permission(gl.perm_admin, gl.perm_user)
    model = Attributs
    table = attibut_table
    table_filler = attribut_table_filler
    edit_form = attribut_edit_form #TODO useless - to check
    new_form = new_attribut_form #TODO useless - to check
    edit_filler = attribut_edit_filler

    @with_trailing_slash
    @expose('biorepo.templates.list')
    @expose('json')
    def get_all(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        # user attributs
        #to block to one specific user
        attributs = DBSession.query(Attributs).all()
        all_attributs = [util.to_datagrid(attribut_grid, attributs, "Attributs Table", len(attributs) > 0)]
        return dict(page='attributs', model='attribut', form_title="new attribut", items=all_attributs, value=kw)

    @expose('genshi:tgext.crud.templates.new')
    def new(self, *args, **kw):
        tmpl_context.widget = new_attribut_form
        #take the logged user
        user = handler.user.get_user_in_session(request)
        #take the logged user samples
        samples = DBSession.query(Samples).join(Projects).join(User).filter(User.id == user.id).all()
        meas = DBSession.query(Measurements).all()
        attributs = DBSession.query(Attributs).all()
        tmpl_context.samples = samples
        tmpl_context.meas = meas
        tmpl_context.attributs = attributs

        return dict(page='samples', value=kw, title='New Sample', model='Sample')

    @expose('genshi:tgext.crud.templates.edit')
    def edit(self, *args, **kw):
        tmpl_context.widget = attribut_edit_form
        user = handler.user.get_user_in_session(request)
        attribut = DBSession.query(Attributs).filter(Attributs.id == args[0]).first()


    @expose('genshi:tgext.crud.templates.get_delete')
    def get_delete(self, *args, **kw):

        return CrudRestController.get_delete(self, *args, **kw)

