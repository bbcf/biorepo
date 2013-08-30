import tw2.forms as twf
import tw2.core as twc
import tw2.dynforms as twd
from tg import tmpl_context, session, flash
from biorepo.lib import constant
from biorepo.model import DBSession, Labs, Attributs, Attributs_values, Samples, Measurements
from tg.controllers import redirect
from biorepo.lib.util import convert_widget, check_boolean


class MyForm(twf.TableForm):
    child = twd.HidingTableLayout()

#methods
# def get_samples():
#     return [(sample.id, '%s (%s)' % (sample.name, sample.organism)) for sample in tmpl_context.samples]


# def get_projects():
#     return [(project.id, '%s' % project.project_name) for project in tmpl_context.projects]
#check with https://github.com/bbcf/bs/blob/master/bs/operations/form.py
def new_form(user_lab):
    '''for new form'''
    lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()

    #static lists
    list_static_samples = [twf.SingleSelectField(id="project", label_text="Your projects : ",
                    help_text="Select project for this sample", prompt_text=None),
                    twf.TextField(id="name", label_text="Name :", validator=twc.Validator(required=True)),
                    twf.SingleSelectField(id="type", label_text="Type : ",
                    help_text="Technique used", prompt_text=None),
                    twf.TextArea(id="protocole", label_text="Protocole :",)
                    ]
    list_static_measurements = [twf.HiddenField(id="IDselected", label_text="ID selected :"),
                    twf.TextField(id="name", label_text="Name :", placeholder="Measurement name...", validator=twc.Validator(required=True)),
                    twf.TextArea(id="description", label_text="Description :"),
                    twf.MultipleSelectField(id="samples", label_text="Your samples : ",
                    help_text="You can add some of your existing data to this project."),
                    twf.CheckBox(id="status_type", label_text="Private : ",
                    help_text="Check if private data"),
                    twf.CheckBox(id="type", label_text="Raw data : ", help_text="Check if raw data"),
                    twf.MultipleSelectField(id="parents", label_text="Parents : ", help_text="Parent(s) of this measurement."),
                    twd.HidingRadioButtonList(id="upload_way", label_text='Upload my file via...', options=('my computer', 'a Vital-IT path', 'an URL'),
        mapping={
            'my computer': ['upload'],
            'a Vital-IT path': ['vitalit_path'],
            'an URL': ['url_path', 'url_up'],
        }),
    twf.FileField(id="upload", help_text='Please provide a data'),
    twf.TextField(id="vitalit_path", label_text="Scratch path", placeholder="/scratch/el/biorepo/dropbox/"),
    twf.TextField(id="url_path", label_text="File's url", placeholder="http://www..."),
    twf.CheckBox(id="url_up", label_text="I want to upload the file from this URL : ", help_text="tick it if you want to download it in BioRepo")
                    ]
    list_dynamic_samples = []
    list_dynamic_measurements = []
    if lab is None:
        print "----- no dynamic fields detected ---------"
        list_fields = [list_static_samples, list_dynamic_samples, list_static_measurements, list_dynamic_measurements]
        return list_fields
    else:
        lab_id = lab.id
        list_attributs = DBSession.query(Attributs).filter(Attributs.lab_id == lab_id).all()
        #TODO : ERASE IT IF IT'S OK FOR OTHERS LABS
        #if user_lab == "ptbb":

        if len(list_attributs) > 0:
            #lists_construction(list_attributs)
            for a in list_attributs:
                attribut_key = a.key
                deprecated = a.deprecated
                fixed_value = a.fixed_value
                widget = a.widget
                owner = a.owner
                #############################
                ######### NEW SAMPLE ########
                #############################
                if owner == "sample":
                    #dynamic
                    if not deprecated and fixed_value:
                        twf_type = convert_widget(widget)
                        twf_type.id = attribut_key
                        if widget == "multipleselectfield" or widget == "singleselectfield":
                            list_values = []
                            list_attributes_values = DBSession.query(Attributs_values).filter(Attributs_values.attribut_id == a.id).all()
                            for av in list_attributes_values:
                                if not av.deprecated:
                                    list_values.append(av.value)
                            twf_type.options = list_values
                            list_dynamic_samples.append(twf_type)

                        elif widget == "checkbox":
                            list_dynamic_samples.append(twf_type)

                        else:
                            print widget, "-----ERROR----- ELSE, type samples widget in forms.py"
                    elif not deprecated and not fixed_value:
                        twf_type = convert_widget(widget)
                        twf_type.id = attribut_key
                        if widget == "textfield" or widget == "textarea":
                            twf_type.placeholder = "Write here..."
                            list_dynamic_samples.append(twf_type)
                        else:
                            print widget, "WIGDET SAMPLE NOT FOUND, add an elif please"
                            raise
                    elif deprecated:
                        pass
                    else:
                        print "WIDGET SAMPLES ERROR : widget type is not known --> ", widget
                        raise
                ################################
                ######## NEW MEASUREMENT #######
                ################################
                elif owner == "measurement":
                    #dynamic
                    #for attributes with fixed values
                    if not deprecated and fixed_value:
                        twf_type = convert_widget(widget)
                        twf_type.id = attribut_key
                        if widget == "multipleselectfield" or widget == "singleselectfield":
                            list_values = []
                            list_attributes_values = DBSession.query(Attributs_values).filter(Attributs_values.attribut_id == a.id).all()
                            for av in list_attributes_values:
                                if not av.deprecated:
                                    list_values.append(av.value)
                            twf_type.options = list_values
                            list_dynamic_measurements.append(twf_type)
                        #elif widget == "checkbox":
                            #list_dynamic_measurements.append(twf_type)
                        else:
                            print widget, "-----ERROR----- ELSE, type measurements widget in forms.py"
                            raise

                    #for others attributes
                    elif not deprecated and not fixed_value:
                        twf_type = convert_widget(widget)
                        twf_type.id = attribut_key
                        if widget == "textfield" or widget == "textarea":
                            twf_type.placeholder = "Write here..."
                            list_dynamic_measurements.append(twf_type)
                        elif widget == "checkbox":
                            list_dynamic_measurements.append(twf_type)
                        else:
                            print widget, "WIGDET MEASUREMENT NOT FOUND, add an elif please"
                            raise
                    elif deprecated:
                        pass
                    #in bugs case
                    else:
                        print "WIDGET MEASUREMENTS ERROR : widget type is not known --> ", widget
                        raise

            list_fields = [list_static_samples, list_dynamic_samples, list_static_measurements, list_dynamic_measurements]
            return list_fields

        else:
            print "-----forms.py----- Houston, we have a problem : The lab ", lab.name, " doesn't get any attributes -----"
            raise


