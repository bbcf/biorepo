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


def get_info_link(obj_id):
    '''
   Return a HTML info link.
   '''
    return '''<a class='action info_link' href="%s" target="_blank"></a>''' % (url('./measurements/info_meas', params=dict(meas_id=obj_id)))


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
    meas = DBSession.query(Measurements).filter(Measurements.id == obj_id).first()
    status = meas.status_type
    normal_ext = ["bed", "bedgraph", "wig"]
    #binary extension, except bam files
    binary_ext = ["bw", "bigwig", "bigbed", "bb"]
    if status and len(meas.fus) > 0:
        list_fus = meas.fus
        for x in list_fus:
            f_sha1 = x.sha1
            ext = x.extension
        #t is type. 1 == normal extension, 2 == binary extension, 3 == bam
        if ext.lower() in normal_ext:
            return'''
            <a class='action UCSC_link'  href="%s" target="_blank" title="view in UCSC" style="text-decoration:none" target="_blank"></a> ''' % (url('./public/UCSC_link', params=dict(sha1=f_sha1, meas_id=obj_id, t=1)))
        elif ext.lower() in binary_ext:
            return'''
            <a class='action UCSC_link'  href="%s" target="_blank" title="view in UCSC" style="text-decoration:none" target="_blank"></a> ''' % (url('./public/UCSC_link', params=dict(sha1=f_sha1, meas_id=obj_id, t=2)))
        elif ext.lower() == "bam":
            return'''
            <a class='action UCSC_link'  href="%s" target="_blank" title="view in UCSC" style="text-decoration:none" target="_blank"></a> ''' % (url('./public/UCSC_link', params=dict(sha1=f_sha1, meas_id=obj_id, t=3)))
    return ''


def get_GViz_link(obj_id):
    '''
    Return a HTML link to Gviz HTSstation
    '''
    meas = DBSession.query(Measurements).filter(Measurements.id == obj_id).first()
    status = meas.status_type

    if status and len(meas.fus) > 0:
        list_fus = meas.fus
        for x in list_fus:
            f_sha1 = x.sha1
            ext = x.extension
        if ext.lower() == "bam":
            return'''
            <a class='action GViz_link'  href="%s" target="_blank" title="view in GViz" style="text-decoration:none" target="_blank"></a> ''' % (url('./public/Gviz_link', params=dict(sha1=f_sha1, meas_id=obj_id)))
    return ''


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
    #have to be public
    if status and len(meas.fus) > 0:
        list_fus = meas.fus
        for x in list_fus:
            f_sha1 = x.sha1
        return '''
              <a class='action public_link'  href="%s" title="public link for this measurement" style="text-decoration:none"></a> ''' % (url('./public/public_link', params=dict(sha1=f_sha1, m_id=obj_id)))
    else:
        return'''
              <a class='action no_exit' title="This file is private and you can't drop it out of BioRepo" style="text-decoration:none"></a>'''


def view_th(url_th):
    '''
    Return a HTML link to UCSC trackhub section
    '''
    return'''
    <a class='action UCSC_link'  href="%s" target="_blank" title="view trackhub in UCSC" style="text-decoration:none"></a> ''' % url(url_th)


def get_delete_th(th_name, img_src='../images/trash.png'):
    '''
    Delete an object
    '''
    return '''<a class="action delete" onclick="return confirm('Are you sure ?')";
    title="delete" href="%s" style="text-decoration:none"><img src="%s"/></a>''' % (url('./delete/' + str(th_name)), (img_src))