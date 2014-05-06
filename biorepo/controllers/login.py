# -*- coding: utf-8 -*-
"""Login controller."""

from biorepo.lib.base import BaseController
from biorepo.lib import tequila
from tg import expose, url, flash, request, response
from tg.controllers import redirect
from biorepo.model import User, Group, Labs, Attributs, Attributs_values, DBSession
from paste.auth import auth_tkt
from biorepo.config.app_cfg import token
from paste.request import resolve_relative_url
#import transaction
import datetime
from tg import app_globals as gl
import tg
import ConfigParser
from biorepo.lib.constant import path_conf_labs, path_conf_unit, path_raw, path_processed, path_tmp
from sqlalchemy import and_
from tg import session
from biorepo.lib.util import check_boolean
try:
    import simplejson as json
except ImportError:
    import json
import tw2.forms as twf
from biorepo.widgets.forms import LabChoice

__all__ = ['LoginController']


class LoginController(BaseController):

    @expose('biorepo.templates.index')
    def index(self):
        '''
        Redirect user on tequila page in order to log him
        '''
        u = resolve_relative_url(url(), request.environ)
        res = tequila.create_request(u + '/login/auth', 'tequila.epfl.ch')
        raise redirect('https://tequila.epfl.ch/cgi-bin/tequila/requestauth?request' + res)

    @expose('biorepo.templates.index')
    def auth(self, came_from='/', **kw):
        '''
        Fetch user back from tequila.
        Validate the key from tequila.
        Log user.
        '''
        if not kw.has_key('key'):
            raise redirect(came_from)

        # take parameters
        key = kw.get('key')
        environ = request.environ
        authentication_plugins = environ['repoze.who.plugins']
        identifier = authentication_plugins['ticket']
        secret = identifier.secret
        cookiename = identifier.cookie_name
        remote_addr = environ['REMOTE_ADDR']
        # get user
        principal = tequila.validate_key(key, 'tequila.epfl.ch')
        if principal is None:
            raise redirect('./login')

        #in case of user gets several labs
        try:
            if session["first_passage"] == False:
                #second passage
                tmp_user = session["tmp_user"]
                tmp_lab = session['tmp_lab']
        except:
            #first passage
            session["first_passage"] = True
            session["principal_tequila"] = principal
            session.save()
            tmp_user, tmp_lab = self.build_user(principal)
        try:
            mail = tmp_user.email
        except:
            flash("Sorry, you've been disconnected. You can try to relog yourself now", 'error')
            raise redirect('/login/out')
        # log or create him
        user = DBSession.query(User).filter(User.email == tmp_user.email).first()
        if user is None:
            user_group = DBSession.query(Group).filter(Group.name == gl.group_users).first()
            user_group.users.append(tmp_user)
            DBSession.add(tmp_user)
            DBSession.flush()

            user = DBSession.query(User).filter(User.email == mail).first()
            flash(u'Your account has been created  %s' % (user.firstname + ' ' + user.name, ))
            DBSession.flush()
            print "######################"
            print "key user :", user.key

        elif user.name == gl.tmp_user_name:
            user.name = tmp_user.name
            user._set_date(datetime.datetime.now())
            user_group = DBSession.query(Group).filter(Group.name == gl.group_users).first()
            user_group.users.append(tmp_user)
            flash(u'Your account has been created %s' % (user.firstname + ' ' + user.name, ))
            DBSession.add(user)
            DBSession.flush()
            print "######################"
            print "key user :", user.key
            #transaction.commit()
        else:
            #flash(u'Welcome back ' + user.firstname + ' ' + user.name, 'notice')
            #flash(u'Welcome back %s' % (u'' +user.firstname + ' ' + user.name, 'notice'))
            flash('Welcome back')
            print "######################"
            print "key user :", user.key

        #create his/her lab
        lab = DBSession.query(Labs).filter(Labs.name == tmp_lab.name).first()
        if lab is None:
            tmp_lab.users.append(user)
            DBSession.add(tmp_lab)
            DBSession.flush()
            #import transaction
            #transaction.commit()
            lab = DBSession.query(Labs).filter(Labs.name == tmp_lab.name).first()
            print "lab created : ", lab
        else:
            if lab not in user.labs:
                lab.users.append(user)
                DBSession.flush()

            print "lab existing : ", lab

        #create attributs / check existing attributs
        attributs = DBSession.query(Attributs).filter(Attributs.lab_id == lab.id).all()
        if len(attributs) == 0:
            attributs = None
        lab_id = lab.id
        #parsing "unit".ini
        config = ConfigParser.RawConfigParser()
        config.read(path_conf_unit(lab.name))
        list_sample_att = (config.get('samples_attributs:main', 'keys')).split(',')
        list_sample_hiding = (config.get('samples_hiding:main', 'keys')).split(',')
        if len(list_sample_hiding) == 1 and list_sample_hiding[0] == '':
            list_sample_hiding = ''
        list_measurement_att = (config.get('meas_attributs:main', 'keys')).split(',')
        list_meas_hiding = (config.get('meas_hiding:main', 'keys')).split(',')
        if len(list_meas_hiding) == 1 and list_meas_hiding[0] == '':
            list_meas_hiding = ''
        list_searchable = (config.get('searchable_attributs:main', 'keys')).split(',')
        list_deprecated = (config.get('deprecated_attributs:main', 'keys')).split(',')
        dict_att_values_sample = {}
        dict_att_values_meas = {}
        dict_widgets_sample_att = {}
        dict_widgets_meas_att = {}
        dict_hiding_s_att = {}
        dict_hiding_m_att = {}
        for x in list_sample_att:
            dict_att_values_sample[x] = (config.get('samples_attributs:' + x, x)).split(',')
            dict_widgets_sample_att[x] = (config.get('samples_attributs:' + x, 'widget')).split(',')
        for x in list_measurement_att:
            dict_att_values_meas[x] = (config.get('meas_attributs:' + x, x)).split(',')
            dict_widgets_meas_att[x] = (config.get('meas_attributs:' + x, 'widget')).split(',')

        #hidingradiobutton lists
        #samples
        if isinstance(list_sample_hiding, list):
            for x in list_sample_hiding:
                dic_mapping = {}
                list_possibilities = (config.get('samples_attributs:' + x, x)).split(',')
                for p in list_possibilities:
                    attribs_by_poss = (config.get('samples_attributs:' + x, p + "_mapping")).split(',')
                    dic_mapping[p] = attribs_by_poss
                dict_hiding_s_att[x] = dic_mapping
        if len(dict_hiding_s_att.keys()) > 0:
            session["hiding_sample"] = dict_hiding_s_att
        else:
            session["hiding_sample"] = {}
        #measurements
        if isinstance(list_meas_hiding, list):
            for x in list_meas_hiding:
                dic_mapping = {}
                list_possibilities = (config.get('meas_attributs:' + x, x)).split(',')
                for p in list_possibilities:
                    attribs_by_poss = (config.get('meas_attributs:' + x, p + "_mapping")).split(',')
                    dic_mapping[p] = attribs_by_poss
                dict_hiding_m_att[x] = dic_mapping
        if len(dict_hiding_m_att.keys()) > 0:
            session["hiding_meas"] = dict_hiding_m_att
        else:
            session["hiding_meas"] = {}
        session.save()

        #creating fixed values list
        list_fixed_values_samples = []
        list_fixed_values_meas = []
        fixed_value_case = ['singleselectfield', 'multiselectfield', 'hiding_singleselectfield', 'hiding_multiselectfield']

        for fix_s in list_sample_att:
            for i in dict_att_values_sample[fix_s]:
                if i != "None":
                    if fix_s not in list_fixed_values_samples:
                        list_fixed_values_samples.append(fix_s)
        for fix_m in list_measurement_att:
            for i in dict_att_values_meas[fix_m]:
                if i != "None":
                    if fix_m not in list_fixed_values_meas:
                        list_fixed_values_meas.append(fix_m)
        print list_fixed_values_samples, "<--- fixed sample"
        print list_fixed_values_meas, "<---- fixed meas"
        if attributs is None:
            #########################################
            ###### creating samples attributs #######
            #########################################
            for s in list_sample_att:
                #TODO virer cast str
                widget = str(dict_widgets_sample_att[s])
                owner_widget = "sample"
                attribut = self.build_attribut(s, lab_id, list_fixed_values_samples, list_searchable, list_deprecated, widget, owner_widget)
                DBSession.add(attribut)
                DBSession.flush()
                if attribut.fixed_value == False:
                    #if Attribut do not get fixed values
                    att_value = self.build_None_attribut_value(attribut.id)
                    DBSession.add(att_value)
                    DBSession.flush()

            #########################################
            #### creating measurements attributs ####
            #########################################
            for m in list_measurement_att:
                widget = str(dict_widgets_meas_att[m])
                owner_widget = "measurement"
                attribut = self.build_attribut(m, lab_id, list_fixed_values_meas, list_searchable, list_deprecated, widget, owner_widget)
                DBSession.add(attribut)
                DBSession.flush()
                if attribut.fixed_value == False:
                    #if Attribut do not get fixed values
                    att_value = self.build_None_attribut_value(attribut.id)
                    DBSession.add(att_value)
                    DBSession.flush()

            #########################################
            ####### creating attributs values #######
            #########################################
            #######         for samples       #######
            #########################################
            dict_fixed_values_samples = {}
            list_attributs_samples_values = self.build_attribut_value('samples_attributs:', lab_id,  dict_fixed_values_samples, list_fixed_values_samples, config)
            for att_v in list_attributs_samples_values:
                DBSession.add(att_v)
            DBSession.flush()
            #########################################
            ######       for measurements     #######
            #########################################
            dict_fixed_values_meas = {}
            list_attributs_meas_values = self.build_attribut_value('meas_attributs:', lab_id, dict_fixed_values_meas, list_fixed_values_meas, config)
            for att_v in list_attributs_meas_values:
                DBSession.add(att_v)
            DBSession.flush()

        #check if there is a new key (or several...) in the config file of the lab
        else:
            list_existant_keys = []
            print list_searchable, "-------------searchable"
            for k in attributs:
                list_existant_keys.append(str(k.key))
            for att_s in list_sample_att:
                att_s = unicode(att_s)
                if att_s not in list_existant_keys:
                    #########################################
                    ###### creating samples attributs #######
                    #########################################
                    #TODO virer cast str
                    widget = str(dict_widgets_sample_att[att_s])
                    owner_widget = "sample"
                    new_sample_attribut = self.build_attribut(att_s, lab_id, list_fixed_values_samples, list_searchable, list_deprecated, widget, owner_widget)
                    DBSession.add(new_sample_attribut)
                    DBSession.flush()
                    if new_sample_attribut.fixed_value == False:
                        #if Attribut do not get fixed values
                        att_value = self.build_None_attribut_value(new_sample_attribut.id)
                        DBSession.add(att_value)
                        DBSession.flush()
                    #########################################
                    ####### creating attributs values #######
                    #########################################
                    #######         for samples       #######
                    #########################################
                    dict_fixed_values_samples = {}
                    list_attributs_samples_values = self.build_attribut_value('samples_attributs:', lab_id, dict_fixed_values_samples, list_fixed_values_samples, config)
                    for att_v in list_attributs_samples_values:
                        DBSession.add(att_v)
                    DBSession.flush()
                #check widgets type
                att_2_check = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == att_s, Attributs.owner == "sample")).first()
                wid_sample_tmp = dict_widgets_sample_att[att_s]

                for w_s in wid_sample_tmp:
                    if w_s != att_2_check.widget:
                        in_db_before = att_2_check.widget
                        in_db_now = w_s
                        att_2_check.widget = w_s
                        if in_db_before in fixed_value_case and in_db_now not in fixed_value_case:
                            att_2_check.fixed_value = False
                        elif in_db_before not in fixed_value_case and in_db_now in fixed_value_case:
                            att_2_check.fixed_value = True
                        DBSession.flush()
                #check and update search buttons
                if att_2_check is None:
                    print att_s, "not in db"
                if att_2_check is not None and not att_2_check.searchable and att_2_check.key in list_searchable:
                    att_2_check.searchable = True
                    DBSession.flush()
                elif att_2_check is not None and att_2_check.searchable and att_2_check.key not in list_searchable:
                    att_2_check.searchable = False
                    DBSession.flush()

            for att_m in list_measurement_att:
                att_m = unicode(att_m)
                if att_m not in list_existant_keys:
                    #########################################
                    #### creating measurements attributs ####
                    #########################################
                    #TODO virer cast str
                    widget = str(dict_widgets_meas_att[att_m])
                    owner_widget = "measurement"
                    new_meas_attribut = self.build_attribut(att_m, lab_id, list_fixed_values_meas, list_searchable, list_deprecated, widget, owner_widget)
                    DBSession.add(new_meas_attribut)
                    DBSession.flush()
                    if new_meas_attribut.fixed_value == False:
                        #if Attribut do not get fixed values
                        att_value = self.build_None_attribut_value(new_meas_attribut.id)
                        DBSession.add(att_value)
                        DBSession.flush()
                    #########################################
                    ####### creating attributs values #######
                    #########################################
                    ######       for measurements     #######
                    #########################################
                    dict_fixed_values_meas = {}
                    list_attributs_meas_values = self.build_attribut_value('meas_attributs:', lab_id, dict_fixed_values_meas, list_fixed_values_meas, config)
                    for att_v in list_attributs_meas_values:
                        DBSession.add(att_v)
                    DBSession.flush()
                #check the widgets
                att_2_check = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == att_m, Attributs.owner == "measurement")).first()
                wid_meas_tmp = dict_widgets_meas_att[att_m]
                for w_m in wid_meas_tmp:
                    if w_m != att_2_check.widget:
                        in_db_before = att_2_check.widget
                        in_db_now = w_m
                        att_2_check.widget = w_m
                        if in_db_before in fixed_value_case and in_db_now not in fixed_value_case:
                            att_2_check.fixed_value = False
                        elif in_db_before not in fixed_value_case and in_db_now in fixed_value_case:
                            att_2_check.fixed_value = True
                        DBSession.flush()
                #check and update search buttons
                if att_2_check is None:
                    print att_m, "not in db"
                if att_2_check is not None and not att_2_check.searchable and att_2_check.key in list_searchable:
                    att_2_check.searchable = True
                    DBSession.flush()
                elif att_2_check is not None and att_2_check.searchable and att_2_check.key not in list_searchable:
                    att_2_check.searchable = False
                    DBSession.flush()

            #if lab choose to delete an attributs (or undelete a key...)
            #Attributs obj have to stay into the db but user can not add others Attributs() with this key --> deprecated == True
            not_deprecated_in_db = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == False)).all()
            for k in not_deprecated_in_db:
                if k.key in list_deprecated:
                    k.deprecated = True
                    DBSession.add(k)
                    DBSession.flush()

            deprecated_in_db = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.deprecated == True)).all()
            for k in deprecated_in_db:
                if k.key not in list_deprecated:
                    k.deprecated = False
                    DBSession.add(k)
                    DBSession.flush()

            #test if deleted attributs_values
            #build a dictionnary to fast check what is into db
            dict_att_values_db = {}
            for a in attributs:
                #dict_att_values_db[a.key] = empty_list
                list_tmp = []
                for v in a.values:
                    if v.deprecated == False:
                        try:
                            list_tmp.append(str(v.value))
                        except:
                            list_tmp.append(v.value)
                if len(list_tmp) == 0:
                    list_tmp = [None]
                dict_att_values_db[str(a.key)] = list_tmp

            #You have to check deletion BEFORE addition
            #checking attribut value(s) deletion(s) in samples attributs
            self.check_value_deletion(list_sample_att, dict_att_values_sample, dict_att_values_db, lab_id)
            #checking attribut value(s) deletion(s) in measurements attributs
            self.check_value_deletion(list_measurement_att, dict_att_values_meas, dict_att_values_db, lab_id)
            #checking attribut value(s) addition in sample attributs
            self.check_value_addition(list_sample_att, dict_att_values_sample, dict_att_values_db, lab_id)
            #checking attribut value(s) addition in measurements attributs
            self.check_value_addition(list_measurement_att, dict_att_values_meas, dict_att_values_db, lab_id)

        # look if an user is admin or not
        admins = tg.config.get('admin.mails')
        group_admins = DBSession.query(Group).filter(Group.name == gl.group_admins).first()
        if user.email in admins:
            user not in group_admins.users and group_admins.users.append(user)
        else:
            user in group_admins.users and group_admins.users.remove(user)
        DBSession.flush()
        # create the authentication ticket
        user = DBSession.query(User).filter(User.email == mail).first()
        userdata = str(user.id)
        ticket = auth_tkt.AuthTicket( 
                                       secret, user.email, remote_addr, tokens=token, 
                                       user_data=userdata, time=None, cookie_name=cookiename, 
                                       secure=True) 
        val = ticket.cookie_value()
        # set it in the cookies
        response.set_cookie(
                     cookiename, 
                     value=val, 
                     max_age=None, 
                     path='/', 
                     domain=None, 
                     secure=False, 
                     httponly=False, 
                     comment=None, 
                     expires=None, 
                     overwrite=False)
        #transaction.commit()
        extern_meas = session.get("extern_meas", False)
        check_tequila = session.get("check_tequila", False)
        if extern_meas is False and check_tequila is False:
            raise redirect(came_from)
        elif extern_meas is False and check_tequila:
            raise redirect("/search")
        else:
            del session["extern_meas"]
            raise redirect(url('/measurements/external_add'))

    @expose('biorepo.templates.index')
    def out(self):
        '''
        Logout the user.
        '''
        environ = request.environ
        authentication_plugins = environ['repoze.who.plugins']
        identifier = authentication_plugins['ticket']
        cookiename = identifier.cookie_name
        response.delete_cookie(cookiename)
        session.delete()
        session.save()
        raise redirect("/")

