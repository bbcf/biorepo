from biorepo.model.auth import User
import os
from pkg_resources import resource_filename
#file with all the BioRepo constant

#In widgets.sample
#list_organisms = [None, 'human', 'mouse']

list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip', 'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd']
#alphabetical sort
list_types.sort()
#list_cell_types = [None, 'ES cell', 'MEF', 'T-cell', 'B-cell', 'liver', 'forebrain', 'anterior trunk', 'posterior trunk', 'limb']

#list_cell_lines = [None, 'k562 (hES)', 'primary tissue']

#list_ab_targets = [None, 'NlaIII-DpnII', 'Hoxd13', 'Hoxd9', 'Hoxd4', 'H3K27me3', 'H3K4me1', 'H3K4me2', 'H3K4me3', 'input_DNA', 'RNAP2',
                   #'H3K27Ac', 'Prox', 'island I', 'island IV', 'RNA']


#In widgets.measurement
#To replace with GenRep
#list_assemblies = [None, 'hg19', 'mm10', 'mm9', 'mm8', 'mm5']

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
        os.mkdir(path_unit)
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
