import hashlib
import urllib2, urlparse
import tempfile
from urllib2 import HTTPError


def to_datagrid(grid_type, grid_data, grid_title, grid_display):
    '''
    Special method which format the parameters to fit
    on the datagrid template.
    @param grid_type : The DataGrid.
    @type grid_type : a DataGrid Object
    @param grid_data : The data.
    @type grid_data : a list of Object to fill in the DataGrid.
    @param grid_title : DataGrid title
    @type grid_title : A string.
    @param grid_display :True if the DataGrid has to be displayed.
    @type grid_display : a boolean. (Normally it's the len() of the 'grid_data' )
    '''
    data = {'grid': grid_type,
    'grid_data': grid_data,
    'grid_title': grid_title,
    'grid_display': grid_display}
    return data


def get_file_sha1(file_path):
    '''
    Get the sha1 hex digest of a file.
    @param file_path : the absolute path to the file.
    @return the sha1 digest en hexa
    '''
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(128 * 64), ''):
                sha1.update(chunk)
    except:
        print "##############################################################################################################"
        print "###################  ERROR : IMPOSSIBLE TO GENERATE A SHA1 : THE FILE DON'T EXIST ANYMORE ####################"
        print "path given : ", file_path
        print "#############################################################################################################"
    return sha1.hexdigest()