#building functions

    @expose('biorepo.templates.lab_choice')
    def choose_lab(self, list_units):
        '''
        pass the different labs to the js to generate a choice popup at user login
        '''
        choice = LabChoice
        choice.submit = twf.SubmitButton(value="Select as lab")
        form_choice = choice(action=url('/login/choose_lab_post')).req()
        choice.child.children[0].options = list_units
        return dict(page='lab_choice', widget=form_choice)

    @expose()
    def choose_lab_post(self, *args, **kw):
        u = kw.get('lab_choice', None)
        configp = ConfigParser.RawConfigParser()
        configp.read(path_conf_labs())
        list_labs = (configp.get('LABS:main', 'keys')).split(',')
        if u is not None and u in list_labs:
            session['current_lab'] = u
            session['first_passage'] = False
            session.save()
            principal = session["principal_tequila"]
            tmp_user, tmp_lab = self.build_user(principal)
            raise redirect('/login')
        elif u is not None and u not in list_labs:
            flash("Your lab is not registered into BioRepo, please contact the administrator", "error")
            raise redirect('/login/out')
        else:
            print "--------------- Problem in choose_lab() --------"
            flash('Something strange happen, contact your administrator', 'error')
            raise redirect('/login/out')

    def build_user(self, principal):
        '''
        Build an User and his/her Lab(s) from a principal hash from Tequila
        @param principal: the hash from Tequila
        @return: an User, his/her Lab(s)
        '''
        hash = dict(item.split('=') for item in principal.split('\n') if len(item.split('=')) > 1)
        user = User()
        lab = Labs()
        #initialize the configparser
        configp = ConfigParser.RawConfigParser()
        #TODO remove the print
        print "################# NEW CONNEXION ###############"
        print hash, "--- connexion"
        now2 = datetime.datetime.now()
        print "##############       TIME      #############"
        print now2.ctime()

        if(hash.has_key('firstname')):
            user.firstname = hash.get('firstname').decode("utf-8")
        if(hash.has_key('name')):
            user.name = hash.get('name').decode("utf-8")
        if(hash.has_key('email')):
            user.email = hash.get('email')
        #testing unit
        tmp_u = hash['allunits'].lower()
        list_units = tmp_u.split(',')
        print list_units, "list_units"
        #possibility to add one or several external lab(s) to a collaborator without Shibboleth agreement
        test_user = DBSession.query(User).filter(User._email == user.email).first()
        #if it is not the first connexion for the user
        if test_user is not None:
            #get his/her lab(s) registered
            test_labs = test_user.labs
            #check if we get a Shibboleth bypass for this one
            if len(test_labs) > 0:
                for l in test_labs:
                    if str(l.name) not in list_units:
                        print "Shibboleth bypass for : " + str(l.name)
                        list_units.append(str(l.name))

        #parsing conf file labs.ini
        configp.read(path_conf_labs())
        list_labs = (configp.get('LABS:main', 'keys')).split(',')
        print list_labs, "list_labs in labs.ini"
        valid = False
        # try:
        #     test = session['current_lab']
        #     exist = True
        # except:
        #     exist = False

        if len(list_units) > 1 and session['first_passage'] == True:
            cpt_labs = len(list_units)
            cpt = 0
            for u in list_units:
                if u in list_labs:
                    raise redirect('choose_lab', {'list_units': list_units})

                else:
                    cpt += 1
                    pass
                    if cpt == cpt_labs:
                        flash("Sorry, your lab is not registered in BioRepo, please contact the administrator", 'error')
                        raise redirect('/')
        elif len(list_units) > 1 and session['first_passage'] == False:
            valid = True
            u = session["current_lab"]
            lab.name = u
            lab.path_raw = path_raw(u)
            lab.path_processed = path_processed(u)
            lab.path_tmp = path_tmp(u)
            session["tmp_user"] = user
            session["tmp_lab"] = lab
            session.save()
        #the user is affiliated to one lab
        elif len(list_units) < 2 and list_units != ['unsupported']:
            for u in list_units:
                if u in list_labs:
                    #creating the Labs keys
                    valid = True
                    lab.name = u
                    lab.path_raw = path_raw(u)
                    lab.path_processed = path_processed(u)
                    lab.path_tmp = path_tmp(u)
                    session['current_lab'] = u
                    session.save()
                else:
                    flash("Sorry, your lab is not registered in BioRepo, please contact the administrator to do it", 'error')
                    raise redirect('/')
        #the user is an external collaborator, not from EPFL
        elif len(list_units) == 1 and list_units == ['unsupported']:
            valid = True
            mail = user.email
            user_tocheck = DBSession.query(User).filter(User._email == mail).first()
            if user_tocheck is None or len(user_tocheck.labs) == 0 or len(user_tocheck.labs) > 2:
                valid = False
            #ext_users have only one lab
            else:
                for l in user_tocheck.labs:
                    lab_name = str(l.name)
                    lab.name = lab_name
                    lab.path_raw = path_raw(lab_name)
                    lab.path_processed = path_processed(lab_name)
                    lab.path_tmp = path_tmp(lab_name)
                    session['current_lab'] = lab_name
                    session.save()

        #IMPORTANT : where you have to put your name if you are a super admin
        if valid == True or hash['user'] == 'mouscaz':
            return user, lab
        else:
            flash("Sorry, your lab is not registered in BioRepo", 'error')
            raise redirect('/')

    def build_attribut(self, att_type, lab_id, list_fixed_values, list_searchable, list_deprecated, widget, owner):
        '''
        Build an Attribut
        @param principal: att_type, lab_id, list_fixed_values, list_searchable, list_deprecated, widget
        @return an Attribut
        '''
        attribut = Attributs()
        attribut.lab_id = lab_id
        attribut.key = att_type
        attribut.fixed_value = False
        attribut.searchable = False
        attribut.deprecated = False
        if att_type in list_fixed_values:
            attribut.fixed_value = True
        if att_type in list_searchable:
            attribut.searchable = True
        if att_type in list_deprecated:
            attribut.deprecated = True
        try:
            #TODO : check if any widget change
            w = widget.replace("['", "").replace("']", "")
            attribut.widget = w
            attribut.owner = owner
        except:
            print "/!\ -login.py- NO WIGDGET DETECTED FOR THIS ATTRIBUT : ", attribut

        return attribut

    #TODO A COMPLETER / A TESTER
    def build_attribut_value(self, s, lab_id, dict_fixed_values_type, list_fixed_values_type, config):
        '''
        build Attribut values
        @return a list of Attribut values
        '''
        list_objects_value = []
        for att_s in list_fixed_values_type:
            #build a dictionnary of fixed values : {'key':'[value1, value2, value3, ...}'}
            list_values = []
            list_values = (config.get(s + att_s, att_s)).split(',')
            dict_fixed_values_type[att_s] = list_values

        for k, list_values in dict_fixed_values_type.iteritems():
            att_tmp = DBSession.query(Attributs).filter(and_(Attributs.key == k), Attributs.lab_id == lab_id).first()
            for v in list_values:
                attributs_v = Attributs_values()
                attributs_v.attribut_id = att_tmp.id
                attributs_v.value = v
                attributs_v.deprecated = False
                #TODO faire if pour deprecated = True
                list_objects_value.append(attributs_v)
        return list_objects_value

    def build_None_attribut_value(self, att_id):
        '''
        build a None value Attribut value
        @param principal = Attributs.id
        @return an Attribut value
        '''
        att_val = Attributs_values()
        att_val.attribut_id = att_id
        att_val.value = None
        att_val.deprecated = False
        return att_val

    #checking values attribut deletion(s)
    def check_value_deletion(self, list_type_att, dict_att_values_type, dict_att_values_db, lab_id):
        '''
        Checking for value(s) deletion(s)
        @param principal : list_type_att and dict_att_values_type (where "type" == sample or "measurement"), dict_att_values_db, lab_id
        @return an updated db
        '''
        for key_type in list_type_att:
            j_att = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == key_type)).first()
            j_att_value = DBSession.query(Attributs_values).filter(Attributs_values.attribut_id == j_att.id).all()

            if "None" in dict_att_values_type[key_type] and (dict_att_values_db.has_key(key_type) == False or dict_att_values_db[key_type] != ['None']):
                #all the value in db are now deprecated
                #warning : LOOKS USELESS NOW, but it's maybe a mistake --- to be continued ... :/
                pass
                # for v in j_att_value:
                #     print v.value
                #     v.deprecated = True
                #     DBSession.flush()
                # #creation of the new None value
                # new_value_None = Attributs_values()
                # new_value_None.attribut_id = j_att.id
                # new_value_None.value = None
                # new_value_None.deprecated = False
                # DBSession.add(new_value_None)
                # j_att.fixed_value = False
                # DBSession.flush()

            else:
                for j in dict_att_values_db[key_type]:
                    if j == "None":
                        j = None

                    j_att_value_exact = DBSession.query(Attributs_values).filter(and_(Attributs_values.attribut_id == j_att.id,
                    Attributs_values.value == j)).first()
                    if j is None:
                        j = "None"

                    # #for the boolean mess...
                    # if j is not None and j != "None":
                    #     j = check_boolean(j)

                    try:
                        #test presence of value from db in conf file
                        if j not in dict_att_values_type[key_type] and j != "None":
                            j_att_value_exact.deprecated = True
                            DBSession.flush()
                        #if value None in db but not None in conf file
                        elif j not in dict_att_values_type[key_type] and j == "None":
                            if j_att.fixed_value != True:
                                j_att.fixed_value = True
                            j_att_value_exact.deprecated = True
                            DBSession.flush()
                        DBSession.flush()

                    except Exception as e:
                        import sys, traceback
                        a, b, c = sys.exc_info()
                        traceback.print_exception(a, b, c)
                        print "---- error login.py check_value_deletion() ----"
                        print "j ---> ", j
                        print "key_type ---> ", key_type
                        print "list_type_att -->", list_type_att
                        print "dict_att_values_type[key_type] -->", dict_att_values_type[key_type]
                        print "j_att --> ", j_att
                        print "j_att_value", j_att_value

    def check_value_addition(self, list_type_att, dict_att_values_type, dict_att_values_db, lab_id):
        '''
        Checking for value(s) addition
        @param principal
        @return an updated db
        '''
        for key_type in list_type_att:
            for i in dict_att_values_type[key_type]:
                #get the attribut and its value(s)
                i_att = DBSession.query(Attributs).filter(and_(Attributs.lab_id == lab_id, Attributs.key == key_type)).first()
                #warning : i_att_value is a list !
                i_att_value = DBSession.query(Attributs_values).filter(and_(Attributs_values.attribut_id == i_att.id,
                Attributs_values.value == i)).all()
                #warning : i_att_value_deprecatted is a list !
                # i_att_value_deprecatted = DBSession.query(Attributs_values).filter(and_(Attributs_values.attribut_id == i_att.id,
                # Attributs_values.value == i, Attributs_values.deprecated == True)).all()
                try:
                    flag = False
                    if i not in dict_att_values_db[key_type] and i != "None":
                        for existant in i_att_value:
                            if existant.value == i and existant.deprecated == True:
                                existant.deprecated = False
                                DBSession.flush()
                                flag = True
                            if existant.value is None:
                                existant.deprecated = True
                                DBSession.flush()
                        if flag == False:
                            new_value = Attributs_values()
                            new_value.attribut_id = i_att.id
                            new_value.value = i
                            new_value.deprecated = False
                            DBSession.add(new_value)
                            DBSession.flush()

                except Exception as e:
                    import sys, traceback
                    a, b, c = sys.exc_info()
                    traceback.print_exception(a, b, c)
                    print "--- error login.py check_value_addition() ---"
                    print "i --->", i
                    print "key_type --->", key_type
                    print "list_type_att --->", list_type_att
                    print "dict_att_values_type[key_type] -->", dict_att_values_type[key_type]
                    print "i_att --> ", i_att
                    print "i_att_value", i_att_value

