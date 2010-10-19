#!/usr/bin/python

import os
import os.path
import sys

def gethash(bhoma_root):
  gitdir = os.path.join(bhoma_root, '.git')

  try:
    lns = os.popen('git --git-dir %s show .' % gitdir).readlines()
    return lns[0].split()[1][:12]
  except:
    return 'error'

if __name__ == "__main__":
  print gethash(sys.argv[1])
