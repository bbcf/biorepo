from biorepo.model import DBSession, Samples
#from tw.forms.validators import NotEmpty
import tw2.forms as twf
import tw2.core as twc
from biorepo.lib.helpers import get_delete_link, get_edit_link, get_view_link, get_share_link, get_add_link
import genshi
from tg import url, tmpl_context
from biorepo.lib import constant
#from tw2.jquery.autocomplete import AutoCompleteField
#from tw2.forms import TableForm


def get_projects():
    return [(project.id, '%s' % project.project_name) for project in tmpl_context.projects]


# TABLE
# class STable(TableBase):
#     __model__ = Samples
#     __omit_fields__ = ['project_id', 'id']


# TABLE FILLER
# class STableFiller(TableFiller):
#     __model__ = Samples


# NEW
class NewSForm(twf.TableForm):
    # __model__ = Samples
    # __base_widget_args__ = {'hover_help': True}
    # __omit_fields__ = ['id', 'project_id', 'date', 'created']
    #fields
    project = twf.SingleSelectField(label_text="Your projects : ", options=get_projects,
              help_text="Do not forget to select your project for this sample")

    name = twf.TextField(id='name', label_text="Name :", help_text="Please choose a name", validator=twc.Required)

    type = twf.SingleSelectField(id='type', label_text="Type : ", options=constant.list_types,
                                     help_text="What technique do you use ?")

    organism = twf.SingleSelectField(id='organism', label_text="Organism : ", options=constant.list_organisms,
                                     help_text="Select the studied organism")

    cell_type = twf.SingleSelectField(id='cell_type', label_text="Cell Type : ", options=constant.list_cell_types,
                                     help_text="Sample cell type")

    #cell_type = AutoCompleteField(id = 'cell_type', completionURL = 'fetch_cell_types',
                                  #fetchJSON = True, minChars = 1)   # AUTOCOMPLETION WAY

    cell_line = twf.SingleSelectField(id='cell_line', label_text="Cell line : ", options=constant.list_cell_lines,
                                     help_text="Select the studied organism")
    target = twf.SingleSelectField(id='target', label_text="Target : ", options=constant.list_ab_targets,
                                     help_text="Select the antibody target")

    bio_background = twf.TextField(id='bio_background', label_text="Bio Background : ",
                                   help_text="Example : WT or KO or Mutant / Male or Female")

    stage = twf.TextField(id='stage', label_text="Stage :", help_text="Ex : Day 1 or E10.5")


# EDIT
class SEditForm(twf.TableForm):
    # __model__ = Samples
    # __base_widget_args__ = {'hover_help': True}
    # __omit_fields__ = ['id', 'project_id', 'date', 'created']
    id = twf.HiddenField('id')
    #_method = twf.HiddenField('_method')
    #fields
    project = twf.SingleSelectField(id='project', label_text="Your projects : ", options=get_projects,
              help_text="Do not forget to select your project for this sample")

    name = twf.TextField(id='name', label_text="Name :", help_text="Please choose a name", validator=twc.Required)

    type = twf.SingleSelectField(id='type', label_text="Type : ", options=constant.list_types,
                                     help_text="What technique do you use ?")

    organism = twf.SingleSelectField(id='organism', label_text="Organism : ", options=constant.list_organisms,
                                     help_text="Select the studied organism")

    cell_type = twf.SingleSelectField(id='cell_type', label_text="Cell Type : ", options=constant.list_cell_types,
                                     help_text="Sample cell type")

    cell_line = twf.SingleSelectField(id='cell_line', label_text="Cell line : ", options=constant.list_cell_lines,
                                     help_text="Select the studied organism")
    target = twf.SingleSelectField(id='target', label_text="Target : ", options=constant.list_ab_targets,
                                     help_text="Select the antibody target")

    bio_background = twf.TextField(id='bio_background', label_text="Bio Background :",
                                   help_text="Example : WT or KO or Mutant / Male or Female")

    stage = twf.TextField(id='stage', label_text="Stage :", help_text="Ex : Day 1 or E10.5")


# EDIT FILLER
# class SEditFiller(EditFormFiller):
#     __model__ = Samples


#DATAGRID
# class SampleGrid(DataGrid):
#     fields = [("User", "get_username"), ("Name", "name"), ("Type", "type"),
#         ("Organism", "organism"), ("Date", "created"), ("Protocole", "protocole"), ("Action", lambda obj:genshi.Markup(
#         get_delete_link(obj.id)
#         + get_edit_link(obj.id)
#         + get_add_link(obj.id)
#         ))]


# sample_table = STable(DBSession)
# sample_table_filler = STableFiller(DBSession)
#new_sample_form = NewSForm(DBSession)
#sample_edit_form = SEditForm(DBSession)
# sample_edit_filler = SEditFiller(DBSession)
#sample_grid = SampleGrid()