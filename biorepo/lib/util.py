import os
import tw2.forms as twf
from biorepo.handler.util import get_file_sha1
import urllib2, urlparse
from tg import flash, redirect, expose, url, response, request
from biorepo.model import DBSession, Samples, Files_up, Attributs, Attributs_values, Labs
from biorepo.lib.constant import path_processed, path_raw, path_tmp, HTS_path_archive, HTS_path_data
from biorepo.websetup.bootstrap import num_admin
from biorepo.model import Measurements
import shutil
import tempfile
from sqlalchemy import and_
from sqlalchemy.orm import synonym
from datetime import datetime
import re
import genshi
date_format = "%d/%m/%Y"


def isAdmin(user):
    for g in user.groups:
        if g.id == num_admin:
            return True
    return False


def to_datagrid(grid_type, grid_data, grid_title=None, grid_display=None):
    '''
    Special method which format the parameters to fit
    on the datagrid template.
    :param grid_type : The DataGrid.
    :type grid_type : a DataGrid Object
    :param grid_data : The data.
    :type grid_data : a list of Object to fill in the DataGrid
    :param grid_title : DataGrid title
    :type grid_title : A string.
    :param grid_display :True if the DataGrid has to be displayed.
    :type grid_display : a boolean. (Normaly it's the len() of the 'grid_data' )
    '''
    data = {'grid': grid_type, 'grid_data': grid_data}
    if grid_title is not None:
        data['grid_title'] = grid_title
    if grid_display is not None:
        data['grid_display'] = grid_display
    return data


def str2bool(str):
    if str.lower() in [1, 't', 'true', 'y', 'yes', 'on']:
        return True
    else:
        return False


def sha1_generation_controller(local_path, url_path, url_bool, tmp_dirname):
    '''
    method to generate a sha1 with a local file or file from an url
    :param local_path : path of the local file to upload, example : "/Users/Michel/MyFile.bed"
    :type local_path : string
    :param url_path : url path of the file to upload, example : "http://www.michel.com/MyFile.bed"
    :type url_path : string
    :param url_bool : if True -> upload the file form the url, if False -> just store the url, won't upload
    :type url_bool : boolean
    :param tmp_dirname : path of the temporary directory
    :type tmp_dirname : string
    :returns: The sha1's file uploaded the filename and the tmp_path
    '''
    #to avoid that 2 or several user upload the same file with the same name in the same dir
    tmp_dirname2 = tempfile.mkdtemp(dir=tmp_dirname)
    #SITUATION 1 : user just wants to upload with local file
    if local_path is not None and url_bool == False:
        #browser version
        try:
            filename = local_path.filename
        #command line version or vitalit_path
        except:
            filename = os.path.split(local_path)[1]
        #tmp_path = os.path.join(tmp_dirname2, str(filename))
        tmp_path = os.path.join(tmp_dirname2, filename)
        #browser version
        try:
            with open(tmp_path, "w") as t:
                t.write(local_path.value)
        #command line version or vitalit_path
        except:
            shutil.copy(local_path, tmp_path)

        sha1 = get_file_sha1(tmp_path)
        return sha1, filename, tmp_path

    #SITUATION 2 : user wants to upload with an URL
    elif local_path is None and url_path is not None and url_bool:
        test_url = urlparse.urlparse(url_path)
        if test_url.path != '':
            u = urllib2.urlopen(url_path)
            #FROM HTSstation
            if test_url.netloc == "htsstation.epfl.ch":
                #normal files
                if (test_url.path).startswith("/data/"):
                    full_path = HTS_path_data + test_url.path
                    tmp_path = os.path.dirname(full_path)
                    try:
                        infos = u.info().get('Content-Disposition')
                        filename = re.search(('filename=(?P<name>"?.+?(;|$))'), infos).group('name')
                    except:
                        filename = url_path.split('/')[-1]
                    sha1 = os.path.basename(full_path)
                #HTSstation archive
                elif (test_url.path).startswith("/data_arch/"):
                    full_path = HTS_path_archive + test_url.path
                    tmp_path = os.path.dirname(full_path)
                    filename = os.path.basename(full_path)
                    tmp_sha1 = filename.split('.')
                    sha1 = tmp_sha1[0]

                else:
                    flash("HTSstation URL NOT VALID", "error")
                    raise redirect("./")

                return sha1, filename, tmp_path

            #NOT FROM HTSstation
            else:
                try:
                    infos = u.info().get('Content-Disposition')
                    filename = re.search(('filename=(?P<name>"?.+?(;|$))'), infos).group('name')
                    if not filename:
                        filename = url_path.split('/')[-1]
                    if filename[-1] == '"':
                        filename = filename[1:-1]
                    filename = filename.strip()
                    if filename[-1] == ";":
                        filename = filename[:-1]
                except:
                    filename = url_path.split('/')[-1]

                tmp_path = os.path.join(tmp_dirname2, filename)
                with open(tmp_path, "w") as t:
                    #u = urllib2.urlopen(url_path)
                    while True:
                        buffer = u.read(8192)
                        if not buffer:
                            break

                        t.write(buffer)
        else:
            flash("URL NOT VALID", "error")
            raise redirect("./")

        sha1 = get_file_sha1(tmp_path)
        return sha1, filename, tmp_path

    #SITUATION 3 : user don't want to upload anything but provides an url
    elif local_path is None and url_path is not None and url_bool == False:
        sha1 = None
        filename = None
        tmp_path = None
        shutil.rmtree(tmp_dirname2)
        return sha1, filename, tmp_path

    else:
        flash("You can't upload a local file and upload from an URL at the same time, sorry", "error")
        raise redirect("./")


