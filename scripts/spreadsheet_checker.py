# -*- coding: utf-8 -*-
import re
import sys
import os
import tarfile
import urllib2
from xlrd import open_workbook
import getopt

#utilisation : python spreadsheet_checker.py [myPath/data.xls] [myPath/myArchive.tgz]
usemess = """Usage:

python spreadsheet_checker.py [options] <spreadsheet.xls>

Options:
    -a <archive.tgz>, --archive=<archive.tgz>
            : Provide an archive containing some of the files.
    -i <lab.ini>, --lab_ini=<lab.ini>
            : Enable automatic checking of dynamically defined fields using the lab *.ini file.
    -h, --help
            : Print this help message.
"""
if len(sys.argv) == 1:
    print(usemess)
    sys.exit()

opts, spreadsheet = getopt.getopt(sys.argv[1:], 'a:i:h', ['archive=', 'lab_ini=', 'help'])
opts = dict(opts)
if not spreadsheet:
    print "A spreadsheet is required."
    sys.exit()
spreadsheet = spreadsheet[0]

tar_archive = None
if '-a' in opts.keys():
    tar_archive = opts['-a']
if '--archive' in opts.keys():
    tar_archive = opts['--archive']
lab_ini = None
if '-i' in opts.keys():
    lab_ini = opts['-i']
if '--lab_ini' in opts.keys():
    lab_ini = opts['--lab_ini']

if not lab_ini:
    print 'Warning: no lab.ini file given. Field consistency checks will not be performed.'

errors_to_fix = {}

#check given arguments
print "Checking given arguments (xls + tgz) ..."
if not os.path.exists(spreadsheet):
    print "Your .xls does not exist. Try with an other path. Path given : " + spreadsheet
    sys.exit()
if tar_archive and not os.path.exists(tar_archive):
    print "Your .tgz does not exist. Try with an other path. Path given : " + tar_archive
    sys.exit()
tmp_split1 = spreadsheet.split('.')
ext_spreadsheet = tmp_split1[-1]
if ext_spreadsheet != "xls":
    print "Your spreadsheet has to get '.xls' extension"
    sys.exit()
if tar_archive:
    tmp_split2 = tar_archive.split('.')
    ext_tarfile = tmp_split2[-1]
    if ext_tarfile != "tgz":
        print "Your archive has to get '.tgz' extension"
        sys.exit()
print "Given arguments OK !"

#open metadata excel spreadsheet
print "Parsing xls..."
data = open_workbook(spreadsheet, ragged_rows=True, formatting_info=False, encoding_override="cp1252")
if int(data.nsheets) > 0:
    infos = data.sheet_by_index(0)
else:
    infos = ""

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


def get_fields_from_ini(inifile):
    fields = dict(Samples=dict(), Measurements=dict())
    ini = open(inifile).read()

    def get_vals(upper, lower):
        if lower == 'main':
            key = 'keys'
        else:
            key = lower
        # absolut horror of a regular expression follows...
        rematch = re.search(r'\[{upper}:{lower}\]\s{key}\s*=\s*(([\w/]*\s*,?\s*)*)\n(\s*widget\s*=\s*(hiding_)?checkbox\n)?'.format(upper=upper, lower=lower, key=key), ini, re.MULTILINE)
        if rematch:
            if rematch.groups()[2] != None and lower != 'main':
                return [lower, 'Not ' + lower]# special case for boolean properties (checkbox)
            else:
                vals = [s.strip() for s in rematch.groups()[0].strip().split(',') if s.strip() != '' and s.strip() != 'None']
                if vals:
                    return vals
    #Samples
    skeys = get_vals('samples_attributs', 'main')
    for k in skeys:
        fields['Samples'][k] = get_vals('samples_attributs', k)
    add_sample_fields = ['name', 'protocole', 'type']
    for k in add_sample_fields:
        fields['Samples'][k] = None
    #Measurements
    mkeys = get_vals('meas_attributs', 'main')
    for k in mkeys:
        fields['Measurements'][k] = get_vals('meas_attributs', k)
    add_meas_fields = ['samples_names', 'parent_num', 'generated_from', 'name', 'url_up', 'filename', 'vitalit_path', 'url_path', 'type', 'status_type', 'description']
    for k in add_meas_fields:
        fields['Measurements'][k] = None
    return fields


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
    # Fixed: When last column has no values filled in,
    # previous implementation was skipping the property.
    head_len = infos.row_len(start_row)
    for x in range(start_row + 1, end_row):
        if infos.row_len(x):
            out.append({})
            for i in range(0, head_len):
                k = str(infos.cell_value(start_row, i))
                k = re.sub(r'\*', "", str(k))
                #to fix pb with excel cells formats (int/str randomly)
                val = ''
                if i < infos.row_len(x):
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

fields = None
if lab_ini:
    fields = get_fields_from_ini(lab_ini)

#Parse USER and PROJECT infos
user_infos = fill_dict_vert(infos, i_USER[0], i_PROJECT[0], i_USER[1])
project_infos = fill_dict_vert(infos, i_PROJECT[0], i_SAMPLES[0], i_PROJECT[1])

