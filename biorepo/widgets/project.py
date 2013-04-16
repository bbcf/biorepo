from biorepo.model import DBSession, Projects
from tw2.forms.datagrid import DataGrid
import tw2.forms as twf
import tw2.core as twc
from biorepo.lib.helpers import get_delete_link, get_edit_link, get_add_link
import genshi
from tg import url, tmpl_context


#methods
def get_samples():
    return [(sample.id, '%s' % (sample.name)) for sample in tmpl_context.samples]


# TABLE
# class PTable(TableBase):
#     __model__ = Projects
#     __omit_fields__ = ['_created', 'id', 'user_id']


# TABLE FILLER
# class PTableFiller(TableFiller):
#     __model__ = Projects


# NEW
# #TODO try with MultipleSelectionField
class NewPForm(twf.TableForm):
    # __model__ = Projects
    # __base_widget_args__ = {'hover_help': True}
    # __omit_fields__ = ['id', 'user', 'date', 'created']

    project_name = twf.TextField(label_text="Name :", validator=twc.Required)
    description = twf.TextField(label_text="Description :",)
    samples = twf.MultipleSelectField(label_text="Your samples : ", help_text="You can add some of your existing samples to this project.")

    submit = twf.SubmitButton(value="Create my project")


# EDIT
class PEditForm(twf.TableForm):
    # __model__ = Projects
    # __base_widget_args__ = {'hover_help': True}
    # __omit_fields__ = ['user', 'date', 'created']
    id = twf.HiddenField('id')
    project_name = twf.TextField(label_text="Name :", validator=twc.Required)
    samples = twf.MultipleSelectField(label_text="Your samples : ", options=get_samples,
                                      help_text="If you deselect a sample it will be removed")
    description = twf.TextField(label_text="Description :",)

    submit = twf.SubmitButton(value="Edit my project")


# EDIT FILLER
# class PEditFiller(EditFormFiller):
#     __model__ = Projects


# #DATAGRID   ----> REMPLACER project_id par sample_id dans Action
# class ProjectGrid(DataGrid):
#     fields = [("Project id", "id", "User", "get_username"), ("Name", "project_name"),
#          ("Samples", lambda obj:genshi.Markup(obj.samples_display)),
#         ("Date", "created"), ("Description", "description"), ("Action", lambda obj:genshi.Markup(
#         get_delete_link(obj.id)
#         + get_edit_link(obj.id)
#         + get_add_link(obj.id)

#         ))]


# project_table = PTable(DBSession)
# project_table_filler = PTableFiller(DBSession)
#new_project_form = NewPForm()
project_edit_form = PEditForm()
# project_edit_filler = PEditFiller(DBSession)
#project_grid = ProjectGrid()
