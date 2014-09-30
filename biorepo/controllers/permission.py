"""Permission Controller"""
from tgext.crud import CrudRestController
from biorepo.lib.base import BaseController

from repoze.what.predicates import has_permission

from tg import expose, flash
from tg.controllers import redirect
from tg import app_globals as gl

from biorepo.model import DBSession, Permission


class PermissionController(BaseController):
    allow_only = has_permission(gl.perm_admin)
    model = Permission

    @expose('genshi:tgext.crud.templates.post_delete')
    def post_delete(self, *args, **kw):
        for id in args:
            permission = DBSession.query(Permission).filter(Permission.id == id).first()
            if permission.name == gl.perm_admin:
                flash('Cannot delete admin permission')
                redirect('/permissions')
            if permission.name == gl.perm_user:
                flash('Cannot delete read permission')
                redirect('/permissions')
        return CrudRestController.post_delete(self, *args, **kw)
