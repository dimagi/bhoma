#!/usr/bin/python

import sys
import os.path

memcard = '/media/1234-5678'
builds = '/home/drew/dev/bhoma/bhoma/mobile/builds'

if not os.path.exists(memcard):
  print 'memory card not mounted?'
  sys.exit()

try:
  stamp = sys.argv[1]
except:
  stamp = sorted(os.listdir(builds))[-1]

builddir = os.path.join(builds, stamp)
print 'build dir:', builddir

os.popen('rm %s' % os.path.join(memcard, 'CommCare*'))
os.popen('cp %s %s' % (os.path.join(builddir, '*'), memcard))
os.popen('umount %s' % memcard)

print 'done'
