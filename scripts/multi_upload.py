#from xlrd import *
import sys
import re
# import shutil
import json
import os
import tarfile
import subprocess
import urllib
import urllib2
from xlrd import open_workbook

# python ../script/multi_upload.py test_dataDaan.tgz
# or
# python ../script/multi_upload.py test_dataDaan.tgz myMetadataFile.xls
# (!! the myMetadataFile.xls should then be part of the archive and be at the root of it!!)
# default="data.xls"


cpt_m = 0
cpt_s = 0

bioRepo_url_project = "http://biorepo.epfl.ch/biorepo/projects/create/"
bioRepo_url_sample = "http://biorepo.epfl.ch/biorepo/samples/create/"
bioRepo_url_measurement = "http://biorepo.epfl.ch/biorepo/measurements/create/"

#file_path="/home/mouscaz/test_marion/upload/test_dataDaan/"
metadataFile = ""

if len(sys.argv) >= 2:
    allFiles_tar = sys.argv[1]
    print "checking " + allFiles_tar
    if not os.path.exists(allFiles_tar):
        print "Error, the archive passed doesn't exist:" + allFiles_tar
        sys.exit(2)
    else:
        if len(sys.argv) >= 3:
            metadataFile = sys.argv[2]
        else:
            print "No metadata filename given. Will use the default name: data.xls"
            metadataFile = "data.xls"
else:
    print "Usage: python multi_upload.py archive_name.tgz [metadata filename (.xls) - default=data.xls]"
    sys.exit(2)


# open tar file
tar = tarfile.open(allFiles_tar)
print "wait a moment please (can take few minuts)"
tar.extractall()
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
    print "Error, the metadata file passed (" + metadataFile + ") does not exist or has the wrong extension (.xls)"
    print "extension=" + os.path.splitext(metadataFile)[-1]
    sys.exit(2)

print "Metadata file:" + metadataFile

# open metadata excel file (should be .xls!!)
#data=open_workbook("/home/mouscaz/test_marion/upload/data.xls",ragged_rows=True,formatting_info=False)
#data=open_workbook("data.xls",ragged_rows=True,formatting_info=False)
data = open_workbook(metadataFile, ragged_rows=True, formatting_info=False)
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
                out[id_cur_sample][k] = str(infos.cell_value(x, i))
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
    dic_name_id = {'ptbb': 1, 'lvg': 2, 'updub': 3}
    lab_id = dic_name_id[lab_name]
    return lab_id


def create_project(dict_project, u_key="", u_mail="", u_lab="", url=""):
    output_cmd = "new_project.html"
    if os.path.exists(output_cmd):
        os.remove(output_cmd)
    options = "\"" + "key=" + u_key + "&mail=" + u_mail + "&lab=" + str(get_lab_id(u_lab))
    for k, v in dict_project.iteritems():
        k = re.sub(r'\*', "", str(k))
        if len(str(v)) > 0:
            options = options + "&" + str(k) + "=" + str(v)
    options = options + "\""
    cmd = "wget --post-data " + options + " " + url + " -O " + output_cmd
    print cmd
    subprocess.call(cmd, shell=True)
#	shutil.copyfile("/Users/leleu/data/Marion/Duboule/BioRepo/project1.html", "new_project.html") #for test
    if os.path.exists(output_cmd):
        with open(output_cmd, 'r') as f:
            sj = json.loads(f.read())
            if "project_id" in sj:
                PROJECT['project_id'] = sj["project_id"]
            else:
                PROJECT['project_id'] = ""

if createProject:
    create_project(PROJECT, u_key=USER['user_key'], u_mail=USER['user_email'], u_lab=USER['lab'], url=bioRepo_url_project)

#* create the new measurements
#wget --post-data "key=xxxxxxxxxxxxxxxxxxxxx&mail=beta.testeur@epfl.ch&lab=ptbb&name=test&description=blablbalbal&assembly=mm9&
#path=/my/file.tgz&samples=2" http://biorepo.epfl.ch/biorepo/measurements/create/


def create_measurement(dict_measurement, u_key="", u_mail="", u_lab="", parent_id="", url=""):
    output_cmd = "new_measurement.html"
    global cpt_m
    cpt_m += 1
    if os.path.exists(output_cmd):
        os.rename(output_cmd, output_cmd + "_" + str(cpt_m))
    #options = '"' + "key=" + u_key + "&mail=" + u_mail + "&lab=" + u_lab
    options = {'key': u_key, 'mail': u_mail, 'lab': u_lab}
    if len(parent_id) > 0:
        #options = options + "&parent_id=" + parent_id
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
                if str(v) == "Yes":
                    v = "True"
                else:
                    v = "False"
            if re.search(r'url_path', str(k)):
                if re.search(r'uhts-lgtf', str(v)) or re.search(r'uhts-gva', str(v)):
                    n = str(v).split("/")
                    v = "http://www.humanmetrics.com/" + n[-1]
                    print "v=" + v