def create_meas(user, meas, name, description, status_type, type_, list_samples, parents, dest_raw, dest_processed):
#new measurement management
    meas.user_id = user.id
    if name is not None:
        meas.name = name
    if description is not None:
        meas.description = description
    if status_type is not None:
        #fix the issue CheckBox TW1-->TW2
        if status_type == "on":
            status_type = True
        meas.status_type = status_type
    if type_ is not None:
        if type_ == "on":
            type_ = True
        meas.type = type_

    #parents
    l = []
    if parents is None or parents == []:
        meas.children = l
    else:
        #if type(parents) is str or unicode or just 1 value in the list:
        if type(parents) is unicode or type(parents) is str or len(parents) == 1:
            if type(parents) is list:
                for x in parents:
                    me = DBSession.query(Measurements).filter(Measurements.id == x).first()
                    l.append(me)
            else:
                for x in parents.split(','):
                    me = DBSession.query(Measurements).filter(Measurements.id == x).first()
                    l.append(me)
        else:
            for x in parents:
                me = DBSession.query(Measurements).filter(Measurements.id == x.id).first()
                l.append(me)
        meas.parents = l

    #get the sample information
    if list_samples:
        list_samples_id = list_samples
    else:
        list_samples_id = None

    #replace the for loop to test all the samples
    if list_samples_id is not None:
        samples2 = DBSession.query(Samples).filter(Samples.id.in_(list_samples_id)).all()

    else:
        samples2 = []
    meas.samples = samples2

    if not os.path.exists(dest_raw):
        os.mkdir(dest_raw)

    if not os.path.exists(dest_processed):
        os.mkdir(dest_processed)

    return meas


def manage_fu(existing_fu, meas, public_dirname, filename, sha1, up_data, url_path, url_up, dest_raw, dest_processed, tmp_path, lab):

    tmpdir_to_delete = os.path.abspath(os.path.join(tmp_path, os.path.pardir))
    #fixing bug str "true", str "false" for meas.type
    if isinstance(meas.type, basestring):
        bool_type = str2bool(meas.type)
        meas.type = bool_type

    if existing_fu:
        print "-------- EXISTING FILE --------"
        #create symbolic link
        source = existing_fu.path + "/" + sha1

        if meas.type:
            dest = dest_raw + sha1
            #test symlin existance
            if os.path.islink(dest):
                symlink_e = "This file was already in your personal folder"
            else:
                symlink_e = "This file was added to your personal folder"
                os.symlink(source, dest)

        else:
            dest = dest_processed + sha1
            #test symlink existance
            if os.path.islink(dest):
                symlink_e = "This file was already in your personal folder"
            else:
                symlink_e = "This file was added to your personal folder"
                os.symlink(source, dest)

        meas.fus.append(existing_fu)

        DBSession.add(meas)
        DBSession.flush()

        flash(symlink_e + ", measurement created")
        #remove the tmp file
        #os.remove(tmp_path)
        shutil.rmtree(tmpdir_to_delete)
        #raise redirect("./")
        return existing_fu

        ###########################################################################################
    else:
        #new files_up building
        fu = Files_up()
        #raw test for path orientation
        if meas.type:
            fu.path = path_raw(lab)
            data_dirname = os.path.join(public_dirname, fu.path)
        else:
            fu.path = path_processed(lab)
            data_dirname = os.path.join(public_dirname, fu.path)

        #save the filename and the extension to the database
        fu.filename = filename
        if '.' in filename:
            extension = filename.split('.')[-1]
            fu.extension = extension
