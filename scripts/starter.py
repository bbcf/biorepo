# -*- coding: utf-8 -*-
import sys
import os
import urllib
import urllib2

#utilisation : python starter.py [myPath/archive.tgz] [user_mail] [user_key]

path_tgz = sys.argv[1]
mail = sys.argv[2]
key = sys.argv[3]

url = "http://biorepo.epfl.ch/biorepo/create_with_tgz"

params = {'path_tgz': os.path.abspath(path_tgz), 'email': mail, 'key': key}
data = urllib.urlencode(params)
print "Script launched..."
request = urllib2.Request(url, data)
response = urllib2.urlopen(request)
print "No Error 502, good job."
