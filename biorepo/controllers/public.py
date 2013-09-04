# -*- coding: utf-8 -*-
"""Public Controller"""
from biorepo.lib.base import BaseController
from tg import expose, flash, redirect, response, url
from biorepo.model import DBSession, Files_up
from biorepo.lib.constant import dico_mimetypes
import os
from biorepo.lib.util import check_boolean

__all__ = ['PublicController']


class PublicController(BaseController):

    @expose()
    def public_dl(self, sha1, *args, **kw):
        f = DBSession.query(Files_up).filter(Files_up.sha1 == sha1).first
        path_fu = f.path + "/" + f.sha1
        extension = f.extension
        filename = f.filename
        file_size = os.path.getsize(path_fu)
        response.content_length = file_size
        if dico_mimetypes.has_key(extension):
            response.content_type = dico_mimetypes[extension]
        else:
            response.content_type = 'text/plain'
        response.headers['X-Sendfile'] = path_fu
        response.headers['Content-Disposition'] = 'attachement; filename=%s' % (filename)
        response.content_length = '%s' % (file_size)
        return None
