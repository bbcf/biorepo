# -*- coding: utf-8 -*-
"""Treeview Controller"""
import tg
from tg import app_globals as gl
from tg import request, session, expose
from tg.decorators import with_trailing_slash
from repoze.what.predicates import has_any_permission
from biorepo.lib.base import BaseController
from biorepo import handler
from biorepo.model import DBSession, Labs, Projects, Samples, Measurements, User
try:
    import simplejson as json
except ImportError:
    import json


__all__ = ['TreeviewController']


class TreeviewController(BaseController):
    allow_only = has_any_permission(gl.perm_admin, gl.perm_user)

    @with_trailing_slash
    @expose('biorepo.templates.treeview')
    @expose('json')
    def index(self, *args, **kw):
        #user = handler.user.get_user_in_session(request)
        #admins = tg.config.get('admin.mails')
        #mail = user.email
        user_lab = session.get("current_lab", None)
        user_projects = []
        u_projects = []
        u_samples = []
        u_meas = []
        u_children = []
        u_global = []

        dico_final = {}
        #TODO : admin view - watch for a dl link
        if user_lab:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
            lab_users = lab.users
            for u in lab_users:
                projects = []
                projects = DBSession.query(Projects).filter(Projects.user_id == u.id).all()
                if len(projects) > 0:
                    for p in projects:
                        for lab in p.labs:
                            if lab.name == user_lab:
                                user_projects.append(p)
                    for proj in user_projects:
                        for sample in proj.samples:
                            if len(sample.measurements) > 0:
                                for meas in sample.measurements:
                                    if len(meas.children) == 0:
                                        u_meas.append({"name": str(meas.name) + "(" + str(meas.id) + ")"})
                                    else:
                                        for child in meas.children:
                                            u_children.append({"name": str(child.name) + "(" + str(child.id) + ")"})
                                        u_meas.append({"name": str(meas.name) + "(" + str(meas.id) + ")", "children": u_children})
                                        u_children = []
                                u_samples.append({"name": str(sample.name), "children": u_meas})
                                u_meas = []
                            else:
                                u_samples.append({"name": str(sample.name)})
                        if len(proj.samples) > 0:
                            u_projects.append({"name": str(proj.project_name), "children": u_samples})
                            u_samples = []
                        else:
                            u_projects.append({"name": str(proj.project_name)})
                    u_global.append({"name": u.firstname + " " + u.name, "children": u_projects})
                    u_projects = []
                else:
                    u_global.append({"name": u.firstname + " " + u.name})
            dico_final["name"] = user_lab
            dico_final["children"] = u_global
        return {"data": json.dumps(dico_final)}
