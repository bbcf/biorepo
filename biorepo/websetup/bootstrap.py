# -*- coding: utf-8 -*-
"""Setup the biorepo application"""

from biorepo import model
from sqlalchemy.exc import IntegrityError
import transaction

group_admins = 'Admins'
perm_admin = 'admin'

group_users = 'Users'
perm_user = 'user'

num_group = 1
num_admin = 2


def bootstrap(command, conf, vars):
    """Place any commands to setup biorepo here.
    Note that you will have to log in the application one before launching the bootstrap."""

    try:

        print 'Adding default groups and permissions'
        # ADMIN GROUP
        admins = model.Group()
        admins.name = group_admins
        admins.id = num_admin
        #admins.users.append(admin)
        model.DBSession.add(admins)

        # ADMIN PERMISSION
        perm = model.Permission()
        perm.name = perm_admin
        perm.description = u'This permission give admin right to the bearer.'
        perm.groups.append(admins)
        model.DBSession.add(perm)

        #transaction.commit()
        #else :
        # USER GROUP
        users = model.Group()
        users.name = group_users
        users.id = num_group

        model.DBSession.add(users)

        # USER PERMISSION
        read = model.Permission()
        read.name = perm_user
        read.description = u'This permission give user right to users.'
        read.groups.append(users)
        model.DBSession.add(read)

        transaction.commit()

    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Ending with bootstrapping...'

# OLD VERSION
#        admin = model.DBSession.query(model.User).filter(model.User.email == 'yoann.mouscaz@epfl.ch').first()
#
#        if admin:
#            print 'Adding ADMIN group and permission'
#            # ADMIN GROUP
#            admins = model.Group()
#            admins.name = group_admins
#            admins.users.append(admin)
#            model.DBSession.add(admins)
#
#            # ADMIN PERMISSION
#            perm = model.Permission()
#            perm.name = perm_admin
#            perm.description = u'This permission give admin right to the bearer'
#            perm.groups.append(admins)
#            model.DBSession.add(perm)
#            transaction.commit()
#
#        else :
#            print 'Adding USER group and permission'
#            # USER GROUP
#            users = model.Group()
#            users.name = group_users
#            model.DBSession.add(users)
#            # READ PERMISSION
#            read = model.Permission()
#            read.name = perm_user
#            read.description = u'This permission give "read" right to the bearer'
#            read.groups.append(users)
#            model.DBSession.add(read)
#            transaction.commit()
#            print '''
#
#                    Change email value in " biorepo.websetup.bootstrap.py ".
#                    Launch " paster serve --reload development.ini ".
#                    Log in the application.
#                    Re-run "python setup-app development.ini".
#                    It will gives you admin rights.
#
#                  '''
#
#    except IntegrityError:
#        print 'Warning, there was a problem adding your auth data, it may have already been added:'
#        import traceback
#        print traceback.format_exc()
#        transaction.abort()
#        print 'Ending with bootstrapping...'
        
        
        
    
