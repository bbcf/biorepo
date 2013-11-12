import genshi
from tw.forms.datagrid import DataGrid
from biorepo.lib.helpers import get_delete_link, get_delete_project, get_edit_link, get_add_link,\
get_dl_link2, get_UCSC_link, get_GDV_link, get_info_link, get_dl_link, get_SPAN_id, get_public_link, get_GViz_link, view_th
from biorepo.model import DBSession, Samples, Measurements, Projects, Attributs, Attributs_values, Labs
from tg import session, flash, redirect, request
from sqlalchemy import and_
from biorepo import handler
from biorepo.lib.util import value_travel_into_da_list


#special grid for bootstrap theme
class BootstrapGrid(DataGrid):
    css_class = 'table grid table-condensed'


#projects
class ProjectGrid(BootstrapGrid):
    fields = [("Project id", "id"), ("User", "get_username"), ("Name", "project_name"),
    ("Samples", lambda obj:genshi.Markup(obj.samples_display)),
    ("Description", "description"), ("Date", "created"), ("Actions", lambda obj:genshi.Markup(
    get_edit_link(obj.id)
    + get_delete_project(obj.id)
    ))]


#samples
class SampleGrid(BootstrapGrid):
    fields = [("User", "get_username"), ("Name", "name"), ("Type", "type"),  ("Protocole", "protocole"),
    ("Date", "created"), ("Action", lambda obj:genshi.Markup(
    get_edit_link(obj.id)
    + get_delete_link(obj.id)
    ))]


#measurements
class MeasGrid(BootstrapGrid):
    fields = [("User", "get_username"), ("Sample", "samples_display"), ("Name", "name"), ("Description", "description"), ("Visibility", "get_status_type"),
        ("Raw", "get_type"),
        ("Date", "created"), ("Action", lambda obj:genshi.Markup(
        get_dl_link2(obj.id)
        #+ get_UCSC_link(obj.id)
        #+ get_GDV_link(obj.id)
        + get_edit_link(obj.id)
        + get_delete_link(obj.id)
        ))]


#trackhubs
class TrackhubGrid(BootstrapGrid):
    fields = [("Trackhub", "name"), ("Action", lambda obj:genshi.Markup(
    view_th(obj.url_th)
    ))]


#search page
def build_search_grid(measurements):
    search_grid = BootstrapGrid()
    #static end
    end_fields = [('Description', "description"), ("Date", "created"), ("Action", lambda obj: genshi.Markup(
        #get_info_link(obj.id, obj.description)
        get_dl_link(obj.id)
        + get_public_link(obj.id)
        + get_UCSC_link(obj.id)
        #+ get_GViz_link(obj.id)
        + get_SPAN_id(obj.id)
    ))]
    #static and dynamic fields
    fields = []
    fields_static = [("", "scroll_info"), ("User", "user"), ("Samples", lambda obj:genshi.Markup(obj.samples_display)), ("Type", lambda obj:genshi.Markup(obj.sample_type)),\
    ("Measurements", lambda obj:genshi.Markup(obj.name)), ("DataType", lambda obj:genshi.Markup(obj.measurement_type))]
    fields_dyn = []
    list_searchable = []
    positions_not_searchable = []
    hidden_list = []
    lab_id = None
    if len(measurements) > 0:
        meas = measurements[0]
        #dyn meas
        for att in meas.attributs:
            #get the lab_id
            lab_id = att.lab_id
            vals = lambda obj, a=att: obj.get_values_from_attributs_meas(a)
            fields_dyn.append((att.key, vals))
            if att.searchable == True:
                list_searchable.append(att.key)
        #dyn sample
        if len(meas.samples) > 0:
            sample = (meas.samples)[0]
            for att in sample.attributs:
                val = lambda obj, a=att: obj.get_values_from_attributs_sample(a)
                fields_dyn.append((att.key, val))
                if att.searchable == True:
                    list_searchable.append(att.key)
    ############## CUSTOMIZE THE SEARCH GRID BY LAB #######################
    #/!\ the grid begins at 0
    #to customize hidden fields by lab
    lab = DBSession.query(Labs).filter(Labs.id == lab_id).first()
    movable_fields = fields_static + fields_dyn
    if lab:
        if lab.name == "ptbb":
            pass
        elif lab.name == "updub":
            pass
        elif lab.name == "lvg":
            #move some field in the grid
            for f in movable_fields:
                if f[0] == "flag_final":
                    new_list = value_travel_into_da_list(movable_fields, movable_fields.index(f), len(movable_fields))
                    movable_fields = new_list
            for f in movable_fields:
                if f[0] == "quality":
                    new_list = value_travel_into_da_list(movable_fields, movable_fields.index(f), len(movable_fields))
                    movable_fields = new_list

            #hide Samples name
            for f in movable_fields:
                if f[0] == "Samples":
                    i = movable_fields.index(f)
                    hidden_list.append(i)
            for f in movable_fields:
                if f[0] == "ab_source":
                    i = movable_fields.index(f)
                    hidden_list.append(i)

    #addition with the 3 common end-fields
    fields = movable_fields + end_fields
    #build the list (positions_not_searchable) to send to the js for the searchable buttons
    for f in fields:
        search_grid.fields.append(f)
    for i, item in enumerate(search_grid.fields):
        if item[0] not in list_searchable:
            positions_not_searchable.append(i)

    # for i, item in enumerate(fields_static):
    #     if i in positions_not_searchable:
    #         positions_not_searchable.remove(i)
    for f in fields_static:
        for i, item in enumerate(movable_fields):
            #and i not in list_tmp
            if f[0] == item[0] and f[0] != '' and f in fields_static and i in positions_not_searchable:
                positions_not_searchable.remove(i)

    #build the list (ignored_list) for the ignored fields
    total = len(search_grid.fields) - 1
    hidden_list.append(total - 2)

    return search_grid, hidden_list, positions_not_searchable