def edit_form(user_lab, owner, id_object):
    '''
    to edit dynamic form
    '''
    lab = DBSession.query(Labs).filter(Labs.name == user_lab).first()
    #static lists
    list_static_samples = [twf.HiddenField(id="IDselected", label_text="ID selected :"),
                    twf.SingleSelectField(id="project", label_text="Your projects : ",
                    help_text="the project which contains your sample is selected", prompt_text=None),
                    twf.TextField(id="name", label_text="Name :", validator=twc.Required),
                    twf.SingleSelectField(id="type", label_text="Type : ",
                    help_text="What technique do you use ?", prompt_text=None),
                    twf.TextArea(id="protocole", label_text="Protocole :",),
                    twf.MultipleSelectField(id="measurements", label_text="Attached measurement(s) : ")
                    ]
    list_static_measurements = [
                    twf.HiddenField(id="IDselected", label_text="ID selected :"),
                    twf.TextField(id="name", label_text="Name :", placeholder="Measurement name...", validator=twc.Required),
                    twf.TextArea(id="description", label_text="Description :"),
                    twf.MultipleSelectField(id="samples", label_text="Your samples : ",
                    help_text="You can add some of your existing data to this project."),
                    twf.CheckBox(id="status_type", label_text="Private : ",
                    help_text="Check it if you want a private data"),
                    twf.CheckBox(id="type", label_text="Raw data : ", help_text="Check it is a raw data"),
                    twf.MultipleSelectField(id="parents", label_text="Parents : ", help_text="Parent(s) of this measurement."),
                    twf.LabelField(id="uploaded", help_text="is attached to this measurement. If you want to change, it's better to delete this measurement and create a new one."),
                    twf.TextField(id="url_path", help_text="If you want to add a new URL, your old URL will be stored into the description", placeholder="http://www...")
                    #twf.CheckBox(id="url_up", label_text="I want to upload the file from this URL : ",
                    #help_text="tick it if you want to download it in BioRepo")
                    ]

    list_dynamic_samples = []
    list_dynamic_measurements = []
    if lab is None:
        print "----- no dynamic fields detected ---------"
        list_fields = [list_static_samples, list_dynamic_samples, list_static_measurements, list_dynamic_measurements]
        return list_fields
    else:
        if owner == "sample":
            object_edited = DBSession.query(Samples).filter(Samples.id == int(id_object)).first()
            list_dynamic = list_dynamic_samples
            tag = "samples"
        elif owner == "meas":
            object_edited = DBSession.query(Measurements).filter(Measurements.id == int(id_object)).first()
            list_dynamic = list_dynamic_measurements
            tag = "measurements"
        else:
            print "----------------- owner error : ", owner, " <----owner --------------------"
            raise

        if object_edited is not None:
            list_dynamic_attributes = object_edited.attributs
            for att in list_dynamic_attributes:
                if att.deprecated == False:
                    twf_type = convert_widget(att.widget)
                    twf_type.id = att.key
                    list_a_values = att.values

                    if att.widget == "textfield" or att.widget == "textarea":
                        for v in list_a_values:
                            if hasattr(v, tag):
                                value_object = getattr(v, tag)
                            if object_edited in value_object:
                                twf_type.value = v.value
                        list_dynamic.append(twf_type)
                    elif att.widget == "checkbox":
                        for v in list_a_values:
                            if hasattr(v, tag):
                                value_object = getattr(v, tag)
                            if object_edited in value_object:
                                #dynamic boolean are stored in varchar in the db, we have to cast them in boolean for the display
                                value_2_display = check_boolean(v.value)
                                twf_type.value = value_2_display
                        list_dynamic.append(twf_type)
                    elif att.widget == "multipleselectfield":
                        list_possible_values = []
                        for v in list_a_values:
                            list_possible_values.append(v.value)
                        twf_type.options = list_possible_values
                        selected_values = []
                        for v in list_a_values:
                            if hasattr(v, tag):
                                value_object = getattr(v, tag)
                            if object_edited in value_object:
                                selected_values.append(v.value)
                        twf_type.value = selected_values
                        list_dynamic.append(twf_type)

                    elif att.widget == "singleselectfield":
                        list_possible_values = []
                        for v in list_a_values:
                            list_possible_values.append(v.value)
                        twf_type.options = list_possible_values
                        for v in list_a_values:
                            if hasattr(v, tag):
                                value_object = getattr(v, tag)
                            if object_edited in value_object:
                                twf_type.value = v.value
                        list_dynamic.append(twf_type)

        else:
            print "Your ", owner, " was not found. ID problem. id :", id_object
            raise

        list_fields = [list_static_samples, list_dynamic_samples, list_static_measurements, list_dynamic_measurements]
        return list_fields


