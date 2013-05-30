# -*- coding: utf-8 -*-
"""Sample Controller"""

from tgext.crud import CrudRestController
from biorepo.lib.base import BaseController
import tg
from tg import expose, flash, request, tmpl_context, validate, url, session
from repoze.what.predicates import has_any_permission
from tg.controllers import redirect
from biorepo.widgets.datagrids import SampleGrid
from biorepo.widgets.forms import build_form
from biorepo.model import DBSession, Samples, Measurements, Projects, Attributs, Attributs_values, Labs, User
from tg import app_globals as gl
from tg.decorators import paginate, with_trailing_slash
from biorepo import handler
from biorepo.lib import util, constant
#import pylons
from biorepo.lib.util import isAdmin, list_lower, check_boolean
from biorepo.lib.constant import list_ab_targets, list_cell_lines, list_cell_types,\
    list_dataType, list_organisms, list_types
from sqlalchemy import and_

__all__ = ['SampleController']


class SampleController(BaseController):
    allow_only = has_any_permission(gl.perm_admin, gl.perm_user)
    #model = Samples
    #table = sample_table
    #table_filler = sample_table_filler
    #edit_form = sample_edit_form
    #new_form = new_sample_form
    #edit_filler = sample_edit_filler

    @with_trailing_slash
    @expose('biorepo.templates.list')
    @expose('json')
    #@paginate('items', items_per_page=10)
    def index(self, *args, **kw):
        user = handler.user.get_user_in_session(request)

        # user sample
        #to block to one specific user
        #user_projects = [util.to_datagrid(project_grid, user.projects, "Projects Table", len(user.projects)>0)]
        user_lab = session.get("current_lab", None)
        admins = tg.config.get('admin.mails')
        mail = user.email
        if user_lab and mail not in admins:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
            attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).all()
            projects = [p.id for p in user.projects if p in lab.projects]
            samples = []
            for a in attributs:
                for s in a.samples:
                    if s not in samples and s.project_id in projects:
                        samples.append(s)
        elif mail in admins:
            samples = DBSession.query(Samples).all()

        all_samples = [util.to_datagrid(SampleGrid(), samples, "Samples Table", len(samples) > 0)]

        return dict(page='samples', model='sample', form_title="new sample", items=all_samples, value=kw)

    @expose('biorepo.templates.new_sample')
    def new(self, *args, **kw):
        #take the logged user
        user = handler.user.get_user_in_session(request)
        user_lab = session.get("current_lab", None)
        if user_lab:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
        #take the logged user projects
        #projects = user.projects
        projects = DBSession.query(Projects).filter(Projects.user_id == user.id).all()
        for p in projects:
            if p not in lab.projects:
                projects.remove(p)

        new_form = build_form("new", "sample", None)(action=url('/samples/post')).req()
        #static fields
        new_form.child.children[0].options = [(project.id, '%s' % project.project_name) for project in projects]
        new_form.child.children[1].placeholder = "Your sample name..."
        new_form.child.children[2].options = list_types
        new_form.child.children[3].placeholder = "Your protocole here..."

        return dict(page='samples', widget=new_form)

    @expose('biorepo.templates.edit_sample')
    def edit(self, *args, **kw):

        user = handler.user.get_user_in_session(request)
        sample = DBSession.query(Samples).filter(Samples.id == args[0]).first()
        admin = isAdmin(user)
        user_lab = session.get("current_lab", None)
        if user_lab:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()

        if admin:
            projects = DBSession.query(Projects).all()
            measurements = DBSession.query(Measurements).all()
        else:
            projects = DBSession.query(Projects).filter(Projects.user_id == user.id).all()
            for p in projects:
                if p not in lab.projects:
                    projects.remove(p)
            #measurements = DBSession.query(Measurements).filter(Measurements.user_id == user.id).all()
            attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).all()
            measurements = []
            for a in attributs:
                for m in a.measurements:
                    if m not in measurements and m.user_id == user.id:
                        measurements.append(m)

        if sample.get_userid == user.id or admin:

            edit_form = build_form("edit", "sample", sample.id)(action=url('/samples/post_edit'))
            edit_form.child.children[0].value = sample.id
            projects_list = [(p.id, '%s' % p.project_name) for p in projects]
            edit_form.child.children[1].options = projects_list
            id_project = DBSession.query(Projects.id).filter(Projects.id == sample.project_id).first()
            #measurement(s) attached to the sample
            list_unselected = [m for m in measurements if m not in sample.measurements]
            meas_selected = [(meas.id, '%s' % (meas.name)) for meas in list_unselected] + [(meas.id, '%s' % (meas.name), {'selected': True}) for meas in sample.measurements]
            edit_form.child.children[1].value = id_project[0]
            edit_form.child.children[2].value = sample.name
            edit_form.child.children[3].options = list_types
            edit_form.child.children[3].value = sample.type
            edit_form.child.children[4].value = sample.protocole
            edit_form.child.children[5].options = meas_selected

            return dict(page='samples', widget=edit_form.req(), value=kw)
        else:
            flash("It is not your sample -> you are not allowed to edit this sample", 'error')
            raise redirect('/samples')

    @expose('json')
    def create(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        kw['user'] = user.id
        lab = kw.get("lab", None)
        if lab is None:
            return {"ERROR": "We need to know the lab of the user..."}
        sample = Samples()
        if not kw.has_key('project_id'):
            return {"ERROR": "project_id missing"}
        type_ = kw.get('type', None)
        sample.project_id = kw['project_id']
        sample.name = kw.get('name', 'Give me a name please')

        if type_ is not None:
            try:
                ret1 = list_lower(type_, list_types)
                sample.type = ret1
            except:
                return {"ERROR": "your " + type_ + " is not known in types list"}
        elif type_ is None:
            sample.type = type_

        sample.protocole = kw.get('protocole', None)

        get_meas = kw.get('measurements', None)
        l = []
        if get_meas is None:
            sample.measurements = l
        else:
            for x in get_meas.split(','):
                meas = DBSession.query(Measurements).filter(Measurements.id == x).first()
                l.append(meas)

            sample.measurements = l
        #print server
        print sample, "building sample with wget"

        #dynamicity
        list_static = ['project', 'name', 'type', 'protocole', 'measurements', 'lab', 'user', 'key', 'mail', 'project_id']
        list_dynamic = []
        labo = DBSession.query(Labs).filter(Labs.name == lab).first()
        lab_id = labo.id

        #save the attributs of the lab for final comparison
        dynamic_keys = []
        lab_attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False, Attributs.owner == "sample")).all()
        for i in lab_attributs:
            dynamic_keys.append(i.key)

        for x in kw:
            #exclude the static fields belonging to Samples()
            if x not in list_static:
                list_dynamic.append(x)
                #get the attribut
                a = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == x, Attributs.deprecated == False, Attributs.owner == "sample")).first()
                if a is not None:
                    #get its value(s)
                    (sample.attributs).append(a)
                    #if values of the attribute are fixed
                    if a.fixed_value == True and kw[x] is not None and kw[x] != '' and a.widget != "checkbox":
                        value = kw[x]
                        list_value = DBSession.query(Attributs_values).filter(Attributs_values.attribut_id == a.id).all()
                        for v in list_value:
                            #if the keyword value is in the value list, the attributs_values object is saved in the cross table
                            if v.value == value:
                                (sample.a_values).append(v)
                                DBSession.flush()
                    #if values of the attribute are free
                    elif a.fixed_value == False and a.widget != "checkbox":
                        av = Attributs_values()
                        av.attribut_id = a.id
                        av.value = kw.get(x, None)
                        av.deprecated = False
                        DBSession.add(av)
                        DBSession.flush()
                        (sample.a_values).append(av)
                        DBSession.flush()
                    #special case for checkbox because of the "on" and None value of TW2 for True and False...(here it's True)
                    elif a.widget == "checkbox":
                        #Why 3 ? Because 3 cases max registred : True, False and None ---> so <3
                        if len(a.values) < 3:
                            av = Attributs_values()
                            av.attribut_id = a.id
                            #for True value, Attribut key and value have to be similar into the excel sheet...
                            if (kw[x]).lower() == x.lower():
                                av.value = True
                            #...and different for the False :)
                            else:
                                av.value = False
                            av.deprecated = False
                            DBSession.add(av)
                            DBSession.flush()
                            (sample.a_values).append(av)
                            DBSession.flush()
                        else:
                            if (kw[x]).lower() == x.lower():
                                for v in a.values:
                                    if check_boolean(v.value) and v.value is not None:
                                        (sample.a_values).append(v)
                            else:
                                for v in a.values:
                                    if check_boolean(v.value) == False and v.value is not None:
                                        (sample.a_values).append(v)

                            DBSession.flush()

        #to take in account the empty dynamic fields in the excel sheet
        for k in dynamic_keys:
            if k not in list_dynamic:
                print k, " -------------------- NOT FOUND IN SAMPLE DESCRIPTION EXCEL SHEET"
                a = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == k, Attributs.deprecated == False, Attributs.owner == "sample")).first()
                (sample.attributs).append(a)
                DBSession.flush()

        DBSession.add(sample)
        DBSession.flush()

        return {"sample": sample, "measurements": l}

    @expose()
    def post(self, *args, **kw):
        #user = handler.user.get_user_in_session(request)
        user_lab = session.get("current_lab", None)
        lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
        lab_id = lab.id
        s = Samples()
        list_static = ['project', 'name', 'type', 'protocole']
        list_dynamic = []
        #new sample object
        if 'project' not in kw:
            flash("You have to choose a project to attach to your new sample, retry please", "error")
            raise redirect('./')
        s.project_id = kw['project']
        #TODO : make a correct validator for NewSample
        if kw['name'] == '':
            flash("Bad Sample : you have to give a name to your sample", "error")
            raise redirect('./new')
        s.name = kw['name']
        s.type = kw.get('type', None)
        s.protocole = kw.get('protocole', None)
        DBSession.add(s)
        DBSession.flush()

        #link the new sample to the attributs object
        for x in kw:
            #exclude the static fields belonging to Samples()
            if x not in list_static:
                list_dynamic.append(x)
                #get the attribut
                a = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == x, Attributs.deprecated == False, Attributs.owner == "sample")).first()
                if a is not None:
                    #get its value(s)
                    (s.attributs).append(a)
                    #if values of the attribute are fixed
                    if a.fixed_value == True and kw[x] is not None and kw[x] != '' and a.widget != "checkbox":
                        value = kw[x]
                        list_value = DBSession.query(Attributs_values).filter(Attributs_values.attribut_id == a.id).all()
                        for v in list_value:
                            #if the keyword value is in the value list, the attributs_values object is saved in the cross table
                            if v.value == value:
                                (s.a_values).append(v)
                                DBSession.flush()
                    #if values of the attribute are free
                    elif a.fixed_value == False and a.widget != "checkbox":
                        av = Attributs_values()
                        av.attribut_id = a.id
                        av.value = kw.get(x, None)
                        av.deprecated = False
                        DBSession.add(av)
                        DBSession.flush()
                        (s.a_values).append(av)
                        DBSession.flush()
                    #special case for checkbox because of the "on" and None value of TW2 for True and False...(here it's True)
                    elif a.widget == "checkbox":
                        found = False
                        for v in a.values:
                            if check_boolean(v.value) and v.value is not None:
                                (s.a_values).append(v)
                                found = True
                        if not found:
                            av = Attributs_values()
                            av.attribut_id = a.id
                            av.value = True
                            av.deprecated = False
                            DBSession.add(av)
                            DBSession.flush()
                            (s.a_values).append(av)
                            DBSession.flush()

        #special case for checkbox because of the "on" and None value of TW2 for True and False...(here it's False)
        dynamic_booleans = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False, Attributs.owner == "sample", Attributs.widget == "checkbox")).all()
        if len(dynamic_booleans) > 0:
            for d in dynamic_booleans:
                if d.key not in list_dynamic:
                    if d.widget == "checkbox":
                        found = False
                        for v in d.values:
                            if not check_boolean(v.value) and v.value is not None:
                                (s.attributs).append(d)
                                (s.a_values).append(v)
                                found = True
                        if not found:
                            av = Attributs_values()
                            av.attribut_id = d.id
                            av.value = False
                            av.deprecated = False
                            DBSession.add(av)
                            DBSession.flush()
                            (s.attributs).append(d)
                            (s.a_values).append(av)
                            DBSession.flush()

        flash("Sample created !")
        raise redirect('/samples')

    @expose()
    def post_edit(self, *args, **kw):
        id_sample = kw['IDselected']
        sample = DBSession.query(Samples).filter(Samples.id == id_sample).first()
        try:
            project_id = kw.get("project")
            if project_id is None or project_id == "":
                flash("Edition rejected : Your sample must be in a project", 'error')
                raise redirect("./")
            sample.project_id = project_id
            #sample.project_id = project_id
        except:
            flash("Your sample must be in a project", 'error')
            raise redirect("./")

        if kw['name'] == '' or kw['name'] is None:
            flash("Bad Sample : you have to give a name to your sample", "error")
            raise redirect("./edit/" + id_sample)
        sample.name = kw.get("name", None)
        sample.protocole = kw.get("protocole", None)
        sample.type = kw.get("type", None)
        meas_ids = kw.get("measurements", None)
        if meas_ids is not None:
            if not isinstance(meas_ids, (list, tuple)):
                meas_ids = [int(meas_ids)]
            else:
                #from unicode to integer for comparison
                list_tmp = []
                for i in meas_ids:
                    i = int(i)
                    list_tmp.append(i)
                meas_ids = list_tmp
        else:
            meas_ids = []
        list_meas = []
        for m in meas_ids:
            measurement = DBSession.query(Measurements).filter(Measurements.id == m).first()
            list_meas.append(measurement)
        sample.measurements = list_meas

        #DYNAMICITY
        list_static = ['project', 'name', 'type', 'protocole', 'IDselected', 'measurements']
        list_attributs = []
        list_a_values = sample.a_values
        for a in sample.attributs:
            if a.deprecated == False:
                list_attributs.append(a)

        for x in kw:
            if x not in list_static:
                for a in list_attributs:
                    if x == a.key:
                        object_2_delete = None
                        #search if the field was edited
                        for v in list_a_values:
                            if v.attribut_id == a.id and v.value != kw[x] and a.widget != "multipleselectfield":
                                object_2_delete = v
                        if a.widget == "textfield" or a.widget == "textarea":
                            if object_2_delete:
                                object_2_delete.value = kw[x]

                        elif a.widget == "checkbox":
                            if len(a.values) < 3:
                                for old_v in a.values:
                                    if old_v.value is not None and old_v.value != '':
                                        list_a_values.remove(old_v)
                                av = Attributs_values()
                                av.attribut_id = a.id
                                av.value = True
                                av.deprecated = False
                                DBSession.add(av)
                                list_a_values.append(av)
                                DBSession.flush()

                            elif len(a.values) == 3:
                                if object_2_delete:
                                    list_a_values.remove(object_2_delete)
                                for val in a.values:
                                    val_to_avoid = [None, "", object_2_delete.value]
                                    if val.value not in val_to_avoid:
                                        list_a_values.append(val)
                            else:
                                print "boolean with more thant 2 values"
                                raise

                        elif a.widget == "singleselectfield":
                            #edition : delete the connexion to the older a_value, make the connexion between the new a_value and the sample
                            if object_2_delete:
                                list_a_values.remove(object_2_delete)
                                list_possible = a.values
                                for p in list_possible:
                                    if p.value == kw[x]:
                                        list_a_values.append(p)

                        elif a.widget == "multipleselectfield":
                            #!!! NOT TESTED !!!
                            list_objects_2_delete = []
                            for v in list_a_values:
                                #warning : types of i and v.value have to be similar...
                                for i in kw[x]:
                                    if v.attribut_id == a.id and v.value != i:
                                        list_objects_2_delete.append(v)
                                    if len(list_objects_2_delete) > 0:
                                        for v in list_objects_2_delete:
                                            list_a_values.remove(v)

                                        if a.fixed_value == True:
                                            to_add = DBSession.query(Attributs_values).filter(and_(Attributs_values.value == i, Attributs_values.attribut_id == a.id)).first()
                                            list_a_values.append(to_add)
                                        else:
                                            #mutliple selected field can't be not a fixed value.
                                            print "something wrong happenned - illogical - controller sample post_edit()"
                                            raise
        #special case for checkbox because of the "on" and None value of TW2 for True and False... (Here it's False)
        lab = session.get('current_lab', None)
        labo = DBSession.query(Labs).filter(Labs.name == lab).first()
        lab_id = labo.id
        dynamic_booleans = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False, Attributs.owner == "sample", Attributs.widget == "checkbox")).all()

        if len(dynamic_booleans) > 0:
            for b in dynamic_booleans:
                if b.key not in kw:
                    list_value = b.values
                    #2 cases possibles
                    #1 : values are None and (True or False)
                    if len(list_value) == 2:
                        for v in list_value:
                            #1.1 : None and True
                            if v.value is not None:
                                val = check_boolean(v.value)
                            else:
                                val = None
                            if val == True:
                                list_a_values.remove(v)
                                av = Attributs_values()
                                av.attribut_id = b.id
                                av.value = False
                                av.deprecated = False
                                DBSession.add(av)
                                list_a_values.append(av)
                                DBSession.flush()
                                break
                            #1.2 : None and False
                            elif val == False:
                                #because nothing was edited for the field
                                pass
                    #2 : values are None, True and False
                    elif len(list_value) == 3:
                        for v in list_value:
                            if v.value is not None:
                                val = check_boolean(v.value)
                            else:
                                val = None
                            if val == True:
                                try:
                                    list_a_values.remove(v)
                                except:
                                    pass
                            elif val == False:
                                list_a_values.append(v)

        flash("Sample edited !")
        raise redirect("./")

    @expose('genshi:tgext.crud.templates.put')
    def put(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        tmpl_context.projects = user.projects

        return CrudRestController.put(self, *args, **kw)

    @expose('genshi:tgext.crud.templates.post_delete')
    def delete(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        sample = DBSession.query(Samples).filter(Samples.id == args[0]).first()
        admin = isAdmin(user)

        if sample.get_userid == user.id or admin:
            try:
                flash("Your sample " + str(sample.name) + " has been deleted with success")
            except:
                flash("Your sample " + (sample.name) + " has been deleted with success")
            DBSession.delete(sample)
            DBSession.flush()
            raise redirect("/samples")
        #TO CHECK : check if sample get already an user as owner
        elif sample.get_userid == None or admin:
            DBSession.delete(sample)
            DBSession.flush()
            flash("Your sample has been deleted")
            raise redirect("/samples")
        else:
            flash("It is not your sample -> you are not allowed to delete it", 'error')
            raise redirect('/samples')

    # @expose('genshi:tgext.crud.templates.get_delete')
    # def get_delete(self, *args, **kw):

    #     return CrudRestController.get_delete(self, *args, **kw)

    #TEST

    @expose('json')
    def fetch_cell_types(self):
        return dict(data=constant.list_cell_types)
