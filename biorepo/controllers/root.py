# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, request, tmpl_context, validate, session, redirect

from biorepo.lib.base import BaseController
from biorepo.model import DBSession, User, Labs, Attributs, Attributs_values
from repoze.what.predicates import has_permission

from biorepo.controllers import ErrorController, LoginController, GroupController
from biorepo.controllers import PermissionController, UserController, ProjectController,\
                                SampleController, MeasurementController, PublicController, TrackhubController,\
                                TreeviewController
from sqlalchemy import distinct
#from tgext.crud import CrudRestController

try:
    import simplejson as json
except ImportError:
    import json

import inspect
import os
from sqlalchemy.orm import class_mapper

import biorepo.model.auth
import biorepo.model.database
# models = {}
# for m in biorepo.model.auth.__all__:
#     m = getattr(biorepo.model.auth, m)
#     if not inspect.isclass(m):
#         continue
#     try:
#         mapper = class_mapper(m)
#         models[m.__name__.lower()] = m
#     except:
#         pass
from biorepo.model import Projects, Samples, Measurements, Group, Files_up
from tg import app_globals as gl
from repoze.what.predicates import has_any_permission
from biorepo.lib import util
from sqlalchemy import and_, or_
from biorepo.lib.util import SearchWrapper as SW
from biorepo.widgets.datagrids import build_search_grid, build_columns
from scripts.multi_upload import run_script as MU
from biorepo.lib.util import print_traceback, check_boolean, time_it
from biorepo.lib.constant import path_raw, path_processed, path_tmp, get_list_types, HTS_path_archive, HTS_path_data
#FullTextSearch
#from sqlalchemy_searchable import search
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
    #groups = GroupController(DBSession, menu_items=models)
    groups = GroupController()
    projects = ProjectController()
    samples = SampleController()
    measurements = MeasurementController()
    #permissions = PermissionController(DBSession, menu_items=models)
    permissions = PermissionController()
    #users = UserController(DBSession, menu_items=models)
    users = UserController()
    public = PublicController()
    trackhubs = TrackhubController()
    treeview = TreeviewController()

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
    @expose('biorepo.templates.search_old')
    def search_old(self, *args, **kw):
        """
        Handle the searching page
        """
        user_lab = session.get("current_lab", None)
        if user_lab:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
            measurements = DBSession.query(Measurements).join(Measurements.attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).distinct().all()
            #attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).all()
            # measurements = []
            # for a in attributs:
            #     for m in a.measurements:
            #         if m not in measurements:
            #             measurements.append(m)
            searching = [SW(meas) for meas in measurements]
            search_grid, hidden_positions, positions_not_searchable = build_search_grid(measurements)

            items = [util.to_datagrid(search_grid, searching, '', grid_display=len(searching) > 0)]

            return dict(
                page='search_old',
                items=items,
                searchlists=json.dumps([hidden_positions, positions_not_searchable]),
                value=kw,
        )
        else:
            flash("Your lab is not registred, contact the administrator please", "error")
            raise redirect("./")

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('biorepo.templates.search')
    def search(self, *args, **kw):
        """
        Handle the searching page
        """
        user_lab = session.get("current_lab", None)
        if user_lab:
            columns = build_columns()
            return dict(
                page='search',
                columns=json.dumps(columns),
                value=kw
        )
        else:
            flash("Your lab is not registred, contact the administrator please", "error")
            raise redirect("./")

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('json')
    def search_engine(self, list_search_words, lab):
        #TODO : dynamic booleans
        empty = False
        first_lap = True
        special_cases = {"status_type": ["%public%", "%private%"], "type": ["%raw%", "%processed%"]}
        bool_special = {"%public%": True, "%private%": False, "%raw%": True, "%processed%": False}
        answer = []
        for w in list_search_words:
            final_request = []
            not_found = 0
            #apply nomenclature for the ilike requests
            w = '%' + w + '%'

            #FIRST REQUEST : MEASUREMENTS TABLE
            #query on Measurements table (columns requested : name, description) TODO : type and status_type (boolean)
            meas_queried = DBSession.query(Measurements).join(Measurements.attributs)\
            .filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False))\
            .filter(or_(Measurements.name.ilike(w), Measurements.description.ilike(w))).all()
            if len(meas_queried) > 0:
                if len(final_request) > 0 and not first_lap:
                    for m in reversed(final_request):
                        if m not in meas_queried:
                            final_request.remove(m)
                elif len(final_request) > 0 and first_lap:
                    for m in meas_queried:
                        if m not in final_request:
                            final_request.append(m)
                else:
                    final_request = [catched for catched in meas_queried if catched not in final_request]
            else:
                if len(list_search_words) > 1:
                    not_found += 1

            #SECOND REQUEST : USER TABLE
            #query on User table (columns requested : name, firstname)
            users_queried = DBSession.query(User).join(User.labs)\
                            .filter(Labs.id == lab.id)\
                            .filter(or_(User.name.ilike(w), User.firstname.ilike(w))).all()
            if len(users_queried) > 0:
                for u in users_queried:
                    query_u = DBSession.query(Measurements).join(Measurements.attributs)\
                            .filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False))\
                            .filter(Measurements.user_id == u.id).all()
                    #Sort the good matches with others finded in previous lap(s)
                    if len(final_request) > 0 and not first_lap:
                        for m in reversed(final_request):
                            if len(query_u) > 0 and m not in query_u:
                                final_request.remove(m)
                    #Add all the good matches for the first lap
                    elif len(final_request) > 0 and first_lap:
                        for m in query_u:
                            if m not in final_request:
                                final_request.append(m)
                    #final_request is empty and have to be fill
                    else:
                        final_request = [catched for catched in query_u if catched not in final_request]
            else:
                if len(list_search_words) > 1:
                    not_found += 1

            #THIRD REQUEST (the longest in terms of time execution): ATTRIBUT_VALUES TABLE
            #query on Attribut_values table (column requested : value)
            #WARNING : owner --> meas or sample.
            att_val_queried = DBSession.query(Attributs_values).filter(Attributs_values.value.ilike(w)).all()
            if len(att_val_queried) > 0:
                #sorting : sample/meas attribut values
                att_val_sample = []
                att_val_meas = []
                for val in att_val_queried:
                    att_id = val.attribut_id
                    att = DBSession.query(Attributs).filter(Attributs.id == att_id).first()
                    if att.lab_id == lab.id:
                        #sample att
                        if att.owner == "sample" and val not in att_val_sample:
                            att_val_sample.append(val)
                        #measurement att
                        elif att.owner == "measurement" and val not in att_val_meas:
                            att_val_meas.append(val)

                #filtering meas from meas attribut values
                meas_checked = []
                for value in att_val_meas:
                    measurements_list = value.measurements
                    for m in measurements_list:
                        if m not in meas_checked:
                            meas_checked.append(m)
                #filtering samples from sample attribut values
                samples_checked = []
                for val in att_val_sample:
                    samples_list = val.samples
                    for s in samples_list:
                        if s not in samples_checked:
                            samples_checked.append(s)
                for sample in samples_checked:
                    if len(sample.measurements) > 0:
                        meas_checked = list(set(meas_checked + sample.measurements))

                if len(final_request) > 0:
                    for m in meas_checked:
                        if m not in final_request:
                            final_request.append(m)
                else:
                    final_request = meas_checked
                #control
                if len(final_request) == 0 and len(list_search_words) > 1:
                    not_found += 1
            else:
                if len(list_search_words) > 1:
                    not_found += 1

            #FOURTH REQUEST : SAMPLES TABLE
            #query on Samples table (columns requested : name, type, protocole)
            samples_queried = DBSession.query(Samples).filter(or_(Samples.name.ilike(w), Samples.type.ilike(w),\
                              Samples.protocole.ilike(w))).all()
            list_meas_sample = []
            if len(samples_queried) > 0:
                for s in samples_queried:
                    list_meas_sample_tmp = s.measurements
                    for m in list_meas_sample_tmp:
                        tmp_request = DBSession.query(Measurements).join(Measurements.attributs)\
                                  .filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False))\
                                  .filter(Measurements.id == m.id).all()
                        list_meas_sample = list(set(list_meas_sample + tmp_request))

                    if len(final_request) > 0:
                        for m in list_meas_sample:
                            if m not in final_request:
                                final_request.append(m)
                    else:
                        #check the lab
                        for meas in list_meas_sample:
                            tmp_request = DBSession.query(Measurements).join(Measurements.attributs)\
                                      .filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False))\
                                      .filter(Measurements.id == meas.id).all()
                            final_request = list(set(final_request + tmp_request))
                #control
                if len(final_request) == 0 and len(list_search_words) > 1:
                    not_found += 1
            else:
                if len(list_search_words) > 1:
                    not_found += 1

            #FIFTH REQUEST : PROJECTS TABLE
            #query on Projects table (column requested : project_name)
            projects_queried = DBSession.query(Projects).filter(Projects.project_name.ilike(w)).all()
            if len(projects_queried) > 0:
                list_meas_from_project = []
                for p in projects_queried:
                    list_samples_project = p.samples
                    for s in list_samples_project:
                        list_meas_from_project = list(set(list_meas_from_project + s.measurements))

                for meas in list_meas_from_project:
                    tmp_request = DBSession.query(Measurements).join(Measurements.attributs)\
                              .filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False))\
                              .filter(Measurements.id == meas.id).all()
                    final_request = list(set(final_request + tmp_request))
                #control
                if len(final_request) == 0 and len(list_search_words) > 1:
                    not_found += 1
            else:
                if len(list_search_words) > 1:
                    not_found += 1

            #SPECIAL CASES
            #Boolean values for Measurements
            for k, v in special_cases.items():
                if w in v:
                    meas_toFind = DBSession.query(Measurements).join(Measurements.attributs)\
                                .filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False))\
                                .filter(getattr(Measurements, k) == bool_special[w]).all()
                    if len(meas_toFind) > 0:
                        not_found = not_found - 1
                        if len(final_request) > 0 and not first_lap:
                            for m in reversed(final_request):
                                if m not in meas_toFind:
                                    final_request.remove(m)
                        elif len(final_request) > 0 and first_lap:
                            for m in meas_toFind:
                                if m not in final_request:
                                    final_request.append(m)
                        else:
                            final_request = [catched for catched in meas_toFind if catched not in final_request]

            #No results for all the queries for this word (we have here 5 different types of query, so 5 is the stop number)
            if not_found == 5:
                empty = True
            if first_lap:
                answer = final_request
            else:
                for m in reversed(answer):
                    if m not in final_request:
                        answer.remove(m)
            first_lap = False

        if empty:
            final_request = []
        return answer

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('json')
    def search_to_json(self, *args, **kw):
        #TODO : sort by column on user's click
        user_lab = session.get("current_lab", None)
        #get parameters from ajax request
        search_value = kw.get("search[value]", None)
        if search_value == '':
            search_value = None
        #word lenght > 2 to avoid DDoS in your server....
        elif search_value is not None:
            list_search_words = [x for x in search_value.split(" ") if len(x) > 2]

        draw = int(kw.get("draw", 1))
        start_point = int(kw.get("start", 0))
        data_by_page = int(kw.get("length", 50))
        stop_point = start_point + data_by_page

        if user_lab:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
            #measurements = DBSession.query(Measurements).join(Measurements.attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).distinct()[:50]
            measurements_total = DBSession.query(Measurements).join(Measurements.attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).all()
            measurements = DBSession.query(Measurements).join(Measurements.attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).distinct()[start_point:stop_point]
            if search_value is not None:
                final_request = self.search_engine(list_search_words, lab)
                #query mixed with results from all the table of interest
                paginated_request = final_request[start_point:stop_point]
                searching_tosort = [SW(meas).to_json_test() for meas in paginated_request]
                searching = sorted(searching_tosort, key=lambda k: (k['User'], k['Type']))
                return json.dumps({"draw": draw, "recordsTotal": len(measurements_total), "recordsFiltered": len(final_request), "data": searching})

            searching_tosort = [SW(meas).to_json_test() for meas in measurements]
            searching = sorted(searching_tosort, key=lambda k: (k['User'], k['Type']))

        return json.dumps({"draw": draw, "recordsTotal": len(measurements_total), "recordsFiltered": len(measurements_total), "data": searching})

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('json')
    def searchlists_to_json(self, *args, **kw):
        user_lab = session.get("current_lab", None)
        if user_lab:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
            one_meas = DBSession.query(Measurements).join(Measurements.attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).first()
            search_grid, hidden_positions, positions_not_searchable = build_search_grid(one_meas)
            searchlists = json.dumps([hidden_positions, positions_not_searchable])

            return searchlists

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose()
    def create_with_tgz(self, path_tgz, mail, key):
        try:
            print "working on : ", path_tgz
        except:
            print "error, bad path_tgz"
        MU(self, path_tgz)

    @require(has_permission(gl.perm_admin))
    @expose()
    def create_gone_user(self, mail, key, lab_id, firstname, name, user_mail):
        #utilisation (only for admins) :
        #wget --post-data "key=xxxxxxxxxxxxxxxxxxxxx&mail=beta.testeur@epfl.ch&lab_id=lab_id&firstname=jean-michel&name=michel&user_mail=michel@epfl.ch" \
        # http://biorepo.epfl.ch/biorepo/create_gone_user
        try:
            user = User()
            user.firstname = firstname.capitalize()
            user.name = name.capitalize()
            lab = DBSession.query(Labs).filter(Labs.id == lab_id).first()
            user.labs.append(lab)
            user._email = user_mail
            group = DBSession.query(Group).filter(Group.id == 1).first()
            user.groups.append(group)
            DBSession.add(user)
            DBSession.flush()
            print "Gone/Exterior user created :", user
        except:
            print_traceback()
            print "Gone/Exterior user NOT created --> ERROR"

    @require(has_permission(gl.perm_admin))
    @expose()
    def create_ext_lab(self, mail, key, lab_name):
        #utilisation (only for admins) :
        #wget --post-data "mail=admin.biorepo@epfl.ch&key=xxxxxxxxxxx&lab_name=bbcf" http://biorepo.epfl.ch/biorepo/create_ext_lab
        lab_test = DBSession.query(Labs).filter(Labs.name == lab_name).first()
        if lab_test is None:
            try:
                lab = Labs()
                lab.name = lab_name
                lab.path_raw = path_raw(lab_name)
                lab.path_processed = path_processed(lab_name)
                lab.path_tmp = path_tmp(lab_name)
                DBSession.add(lab)
                DBSession.flush()
                print "Exterior lab created :", lab_name
            except:
                print_traceback()
                print "Exterior lab NOT created --> ERROR"
        else:
            print "This lab : ", str(lab_name), " is in the db yet. --> ERROR"

    @require(has_permission(gl.perm_admin))
    @expose()
    def add_lab_4_user(self, mail, key, user_mail, lab2add):
        '''
        Allow to bypass Shibboleth. You can add here a registered lab for a registered user.
        Warning : Don't use it for someone who is not from EPFL.
        '''
        #utilisation (only for admins) :
        #wget --post-data "mail=admin.biorepo@epfl.ch&key=xxxxxxxxxxx&user_mail=registered.user@mail.com&lab2add=bbcf" http://biorepo.epfl.ch/biorepo/add_lab_4_user
        user = DBSession.query(User).filter(User._email == user_mail).first()
        if user is None:
            print "User not found."
        lab = DBSession.query(Labs).filter(Labs.name == lab2add).first()
        if lab is None:
            print "Lab not found."
        registred = False
        if lab is not None and lab in user.labs:
            print "This lab is already registered for this user."
            registred = True

        if user is not None and lab is not None and not registred:
            (user.labs).append(lab)
            DBSession.flush()
        else:
            print "Error, lab was not added to the user"

    #docs
    @expose('biorepo.templates.manual')
    def userdoc(self):
        return {}

    @expose('biorepo.templates.documentation')
    def devdoc(self):
        return {}

    #API
    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('json')
    def get_my_lab_projects(self, mail, key):
        '''
        Get a JSON with all user's projects by lab
        input : mail an biorepo key
        output : {'lab':{'project id':{'name': "my_project_name", 'description': "my project description",
        "owner": "project owner name"}}}
        '''
        dico_lab_projects = {}
        dico_by_labs = {}
        user = DBSession.query(User).filter(User._email == mail).first()
        if user is None:
            return {'ERROR': "User " + mail + " not in BioRepo."}
        else:
            user_labs = user.labs
            if len(user_labs) == 1:
                for lab in user_labs:
                    lab_projects = lab.projects
                if isinstance(lab_projects, list):
                    for p in lab_projects:
                        u = DBSession.query(User).filter(User.id == p.user_id).first()
                        owner = u.name
                        dico_lab_projects[p.id] = {'name': p.project_name, 'description': p.description,
                                'owner': owner}
                else:
                    u = DBSession.query(User).filter(User.id == p.user_id).first()
                    owner = u.name
                    dico_lab_projects[lab_projects.id] = {'name': lab_projects.project_name, 'description': lab_projects.description,
                                'owner': owner}
                if len(lab_projects) == 0:
                    return {'ERROR': "No projects found for " + lab.name}
                dico_by_labs[lab.name] = dico_lab_projects
                return dico_by_labs

            elif len(user.labs) > 1:
                for l in user.labs:
                    lab_projects = l.projects
                    if isinstance(lab_projects, list):
                        for p in lab_projects:
                            u = DBSession.query(User).filter(User.id == p.user_id).first()
                            owner = u.name
                            dico_lab_projects[p.id] = {'name': p.project_name, 'description': p.description,
                                'owner': owner}
                    else:
                        u = DBSession.query(User).filter(User.id == p.user_id).first()
                        owner = u.name
                        dico_lab_projects[lab_projects.id] = {'name': lab_projects.project_name, 'description': lab_projects.description,
                                'owner': owner}
                    dico_by_labs[l.name] = dico_lab_projects
                    dico_lab_projects = {}
                return dico_by_labs

            else:
                return {'ERROR': "This user " + mail + " has no lab. Contact the administrator please."}

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('json')
    def get_samples_from_project(self, mail, key, p_id):
        '''
        Get a JSON with all samples from a given project
        input : mail and biorepo key, p_id (project id)
        output : {"project id": [{"sample id": {"name": "my sample name", "type": "4C-seq",
        "protocole": "my sample protocole", "dynamic field": "my dynamic field, ..."}}, ...]}
        '''
        user = DBSession.query(User).filter(User._email == mail).first()
        user_lab = user.labs
        list_samples = []
        dico_final = {}
        target = DBSession.query(Projects).filter(Projects.id == p_id).first()
        if target is None:
            return {'ERROR': "This project ID does not exist."}
        lab_target = target.labs[0]
        #check if the project is owned by the user or his lab
        access_ok = False
        for l in user_lab:
            if l.id == lab_target.id:
                access_ok = True
        if access_ok:
            samples = target.samples
            if len(samples) == 0:
                return {'ERROR': 'This project id : ' + str(target.id) + ' is empty.'}
            for s in samples:
                dico_sample = {}
                dico_dynamic = {}
                sample_attributs = s.attributs
                sample_a_values = s.a_values
                for att in sample_attributs:
                    att_id = att.id
                    att_key = att.key
                    for val in sample_a_values:
                        value = val.value
                        if val.attribut_id == att_id:
                            #for the true weird checkbox
                            if value == "true":
                                dico_dynamic[att_key] = att_key
                            else:
                                dico_dynamic[att_key] = value
                #check the weird checkbox widget with "false" value
                if len(sample_attributs) != len(dico_dynamic.keys()):
                    for att in sample_attributs:
                        att_key = att.key
                        att_widget = att.widget
                        if att_key not in dico_dynamic.keys() and att_widget == "checkbox":
                            dico_dynamic[att_key] = "Not " + str(att_key)
                        elif att_key not in dico_dynamic.keys() and att_widget != "checkbox":
                            dico_dynamic[att_key] = "Not specified"

                dico_sample = {"name": s.name, "type": s.type, "protocole": s.protocole}
                dico_sample.update(dico_dynamic)
                list_samples.append({s.id: dico_sample})
            dico_final[p_id] = list_samples
            return dico_final

        else:
            return {'ERROR': "This project is not a project from your lab, you cannot access to it."}

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('json')
    def get_meas_from_sample(self, mail, key, s_id):
        '''
        Get a JSON with all measurements from a given sample
        input : mail and biorepo key, s_id (sample id)
        output : {"sample id": [{"measurement id": {"name": "my measurement name", "status": "public/private",
        "type": "raw/processed", "description": "my description", "URL(only if public)": "http...",
         "dynamic field": "my dynamic field, ..."}}, ...]}
        '''
        user = DBSession.query(User).filter(User._email == mail).first()
        user_lab = user.labs
        list_measurements = []
        dico_final = {}
        target = DBSession.query(Samples).filter(Samples.id == s_id).first()
        if target is None:
            return {'ERROR': "This sample ID does not exist."}
        sample_project = DBSession.query(Projects).filter(Projects.id == target.project_id).first()
        lab_target = sample_project.labs[0]
        #check if the project is owned by the user or his lab
        access_ok = False
        for l in user_lab:
            if l.id == lab_target.id:
                access_ok = True
        if access_ok:
            measurements = target.measurements
            if len(measurements) == 0:
                return {'ERROR': 'This project id : ' + str(target.id) + ' is empty.'}
            for m in measurements:
                dico_meas = {}
                dico_dynamic = {}
                meas_attributs = m.attributs
                meas_a_values = m.a_values
                parent_id = []
                if len(m.parents) > 0:
                    for p in m.parents:
                        parent_id.append(p.id)
                children_id = []
                if len(m.children) > 0:
                    for c in m.children:
                        children_id.append(c.id)
                for att in meas_attributs:
                    att_id = att.id
                    att_key = att.key
                    for val in meas_a_values:
                        value = val.value
                        if val.attribut_id == att_id:
                            #for the true weird checkbox
                            if value == "true":
                                dico_dynamic[att_key] = att_key
                            else:
                                dico_dynamic[att_key] = value
                #check the weird checkbox widget with "false" value
                if len(meas_attributs) != len(dico_dynamic.keys()):
                    for att in meas_attributs:
                        att_key = att.key
                        att_widget = att.widget
                        if att_key not in dico_dynamic.keys() and att_widget == "checkbox":
                            dico_dynamic[att_key] = "Not " + str(att_key)
                        elif att_key not in dico_dynamic.keys() and att_widget != "checkbox":
                            dico_dynamic[att_key] = "Not specified"

                m_type = "processed data"
                if m.type:
                    m_type = "raw data"
                m_status = "private"
                if m.status_type:
                    m_status = "public"

                dico_meas = {"name": m.name, "status": m_status, "type": m_type, "description": m.description, "parent_id": parent_id, "children_id": children_id}
                if check_boolean(m.status_type):
                    if len(m.fus) > 0:
                        for fu in m.fus:
                            sha1 = fu.sha1
                            filename = fu.filename
                        dico_meas["URL"] = "/biorepo/public/public_link?m_id=" + str(m.id) + "&sha1=" + str(sha1)
                        dico_meas["filename"] = filename
                dico_meas.update(dico_dynamic)
                list_measurements.append({m.id: dico_meas})
            dico_final[s_id] = list_measurements
            return json.dumps(dico_final)

        else:
            return json.dumps({'ERROR': "This sample is not a sample from your lab, you cannot access to it."})

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose('json')
    def get_my_fields(self, mail, key):
        '''
        Get a JSON with all the Projects/Samples/Measurements fields by lab
        input : mail and biorepo key
        output : {"lab": {"Projects": [field1, field2], "Samples": [field1, field2, field3],
        "Measurements": [field1, field2, field3, field4]}}
        '''
        dico_by_labs = {}
        dico_fields = {}
        user = DBSession.query(User).filter(User._email == mail).first()
        if user is None:
            return {'ERROR': "User " + mail + " not in BioRepo."}
        else:
            user_labs = user.labs
            if len(user_labs) > 0:
                for lab in user_labs:
                    lab_name = lab.name
                    fields_projects = {'id': 'auto assigned id', 'user_id': 'auto assigned id', 'project_name': 'free text', 'description': 'free text'}
                    fields_samples = {'id': 'auto assigned id', 'project_id': 'auto assigned id', 'name': 'free text', 'type': get_list_types(lab_name), 'protocole': 'free text'}
                    fields_meas = {'id': 'auto assigned id', 'user_id': 'auto assigned id', 'name': 'free text', 'description': 'free text', 'status_type': ['Public', 'Private'], 'type': ['Raw', 'Processed']}
                    lab_id = lab.id
                    sample_attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.owner == "sample", Attributs.deprecated == False)).all()
                    meas_attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.owner == "measurement", Attributs.deprecated == False)).all()
                    for s_att in sample_attributs:
                        if not s_att.deprecated and (s_att.widget == "textfield" or s_att.widget == "textarea" or s_att.widget == "hiding_textfield" or s_att.widget == "hiding_area"):
                            fields_samples[s_att.key] = "free text"
                        elif not s_att.deprecated and (s_att.widget == "singleselectfield" or s_att.widget == "multiselectfield" or s_att.widget == "hiding_singleselectfield" or s_att.widget == "hiding_multiselectfield"):
                            att_id = s_att.id
                            values = DBSession.query(Attributs_values).filter(and_(Attributs_values.attribut_id == att_id, Attributs_values.deprecated == False)).all()
                            list_v = []
                            for v in values:
                                if v.value not in list_v:
                                    list_v.append(v.value)
                            fields_samples[s_att.key] = list_v
                        elif not s_att.deprecated and (s_att.widget == "checkbox" or s_att.widget == "hiding_checkbox"):
                            fields_samples[s_att.key] = [s_att.key, "Not " + str(s_att.key)]

                    for m_att in meas_attributs:
                        if not m_att.deprecated and (m_att.widget == "textfield" or m_att.widget == "textarea" or m_att.widget == "hiding_textfield" or m_att.widget == "hiding_area"):
                            fields_meas[m_att.key] = "free text"
                        elif not m_att.deprecated and (m_att.widget == "singleselectfield" or m_att.widget == "multiselectfield" or m_att.widget == "hiding_singleselectfield" or m_att.widget == "hiding_multiselectfield"):
                            att_id = m_att.id
                            values = DBSession.query(Attributs_values).filter(and_(Attributs_values.attribut_id == att_id, Attributs_values.deprecated == False)).all()
                            list_v = []
                            for v in values:
                                if v.value not in list_v:
                                    list_v.append(v.value)
                            fields_meas[m_att.key] = list_v
                        elif not m_att.deprecated and (m_att.widget == "checkbox" or m_att.widget == "hiding_checkbox"):
                            fields_meas[s_att.key] = [m_att.key, "Not " + str(m_att.key)]
                    dico_fields["Projects"] = fields_projects
                    dico_fields["Samples"] = fields_samples
                    fields_samples = {}
                    dico_fields["Measurements"] = fields_meas
                    fields_meas = {}
                    dico_by_labs[str(lab.name) + '(' + str(lab.id) + ')'] = dico_fields
                    dico_fields = {}
                return dico_by_labs

            else:
                return {'ERROR': "This user " + mail + " has no lab. Contact the administrator please."}

    @require(has_any_permission(gl.perm_admin, gl.perm_user))
    @expose()
    def multi_meas_delete(self, p_id, s_id, mail, key):
        '''
        deleted ALL the measurements for a given sample
        /!\ IRREVERSIBLE /!\
        '''
        try:
            project = DBSession.query(Projects).filter(Projects.id == p_id).first()
            sample = DBSession.query(Samples).filter(Samples.id == s_id).first()
            user = DBSession.query(User).filter(User._email == mail).first()
            #checking
            print "--- Check your inputs... ---"
            if project is None:
                print "Project " + str(p_id) + " not found."
            if sample is None:
                print "Sample " + str(s_id) + " not found."
            if user is None:
                print "Your mail " + mail + " is not recorded in BioRepo."

            if project.id == sample.project_id and user.id == project.user_id:
                print "--- Begin the purge... ---"
                list_meas = sample.measurements
                print "Today, " + str(len(list_meas)) + " will die..."
                print "--------------------------"
                for m in list_meas:
                    list_fus = m.fus
                    for f in list_fus:
                        #delete the file on the server only if it is not used by anyone else anymore
                        if len(f.measurements) == 1 and not (f.path).startswith(HTS_path_data()) and not (f.path).startswith(HTS_path_archive()):
                            path_fu = f.path + "/" + f.sha1
                            mail = user._email
                            mail_tmp = mail.split('@')
                            path_mail = "AT".join(mail_tmp)
                            path_symlink = f.path + "/" + path_mail + "/" + f.sha1
                            DBSession.delete(f)
                            path_symlink = f.path + "/" + path_mail + "/" + f.sha1
                            try:
                                os.remove(path_symlink)
                            except:
                                print "---- path_symlink deleted yet ----"
                                pass
                            os.remove(path_fu)
                        elif (f.path).startswith(HTS_path_data()) or (f.path).startswith(HTS_path_archive()):
                            DBSession.delete(f)
                            #TODO send back something to hts to notify that it's not into biorepo anymore
                    print str(m.name) + "(" + str(m.id) + ") ... Sorry ... PAN."
                    DBSession.delete(m)
                    DBSession.flush()
                print "--- They are all died T_T ---"

            else:
                print "It's not your project/sample. The FBI was notified. Run."
        except:
            print_traceback()
            "Something went wrong...Please, don't cry."
