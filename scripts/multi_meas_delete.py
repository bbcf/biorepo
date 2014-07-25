# -*- coding: utf-8 -*-
import sys
import os
import urllib
import urllib2

#utilisation : python multi_meas_delete.py [project_id] [sample_id] [user_mail] [user_key]

project_id = sys.argv[1]
sample_id = sys.argv[2]
mail = sys.argv[3]
key = sys.argv[4]

if len(sys.argv) != 5:
    print "utilisation : python multi_meas_delete.py [project_id] [sample_id] [user_mail] [user_key]"
    print "One or several arguments are missing"
    print "You provide : ", sys.argv
    sys.exit()


url = "http://biorepo.epfl.ch/biorepo/multi_meas_delete"

params = {'p_id': int(project_id), 's_id': int(sample_id), 'mail': mail, 'key': key}
data = urllib.urlencode(params)
print "Script launched..."
request = urllib2.Request(url, data)
response = urllib2.urlopen(request)
print "Measurements deleted."