#Parse SAMPLES and MEASUREMENTS infos
samples_infos = fill_dict_hor(infos, i_SAMPLES[0] + 1, i_MEASUREMENTS[0] - 1)
measurements_infos = fill_dict_hor(infos, i_MEASUREMENTS[0] + 1, i_COMMENTS[0] - 1)
i_measurements_to_create = range(0, len(measurements_infos))

lab = user_infos['lab']
print "Parsing completed !"

###############################
##### check Samples names #####
###############################
samples_names = []
samples_names_in_meas = []
for s in samples_infos:
    samples_names.append(s["name"])
for sample in measurements_infos:
    names_list = sample["samples_names"].split(',')
    for name in names_list:
        if name not in samples_names_in_meas:
            samples_names_in_meas.append(name)

for sa in samples_names_in_meas:
    if sa not in samples_names:
        errors_to_fix.setdefault("sampleName_missing", []).append(sa)

for sam in samples_names:
    if sam not in samples_names_in_meas:
        errors_to_fix.setdefault("sampleName_defined_but_not_used", []).append(sam)
print "Samples checked !"
###############################
##### check Samples fields ####
###############################
if fields:
    for s in samples_infos:
        # missing fields in spreadsheet
        for k in fields['Samples'].keys():
            if not k in s.keys():
                errors_to_fix.setdefault('sample_field_missing', []).append(k)
        # Bad value when defined values are constrained
        for k in fields['Samples'].keys():
            if k in s.keys():
                if fields['Samples'][k]:
                    if s[k] and not s[k] in fields['Samples'][k]:
                        errors_to_fix.setdefault('sample_value_undefined_for_field', []).append(dict(field=k, value=s[k]))
        # Fields which do not match any field in the ini file
        for k in s.keys():
            if not k in fields['Samples']:
                errors_to_fix.setdefault('sample_field_undefined', []).append(k)
###############################
###### check Measurements #####
###############################
#get filenames which are in the given tgz
meas_in_tgz = []
if tar_archive:
    print "Parsing tarfile...(can take few minuts)"
    tar = tarfile.open(tar_archive)
    for finfo in tar.getmembers():
        if not finfo.isdir() and not (finfo.name).endswith('.xls'):
            try:
                tmp = (finfo.name).split('/')
                toTest = tmp[1]
                if not toTest.startswith('.'):
                    meas_in_tgz.append(toTest)
            except:
                errors_to_fix.setdefault("TGZ_NOT_BUILT_CORRECTLY", []).append(finfo.name)
    print "Parsing completed !"
###############################
##### check Samples fields ####
###############################
if fields:
    for m in measurements_infos:
        # missing fields in spreadsheet
        for k in fields['Measurements'].keys():
            if not k in m.keys():
                errors_to_fix.setdefault('measurement_field_missing', []).append(k)
        # Bad value when defined values are constrained
        for k in fields['Measurements'].keys():
            if k in m.keys():
                if fields['Measurements'][k]:
                    if m[k] and not m[k] in fields['Measurements'][k]:
                        errors_to_fix.setdefault('measurement_value_undefined_for_field', []).append(dict(field=k, value=m[k]))
        # Fields which do not match any field in the ini file
        for k in m.keys():
            if not k in fields['Measurements']:
                errors_to_fix.setdefault('measurement_field_undefined', []).append(k)

meas_in_xls = []
parents = []
for m in measurements_infos:
    #get filenames referenced in xls
    if "filename" in m.keys():
        filename = m["filename"]
        if filename and filename not in meas_in_xls:
            meas_in_xls.append(filename)
    #check vital-it paths
    if "vitalit_path" in m.keys():
        vitalit_path = m["vitalit_path"]
        if vitalit_path and not os.path.exists(vitalit_path):
            errors_to_fix.setdefault("Bad_VitalIT_path", []).append(vitalit_path)
    #check URL to upload
    if "url_path" in m.keys():
        url_path = m["url_path"]
        url_up = (m["url_up"]).lower()
        if url_path and url_up == "yes":
            try:
                url_test = urllib2.urlopen(urllib2.Request(url_path))
            except:
                errors_to_fix.setdefault("Dead_Link_Found", []).append(url_path)
    if "parent_num" in m.keys():
        parent_num = m["parent_num"]
        if parent_num not in parents and parent_num != '':
            parents.append(parent_num)
        elif parent_num in parents and parent_num != '':
            errors_to_fix.setdefault("Not_Unique_Parent_Num", []).append(parent_num)


for m in meas_in_tgz:
    if m not in meas_in_xls:
        errors_to_fix.setdefault("File_not_referenced_in_xls", []).append(m)
for meas in meas_in_xls:
    if meas not in meas_in_tgz:
        errors_to_fix.setdefault("Missing_File_in_tgz", []).append(meas)
print "Measurements checked !"

############################
##### Analysis results #####
############################
if errors_to_fix:
    print ""
    print "--- /!\ " + str(len(errors_to_fix.keys())) + " errors found during the analyze  /!\ ---"
    print ""
    for key in errors_to_fix.keys():
        print "+ ERROR -> " + key + " spotted with " + str(errors_to_fix[key])
        print ""
else:
    print "Perfect spreadsheet. Congratulations !"
    print "NB : Your spreadsheet contains " + str(len(measurements_infos)) + " measurements and you will add " \
    + (str(len(meas_in_tgz))) + " files from the given tgz."
