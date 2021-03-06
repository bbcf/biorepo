from biorepo.model.auth import User
import os
from pkg_resources import resource_filename
from tg import flash, redirect
#file with all the BioRepo constant


def get_list_types(user_lab):
    if user_lab:
        if user_lab == "ptbb":
            list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip',
                        'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd']
        elif user_lab == "updub":
            list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip',
                        'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd', 'ChIP', 'Input', 'RNA tiling', 'Affymetrix GeneChip']
        elif user_lab == "lvg":
            list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip',
                         'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd', 'MeDIP-seq']
        elif user_lab == "upnae":
            list_types = ['RNA-seq', 'DNAse1', '4C', 'ChIP-seq']
        elif user_lab == "shore":
            list_types = ['MNase-seq', 'DNA-seq', 'ChIP-seq', 'RNA-seq', 'ChIP-chip', 'MicroArray', 'DNase-seq', 'ORGANIC-seq',
                        'chemical nucleosome mapping', 'sort-seq']
        elif user_lab == "stutz":
            list_types = ['MNase-seq', 'DNA-seq', 'ChIP-seq', 'RNA-seq', 'ChIP-chip', 'MicroArray', 'DNase-seq', 'ORGANIC-seq',
                        'chemical nucleosome mapping', 'sort-seq']
    else:
        print "--------------- NO USER LAB DETECTED --------------------"
        list_types = ['ChIP-seq', 'RNA-seq', '4C-seq', 'ChIP-chip', 'NanoString', 'MicroArray', 'RNA-chip', '4C-chip',
                     'BS-seq', 'RRBS', 'microRNA-seq', 'sRNA-seq rRNAd']

    list_types_extern = ['External_app_sample', 'HTSstation/Mapping analysis', 'HTSstation/Demultiplexing analysis',
                        'HTSstation/4C-seq analysis', 'HTSstation/ChIP-seq analysis', 'HTSstation/RNA-seq analysis',
                        'HTSstation/SNP analysis', 'HTSstation/BioScript analysis', 'BioScript analysis']

    list_types = list_types + list_types_extern
    #alphabetical sort
    list_types.sort()
    return list_types

list_types_extern = ['External_app_sample', 'HTSstation/Mapping analysis', 'HTSstation/Demultiplexing analysis',
                        'HTSstation/4C-seq analysis', 'HTSstation/ChIP-seq analysis', 'HTSstation/RNA-seq analysis',
                        'HTSstation/SNP analysis', 'HTSstation/BioScript analysis', 'BioScript analysis']

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


def path_archive(pzip):
    path_arch = os.path.abspath(resource_filename('biorepo', ("archives/" + pzip)))
    return str(path_arch)

def path_dropbox(unit):
    dropbox = "/scratch/el/biorepo/public_access/"
    path_unit = dropbox + unit
    if not os.path.exists(path_unit):
        os.mkdir(path_unit)
    return path_unit

##########################################################################################################################################################
################       HTSstation paths - to comment if you install BioRepo on another server than pttbsrv2        #######################################
##########################################################################################################################################################


def HTS_path_data():
    p = "/data/epfl/bbcf/htsstation"
    return p


def HTS_path_archive():
    p = "/archive/epfl/bbcf"
    return p


def trackhubs_path():
    p = "/data/epfl/bbcf/biorepo/trackHubs"
    return p


def hts_bs_path():
    p = "/data/epfl/bbcf/htsstation/bs"
    return p


def archives_path():
    p = "/data/epfl/bbcf/biorepo/zipArchives"
    return p
