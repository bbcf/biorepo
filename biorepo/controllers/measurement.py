# -*- coding: utf-8 -*-
"""Measurement Controller"""
from tgext.crud import CrudRestController
from biorepo.lib.base import BaseController
import tg
from tg import expose, flash, request
from repoze.what.predicates import has_any_permission
from tg.controllers import redirect
from biorepo.widgets.forms import build_form, EditMeas
from biorepo.widgets.datagrids import MeasGrid
from biorepo.model import DBSession, Measurements, User, Samples, Projects, Files_up, Attributs, Attributs_values, Labs
from tg import app_globals as gl
from tg.decorators import paginate, with_trailing_slash
from biorepo import handler
from biorepo.lib import util
from tg import url, validate, response

import os
from pkg_resources import resource_filename
from biorepo.lib.constant import path_processed, path_raw, path_tmp, list_assemblies, dico_mimetypes
from biorepo.lib.util import sha1_generation_controller, create_meas, manage_fu, isAdmin, name_org, check_boolean
from tg import session
import cgi
from sqlalchemy import and_
import genshi

import datetime
date_format = "%d/%m/%Y"

#FOR THE DATA UPLOAD
public_dirname = os.path.join(os.path.abspath(resource_filename('biorepo', 'public')))
#data_dirname = os.path.join(public_dirname, 'data')

#sha1 dico


__all__ = ['MeasurementController']