def build_form(state, owner, id_object):
    '''
    build the new/edit widget for dynamic samples/measurements
    '''
    user_lab = session.get("current_lab", None)
    if state == "new":
        lists_fields = new_form(user_lab)
    elif state == "edit":
        lists_fields = edit_form(user_lab, owner, id_object)
    list_static_samples = lists_fields[0]
    list_dynamic_samples = lists_fields[1]
    list_static_measurements = lists_fields[2]
    list_dynamic_measurements = lists_fields[3]
    #form_widget = twf.TableForm()
    form_widget = MyForm()
    if state == "new" and owner == "sample":
        all_fields = list_static_samples + list_dynamic_samples
        form_widget.submit = twf.SubmitButton(value="Create my sample")
    elif state == "new" and owner == "meas":
        all_fields = list_static_measurements + list_dynamic_measurements
        form_widget.submit = twf.SubmitButton(id="submit", value="Create my measurement")
    elif state == "edit" and owner == "sample":
        all_fields = list_static_samples + list_dynamic_samples
        form_widget.submit = twf.SubmitButton(value="Edit my sample")
    elif state == "edit" and owner == "meas":
        all_fields = list_static_measurements + list_dynamic_measurements
        form_widget.submit = twf.SubmitButton(value="Edit my measurement")
    form_widget.children = all_fields
    return form_widget