#					str(v).replace("http://uhts-lgtf.vital-it.ch/","http://www.humanmetrics.com/")
            #if re.search(r'path',str(k)) and not re.search(r'_',str(k)):
            if re.search(r'filename', str(k)):
                for i, p in enumerate(allfiles):
                    if re.search(str(v), p):
                        file_path = p
                        print str(v) + "=>" + p + ".\t***** " + file_path
                        break
                    else:
                        file_path = ""
                v = os.getcwd() + "/" + file_path
                print "v=" + str(v)
                k = "path"
            #options = options + "&" + str(k) + "=" + str(v)
            options[str(k)] = str(v)
    #options = options + '"''
    #cmd = "wget --post-data " + options + " " + url + " -O " + output_cmd
    data = urllib.urlencode(options)
    request = urllib2.urlopen(url, data)
    with open(output_cmd, 'w') as output:
        output.write(request.read())
    #print cmd
    #try:
        #subprocess.call(cmd, shell=True)
    #except Exception as e:
        #print e
        #print "dans le except du subprocess"
    #shutil.copyfile("/Users/leleu/data/Marion/Duboule/BioRepo/measurement1.html", "new_measurement.html") #for test
    if os.path.exists(output_cmd):
        with open(output_cmd, 'r') as f:
            sj = json.loads(f.read())
            if "meas_id" in sj:
                dict_measurement["meas_id"] = sj["meas_id"]
    return output_cmd


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
        all_parents = (curMeasurement['generated_from']).split(',')
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
                if 'name' in MEASUREMENTS[m]:
                    created_measurements[MEASUREMENTS[m]['name']] = MEASUREMENTS[m]['meas_id']
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
    output_cmd = "new_sample.html"
    global cpt_s
    cpt_s += 1
    if os.path.exists(output_cmd):
        os.rename(output_cmd, output_cmd + "_" + str(cpt_s))
    options = "\"" + "key=" + u_key + "&mail=" + u_mail + "&lab=" + u_lab + "&project_id=" + p_id
    for k, v in dict_sample.iteritems():
        k = re.sub(r'\*', "", str(k))
        #TEST : delete if it's ok
        #if len(str(v)) > 0:
        options = options + "&" + str(k) + "=" + v
    if "name" in dict_sample:
        if dict_sample["name"] in ids_meas:
            L = ids_meas[dict_sample["name"]]
            l = ""
            if len(L) == 1:
                l = str(L[0])
                options = options + "&measurements=" + l
            elif len(L) > 1:
                for i in range(0, len(L) - 1):
                    l = l + str(L[i]) + ","
                l = l + str(L[i + 1])
                options = options + "&measurements=" + l
    options = options + "\""
    cmd = "wget --post-data " + options + " " + url + " -O " + output_cmd
    print cmd
    subprocess.call(cmd, shell=True)
    #shutil.copyfile("/Users/leleu/data/Marion/Duboule/BioRepo/sample1.html", "new_sample.html") #for test
    if os.path.exists(output_cmd):
        with open(output_cmd, 'r') as f:
            sj = json.loads(f.read())
            if "id" in sj:
                dict_sample["id"] = sj["id"]
    return output_cmd

print "************* create Samples *************"
for s in range(0, len(SAMPLES)):
    output_cmd = create_sample(SAMPLES[s], u_key=USER['user_key'], u_mail=USER['user_email'], u_lab=USER['lab'], p_id=str(PROJECT["project_id"]), ids_meas=sample_measurements, url=bioRepo_url_sample)
    if os.path.exists(output_cmd):
        with open(output_cmd, 'r') as f:
            sj = json.loads(f.read())
            if "sample" in sj and "id" in sj["sample"]:
                print "Sample " + SAMPLES[s]["name"] + " has been created"
    else:
        print "Sample " + SAMPLES[s]["name"] + " failed to create"

print "Done!"



## get the newest file
#files = filter(os.path.isfile, glob.glob("project*.html"))
#file_date_tuple_list = [(x,os.path.getmtime(x)) for x in files]
#file_date_tuple_list.sort(key=lambda x: x[1],reverse=True)
#newest_created_file=file_date_tuple_list[0][0]