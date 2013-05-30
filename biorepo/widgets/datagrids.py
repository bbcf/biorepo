import genshi
from tw.forms.datagrid import DataGrid
from biorepo.lib.helpers import get_delete_link, get_delete_project, get_edit_link, get_add_link,\
get_dl_link2, get_UCSC_link, get_GDV_link, get_info_link, get_dl_link, get_SPAN_id
from biorepo.model import DBSession, Samples, Measurements, Projects, Attributs, Attributs_values, Labs
from tg import session, flash, redirect, request
from sqlalchemy import and_
from biorepo import handler


#projects
class ProjectGrid(DataGrid):
    fields = [("Project id", "id"), ("User", "get_username"), ("Name", "project_name"),
    ("Samples", lambda obj:genshi.Markup(obj.samples_display)),
    ("Description", "description"), ("Date", "created"), ("Actions", lambda obj:genshi.Markup(
    get_edit_link(obj.id)
    + get_delete_project(obj.id)
    ))]


#samples
class SampleGrid(DataGrid):
    fields = [("User", "get_username"), ("Name", "name"), ("Type", "type"),  ("Protocole", "protocole"),
    ("Date", "created"), ("Action", lambda obj:genshi.Markup(
    get_edit_link(obj.id)
    + get_delete_link(obj.id)
    ))]


#measurements
class MeasGrid(DataGrid):
    fields = [("User", "get_username"), ("Name", "name"), ("Description", "description"), ("Visibility", "get_status_type"),
        ("Raw", "get_type"),
        ("Date", "created"), ("Action", lambda obj:genshi.Markup(
        get_dl_link2(obj.id)
        #+ get_UCSC_link(obj.id)
        #+ get_GDV_link(obj.id)
        + get_edit_link(obj.id)
        + get_delete_link(obj.id)
        ))]


#search page
def build_search_grid(measurements):
    search_grid = DataGrid()
    #static end
    end_fields = [('Description', "description"), ("Date", "created"), ("Action", lambda obj: genshi.Markup(
        get_info_link(obj.id, obj.description)
        + get_dl_link(obj.id)
        #+ get_UCSC_link(obj.id)
        #+ get_GDV_link(obj.id)
        + get_SPAN_id(obj.id)
    ))]
    #static and dynamic fields
    fields = []
    fields_static = [("User", "user"), ("Samples", lambda obj:genshi.Markup(obj.samples_display)), ("Type", lambda obj:genshi.Markup(obj.sample_type)),\
    ("Measurements", "name"), ("DataType", lambda obj:genshi.Markup(obj.measurement_type))]
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

    #addition with the 3 common end-fields
    fields = fields_static + fields_dyn + end_fields
    #build the list (positions_not_searchable) to send to the js for the searchable buttons
    for f in fields:
        search_grid.fields.append(f)
    for i, item in enumerate(search_grid.fields):
        if item[0] not in list_searchable:
            positions_not_searchable.append(i)
    for i, item in enumerate(fields_static):
        if i in positions_not_searchable:
            positions_not_searchable.remove(i)
    #build the list (ignored_list) for the ignored fields
    lab = DBSession.query(Labs).filter(Labs.id == lab_id).first()
    total = len(search_grid.fields) - 1
    hidden_list.append(total - 2)
    #/!\ the grid begins at 0
    #to customize hidden fields by lab
    if lab:
        if lab.name == "ptbb":
            for i in hidden_list:
                if i > total:
                    pass
        elif lab.name == "updub":
            pass
        else:
            pass
    return search_grid, hidden_list, positions_not_searchable