#            root, ext = os.path.splitext(filename)
#            DOUBLE_EXTENSIONS = ['tar.gz','tar.bz2','bedGraph.gz','bed.gz']
#            if any([filename.endswith(x) for x in DOUBLE_EXTENSIONS]):
#                root, first_ext = os.path.splitext(root)
#                ext = first_ext + ext
#                fu.extension = ext
#            else:
#                fu.extension = ext
        else:
            fu.extension = "not specified"
        data_path = os.path.join(data_dirname, str(sha1))
        fu.sha1 = sha1
        fu.url_path = url_path

        #writing the file into the server HD
        #version browser
        try:
            with open(data_path, "w") as d:
                if up_data is not None:
                    d.write(up_data.value)
                elif url_path is not None and url_up:

                    u = urllib2.urlopen(url_path)
                    while True:
                        buffer = u.read(8192)
                        if not buffer:
                            break

                        d.write(buffer)
                else:
                    print "ERROR"
        #version commandline
        except:
            shutil.move(tmp_path, data_path)

        #symlink
        source = data_path
        if meas.type:
            dest = dest_raw + sha1
            if os.path.islink(dest):
                symlink_e = "This file was already in your personal folder"
            else:
                symlink_e = "This file was added to your personal folder"
                os.symlink(source, dest)

        else:
            dest = dest_processed + sha1
            if os.path.islink(dest):
                symlink_e = "This file was already in your personal folder"
            else:
                symlink_e = "This file was added to your personal folder"
                os.symlink(source, dest)

        #add to the crossing table (measurement <-> file uploaded)
        meas.fus.append(fu)

        #adding new measurement and new files_up to the db
        DBSession.add(meas)
        DBSession.add(fu)

        DBSession.flush()

        if meas.type:
            flash(symlink_e + ", raw data was successfully created")
        else:
            flash(symlink_e + ", processed data was successfully created")

        #remove the tmp file
        #os.remove(tmp_path)
        shutil.rmtree(tmpdir_to_delete)

        return fu
        #raise redirect("./")


def manage_fu_from_HTS(existing_fu, meas, filename, sha1, url_path, hts_path):

    #fixing bug str "true", str "false" for meas.type
    if isinstance(meas.type, basestring):
        bool_type = str2bool(meas.type)
        meas.type = bool_type

    if existing_fu:
        print "-------- EXISTING FILE FROM HTS--------"
        meas.fus.append(existing_fu)

        DBSession.add(meas)
        DBSession.flush()
        return existing_fu
        ###########################################################################################
    else:
        #new files_up building
        fu = Files_up()
        fu.path = hts_path
        #save the filename and the extension to the database
        fu.filename = filename
        if '.' in filename:
            extension = filename.split('.')[-1]
            fu.extension = extension
        else:
            fu.extension = "not specified"
        fu.sha1 = sha1
        fu.url_path = url_path

        #add to the crossing table (measurement <-> file uploaded)
        meas.fus.append(fu)

        #adding new measurement and new files_up to the db
        DBSession.add(meas)
        DBSession.add(fu)
        DBSession.flush()
        return fu


def list_lower(key_, list_keys):
    list_tmp = []
    if key_ is not None:
        key_lower = key_.lower()
        for i in list_keys:
            if i is not None:
                j = i.lower()
                list_tmp.append(j)

        num_key = list_tmp.index(key_lower)
        return list_keys[num_key]
    else:
        return None


def name_org(assembly):
    dico_translate = {'mm': 'mouse', 'hg': 'human'}
    assembly = assembly[:2]
    if dico_translate.has_key(assembly):
        return dico_translate[assembly]
    else:
        flash("Assembly not known in dico_translate, contact the admin please", "error")
        raise redirect(url("/search"))


def check_boolean(bool_to_test):
    try:
        return str(bool_to_test).lower() in ("on", "true", "1", "t", "y", "yes")
    except:
        print "BOOLEAN PROBLEM, bool = ", bool_to_test
        raise


def convert_widget(widget):
    '''
    input = widget name from config file
    output = widget correct form
    '''

    dic_widget = {
    'singleselectfield': twf.SingleSelectField,
    'checkbox': twf.CheckBox,
    'textfield': twf.TextField,
    'textarea': twf.TextArea,
    'multipleselectfield': twf.MultipleSelectField
    }

    return dic_widget[widget]()


def print_traceback():
    import sys
    import traceback
    traceback.print_exception(*sys.exc_info())


def value_travel_into_da_list(daList, initial_position, final_position):
    new_list = daList[:initial_position] + daList[initial_position + 1:final_position] + [daList[initial_position]] + daList[final_position + 1:]
    return new_list


