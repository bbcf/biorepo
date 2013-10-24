# -*- coding: utf-8 -*-
"""Measurement Controller"""
from tgext.crud import CrudRestController
from biorepo.lib.base import BaseController
import tg
from tg import expose, flash, request
from repoze.what.predicates import has_any_permission
from tg.controllers import redirect
from biorepo.widgets.forms import build_form, EditMeas, NewTrackHub
from biorepo.widgets.datagrids import MeasGrid
from biorepo.model import DBSession, Measurements, User, Samples, Projects, Files_up, Attributs, Attributs_values, Labs
from tg import app_globals as gl
from tg.decorators import paginate, with_trailing_slash
from biorepo import handler
from biorepo.lib import util
from tg import url, validate, response

import os
from pkg_resources import resource_filename
from biorepo.lib.constant import path_processed, path_raw, path_tmp, dico_mimetypes, list_types_extern, HTS_path_data, HTS_path_archive
from biorepo.lib.util import sha1_generation_controller, create_meas, manage_fu, manage_fu_from_HTS, isAdmin, name_org, check_boolean, display_file_size
from tg import session
import cgi
from sqlalchemy import and_
import genshi
import socket
from random import randint
import uuid
import json

import datetime
date_format = "%d/%m/%Y"

#FOR THE DATA UPLOAD
public_dirname = os.path.join(os.path.abspath(resource_filename('biorepo', 'public')))
#data_dirname = os.path.join(public_dirname, 'data')


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
        if list_parents == "null":
            flash("Select one or several parent(s) measurement(s) please", 'error')
            raise redirect(url('/search'))
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
        url_bool_tmp = kw.get('url_up', False)
        url_bool = check_boolean(url_bool_tmp)
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
        #nb : tmp_path is None when user gave just an url and didn't want to upload the file into BioRepo
        if tmp_path is not None:
            fu_ = manage_fu(existing_fu, meas, public_dirname, filename, sha1, local_path, url_path, url_bool, dest_raw, dest_processed, tmp_path, lab)
            if url_path is not None:
                if meas.description is None:
                    meas.description = "Attached file uploaded from : " + url_path
                else:
                    meas.description = meas.description + "\nAttached file uploaded from : " + url_path
            else:
                if meas.description is None:
                    meas.description = "Attached file : " + filename
                else:
                    meas.description = meas.description + "\nAttached file : " + filename
        else:
            fu_ = None
            if meas.description is None:
                meas.description = "URL PROVIDED : " + url_path
            else:
                meas.description = meas.description + "\nURL PROVIDED : " + url_path
            DBSession.add(meas)
            DBSession.flush()

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
                            if (v.value).lower() == value.lower():
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
        if fu_:
            return {"meas_id": meas.id, "fu_id": fu_.id, "fu_filename": fu_.filename, "fu_url": fu_.url_path}
        else:
            return {"meas_id": meas.id}

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

        if vitalit_path is not None and (not vitalit_path.startswith("/scratch/el/biorepo/dropbox/"
        ) and not vitalit_path.startswith("/scratch/cluster/dropbox/biorepo/")):
            flash("Sorry, your Vital-IT path must begin with '/scratch/el(or cluster)/biorepo/dropbox/'", "error")
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
                                #to avoid IntegrityError in the db
                                break
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
            #if it is a HTSstation archive
            if x.path.startswith('/archive/epfl/bbcf/'):
                path_fu = x.path + "/" + x.filename
            #or not
            else:
                path_fu = x.path + "/" + x.sha1
            extension = x.extension
            filename = x.filename
            file_size = os.path.getsize(path_fu)
            response.content_length = file_size
            if dico_mimetypes.has_key(extension):
                response.content_type = dico_mimetypes[extension]
            else:
                response.content_type = 'text/plain'
            response.headers['X-Sendfile'] = path_fu
            response.headers['Content-Disposition'] = 'attachement; filename=%s' % (filename)
            response.content_length = '%s' % (file_size)
            return None

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
                            #if the value was "None", just add the new value edited
                            elif object_2_delete is None:
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
        list_fus = measurement.fus
        admin = isAdmin(user)

        if measurement.user_id == user.id or admin:
            try:
                flash("Your measurement " + str(measurement.name) + " has been deleted with success")
            except:
                flash("Your measurement " + (measurement.name) + " has been deleted with success")
            #TO TEST
            for f in list_fus:
                #delete the file on the server only if it is not used by anyone else anymore
                if len(f.measurements) == 1 and not (f.path).startswith(HTS_path_data()) and not (f.path).startswith(HTS_path_archive()):
                    path_fu = f.path + "/" + f.sha1
                    mail = user._email
                    mail_tmp = mail.split('@')
                    path_mail = "AT".join(mail_tmp)
                    path_symlink = f.path + "/" + path_mail + "/" + f.sha1
                    DBSession.delete(f)
                    if admin:
                        user_id = measurement.user_id
                        owner = DBSession.query(User).filter(User.id == user_id).first()
                        mail_owner = owner._email
                        mail_owner_tmp = mail_owner.split('@')
                        path_mail_owner = "AT".join(mail_owner_tmp)
                        path_symlink = f.path + "/" + path_mail_owner + "/" + f.sha1
                    else:
                        path_symlink = f.path + "/" + path_mail + "/" + f.sha1
                    os.remove(path_symlink)
                    os.remove(path_fu)
                elif (f.path).startswith(HTS_path_data()) or (f.path).startswith(HTS_path_archive()):
                    DBSession.delete(f)
                    #TODO send back something to hts to notify that it's not into biorepo anymore

            DBSession.delete(measurement)
            DBSession.flush()
            raise redirect("/measurements")
        else:
            flash("It is not your data -> you are not allowed to delete it", 'error')
            raise redirect(url('/measurements'))

    @expose('json')
    def info_display(self, meas_id):
        #TODO : make display by lab and put this one as the default one.
        meas = DBSession.query(Measurements).filter(Measurements.id == meas_id).first()
        if meas:
            name = meas.name
            meas_descr = meas.description
            list_fus = meas.fus
            list_parents = meas.parents
            par = ""
            #the measurement get a file attached to and is generated from other(s)
            if len(list_fus) > 0 and len(list_parents) > 0:
                for f in list_fus:
                    ext = f.extension
                    filename = f.filename
                    path_fu = f.path + "/" + f.sha1
                    file_size = os.path.getsize(path_fu)
                    final_size = display_file_size(file_size)
                for p in list_parents:
                    #p_obj = DBSession.query(Measurements).filter(Measurements.id == p).first()
                    par = par + p.name + " (id:" + str(p.id) + ")" + " | "
                #delete the last " | "
                par = par[:-3]
                #display the bam or the bam.bai related... or not :)
                if ext.lower() == "bam":
                    bai_name = filename + ".bai"
                    bai_obj = DBSession.query(Files_up).filter(Files_up.filename == bai_name).first()
                    if bai_obj is None:
                        list_meas = []
                    else:
                        list_meas = bai_obj.measurements
                    for m in list_meas:
                        lab_name = session.get("current_lab")
                        lab = DBSession.query(Labs).filter(Labs.name == lab_name).first()
                        list_meas_owners = DBSession.query(User).filter(User.id == m.user_id).all()
                        for u in list_meas_owners:
                            if lab in u.labs:
                                bai_m_id = m.id
                                return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'From': par, 'Size': final_size, 'bai measurement id': bai_m_id}
                    #if .bam.bai is not found
                    return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'From': par, 'Size': final_size, 'bai measurement id': ' NOT FOUND IN BioRepo db'}
                elif ext.lower() == "bam.bai" or ext.lower() == "bai":
                    bam_name = filename[:-4]
                    bam_obj = DBSession.query(Files_up).filter(Files_up.filename == bam_name).first()
                    if bam_obj is None:
                        list_meas = []
                    else:
                        list_meas = bam_obj.measurements
                    for m in list_meas:
                        lab_name = session.get("current_lab")
                        lab = DBSession.query(Labs).filter(Labs.name == lab_name).first()
                        list_meas_owners = DBSession.query(User).filter(User.id == m.user_id).all()
                        for u in list_meas_owners:
                            if lab in u.labs:
                                bam_m_id = m.id
                            return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'From': par, 'Size': final_size, 'bam measurement id ': bam_m_id}
                    #if bam is not found
                    return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'From': par, 'Size': final_size, 'bam measurement id': ' NOT FOUND IN BioRepo db'}
                else:
                    return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'From': par, 'Size': final_size}

            #no parent(s)
            elif len(list_fus) > 0 and len(list_parents) == 0:
                for f in list_fus:
                    ext = f.extension
                    filename = f.filename
                    path_fu = f.path + "/" + f.sha1
                    file_size = os.path.getsize(path_fu)
                    final_size = display_file_size(file_size)
                #display the bam or the bam.bai related... or not :)
                if ext.lower() == "bam":
                    bai_name = filename + ".bai"
                    bai_obj = DBSession.query(Files_up).filter(Files_up.filename == bai_name).first()
                    if bai_obj is None:
                        list_meas = []
                    else:
                        list_meas = bai_obj.measurements
                    for m in list_meas:
                        lab_name = session.get("current_lab")
                        lab = DBSession.query(Labs).filter(Labs.name == lab_name).first()
                        list_meas_owners = DBSession.query(User).filter(User.id == m.user_id).all()
                        for u in list_meas_owners:
                            if lab in u.labs:
                                bai_m_id = m.id
                                return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'Size': final_size, 'bai measurement id ': bai_m_id}
                    #if .bam.bai is not found
                    return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'Size': final_size, 'bai measurement id': ' NOT FOUND IN BioRepo db'}
                elif ext.lower() == "bam.bai" or ext.lower() == "bai":
                    bam_name = filename[:-4]
                    bam_obj = DBSession.query(Files_up).filter(Files_up.filename == bam_name).first()
                    if bam_obj is None:
                        list_meas = []
                    else:
                        list_meas = bam_obj.measurements
                    for m in list_meas:
                        lab_name = session.get("current_lab")
                        lab = DBSession.query(Labs).filter(Labs.name == lab_name).first()
                        list_meas_owners = DBSession.query(User).filter(User.id == m.user_id).all()
                        for u in list_meas_owners:
                            if lab in u.labs:
                                bam_m_id = m.id
                                return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'Size': final_size, 'bam measurement id ': bam_m_id}
                    #if bam is not found
                    return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'Size': final_size, 'bam measurement id': ' NOT FOUND IN BioRepo db'}
                else:
                    return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'Extension': ext, 'Filename': filename, 'Size': final_size}

            #no file attached
            elif len(list_fus) == 0 and len(list_parents) > 0:
                for p in list_parents:
                    #p_obj = DBSession.query(Measurements).filter(Measurements.id == p).first()
                    par = par + p.name + " (id:" + str(p.id) + ")" + " | "
                #delete the last " | "
                par = par[:-3]
                return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr, 'From': par}
            else:
                return {'Measurement': name + " (id:" + meas_id + ")", 'Description': meas_descr}
        else:
            return {'Error': 'Problem with this measurement, contact your administrator'}

    @expose()
    def external_add(self, *args, **kw):
        '''
        used to upload a file from another web application
        Just need the url of the file
        '''
        user = handler.user.get_user_in_session(request)
        user_id = user.id
        lab = session.get('current_lab', None)
        labo = DBSession.query(Labs).filter(Labs.name == lab).first()
        lab_id = labo.id
        #get the initial kws from the external app which
        backup_dico = session.get("backup_kw")
        file_path = backup_dico["file_path"]
        description = backup_dico["description"]
        project_name = backup_dico["project_name"]
        sample_name = backup_dico["sample_name"]
        sample_type = backup_dico["sample_type"]

        #test sha1
        tmp_dirname = os.path.join(public_dirname, path_tmp(lab))
        if file_path.startswith("http://"):
            sha1, filename, tmp_path = sha1_generation_controller(None, file_path, True, tmp_dirname)
        else:
            sha1, filename, tmp_path = sha1_generation_controller(file_path, None, False, tmp_dirname)
        filename_tmp = filename.split('.')
        name_without_ext = filename_tmp[0]
        #new measurement management
        new_meas = Measurements()
        dest_raw = path_raw(lab) + User.get_path_perso(user)
        dest_processed = path_processed(lab) + User.get_path_perso(user)

        #create project and sample
        project = DBSession.query(Projects).filter(and_(Projects.user_id == user_id, Projects.project_name == project_name)).first()
        if project is None or labo not in project.labs:
            project = Projects()
            project.project_name = project_name
            project.user_id = user_id
            #HTS spec
            if "project_description" in backup_dico:
                project.description = backup_dico["project_description"]
            (project.labs).append(labo)
            DBSession.add(project)
            DBSession.flush()

        sample = DBSession.query(Samples).filter(and_(Samples.project_id == project.id, Samples.name == sample_name)).first()
        if sample is None:
            sample = Samples()
            sample.project_id = project.id
            sample.name = sample_name
            for t in list_types_extern:
                if t.lower() == sample_type.lower():
                    sample.type = t
                    break
                else:
                    sample.type = "External_app_sample"
            DBSession.add(sample)
            DBSession.flush()
            #sample dynamicity
            labo_attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False, Attributs.owner == "sample")).all()
            if len(labo_attributs) > 0:
                for a in labo_attributs:
                    sample.attributs.append(a)

                    if a.fixed_value == True and a.widget != "checkbox":
                        DBSession.flush()
                    #if values of the attribute are free
                    elif a.fixed_value == False and a.widget != "checkbox":
                        av = Attributs_values()
                        av.attribut_id = a.id
                        av.value = None
                        av.deprecated = False
                        DBSession.add(av)
                        DBSession.flush()
                        (sample.a_values).append(av)
                        DBSession.flush()
                    elif a.widget == "checkbox":
                        found = False
                        for v in a.values:
                            if not check_boolean(v.value) and v.value is not None:
                                (sample.a_values).append(v)
                                found = True
                        if not found:
                            av = Attributs_values()
                            av.attribut_id = a.id
                            av.value = False
                            av.deprecated = False
                            DBSession.add(av)
                            DBSession.flush()
                            (sample.a_values).append(av)
                            DBSession.flush()

        list_sample_id = []
        list_sample_id.append(sample.id)

        meas = create_meas(user, new_meas, name_without_ext, description, False,
                False, list_sample_id, None, dest_raw, dest_processed)

        #file upload management
        existing_fu = DBSession.query(Files_up).filter(Files_up.sha1 == sha1).first()
        #from HTSstation
        HTS = False
        if tmp_path.startswith("/data") or tmp_path.startswith("/archive/epfl"):
            try:
                manage_fu_from_HTS(existing_fu, meas, filename, sha1, file_path, tmp_path)
                HTS = True
            except:
                if "callback" in backup_dico:
                    return str(backup_dico["callback"]) + "(" + json.dumps({"error": "Problem with the file path"}) + ")"
                else:
                    print "no call back"
                    return json.dumps({"error": "No callback detected"})

        #not from HTSstation
        else:
            manage_fu(existing_fu, meas, public_dirname, filename, sha1, None, file_path, True, dest_raw, dest_processed, tmp_path, lab)
        #nice description's end
        meas.description = meas.description + "\nAttached file uploaded from : " + project_name
        DBSession.add(meas)
        DBSession.flush()
        #measurement dynamicity
        lab_attributs = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False, Attributs.owner == "measurement")).all()
        if len(lab_attributs) > 0:
            for a in lab_attributs:
                meas.attributs.append(a)

                if a.fixed_value == True and a.widget != "checkbox":
                    DBSession.flush()
                #if values of the attribute are free
                elif a.fixed_value == False and a.widget != "checkbox":
                    av = Attributs_values()
                    av.attribut_id = a.id
                    av.value = None
                    av.deprecated = False
                    DBSession.add(av)
                    DBSession.flush()
                    (meas.a_values).append(av)
                    DBSession.flush()
                elif a.widget == "checkbox":
                    found = False
                    for v in a.values:
                        if not check_boolean(v.value) and v.value is not None:
                            (meas.a_values).append(v)
                            found = True
                    if not found:
                        av = Attributs_values()
                        av.attribut_id = a.id
                        av.value = False
                        av.deprecated = False
                        DBSession.add(av)
                        DBSession.flush()
                        (meas.a_values).append(av)
                        DBSession.flush()
        #answer for HTSstation
        if HTS:
            if "callback" in backup_dico:
                return str(backup_dico["callback"]) + "(" + json.dumps({"meas_id": meas.id, "key": project.description}) + ")"
            else:
                print "no call back"
                return json.dumps({"error": "No callback detected"})
        #or normal redirect for others
        else:
            flash("Your measurement id " + str(meas.id) + " was succesfully saved into BioRepo")
            raise redirect(url('/search'))

    @expose('biorepo.templates.new_trackhub')
    def trackHubUCSC(self, *args, **kw):
        '''
        :meas_id in kw is a string of one or several measurements id which are coma separated
        '''
        meas_ids = kw.get("meas_id", None)
        list_meas = []
        try:
            #several ids case
            for i in meas_ids.split(','):
                measu = DBSession.query(Measurements).filter(Measurements.id == i).all()
                for j in measu:
                    list_meas.append(j)
        except:
            #single id case
            for i in meas_ids:
                measu = DBSession.query(Measurements).filter(Measurements.id == i).all()
                for j in measu:
                    list_meas.append(j)
        list_extensions = []
        list_assemblies = []
        for m in list_meas:
            #test if export out of BioRepo is allowed
            if m.status_type == False:
                flash("One or several measurements selected are not allowed to get out of BioRepo. Edit them from private to public if you can/want", 'error')
                return redirect(url('/search'))

            #test extensions
            list_file = m.fus
            if len(list_file) > 0:
                for f in list_file:
                    ext = f.extension
                    if ext not in list_extensions:
                        list_extensions.append(ext)
            else:
                flash("One or several measurements selected don't get file attached (just url). Impossible to link it/them into a trackhub", 'error')
                return redirect(url('/search'))

            #test assembly
            list_attributs = m.attributs
            for a in list_attributs:
                if a.key == "assembly":
                    list_assembly_values = a.values
                    for v in list_assembly_values:
                        if v in m.a_values and v.value not in list_assemblies:
                            list_assemblies.append(v.value)
        if len(list_extensions) > 1:
            flash("Different type of extensions are not allowed.", 'error')
            return redirect(url('/search'))
        elif len(list_assemblies) > 1:
            flash("Different assemblies are not allowed.", 'error')
            return redirect(url('/search'))
        elif len(list_extensions) == 0:
            flash("Problem with file extension : not found", 'error')
            return redirect(url('/search'))
        elif len(list_assemblies) == 0:
            flash("You must set assembly to your measurements. Edit them.", 'error')
            return redirect(url('/search'))

        files = []
        for m in list_meas:
            for f in m.fus:
                if f not in files:
                    files.append(f)
        for a in list_assemblies:
            assembly = a
        for e in list_extensions:
            extension = e

        #fill the form
        new_th = NewTrackHub(action=url('/measurements/post_trackHub')).req()
        new_th.child.children[0].placeholder = "Your trackhub name..."
        new_th.child.children[1].value = assembly
        new_th.child.children[2].options = [(f.id, '%s' % f.filename, {'selected': True}) for f in files]
        new_th.child.children[3].value = extension

        return dict(page='measurements/trackhub', widget=new_th)

    @expose()
    def post_trackHub(self, *args, **kw):
        '''
        build and put the trackhubs on bbcf-serv01 to /data/epfl/bbcf/biorepo/trackhubs/LAB/USERMAIL
        '''
        #Thx to Jonathan SOBEL (jonathan.sobelATepfl.ch) for his help.
        #He read the entire UCSC TrackHub Doc (even Chuck Norris did not) and explained it to me. This man is a hero.
        ## /!\ Don't forget to symlink the trackHubs path into the /public directory during the BioRepo installation /!\
        assembly = str(kw["assembly"])
        extension = str(kw["extension"])
        file_ids = kw["files"]

        hostname = socket.gethostname().lower()
        #because of aliasing
        if hostname == "ptbbsrv2.epfl.ch":
            hostname = "biorepo.epfl.ch"

        dico_ext_container = {"bigwig": "multiWig", "bw": "multiWig", "bigbed": "multiBed", "bam": "multiBam"}
        dico_ext_type = {"bw": "bigWig", "bb": "bigBed", "bigbed": "bigBed", "bam": "bam"}
        #paths preparation
        th_dest_path = "/data/epfl/bbcf/biorepo/trackHubs/"
        user = handler.user.get_user_in_session(request)
        user_lab = session.get('current_lab', None)
        if user_lab is None:
            flash("Lab error. Report it to your administrator", 'error')
            raise redirect(url('/search'))
        tmp_mail = (user._email).split('@')
        user_mail = tmp_mail[0] + "AT" + tmp_mail[1]
        path_completion = user_lab + "/" + user_mail + "/"
        lab_path = th_dest_path + user_lab
        final_path = th_dest_path + path_completion
        #building destination path if not built yet
        try:
            if not os.path.exists(lab_path):
                os.mkdir(lab_path)
                os.mkdir(final_path)
            if not os.path.exists(final_path):
                os.mkdir(final_path)
        except:
            print "!!!!!!!!!!!!!! /data/epfl/bbcf/biorepo/trackhubs/ NOT ACCESSIBLE !!!!!!!!!!!!!!!!!"
            flash("Internal error. /data is not accessible. You can contact your administrator.", "error")
            raise redirect(url('/search'))

        if kw['name'] == u'':
            #generate a random name
            kw['name'] = str(uuid.uuid4()).split('-')[0]
        kw['name'] = kw['name'].encode('ascii', 'ignore')
        kw['name'] = kw['name'].replace(' ', '_')
        trackhub_dest = final_path + kw['name']

        kw['name'] = str(kw['name'])

        #if a directory with the same name is here
        if os.path.exists(trackhub_dest):
            trackhub_dest = trackhub_dest + "_" + str(uuid.uuid4()).split('-')[0]
            os.mkdir(trackhub_dest)
        else:
            os.mkdir(trackhub_dest)
        #last directory level creation
        assembly_path = trackhub_dest + "/" + assembly
        os.mkdir(assembly_path)
        ########### end of the directories creation #############
        #time to create hub.txt, genome.txt, /assembly and /assembly/trackDB.txt
        hub = trackhub_dest + "/hub.txt"
        genome = trackhub_dest + "/genomes.txt"
        trackDB = assembly_path + "/trackDb.txt"
        #hub.txt - give the trackhub path to UCSC and others nominative information
        shortLabel = str(kw['name']).split('_')[0]
        longLabel = str(kw['name'])
        #short and long lab can't be the same (stupid UCSC...)
        if shortLabel == longLabel:
            longLabel = longLabel + "_1"
        with open(hub, "a") as h:
            h.write("hub " + trackhub_dest.split('/')[-1] + "\n" + "shortLabel " + shortLabel + "\n" +
                "longLabel " + longLabel + "\n" + "genomesFile genomes.txt" + "\n" +
                "email " + str(user._email) + "\n")
        #genome.txt - first line assembly, second line trackDB.txt path
        with open(genome, "a") as g:
            g.write("genome " + assembly + "\n" + "trackDb " + assembly + "/trackDb.txt")
        #trackDB.txt - THE important file of the thing, big thx to UCSC and guys who developped it for the horrible way to build all this sh*t ><
        with open(trackDB, "a") as t:
            #file header
            t.write("track " + str(kw['name']) + "\n" + "container " + dico_ext_container[extension.lower()] + "\n" +
                "shortLabel " + shortLabel + "\n" + "longLabel " + longLabel + "\n" +
                "type " + dico_ext_type[extension.lower()] + "\n" + "visibility full\n" + "maxHeightPixels 70:70:32\n" + "configurable on\n" +
                "aggregate transparentOverlay\n" + "showSubtrackColorOnUi on\n" + "priority 1.0\n\n")
            #tracks
            list_files = []
            try:
                #several ids case
                for i in file_ids.split(','):
                    fu = DBSession.query(Files_up).filter(Files_up.id == i).all()
                    for j in fu:
                        list_files.append(j)
            except:
                #single id case
                for i in file_ids:
                    fu = DBSession.query(Files_up).filter(Files_up.id == i).all()
                    for j in fu:
                        list_files.append(j)
            for f in list_files:
                t.write("\t" + "track " + str(f.filename) + "\n" +
                        "\t" + "parent " + str(kw['name']) + "\n" +
                        "\t" + "bigDataUrl http://" + hostname + url("/public/public_link?sha1=" + str(f.sha1) + "\n" +
                        "\t" + "shortLabel " + shortLabel + "\n" +
                        "\t" + "longLabel " + longLabel + "\n" +
                        "\t" + "type " + dico_ext_type[extension.lower()] + "\n" +
                        "\t" + "autoScale on" + "\n" +
                        "\t" + "color " + str(randint(0, 255)) + "," + str(randint(0, 255)) + "," + str(randint(0, 255)) + "\n\n"))

        #build the final hub_url accessible
        track_name = hub.split('/')[-2]
        hub_name = hub.split('/')[-1]
        hub_url = "http://" + hostname + url("/trackHubs/") + user_lab + "/" + user_mail + "/" + track_name + "/" + hub_name
        print "####### Trackhub " + longLabel + " successfully created by " + str(user.firstname) + " " + str(user.name)
        raise redirect('http://genome.ucsc.edu/cgi-bin/hgTracks?hubUrl=' + hub_url + "&db=" + assembly)
