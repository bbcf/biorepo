# -*- coding: utf-8 -*-
import re
import sys
import os
import tarfile
from xlrd import open_workbook

#utilisation : python spreadsheet_checker.py [myPath/data.xls]

#path data.xls
spreadsheet = sys.argv[1]
tar_archive = sys.argv[2]
errors_to_fix = {}

if not os.path.exists(spreadsheet):
    print "Your .xls does not exist. Try with an other path. Path given : " + spreadsheet
    raise
#open metadata excel fil (should be .xls)
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
###### check Measurements #####
###############################
print "Parsing tarfile...(can take few minuts)"
#get filenames which are in the given tgz
tar = tarfile.open(tar_archive)
meas_in_tgz = []
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

#get filenames referenced in xls
meas_in_xls = []
for m in measurements_infos:
    filename = m["filename"]
    if filename and filename not in meas_in_xls:
        meas_in_xls.append(filename)


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
