from biorepo.model.auth import User
import os
from pkg_resources import resource_filename
from tg import session, flash, redirect
#file with all the BioRepo constant

user_lab = session.get("current_lab", None)
if user_lab:
    if user_lab == "ptbb":
        list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip',
                    'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd']
    elif user_lab == "updub":
        list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip',
                    'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd']
    elif user_lab == "lvg":
        list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip',
                     'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd']
else:
    list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip',
                 'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd']

list_types_extern = ['External_app_sample', 'HTSstation/Mapping analysis', 'HTSstation/Demultiplexing analysis',
                    'HTSstation/4C-seq analysis', 'HTSstation/ChIP-seq analysis', 'HTSstation/RNA-seq analysis',
                    'HTSstation/SNP analysis', 'HTSstation/BioScript analysis', 'BioScript analysis']

list_types = list_types + list_types_extern
#alphabetical sort
list_types.sort()

#list dataType to test
list_dataType = ['Raw', 'Processed']

#dico MIME types
dico_mimetypes = {'gz': 'application/x-gzip', 'pdf': 'application/pdf', 'xls': 'application/excel', 'xlsx': 'application/excel',
                  'ppt': 'application/vnd.ms-powerpoint', 'pps': 'application/vnd.ms-powerpoint', 'doc': 'application/word',
                  'docx': 'application/word', 'zip': 'application/zip', 'rar': 'application/x-rar-compressed',
                  'tgz': 'application/x-tar-gz', 'tar': 'application/x-tar', 'png': 'image/png', 'jpg': 'image/jpeg',
                  'jpeg': 'image/jpeg', 'jpe': 'image/jpeg', 'gif': 'image/gif', 'tiff': 'image/tiff', 'tif': 'image/tiff',
                  'fasta': 'text/plain', 'fastq': 'text/plain', 'bedgraph': 'text/plain', 'bam': 'application/octet-stream',
                  'mpg': 'video/mpeg', 'mpeg': 'video/mpeg', 'avi': 'video/x-msvideo', 'wmv': 'video/x-ms-wmv',
                  'html': 'text/html', 'pdb': 'chemical/x-pdb', 'xyz': 'chemical/x-pdb', 'tar.gz': 'application/x-tar-gz',
                  'bw': 'application/octet-stream', 'bigwig': 'application/octet-stream', 'CEL': 'application/octet-stream',
                  'bar': 'application/octet-stream', 'bpmap': 'application/octet-stream'}


#paths
def path_conf():
    return os.path.abspath(resource_filename('biorepo', 'conf'))


def path_conf_labs():
    return os.path.join(path_conf(), 'labs.ini')


def path_conf_unit(unit):
    try:
        return os.path.join(path_conf(), unit + '.ini')
    except:
        return os.path.join(path_conf(), 'default.ini')


def path_raw(unit):
    path_unit = os.path.abspath(resource_filename('biorepo', ("upload/" + unit)))
    if os.path.exists(path_unit) == False:
        try:
            os.mkdir(path_unit)
        except:
            flash("Vital-IT is not accessible : file upload and file download are not possible. Be patient :) ", 'error')
            raise redirect('/')
    raw = os.path.join(path_unit, 'raw')
    if os.path.exists(raw) == False:
        os.mkdir(raw)
    return raw


def path_processed(unit):
    path_unit = os.path.abspath(resource_filename('biorepo', ("upload/" + unit)))
    if os.path.exists(path_unit) == False:
        os.mkdir(path_unit)
    processed = os.path.join(path_unit, 'processed')
    if os.path.exists(processed) == False:
        os.mkdir(processed)
    return processed


def path_tmp(unit):
    path_unit = os.path.abspath(resource_filename('biorepo', ("upload/" + unit)))
    if os.path.exists(path_unit) == False:
        os.mkdir(path_unit)
    tmp_ = os.path.join(path_unit, 'tmp')
    if os.path.exists(tmp_) == False:
        os.mkdir(tmp_)
    return tmp_


#HTSstation paths - to comment if you install BioRepo on another server than pttbsrv2
def HTS_path_data():
    p = "/data/epfl/bbcf/htsstation"
    return p


def HTS_path_archive():
    p = "/archive/epfl/bbcf"
    return p


def trackhubs_path():
    p = "/data/epfl/bbcf/biorepo/trackHubs"
    return p