class MeasurementController(BaseController):
    allow_only = has_any_permission(gl.perm_admin, gl.perm_user)
    #model = Measurements
    # table = measurement_table
    # table_filler = measurement_table_filler
    # edit_form = measurement_edit_form
    # new_form = new_measurement_form
    # edit_filler = measurement_edit_filler

    @with_trailing_slash
    @expose('biorepo.templates.list')
    @expose('json')
    #@paginate('items', items_per_page=10)
    def index(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        admins = tg.config.get('admin.mails')
        mail = user.email
        # user data
        #to block to one specific user
        #user_data = [util.to_datagrid(data_grid, user.datas, "Datas Table", len(user.datas)>0)]
        user_lab = session.get("current_lab", None)
        if user_lab and mail not in admins:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
            attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).all()
            measurements = []
            for a in attributs:
                for m in a.measurements:
                    if m not in measurements and m.user_id == user.id:
                        measurements.append(m)
        elif mail in admins:
            measurements = DBSession.query(Measurements).all()

        all_measurements = [util.to_datagrid(MeasGrid(), measurements, "Measurements Table", len(measurements) > 0)]

        # shared projects
        #TODO check with permissions

        return dict(page='measurements', model='measurement', form_title="new measurement", items=all_measurements,
                    value=kw)

    #BROWSER VERSION
    @expose('biorepo.templates.new_meas')
    def new(self, *args, **kw):
        #tmpl_context.widget = new_measurement_form
        #take the logged user
        user = handler.user.get_user_in_session(request)
        user_lab = session.get('current_lab', None)
        samples = []
        if user_lab is not None:
            lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
            attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).all()
            projects = [p.id for p in user.projects if p in lab.projects]
            for a in attributs:
                for s in a.samples:
                    if s not in samples and s.project_id in projects:
                        samples.append(s)
        #take the logged user samples
        #samples = DBSession.query(Samples).join(Projects).join(User).filter(User.id == user.id).all()
        #samples = DBSession.query(Samples).join(Projects).join(User).filter(and_(User.id == user.id, lab in user.labs)).all()
        meas = DBSession.query(Measurements).all()

        #make_son (button "upload as child of..." in /search)
        list_meas = []
        list_parents = kw.get('parents', None)
        if list_parents is not None:
            listID = list_parents
            try:
                for i in listID.split(','):
                    measu = DBSession.query(Measurements).filter(Measurements.id == i).all()
                    for j in measu:
                        list_meas.append(j)
            except:
                for i in listID:
                    measu = DBSession.query(Measurements).filter(Measurements.id == i).all()
                    for j in measu:
                        list_meas.append(j)

        parents = list_meas
        #kw['parents']=parents
        kw['parents'] = parents

        new_form = build_form("new", "meas", None)(action=url('/measurements/post')).req()
        new_form.child.children[3].options = [(sample.id, '%s' % (sample.name)) for sample in samples]
        new_form.child.children[6].options = [(m.id, '%s (%s)' % (m.name, m.id), {'selected': True}) for m in parents]

        #DYNAMICITY
        #use user_lab
        #PTBB
        #
        #LVG
        #
        #UPDUB
        return dict(page='measurements', widget=new_form)

    @expose('biorepo.templates.edit_meas')
    def edit(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        measurement = DBSession.query(Measurements).filter(Measurements.id == args[0]).first()
        admin = isAdmin(user)
        if admin:
            samples = DBSession.query(Samples).all()
        else:
            user_lab = session.get('current_lab', None)
            samples = []
            if user_lab is not None:
                lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
                attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab.id, Attributs.deprecated == False)).all()
                projects = [p.id for p in user.projects if p in lab.projects]
                for a in attributs:
                    for s in a.samples:
                        if s not in samples and s.project_id in projects:
                            samples.append(s)
        fus = measurement.fus
        #TODO : change if it will be possible to multiupload in a measurement form
        for i in fus:
            fu = i
        #admin = isAdmin(user)
        kw['user'] = user.id
        kw['description'] = measurement.description
        if measurement.get_userid == user.id or admin:
            #samples selected
            list_unselected = [s for s in samples if s not in measurement.samples]
            samples_selected = [(sample.id, '%s' % (sample.name)) for sample in list_unselected] + [(sample.id, '%s' % (sample.name), {'selected': True}) for sample in measurement.samples]
            #parents selected
            edit_form = build_form("edit", "meas", measurement.id)(action=url('/measurements/post_edit')).req()
            edit_form.child.children[0].value = measurement.id
            edit_form.child.children[1].value = measurement.name
            edit_form.child.children[2].value = measurement.description
            edit_form.child.children[3].options = samples_selected
            edit_form.child.children[4].value = measurement.status_type
            edit_form.child.children[5].value = measurement.type
            parents = measurement.parents
            edit_form.child.children[6].options = [(m.id, '%s (%s)' % (m.name, m.id), {'selected': True}) for m in parents]
            try:
                edit_form.child.children[7].value = fu.filename
                edit_form.child.children[8].value = fu.url_path
            except:
                edit_form.child.children[7].value = "NO FILE"
                try:
                    url_tmp = (measurement.description).split('URL added : ')
                    str(url_tmp[1])
                except:
                    url_tmp = (measurement.description).split('URL PROVIDED : ')
                try:
                    if len(url_tmp) > 2:
                        n = len(url_tmp) - 1
                        url_tmp2 = url_tmp[n].split('\n')
                    else:
                        url_tmp2 = url_tmp[1].split('\n')
                    url_path = url_tmp2[0]
                    edit_form.child.children[8].value = url_path
                except:
                    edit_form.child.children[8].value = None

            return dict(page='measurements', widget=edit_form, value=kw)
        else:
            flash("It is not your data -> you are not allowed to edit it", 'error')
            raise redirect(url('/measurements'))

    #COMMAND LINE VERSION
    @expose('json')
    def create(self, *args, **kw):
        #TODO : for version 2, upgrade the checking of the url
        user = handler.user.get_user_in_session(request)
        lab = kw.get("lab", None)
        if lab is None:
            return {"ERROR": "We need to know the lab of the user..."}

        tmp_dirname = os.path.join(public_dirname, path_tmp(lab))
        local_path = kw.get('path', None)
        if local_path is not None and local_path.endswith("/"):
            return {"ERROR": "your file is not in the archive or you made a mistake with its name"}
        url_path = kw.get('url_path', None)
        url_bool = kw.get('url_up', False)
        #testing the sha1 and generate it with other stuff of interest
        sha1, filename, tmp_path = sha1_generation_controller(local_path, url_path, url_bool, tmp_dirname)

        #new measurement management
        new_meas = Measurements()
        dest_raw = path_raw(lab) + User.get_path_perso(user)
        dest_processed = path_processed(lab) + User.get_path_perso(user)

        #correction for the kw from the multi_upload.py
        status_type = kw.get('status_type', True)
        if status_type == "True":
            status_type = True
        elif status_type == "False":
            status_type = False

        type_ = kw.get('type', True)
        if type_ == "True":
            type_ = True
        elif type_ == "False":
            type_ = False

        meas = create_meas(user, new_meas, kw.get('name', None), kw.get('description', None), status_type,
                type_, kw.get('samples', None), kw.get('parent_id', None), dest_raw, dest_processed)

        #print serveur
        print meas, "building measurement with wget"
        #file upload management
        existing_fu = DBSession.query(Files_up).filter(Files_up.sha1 == sha1).first()

        fu_ = manage_fu(existing_fu, meas, public_dirname, filename, sha1, local_path, url_path, url_bool, dest_raw, dest_processed, tmp_path, lab)
        #dynamicity
        list_static = ['upload', 'url_path', 'path', 'url_up', 'parents', 'name', 'description', 'user_id', 'status_type', 'type', 'samples', 'IDselected', 'lab', 'key', 'mail', 'vitalit_path', 'upload_way']
        list_dynamic = []
        labo = DBSession.query(Labs).filter(Labs.name == lab).first()
        lab_id = labo.id
        #save the attributs of the lab for final comparison
        dynamic_keys = []
        lab_attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False, Attributs.owner == "measurement")).all()
        for i in lab_attributs:
            dynamic_keys.append(i.key)

        #check each dynamic kw
        for x in kw:
            if x not in list_static:
                list_dynamic.append(x)
                #get the attribut
                a = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == x, Attributs.deprecated == False, Attributs.owner == "measurement")).first()
                if a is not None:
                    #get its value(s)
                    (meas.attributs).append(a)
                    #if values of the attribute are fixed
                    if a.fixed_value == True and kw[x] is not None and kw[x] != '' and a.widget != "checkbox":
                        value = kw[x]
                        list_value = DBSession.query(Attributs_values).filter(Attributs_values.attribut_id == a.id).all()
                        for v in list_value:
                            #if the keyword value is in the value list, the attributs_values object is saved in the cross table
                            if v.value == value:
                                (meas.a_values).append(v)
                                DBSession.flush()
                    #if values of the attribute are free
                    elif a.fixed_value == False and a.widget != "checkbox":
                        av = Attributs_values()
                        av.attribut_id = a.id
                        av.value = kw.get(x, None)
                        if av.value == '':
                            av.value = None
                        av.deprecated = False
                        DBSession.add(av)
                        DBSession.flush()
                        (meas.a_values).append(av)
                        DBSession.flush()
                    #
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
                            (meas.a_values).append(av)
                            DBSession.flush()
                        else:
                            if (kw[x]).lower() == x.lower():
                                for v in a.values:
                                    if check_boolean(v.value) and v.value is not None:
                                        (meas.a_values).append(v)
                            else:
                                for v in a.values:
                                    if check_boolean(v.value) == False and v.value is not None:
                                        (meas.a_values).append(v)

                            DBSession.flush()

        #to take in account the empty dynamic fields in the excel sheet
        for k in dynamic_keys:
            if k not in list_dynamic:
                print k, "--------- NOT FOUND IN MEASUREMENTS DESCRIPTION IN EXCEL SHEET"
                a = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == k, Attributs.deprecated == False, Attributs.owner == "measurement")).first()
                (meas.attributs).append(a)
                DBSession.flush()

        return {"meas_id": meas.id, "fu_id": fu_.id, "fu_filename": fu_.filename, "fu_url": fu_.url_path}

    #@validate(new_measurement_form, error_handler=new)
    @expose('genshi:tgext.crud.templates.post')
    def post(self, *args, **kw):
        #TODO : for version 2, upgrade the checking of the url
        #define the request type
        #request_type = "browser"
        user = handler.user.get_user_in_session(request)
        lab = session.get('current_lab', None)
        if lab is None:
            flash("Sorry, something wrong happened with your lab id. Retry or contact admin.", "error")
            raise redirect('./measurements')
        #TODO recuperer la session pour l'id du lab ou le nom du lab
        tmp_dirname = os.path.join(public_dirname, path_tmp(lab))
        local_path = kw['upload']
        #if not local_path:
        if isinstance(local_path, cgi.FieldStorage) and not getattr(local_path, 'filename'):
            local_path = None
        if local_path == '':
            local_path = None
        url_path = kw.get('url_path', None)
        if url_path == '':
            url_path = None
        url_bool = kw.get('url_up', False)
        #change TW1 -> TW2 : True == on and False == None
        if url_bool == "on":
            url_bool = True
        elif url_bool is None:
            url_bool = False

        vitalit_path = kw.get("vitalit_path", None)
        if vitalit_path == '':
            vitalit_path = None

        #make_son (button "upload as child of..." in /search) #TODO juste mettre les ids
        list_meas = []
        list_parents = kw.get('parents', None)
        if list_parents is not None:
            listID = list_parents
            try:
                for i in listID.split(','):
                    measu = DBSession.query(Measurements).filter(Measurements.id == i).all()
                    for j in measu:
                        list_meas.append(i)
            except:
                for i in listID:
                    measu = DBSession.query(Measurements).filter(Measurements.id == i).all()
                    for j in measu:
                        list_meas.append(j)

        kw['parents'] = list_meas
        list_s = kw.get('samples', None)
        if list_s is not None and type(list_s) is not list:
            list_s = [list_s]

        if vitalit_path is not None and not vitalit_path.startswith("/scratch/biorepo/dropbox/"):
            flash("Sorry, your Vital-IT path must begin with '/scratch/biorepo/dropbox/'", "error")
            raise redirect('./new')
        elif local_path is None and url_path is None and vitalit_path is None:
            flash("Bad Measurement : You have to give a file or an url with it.", "error")
            raise redirect("./new")

        else:
            #testing the sha1 and generate it with other stuff of interest
            if not url_bool and local_path is None:
                sha1, filename, tmp_path = sha1_generation_controller(vitalit_path, url_path, url_bool, tmp_dirname)
            elif vitalit_path is None:
                sha1, filename, tmp_path = sha1_generation_controller(local_path, url_path, url_bool, tmp_dirname)
            else:
                flash("Sorry, you have to choose one and only one way to attach the file to the measurement", "error")
                raise redirect('./measurements')
        #testing the sha1 and generate it with other stuff of interest
        #sha1, filename, tmp_path = sha1_generation_controller(local_path, url_path, url_bool, tmp_dirname)

        #new measurement management
        new_meas = Measurements()
        dest_raw = path_raw(lab) + User.get_path_perso(user)
        dest_processed = path_processed(lab) + User.get_path_perso(user)
        if kw['name'] == '' or kw['name'] is None:
            flash("Bad Measurement : You have to give a name to your measurement.", "error")
            raise redirect("./new")
        meas = create_meas(user, new_meas, kw['name'], kw['description'], kw.get('status_type', False), kw.get('type', False),
        list_s, kw['parents'], dest_raw, dest_processed)

        #file upload management
        existing_fu = DBSession.query(Files_up).filter(Files_up.sha1 == sha1).first()
        #nb : tmp_path is None when user gave just an url and didn't want to upload the file into BioRepo
        if tmp_path is not None:
            manage_fu(existing_fu, meas, public_dirname, filename, sha1, local_path, url_path, url_bool, dest_raw, dest_processed, tmp_path, lab)
            if url_path is not None:
                meas.description = meas.description + "\nAttached file uploaded from : " + url_path
            else:
                meas.description = meas.description + "\nAttached file : " + filename
        else:
            meas.description = meas.description + "\nURL PROVIDED : " + url_path
            DBSession.add(meas)
            DBSession.flush()
        #dynamicity
        list_static = ['upload', 'url_path', 'url_up', 'parents', 'name', 'description', 'user_id', 'status_type', 'type', 'samples', 'IDselected', 'vitalit_path', 'upload_way']
        list_dynamic = []
        labo = DBSession.query(Labs).filter(Labs.name == lab).first()
        lab_id = labo.id

        for x in kw:
            if x not in list_static:
                list_dynamic.append(x)
                #get the attribut
                a = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == x, Attributs.deprecated == False, Attributs.owner == "measurement")).first()
                if a is not None:
                    #get its value(s)
                    (meas.attributs).append(a)
                    #if values of the attribute are fixed
                    if a.fixed_value == True and kw[x] is not None and kw[x] != '' and a.widget != "checkbox":
                        value = kw[x]
                        list_value = DBSession.query(Attributs_values).filter(Attributs_values.attribut_id == a.id).all()
                        for v in list_value:
                            #if the keyword value is in the value list, the attributs_values object is saved in the cross table
                            if v.value == value:
                                (meas.a_values).append(v)
                                DBSession.flush()
                    #if values of the attribute are free
                    elif a.fixed_value == False and a.widget != "checkbox":
                        av = Attributs_values()
                        av.attribut_id = a.id
                        av.value = kw.get(x, None)
                        av.deprecated = False
                        DBSession.add(av)
                        DBSession.flush()
                        (meas.a_values).append(av)
                        DBSession.flush()
                    #special case for checkbox because of the "on" and None value of TW2 for True and False... (Here it's True)
                    elif a.widget == "checkbox":
                        found = False
                        for v in a.values:
                            if check_boolean(v.value) and v.value is not None:
                                (meas.a_values).append(v)
                                found = True
                        if not found:
                            av = Attributs_values()
                            av.attribut_id = a.id
                            av.value = True
                            av.deprecated = False
                            DBSession.add(av)
                            DBSession.flush()
                            (meas.a_values).append(av)
                            DBSession.flush()

        #special case for checkbox because of the "on" and None value of TW2 for True and False... (Here it's False)
        dynamic_booleans = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False, Attributs.owner == "measurement", Attributs.widget == "checkbox")).all()
        if len(dynamic_booleans) > 0:
            for d in dynamic_booleans:
                if d.key not in list_dynamic:
                    if d.widget == "checkbox":
                        found = False
                        for v in d.values:
                            if not check_boolean(v.value) and v.value is not None:
                                (meas.attributs).append(d)
                                (meas.a_values).append(v)
                                found = True
                        if not found:
                            av = Attributs_values()
                            av.attribut_id = d.id
                            av.value = False
                            av.deprecated = False
                            DBSession.add(av)
                            DBSession.flush()
                            (meas.attributs).append(d)
                            (meas.a_values).append(av)
                            DBSession.flush()

        raise redirect("./")

    @expose()
    def download(self, meas_id, *args, **kw):
        meas = DBSession.query(Measurements).filter(Measurements.id == meas_id).first()
        list_fus = meas.fus
        if list_fus == []:
            try:
                msg_tmp = (meas.description).split('URL PROVIDED')
                msg_tmp2 = msg_tmp[1].split('\n')
                msg_url = msg_tmp2[0]
                flash("Sorry, there is no file attached with this measurement. You can download it here " + msg_url, 'error')
            except:
                flash("Sorry, there is nothing (no file, no URL) attached with this measurement. Check if it is really usefull or edit/delete it please.", 'error')

            raise redirect('/search')
        #TODO manage the possibility of multi fus for one meas ---> multidownload()
        for x in list_fus:
            path_fu = x.path + "/" + x.sha1
            extension = x.extension
            filename = x.filename
            if dico_mimetypes.has_key(extension):
                response.content_type = dico_mimetypes[extension]
                response.headerlist.append(('Content-Disposition', 'attachment;filename=' + filename))
            else:
                response.content_type = 'text/plain'
                response.headerlist.append(('Content-Disposition', 'attachment;filename=' + filename))

        return open(path_fu).read()

    @expose()
    def post_edit(self, *args, **kw):
        id_meas = kw['IDselected']
        if kw['name'] == '' or kw['name'] is None:
            flash("Bad Measurement : You have to give a name to your measurement.", "error")
            raise redirect("./edit/" + id_meas)
        measurement = DBSession.query(Measurements).filter(Measurements.id == id_meas).first()
        measurement.name = kw['name']
        measurement.description = kw['description']
        status_type_tmp = kw.get("status_type", False)
        measurement.status_type = check_boolean(status_type_tmp)
        type_tmp = kw.get("type", False)
        measurement.type = check_boolean(type_tmp)
        samples = kw.get('samples', None)
        list_samples = []
        if samples is not None:
            if type(samples) is list:
                for s in samples:
                    sample = DBSession.query(Samples).filter(Samples.id == s).first()
                    list_samples.append(sample)
            else:
                sample = DBSession.query(Samples).filter(Samples.id == samples).first()
                list_samples.append(sample)
        else:
            list_samples = []
        measurement.samples = list_samples

        now = str((datetime.datetime.now()).strftime(date_format))
        if kw['url_path']:
            if measurement.fus:
                fu = measurement.fus
                for f in fu:
                    if kw['url_path'] != f.url_path:
                        measurement.description = measurement.description + "\nEdited " + now + " - new URL : " + kw['url_path']
                        f.url_path = kw['url_path']
            else:
                url_tmp = (measurement.description).split('URL PROVIDED : ')
                try:
                    url_tmp2 = url_tmp[1].split('\n')
                    url_path = url_tmp2[0]
                except:
                    url_path = ''
                if kw['url_path'].strip() != url_path.strip():
                    measurement.description = measurement.description + "\nEdited " + now + " URL added : " + kw['url_path']
                else:
                    measurement.description = measurement.description + "\nEdited " + now

        #DYNAMICITY
        list_static = ['project', 'name', 'type', 'protocole', 'IDselected', 'measurements']
        list_attributs = []
        list_a_values = measurement.a_values
        for a in measurement.attributs:
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
                            #edition : delete the connexion to the older a_value, make the connexion between the new a_value and the measurement
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
                                            to_add = DBSession.query(Attributs_values).filter(and_(Attributs_values.value == i), Attributs_values.attribut_id == a.id).first()
                                            list_a_values.append(to_add)
                                        else:
                                            #multiple selected field can't be not a fixed value.
                                            print "something wrong happenned - illogical - controller sample post_edit()"
                                            pass
        #special case for checkbox because of the "on" and None value of TW2 for True and False... (Here it's False)
        lab = session.get('current_lab', None)
        labo = DBSession.query(Labs).filter(Labs.name == lab).first()
        lab_id = labo.id
        dynamic_booleans = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False, Attributs.owner == "measurement", Attributs.widget == "checkbox")).all()

        if len(dynamic_booleans) > 0:
            for b in dynamic_booleans:
                if b.key not in kw:
                    list_value = b.values
                    #2 cases possibles
                    #1 : values are None and (True or False)
                    if len(list_value) == 2:
                        for v in list_value:
                            #1.1 : None and True
                            val = check_boolean(v.value)
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

        flash("Measurement edited !")
        raise redirect("./")

    @expose()
    def delete(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        measurement = DBSession.query(Measurements).filter(Measurements.id == args[0]).first()
        admin = isAdmin(user)

        if measurement.user_id == user.id or admin:
            try:
                flash("Your measurement " + str(measurement.name) + " has been deleted with success")
            except:
                flash("Your measurement " + (measurement.name) + " has been deleted with success")
            DBSession.delete(measurement)
            DBSession.flush()
            raise redirect("/measurements")
        else:
            flash("It is not your data -> you are not allowed to delete it", 'error')
            raise redirect(url('/measurements'))

    # @expose('genshi:tgext.crud.templates.get_delete')
    # def get_delete(self, *args, **kw):
    #     user = handler.user.get_user_in_session(request)
    #     return CrudRestController.get_delete(self, *args, **kw)

    @expose()
    def UCSC(self, *args, **kw):
        #redirect into UCSC genome browser
        list_meas_id = kw['meas_id']
        list_meas_files = []
        print list_meas_id, "<<---- list meas id"
        print type(list_meas_id)
        test_assembly = []
        if list_meas_id == "null":
            #TODO : fix the bug !
            flash("Sorry but you selected nothing to visualise into UCSC genome browser", 'error')
            raise redirect('http://localhost:8080/search')
        else:
            for i in list_meas_id.split(','):
                measu = DBSession.query(Measurements).filter(Measurements.id == i).all()
                #test if the selected measurements belong to the same assembly
                for j in measu:
                    print j, "j"
                    test_assembly.append(j.assembly)
                    meas_file = j.fus
                    print meas_file, "meas_file"
                    ext = meas_file[0].extension
                    print ext, "ext"
                    pack_info_meas = j.status_type, meas_file[0].sha1, ext
                    print pack_info_meas
                    list_meas_files.append(pack_info_meas)
                print list_meas_files, "list_meas_files"
                test_assembly = list(set(test_assembly))
                if len(test_assembly) > 1:
                    flash("Sorry, conflict between different assemblies detected", 'error')
                    raise redirect('/search')
                else:
                    db = test_assembly[0]
                    print db, "db"
                    org = name_org(db)
                    print org, "org"
                    #TODO build un .txt ou un JSON avec les url dedans et rendre le fichier ou le return accessible sur une page
                    #for m in list_meas_files:
                        #statut = m.statut