#project
class NewProject(twf.TableForm):
    # __omit_fields__ = ['id', 'user', 'date', 'created']
    project_name = twf.TextField(label_text="Name :", validator=twc.Validator(required=True))
    description = twf.TextArea(label_text="Description :",)
    samples = twf.MultipleSelectField(label_text="Your samples : ", help_text="You can add some of your existing samples to this project.")

    submit = twf.SubmitButton(value="Create my project")


class EditProject(twf.TableForm):
    # __omit_fields__ = ['user', 'date', 'created']
    IDselected = twf.HiddenField(label_text="ID selected")
    project_name = twf.TextField(label_text="Name :", validator=twc.Required)
    description = twf.TextArea(label_text="Description :",)
    samples = twf.MultipleSelectField(label_text="Your samples : ", help_text="You can add some of your existing samples to this project.")
    selected_samples = twf.HiddenField(label_text="")

    submit = twf.SubmitButton(id="submit", value="Edit my project")


#samples

class EditSample(twf.TableForm):
    IDselected = twf.HiddenField(label_text="ID selected :")
    project = twf.SingleSelectField(label_text="Your projects : ",
        help_text="the project which contains your sample is selected")
    name = twf.TextField(label_text="Name :", validator=twc.Required)
    type = twf.SingleSelectField(label_text="Type : ")
    protocole = twf.TextArea(label_text="Protocole :")
    measurements = twf.MultipleSelectField(label_text="Attached measurement(s) : ")

    submit = twf.SubmitButton(value="Edit my sample")


class EditMeas(twf.TableForm):
    #fields
    IDselected = twf.HiddenField(label_text="ID selected :")
    name = twf.TextField(label_text="Name :", placeholder="Measurement name...", validator=twc.Required)
    description = twf.TextArea(label_text="Description :")

    samples = twf.MultipleSelectField(label_text="Your samples : ",
                                      help_text="You can add some of your existing data to this project.")

    status_type = twf.CheckBox(label_text="Private : ", help_text="Check it if you want a private data")
    type = twf.CheckBox(label_text="Raw data : ", help_text="Check it is a raw data")

    #parents management
    parents = twf.MultipleSelectField(label_text="Parents : ",
        help_text="Parent(s) of this measurement.")

    uploaded = twf.LabelField(help_text="is attached to this measurement. If you want to change, it's better to delete this measurement and create a new one.")

    url_path = twf.TextField(label_text="File's url", placeholder="http://www....")

    submit = twf.SubmitButton(value="Edit my measurement")


class LabChoice (twf.TableForm):
    lab_choice = twf.SingleSelectField(id="lab_choice", label_text="Choose your lab for the session : ", prompt_text=None)
