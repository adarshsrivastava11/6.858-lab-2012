#!/usr/bin/python

from unixclient import call

resp = call("/jail/echosvc/sock", "hello")
print "Response = ", resp