def display_file_size(file_size):
    if file_size < 1000:
        file_size = str(file_size) + " o"
    elif file_size >= 1000 and file_size < 1000000:
        file_size = str(file_size)[:-3] + ',' + str(file_size)[-3] + " ko"
    elif file_size >= 100000 and file_size < 1000000000:
        file_size = str(file_size)[:-6] + ',' + str(file_size)[-6] + " Mo"
    else:
        file_size = str(file_size)[:-9] + ',' + str(file_size)[-9] + " Go"
    return file_size

##########################################################################################
######################################  FOR SEARCH GRID  #################################
##########################################################################################


class SearchWrapper(object):
    def __init__(self, meas):
        self.meas = meas
        self.id = self.meas.id
        self.user = self.get_name()
        self.description = self.meas.description
        self.date = self.meas.date
        self.created = self.date.strftime(date_format)
        self.samples = self.meas.samples
        self.samples_display = ' ; '.join(['%s' % (sample.name) for sample in self.samples])
        self.name = self.get_meas_name()
        self.sample_type = self.get_sample_type()
        self.measurement_type = self.get_measurement_type()
        self.attributs_meas = [a for a in self.meas.attributs if not a.deprecated]
        #self.searchable_attributs_meas = [a for a in self.attributs_meas if a.searchable]
        self.attributs_samples = self.get_attributs_samples()
        #self.searchable_attributs_samples = [a for a in self.attributs_samples if a.searchable]
        self.scroll_info = genshi.Markup(self.get_img_scroll())

    def get_name(self):
        name = self.meas.user.name
        first_letter = (self.meas.user.firstname)[0].upper()
        name_display = first_letter + ". " + name
        return name_display

    def get_meas_name(self):
        name = self.meas.name
        meas_id = self.meas.id
        name_display = name + " (id:" + str(meas_id) + ")"
        return name_display

    def get_sample_type(self):
        list_type = []
        for sample in self.samples:
            if sample.type is not None:
                list_type.append(sample.type)
        return ' ; '.join(list_type)

    def get_measurement_type(self):
        """
        for a nice raw/processed type on search page
        """
        if self.meas.type == False:
            return "Processed"
        else:
            return "Raw"

    def get_values_from_attributs_meas(self, att):
        '''
        for a nice display of several attributs_values.value by one attributs.key
        '''
        att_values = DBSession.query(Attributs_values).filter(and_(Attributs_values.attribut_id == att.id,\
        Attributs_values.deprecated == False)).all()
        #for the boolean display
        if att.widget == "checkbox":
            for v in att_values:
                if v in self.meas.a_values:
                    val = check_boolean(v.value)
                    att_key = att.key
                    att_key = att_key.replace("_", " ")
                    if not val:
                        return "NOT " + att_key
                    else:
                        return att_key
        #for the others widget's types
        else:
            return ' ; '.join(['%s' % (v.value) for v in att_values if v in self.meas.a_values])

    def get_values_from_attributs_sample(self, att):
        '''
        for a nice display of several attributs_values.value by one attributs.key
        '''
        att_values = DBSession.query(Attributs_values).filter(and_(Attributs_values.attribut_id == att.id,\
        Attributs_values.deprecated == False)).all()
        list_values = []
        #for the boolean display
        if att.widget == "checkbox":
            for v in att_values:
                for s in self.samples:
                    if v in self.s.a_values:
                        val = check_boolean(v.value)
                        att_key = att.key
                        att_key = att_key.replace("_", " ")
                        if not val:
                            word = "NOT " + att_key
                            if word not in list_values:
                                list_values.append(word)
                        else:
                            if att_key not in list_values:
                                list_values.append(att_key)
        #for the others widget's types
        else:
            for v in att_values:
                for s in self.samples:

                    if v in s.a_values:
                        if v.value not in list_values:
                            list_values.append(v.value)
        list_values = [l for l in list_values if l]
        final = " ; ".join(list_values)
        return final

    def get_attributs_samples(self):
        list_a = []
        for s in self.samples:
            for a in s.attributs:
                list_a.append(a)
        return list_a

    def searchable_attributs(self):
        '''
        to reference the search buttons
        '''
        return [a.key for a in self.attributs_meas if a.searchable] + [a.key for a in self.attributs_samples if a.searchable]

    def get_img_scroll(self):
        '''
    test to display scroll picture into datagrid
    '''
        return'''
        <img src="%s"/> ''' % ('./images/open.png')


###############################################
class FileChunk(object):

    chunk_size = 4096

    def __init__(self, filename, length, start=None, stop=None):
        self.filename = filename
        self.start = start
        self.stop = stop
        self.len = length

    def read(self):
        self.fileobj = open(self.filename, 'rb')
        if self.start:
            self.fileobj.seek(self.start)
        if self.stop:
            sz = self.stop - self.start
            return self.fileobj.read(sz)
        return self.fileobj.read()
