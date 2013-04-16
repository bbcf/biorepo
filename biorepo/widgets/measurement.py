from biorepo.model import DBSession, Measurements
from tw2.forms.datagrid import DataGrid
import tw2.forms as twf
import tw2.core as twc
from biorepo.lib.helpers import get_delete_link, get_edit_link, get_dl_link2, get_UCSC_link, get_GDV_link
import genshi
from tg import url, tmpl_context
from biorepo.lib import constant
#from biorepo.controllers.measurement import get_all


#methods
def get_samples():
    return [(sample.id, '%s (%s)' % (sample.name, sample.organism)) for sample in tmpl_context.samples]


def get_meas():
    return [(meas.id, '%s (%s)' % (meas.name, meas.id), {'selected': True}) for meas in tmpl_context.parents]


# TABLE
# class MTable(TableBase):
#     __model__ = Measurements
#     __omit_fields__ = ['id']


# TABLE FILLER
# class MTableFiller(TableFiller):
#     __model__ = Measurements


# NEW
class NewMForm(twf.TableForm):
    # __model__ = Measurements
    # __base_widget_args__ = {'hover_help': True}
    # __omit_fields__ = ['id', 'user', 'date', 'collab', 'created', 'files_up', 'IDselected', 'parents', 'children', 'fus']
    # __field_order__ = ['name', 'description', 'status_type', 'type', 'assembly', 'flag_final', 'samples', 'upload', 'url_path', 'url_up']

    #fields
    IDselected = twf.TextField(id='IDselected', label_text="ID selected :")
    name = twf.TextField(id='name', label_text="Name :", help_text="Please choose a name", validator=twc.Required)

    samples = twf.MultipleSelectField(id='samples', label_text="Your samples : ", options=get_samples,
                                      help_text="You can add some of your existing data to this project.")

    assembly = twf.SingleSelectField(id='assembly', label_text="Assembly : ", options=constant.list_assemblies,
                                     help_text="Select your assembly")
    status_type = twf.CheckBox(id='status_type', label_text="Private : ",
                                     help_text="Check it if you want a private data")
    type = twf.CheckBox(id='type', label_text="Raw data : ",
                                     help_text="Check it is a raw data")

    flag_final = twf.CheckBox(id='flag_final', label_text="Final data : ",
                                     help_text="Check it if it is a final data")
    #parents management
    parents = twf.MultipleSelectField(id='parents', label_text="Parents : ", options=get_meas,
        help_text="Parent(s) of this measurement.")
    #parents(value={"parents":2})

    upload = twf.FileField('Upload_your_data', help_text='Please provide a data')

    url_path = twf.TextField(id='url_path', label_text="File's url")

    url_up = twf.CheckBox(id='url_up', label_text="I want to upload the file from this URL : ",
        help_text="Choose if you just stock the url or if you want to upload the file from this url")


# EDIT
class MEditForm(twf.TableForm):
    # __model__ = Measurements
    # __base_widget_args__ = {'hover_help': True}
    # __omit_fields__ = ['id', 'user', 'date', 'collab', 'created', 'parents', 'children', 'fus']
    id = twf.HiddenField('id')
    samples = twf.MultipleSelectField(id='samples', label_text="Your samples : ", options=get_samples)

    #fields
    name = twf.TextField(id='name', label_text="Name :", help_text="Please choose a name", validator=twc.Required)

    samples = twf.MultipleSelectField(id='samples', label_text="Your samples : ", options=get_samples,
                                      help_text="You can add some of your existing data to this project.")

    assembly = twf.SingleSelectField(id='assembly', label_text="Assembly : ", options=constant.list_assemblies,
                                     help_text="Select your assembly")
    status_type = twf.CheckBox(id='status_type', label_text="Private : ",
                                     help_text="Check it if you want a private data")
    type = twf.CheckBox(id='type', label_text="Raw data : ",
                                     help_text="Check it is a raw data")

    flag_final = twf.CheckBox(id='flag_final', label_text="Final data : ",
                                     help_text="Check it if it is a final data")

    upload = twf.FileField('Upload_your_data')

    url_path = twf.TextField(id='url_path', label_text="File's url")

    url_up = twf.CheckBox(id='url_up', label_text="I want to upload the file from this URL : ",
                                     help_text="Choose if you just stock the url or if you want to upload the file from this url")


# EDIT FILLER
# class MEditFiller(EditFormFiller):
#     __model__ = Measurements


#DATAGRID   ----> REMPLACER project_id par sample_id dans Action
class MGrid(DataGrid):

    fields = [("User", "get_username"), ("Name", "name"), ("Description", "description"), ("Visibility", "status_type"),
        ("Raw", "type"), ("Assembly", "assembly"),
        ("Date", "created"), ("Final", "flag_final"), ("Collaborator(s)", "get_collabo"), ("Action", lambda obj:genshi.Markup(
         get_edit_link(obj.id)
        + get_dl_link2(obj.id)
        + get_UCSC_link(obj.id)
        + get_GDV_link(obj.id)
        + get_delete_link(obj.id)
        ))]

# measurement_table = MTable(DBSession)
# measurement_table_filler = MTableFiller(DBSession)
#new_measurement_form = NewMForm(DBSession)
#measurement_edit_form = MEditForm(DBSession)
#measurement_edit_filler = MEditFiller(DBSession)
#measurement_grid = MGrid()

#new_measurement_form(value={"parents":1})