from biorepo.model import DBSession, Projects, Samples, Measurements
from tw.forms.datagrid import DataGrid
#from tw.forms import Form
import tw2.forms as twf
from biorepo.lib.helpers import get_dl_link, get_info_link, get_UCSC_link, get_GDV_link, get_SPAN_id
import genshi
from tg import tmpl_context, session
from biorepo.lib.constant import list_cell_types, get_list_types, list_dataType


#methods
def get_users():
    return [(u.id, u.name) for u in tmpl_context.users]


def get_cell_types():
    return [('%s' % c) for c in list_cell_types if c != None]


# def get_ab_targets():
#     return [('%s' % ab) for ab in list_ab_targets if ab != None]


def get_sample_types():
    user_lab = session.get("current_lab", None)
    return [('%s' % type) for type in get_list_types(user_lab) if type != None]


def get_dataTypes():
    return [('%s' % dtype) for dtype in list_dataType if dtype != None]


# def get_bio_bgs():
#     #how to get the bio_bgs args
#     list_bio_bgs = []
#     [(list_bio_bgs.append(bio)) for bio in tmpl_context.bio_bgs if bio not in list_bio_bgs]
#     return [('%s' % biobg) for biobg in list_bio_bgs if biobg != None]


def get_sample_names():
    list_sample_names = []
    [(list_sample_names.append(name)) for name in tmpl_context.sample_names]
    return [('%s' % sample_name) for sample_name in list_sample_names if sample_name != None]


def get_measurement_names():
    list_measurement_names = []
    [(list_measurement_names.append(name)) for name in tmpl_context.measurement_names]
    return [('%s' % measurement_name) for measurement_name in list_measurement_names if measurement_name != None]


# def get_assemblies():
#     list_assemblies = []
#     [(list_assemblies.append(ass)) for ass in tmpl_context.assemblies]
#     return [('%s' % assembly) for assembly in list_assemblies if assembly != None]


# def get_stage():
#     list_stage = []
#     [(list_stage.append(sta)) for sta in tmpl_context.stage]
#     return [('%s' % stage) for stage in list_stage if stage != None]


# def get_flag():
#     list_flag = []
#     for flag in tmpl_context.final_flag:
#         if flag == (True,):
#             flag = "Final"
#             list_flag.append(flag)
#         else:
#             flag = "Draft"
#             list_flag.append(flag)
#     return [('%s' % final_flag) for final_flag in list_flag if final_flag != None]


# def get_species():
#     list_stage = []
#     [(list_stage.append(spe)) for spe in tmpl_context.organism]
#     return [('%s' % specie) for specie in list_stage if specie != None]


#DATAGRIDS
#TRONOGRID
class SearchGridT(DataGrid):
#    fields = [("User","get_username"),("Cell Type", lambda obj:genshi.Markup(obj.sample_cell_type)),
#        ("Species",lambda obj:genshi.Markup(obj.sample_species)),
#         ("Ab target", lambda obj:genshi.Markup(obj.sample_ab_target)),("Bio bg",lambda obj:genshi.Markup(obj.sample_bio_bg)),
#        ("Type",lambda obj:genshi.Markup(obj.sample_type)),("DataType",lambda obj:genshi.Markup(obj.measurement_type)),
#        ("Description",lambda obj:genshi.Markup(obj.description)),
#        ("Action", lambda obj:genshi.Markup(
#        get_info_link(obj.id,obj.description)
#        +get_dl_link(obj.id)
#        +get_UCSC_link(obj.id)
#        +get_GDV_link(obj.id)
#        +get_SPAN_id(obj.id)
#    ))]
# -----------------------------   old version           ---------------
    # fields = [("User", "get_username"),
    #     ("Samples", lambda obj:genshi.Markup(obj.samples_display)), ("Type", lambda obj:genshi.Markup(obj.sample_type)),
    #     ("Cell Type", lambda obj:genshi.Markup(obj.sample_cell_type)), ("Target", lambda obj:genshi.Markup(obj.sample_ab_target)),
    #     ("Bio bg", lambda obj:genshi.Markup(obj.sample_bio_bg)), ("Stage", lambda obj:genshi.Markup(obj.sample_stage)),
    #     ("Measurements", "name"), ("Assembly", "assembly"),
    #     ("DataType", lambda obj:genshi.Markup(obj.measurement_type)), ("Date", "created"), ("Final", lambda obj:genshi.Markup(obj.flag_final_type)),
    #     ("Description", lambda obj:genshi.Markup(obj.description)),
    #     ("Action", lambda obj:genshi.Markup(
    #         get_info_link(obj.id, obj.description)
    #         + get_dl_link(obj.id)
    #         + get_UCSC_link(obj.id)
    #         + get_GDV_link(obj.id)
    #         + get_SPAN_id(obj.id)
    #     ))]

    fields = [("User", "get_username"),
        ("Samples", lambda obj:genshi.Markup(obj.samples_display)), ("Type", lambda obj:genshi.Markup(obj.sample_type)),
        ("Measurements", "name"), ("DataType", lambda obj:genshi.Markup(obj.measurement_type)), ("Date", "created"),
        ("Action", lambda obj:genshi.Markup(
            get_info_link(obj.id, obj.description)
            + get_dl_link(obj.id)
            + get_UCSC_link(obj.id)
            + get_GDV_link(obj.id)
            + get_SPAN_id(obj.id)
        ))]

##DUBOULEGRID
#class SearchGridD(DataGrid):
#    fields = [("User","get_username"),
#         ("Samples",lambda obj:genshi.Markup(obj.samples_display)),("Type",lambda obj:genshi.Markup(obj.sample_type)),
#        ("Cell Type", lambda obj:genshi.Markup(obj.sample_cell_type)),("Target", lambda obj:genshi.Markup(obj.sample_ab_target)),
#        ("Bio bg",lambda obj:genshi.Markup(obj.sample_bio_bg)),("Stage",lambda obj:genshi.Markup(obj.sample_stage)),
#        ("Measurements", "name"),("Assembly","assembly"),
#        ("DataType",lambda obj:genshi.Markup(obj.measurement_type)),("Date","created"),("Final",lambda obj:genshi.Markup(obj.flag_final_type)),
#        ("Description",lambda obj:genshi.Markup(obj.description)),
#        ("Action", lambda obj:genshi.Markup(
#        get_info_link(obj.id,obj.description)
#        +get_dl_link(obj.id)
#        +get_UCSC_link(obj.id)
#        +get_GDV_link(obj.id)
#        ))]

#search_grid_trono = SearchGridT()
#search_grid_dub = SearchGridD()
