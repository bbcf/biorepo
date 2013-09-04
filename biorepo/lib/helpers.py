# -*- coding: utf-8 -*-

"""WebHelpers used in biorepo."""

from webhelpers import date, feedgenerator, html, number, misc, text
from tg import url, redirect, flash
from biorepo.model import DBSession, Measurements
#from biorepo.lib.util import check_boolean


# def get_delete_link(obj_id):
#     '''
#    Get an HTML delete link for an object.
#    @param obj_id: the object_id
#    @type obj_id: an integer
#    @return: the HTML link
#    '''
#     return '''
#    <form method="POST" action=%s class="button-to">
#    <input name="_method" value="DELETE" type="hidden"/>

#    <input class="action delete-button" onclick="return confirm('Are you sure?');"
#        value=" " style="background-image: url('../images/trash.png'); background-color: transparent;
#        background-repeat: no-repeat; float:left;
#        border:0; color: #286571; display: inline; margin: 0; padding-left: 20px;"
#    type="submit"/>
#    </form>
#        ''' % (obj_id)

def get_delete_link(obj_id, img_src='../images/trash.png'):
    '''
    Delete an object
    '''
    return '''<a class="action delete" onclick="return confirm('Are you sure ?')";
    title="delete" href="%s" style="text-decoration:none"><img src="%s"/></a>''' % (url('./delete/' + str(obj_id)), (img_src))


def get_delete_project(obj_id, img_src='../images/trash.png'):
    '''
    Delete an object
    '''
    return '''<a class="action delete" onclick="return confirm('Are you sure ? WARNING : If you delete this project, the attached sample(s) will be removed too.')";
    title="delete" href="%s" style="text-decoration:none"><img src="%s"/></a>''' % (url('./delete/' + str(obj_id)), (img_src))


def get_view_link(obj_id):
    '''
   Return a HTML view link.
   '''
    return ''' <a class='action view_link' href="%s"></a>''' % url('./view', params=dict(project_id=obj_id))


def get_share_link(obj_id):
    '''
   Return a HTML share link.
   '''
    return ''' <a class='action share_link' href="%s"></a>''' % url('./share', params=dict(project_id=obj_id))


def get_edit_link(obj_id):
   #  return '''
   # <a class="action edit_link" href="/edit/%s" style="text-decoration:none"></a>
   #        ''' % (obj_id)
    return '''
    <a class="action edit_link" href="%s"></a>''' % url('./edit/' + str(obj_id))


def get_dl_link(obj_id):
    '''
   Return a HTML download link.
   '''
    return '''
    <a class='action dl_link'  href="%s" title="download measurement(s)" style="text-decoration:none"></a> ''' % (url('./measurements/download', params=dict(meas_id=obj_id)))


def get_info_link(obj_id, obj_description):
    '''
   Return a HTML info link.
   '''
    return '''<a class='action info_link' href="%s" target="_blank" title="%s"></a>
    ''' % (url('./info', params=dict(project_id=obj_id)), obj_description)


def get_add_link(obj_id):
    '''
    return a HTML adding project/sample/measurement link
    '''
    return '''
    <a class='action add_link'  href="%s" style="text-decoration:none"></a> ''' % url('./add', params=dict(project_id=obj_id))


def get_UCSC_link(obj_id):
    '''
    Return a HTML link to UCSC
    '''
    return'''
    <a class='action UCSC_link'  href="%s" target="_blank" title="view in UCSC" style="text-decoration:none" target="_blank"></a> ''' % url('http://genome.ucsc.edu/cgi-bin/hgGateway', params=dict(project_id=obj_id))


def get_GDV_link(obj_id):
    '''
    Return a HTML link to GDV
    '''
    return'''
    <a class='action GDV_link'  href="%s" target="_blank" title="view in GDV" style="text-decoration:none"></a> ''' % url('http://gdv.epfl.ch/pygdv', params=dict(project_id=obj_id))


def get_SPAN_id(obj_id):
    '''
    Return the measurement id
    '''
    return'''
    <span style="VISIBILITY:hidden;display:none" class=id_meas>%s</span>''' % obj_id


def get_dl_link2(obj_id):
    '''
   Return a HTML download link.
   '''
    return '''
    <a class='action dl_link'  href="%s" title="download measurement(s)" style="text-decoration:none"></a> ''' % (url('./download', params=dict(meas_id=obj_id)))


def get_public_link(obj_id):
    '''
   Return a HTML public download link.
   '''
    #TODO : understand and fix the bug...
    meas = DBSession.query(Measurements).filter(Measurements.id == obj_id).first()
    status = meas.status_type
    f_sha1 = ''
    if status:
        print "dedans"
        list_fus = meas.fus
        for x in list_fus:
            f_sha1 = x.sha1
    return '''
        <a class='action public_link'  href="%s" title="public link for this measurement" style="text-decoration:none"></a> ''' % (url('./public_link', params=dict(sha1=f_sha1)))
