# -*- coding: utf-8 -*-
"""
Global configuration file for TG2-specific settings in biorepo.

This file complements development/deployment.ini.

Please note that **all the argument values are strings**. If you want to
convert them into boolean, for example, you should use the
:func:`paste.deploy.converters.asbool` function, as in::
    
    from paste.deploy.converters import asbool
    setting = asbool(global_conf.get('the_setting'))
 
"""

from tg.configuration import AppConfig

import tg

import biorepo
from biorepo import model
from biorepo.lib import app_globals, helpers


class MyAppConfig(AppConfig):

    def after_init_config(self):
        s = 'debug.toolbar'
        if s in tg.config and tg.config[s].lower() in ['true', 'yes']:
            from tgext.debugbar import enable_debugbar
            enable_debugbar(base_config)

#base_config = AppConfig()
base_config = MyAppConfig()
base_config.renderers = []


base_config.package = biorepo

#Enable json in expose
base_config.renderers.append('json')
#Set the default renderer
base_config.default_renderer = 'genshi'
base_config.renderers.append('genshi')

# if you want raw speed and have installed chameleon.genshi
# you should try to use this renderer instead.
# warning: for the moment chameleon does not handle i18n translations
#base_config.renderers.append('chameleon_genshi')
#Configure the base SQLALchemy Setup
base_config.use_sqlalchemy = True
base_config.model = model
base_config.DBSession = model.DBSession
base_config.use_transaction_manager = True

#base_config.use_toscawidgets = True
#base_config.use_toscawidgets2 = True
#test
#base_config.prefer_toscawidgets2 = True


# HOOKS
def on_startup():
    import datetime
    print ' --- starting application --- ' + str(datetime.datetime.now())


def on_shutdown():
    print '--- stopping application --- '
base_config.call_on_startup = [on_startup]
base_config.call_on_shutdown = [on_shutdown]


token = 'biorepo'

# #test
# from tgext.debugbar import enable_debugbar
# enable_debugbar(base_config)
