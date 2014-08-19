# -*- coding: utf-8 -*-
import re
import os
import tarfile
from xlrd import open_workbook
from biorepo.model import DBSession, Labs

#* create the new measurements
#wget --post-data "key=xxxxxxxxxxxxxxxxxxxxx&mail=beta.testeur@epfl.ch&lab=labname&name=test&description=blablbalbal&assembly=mm9&
#path=/my/file.tgz&samples=2" http://biorepo.epfl.ch/biorepo/measurements/create/


def run_script(root, path_tgz):
    #path_tgz is the path to acces to the tgz with data and data.xls into it
    projects_c = root.projects
    samples_c = root.samples
    meas_c = root.measurements

    bioRepo_url_project = "http://biorepo.epfl.ch/biorepo/projects/create/"
    bioRepo_url_sample = "http://biorepo.epfl.ch/biorepo/samples/create/"
    bioRepo_url_measurement = "http://biorepo.epfl.ch/biorepo/measurements/create/"

    metadataFile = ""

    allFiles_tar = path_tgz
    print "checking " + allFiles_tar
    if not os.path.exists(allFiles_tar):
        raise NameError("Error, the archive passed doesn't exist:" + allFiles_tar)
    else:
        metadataFile = "data.xls"

    # open tar file
    tar = tarfile.open(allFiles_tar)
    print "wait a moment please (can take few minuts)"
    tmp_path = allFiles_tar.split('/')
    extract_path = "/".join(tmp_path[:-1])
    tar.extractall(path=extract_path)
    allfiles = []
    for finfo in tar.getmembers():
        if not finfo.isdir():
            try:
                tmp = (finfo.name).split('/')
                toTest = tmp[1]
                if not toTest.startswith('.'):
                    allfiles.append(finfo.name)
            except:
                if (finfo.name).endswith('.xls'):
                    allfiles.append(finfo.name)
                pass
    print "Content of the archive:"
    print allfiles

    if len(metadataFile) < 2 or not metadataFile in allfiles or not os.path.splitext(metadataFile)[-1] in ['.xls']:
        raise NameError("Error, the metadata file passed (" + metadataFile + ") does not exist or has the wrong extension (.xls)" + " --> extension=" + os.path.splitext(metadataFile)[-1])

    print "Metadata file:" + metadataFile

    # open metadata excel file (should be .xls!!)
    #data=open_workbook("/home/mouscaz/test_marion/upload/data.xls",ragged_rows=True,formatting_info=False)
    #data=open_workbook("data.xls",ragged_rows=True,formatting_info=False)
    path_excel = extract_path + "/" + metadataFile
    data = open_workbook(path_excel, ragged_rows=True, formatting_info=False, encoding_override="cp1252")
    if int(data.nsheets) > 0:
        infos = data.sheet_by_index(0)
    else:
        infos = ""

    print infos.ncols
    print infos.nrows

    #init i_USER, i_PROJECT, i_SAMPLES and i_MEASUREMENTS + i_COMMENTS
    i_COMMENTS = (infos.nrows, infos.ncols)
    for nr in range(0, infos.nrows):
        for nc in range(0, infos.row_len(nr)):
            if infos.row_len(nr) > 0:
                if isinstance(infos.cell_value(nr, nc), basestring):
                    v = (infos.cell_value(nr, nc)).encode('utf-8')
                else:
                    v = str(infos.cell_value(nr, nc))
                if re.search(r'USER', v) and nr < i_COMMENTS[0]:
                    i_USER = (nr, nc)
                if re.search(r'PROJECT', v) and nr < i_COMMENTS[0]:
                    i_PROJECT = (nr, nc)
                if re.search(r'SAMPLES', v) and nr < i_COMMENTS[0]:
                    i_SAMPLES = (nr, nc)
                if re.search(r'MEASUREMENTS', v) and nr < i_COMMENTS[0]:
                    i_MEASUREMENTS = (nr, nc)
                if re.search(r'COMMENTS', v):
                    i_COMMENTS = (nr, nc)

    print "i_USER=" + str(i_USER) + "=>" + str(infos.cell_value(i_USER[0], i_USER[1]))
    print "i_PROJECT=" + str(i_PROJECT) + "=>" + str(infos.cell_value(i_PROJECT[0], i_PROJECT[1]))
    print "i_SAMPLES=" + str(i_SAMPLES) + "=>" + str(infos.cell_value(i_SAMPLES[0], i_SAMPLES[1]))
    print "i_MEASUREMENTS=" + str(i_MEASUREMENTS) + "=>" + str(infos.cell_value(i_MEASUREMENTS[0], i_MEASUREMENTS[1]))
    print "i_COMMENTS=" + str(i_COMMENTS) + "=>" + str(infos.cell_value(i_COMMENTS[0], i_COMMENTS[1]))

    def fill_dict_vert(sheet, start_row, end_row, start_col):
        out_dict = {}
        for x in range(start_row + 1, end_row):
            if infos.row_len(x) > 1:
                k = str(infos.cell_value(x, start_col))
                k = re.sub(r'\*', "", str(k))
                out_dict[k] = str(infos.cell_value(x, start_col + 1))
            elif infos.row_len(x) == 1:
                k = str(infos.cell_value(x, start_col))
                k = re.sub(r'\*', "", str(k))
                out_dict[k] = ""
        return out_dict

    def fill_dict_hor(sheet, start_row, end_row):
        id_cur_sample = 0
        out = []
        for x in range(start_row, end_row):
            if infos.row_len(x) > 0 and x > start_row:
                out.append({})
                for i in range(0, infos.row_len(x)):
                    k = str(infos.cell_value(start_row, i))
                    k = re.sub(r'\*', "", str(k))
                    #to fix pb with excel cells formats (int/str randomly)
                    val = str(infos.cell_value(x, i))
                    if val.endswith(".0"):
                        try:
                            out[id_cur_sample][k] = str(int(float(val)))
                        except:
                            #for this case, cell contains text too
                            out[id_cur_sample][k] = val
                    else:
                        out[id_cur_sample][k] = val
                id_cur_sample += 1
        return out

    USER = {}
    PROJECT = {}
    SAMPLES = {}
    MEASUREMENTS = {}

    #Parse USER and PROJECT infos
    USER = fill_dict_vert(infos, i_USER[0], i_PROJECT[0], i_USER[1])
    PROJECT = fill_dict_vert(infos, i_PROJECT[0], i_SAMPLES[0], i_PROJECT[1])

    print "*****USER******"
    print USER
    print "*****PROJECT******"
    print PROJECT

    #Parse SAMPLES and MEASUREMENTS infos
    SAMPLES = fill_dict_hor(infos, i_SAMPLES[0] + 1, i_MEASUREMENTS[0] - 1)
    MEASUREMENTS = fill_dict_hor(infos, i_MEASUREMENTS[0] + 1, i_COMMENTS[0] - 1)
    i_MEASUREMENTS_TO_CREATE = range(0, len(MEASUREMENTS))

    ################ PREPARE wget_cmds ######################
    #* create the new Project
    if "project_id" in PROJECT and len(PROJECT["project_id"]) > 0:
        createProject = False
    else:
        createProject = True

    #EACH LAB REGISTRED INTO BIOREPO HAVE TO BE HERE
    def get_lab_id(lab_name):
        #TO TEST
        # lab = DBSession.query(Labs).filter(Labs.name == lab_name).first()
        # lab_id = lab.id
        dic_name_id = {'ptbb': 1, 'lvg': 3, 'updub': 2, 'upnae': 4, 'shore': 5, 'stutz': 6}
        lab_id = dic_name_id[lab_name]
        return lab_id

    def create_project(dict_project, u_key="", u_mail="", u_lab="", url=""):
        options = {'lab': str(get_lab_id(u_lab))}
        for k, v in dict_project.iteritems():
            k = re.sub(r'\*', "", str(k))
            if len(str(v)) > 0:
                options[str(k)] = str(v)
        dico_project = projects_c.create(**options)
        if 'ERROR' in dico_project:
            print dico_project['ERROR']
            raise

        if dico_project["project_id"]:
            #if Excel transform string in float...
            p_id_tmp = (dico_project["project_id"]).split('.')
            p_id = p_id_tmp[0]
            PROJECT['project_id'] = p_id
        else:
            PROJECT['project_id'] = ""

    if createProject:
        print "********** Creating Project : ", PROJECT["project_name"], " ***************"
        create_project(PROJECT, u_key=USER['user_key'], u_mail=USER['user_email'], u_lab=USER['lab'], url=bioRepo_url_project)
        print "********** Project created ***********"

    def create_measurement(dict_measurement, u_key="", u_mail="", u_lab="", parent_id="", url=""):
        options = {'key': u_key, 'mail': u_mail, 'lab': u_lab}
        if len(parent_id) > 0:
            options['parent_id'] = parent_id
        for k, v in dict_measurement.iteritems():
            k = re.sub(r'\*', "", str(k))
            print str(k) + "=>" + str(v)
            if len(str(v)) > 0 and str(k) != "generated_from" and not re.search(r'samples_names', str(k)):
                if str(k) == "type":
                    if str(v).lower() == "processed":
                        v = "False"
                    else:
                        v = "True"
                if str(k) == "status_type":
                    if str(v).lower() == "private":
                        v = "False"
                    else:
                        v = "True"
                if re.search("url_up", str(k)):
                    if str(v).lower() == "yes":
                        v = "True"
                    else:
                        v = "False"
                # if re.search(r'url_path', str(k)):
                #     if re.search(r'uhts-lgtf', str(v)) or re.search(r'uhts-gva', str(v)):
                #         n = str(v).split("/")
                #         v = "http://www.humanmetrics.com/" + n[-1]
                #         print "v=" + v
                if re.search(r'filename', str(k)):
                    for i, p in enumerate(allfiles):
                        reg_v = re.escape(str(v))
                        if re.search(reg_v, p):
                            file_path = p
                            print str(v) + "=>" + p + ".\t***** " + file_path
                            break
                        else:
                            file_path = ""
                    #v = os.getcwd() + "/" + file_path
                    v = os.path.abspath(extract_path + "/" + file_path)
                    print "v=" + str(v)
                    k = "path"
                options[str(k)] = str(v)

        dico_meas = meas_c.create(**options)
        if dico_meas["meas_id"]:
            dict_measurement["meas_id"] = dico_meas["meas_id"]

    def createAndcheck_dependancies(curMeasurement, created_measurements):
        if (not "generated_from" in curMeasurement) or ("generated_from" in curMeasurement and len(curMeasurement['generated_from']) == 0):
            print "No dependancies"
            return (True, "")
        elif "generated_from" in curMeasurement and len(curMeasurement['generated_from']) > 0:
            if len(created_measurements) == 0:
                print "dependancies exist but no measurement has been created yet"
                return (False, "")
            #will check that all linked measurements have been created
            print("will check that all linked measurements have been created")
            all_parents_tmp = (curMeasurement['generated_from']).split(',')
            #check pb int/str wih excel cells formats
            all_parents = [str(int(float(x))) for x in all_parents_tmp]
            print all_parents
            n = 0
            l = ""
            for i in range(0, len(all_parents)):
                if all_parents[i] in created_measurements.keys():
                    l = l + str(created_measurements[all_parents[i]]) + ","
                    n += 1
            if n == len(all_parents):
                return (True, l[0:len(l) - 1])
            else:
                return (False, "")
        else:
            return (True, "")

    print "*************** Create Measurements *****************"
    it = 0
    created_measurements = {}
    print str(len(i_MEASUREMENTS_TO_CREATE)) + " measurements to create:"
    print i_MEASUREMENTS_TO_CREATE
    while len(i_MEASUREMENTS_TO_CREATE) > 0 and it < 5:
        print "###### Iteration " + str(it) + " ############"
        created = []
        for m in i_MEASUREMENTS_TO_CREATE:
            print "*===================== will create measurement" + str(m) + "=====================*"
            dependancies = createAndcheck_dependancies(MEASUREMENTS[m], created_measurements)
            print MEASUREMENTS[m]
            print "dependancies="
            print dependancies
            print "dependancies with:" + str(dependancies[1])
            if dependancies[0]:
                create_measurement(MEASUREMENTS[m], u_key=USER['user_key'], u_mail=USER['user_email'], u_lab=USER['lab'], parent_id=dependancies[1], url=bioRepo_url_measurement)
                if "meas_id" in MEASUREMENTS[m]:
                    print "Measurement " + str(m) + " has been created:"
                    print MEASUREMENTS[m]
                    print "=> has dependancies with:" + dependancies[1]
                    #if 'name' in MEASUREMENTS[m]:
                        #created_measurements[MEASUREMENTS[m]['name']] = MEASUREMENTS[m]['meas_id']
                    if 'parent_num' in MEASUREMENTS[m]:
                        created_measurements[MEASUREMENTS[m]['parent_num']] = MEASUREMENTS[m]['meas_id']
                    created.append(m)
                else:
                    print "Measurement " + str(m) + " Not created:"
        for i in created:
            i_MEASUREMENTS_TO_CREATE.remove(i)
        it += 1
        print "it=" + str(it)
        print i_MEASUREMENTS_TO_CREATE

    print str(len(i_MEASUREMENTS_TO_CREATE)) + " measurements to create:"
    print i_MEASUREMENTS_TO_CREATE

    #create a dict giving a list of measurement, if any, per sample (key)
    sample_measurements = {}
    for i in range(0, len(MEASUREMENTS)):
        keys = str(MEASUREMENTS[i]["samples_names"]).split(',')
        for key in keys:
            if key in sample_measurements:
                sample_measurements[key].append(MEASUREMENTS[i]["meas_id"])
            else:
                sample_measurements[key] = []
                sample_measurements[key].append(MEASUREMENTS[i]["meas_id"])

    #* create the new Samples
    # needs a list of measurement/sample
    #	wget --post-data "key=xxxxxxxxxxxxxxxxxxx&mail=beta.testeur@epfl.ch&project_id=15&name=sample de test&organism=mouse&bio_background=WT&stage=Day 13&measurements=1,3,8" http://localhost:8080/samples/create/
    def create_sample(dict_sample, u_key="", u_mail="", u_lab="", p_id="", ids_meas=[], url=""):
        options = {'key': u_key, 'mail': u_mail, 'lab': u_lab, 'project_id': p_id}
        for k, v in dict_sample.iteritems():
            k = re.sub(r'\*', "", str(k))
            #TEST : delete if it's ok
            #if len(str(v)) > 0:
            options[str(k)] = v
        if "name" in dict_sample:
            if dict_sample["name"] in ids_meas:
                L = ids_meas[dict_sample["name"]]
                l = ""
                if len(L) == 1:
                    l = str(L[0])
                    options["measurements"] = l
                elif len(L) > 1:
                    for i in range(0, len(L) - 1):
                        l = l + str(L[i]) + ","
                    l = l + str(L[i + 1])
                    options["measurements"] = l

        dico_samples = samples_c.create(**options)
        if "id" in dico_samples:
            dict_sample["id"] = dico_samples["id"]

    print "************* create Samples *************"
    for s in range(0, len(SAMPLES)):
        dico_final_s = create_sample(SAMPLES[s], u_key=USER['user_key'], u_mail=USER['user_email'], u_lab=USER['lab'], p_id=str(PROJECT["project_id"]), ids_meas=sample_measurements, url=bioRepo_url_sample)
        print "Sample " + SAMPLES[s]["name"] + " has been created"

    print "Done!"
