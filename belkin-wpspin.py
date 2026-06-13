#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# http://ednolo.alumnos.upv.es/?p=1295
'''
Created on Dec 9, 2012

 
@author       : e.novellalorente@student.ru.nl

Original work : ZhaoChunsheng 04/07/2012

 
'''

import sys

from shared_utils.wps_pin import wps_pin_checksum

VERSION = 0
SUBVERSION = 2

def usage():
    print "[+] WPSpin %d.%d " % (VERSION, SUBVERSION)
    print "[*] Usage : python WPSpin.py 123456"
    sys.exit(0)

try:
    if (len(sys.argv[1]) == 6):
        p = int(sys.argv[1] , 16) % 10000000
        print "[+] WPS pin is : %07d%d" % (p, wps_pin_checksum(p))
    else:
        usage()
except IndexError:
    usage()
except ValueError as e:
    print "[!] Invalid MAC value: %s" % e
    usage()
