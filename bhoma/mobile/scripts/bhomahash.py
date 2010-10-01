#!/usr/bin/python

import os
import os.path
import sys

gitdir = os.path.join(sys.argv[1], '.git')

try:
  lns = os.popen('git --git-dir %s show .' % gitdir).readlines()
  print lns[0].split()[1][:12]
except:
  print 'error'
