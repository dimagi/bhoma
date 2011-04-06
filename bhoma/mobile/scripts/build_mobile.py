#!/usr/bin/python

import os
import os.path
import sys
from datetime import datetime, date, timedelta
import itertools
import shutil
import bhomahash

cc_version = r'v\\\${app.version}bhoma/pilot'

bhoma_root = '/home/drew/dev/bhoma'
bhomamobile_root = os.path.join(bhoma_root, 'bhoma/mobile/bhoma-mobile')
jr_root = '/home/drew/dev/javarosa'
ccbhoma_root = os.path.join(jr_root, 'commcare/application')
builds_root = os.path.join(bhoma_root, 'bhoma/mobile/builds')

build_number = int(sys.argv[1])

stamp = datetime.now().strftime('%m%d%H%M')

cc_content_version = bhomahash.gethash(bhoma_root)

# only first model is built right now!!!
phone_models = ['Nokia/6085', 'Nokia/E51']

def get_jad_properties(path):
    '''Reads the properties of the jad file and returns a dict'''
    file = open(path)
    sep = ': '
    proplines = [line.strip() for line in file.readlines() if line.strip()]
    
    jad_properties = {}
    for propln in proplines:
        i = propln.find(sep)
        if i == -1:
            pass #log error?
        (propname, propvalue) = (propln[:i], propln[i+len(sep):])
        jad_properties[propname] = propvalue
    return jad_properties
    
def write_jad(path, properties):
    '''Write a property dictionary back to the jad file'''
    ordered_start = ['MIDlet-Name', 'MIDlet-Version', 'MIDlet-Vendor', 'MIDlet-Jar-URL',
                     'MIDlet-Jar-Size', 'MIDlet-Info-URL', 'MIDlet-1', 'MIDlet-Permissions']
    ordered_end = ['MIDlet-Jar-RSA-SHA1', 'MIDlet-Certificate-1-1',
                   'MIDlet-Certificate-1-2', 'MIDlet-Certificate-1-3',
                   'MIDlet-Certificate-1-4']

    unordered = [propname for propname in properties.keys() if propname not in ordered_start and propname not in ordered_end]

    props = itertools.chain(ordered_start, sorted(unordered), ordered_end)
    proplines = ['%s: %s\n' % (propname, properties[propname]) for propname in props]
      
    file = open(path, 'w')
    file.write(''.join(proplines))
    file.close()
    
def add_jad_properties(path, propdict):
    '''Add properties to the jad file'''
    props = get_jad_properties(path)
    props.update(propdict)
    write_jad(path, props)

def cmd(x):
  p = os.popen(x)
  ln = None
  while ln == None or ln != '':
    ln = p.readline()
    print ln[:-1]


print '========== COMMIT STATUS ==========='

cmd('hg status -R %s' % os.path.join(jr_root, 'javarosa'))
print

cmd('hg status -R %s' % os.path.join(jr_root, 'commcare'))
print

curdir = os.getcwd()
os.chdir(bhoma_root)
cmd('git status -s')
os.chdir(curdir)
print

print '-----------'
print
print
print


print '========== ACTIVE PROFILE ==========='
print open(os.path.join(bhomamobile_root, 'profile.xml')).read()
print
print '-----------'
print
print
print

jrjar = os.path.join(ccbhoma_root, 'tools/j2merosa-libraries.jar')
if os.path.exists(jrjar):
  os.remove(jrjar)

cmd('ant -f %s -Ddevice.identifier=%s -Dcommcare.version="%s" -Dcc-content-version=%s BuildClean' % (os.path.join(ccbhoma_root, 'build.xml'), phone_models[0], cc_version, cc_content_version))

build_dir = os.path.join(builds_root, stamp)
os.mkdir(build_dir)

shutil.copy(os.path.join(ccbhoma_root, 'dist/CommCare.jar'), build_dir)
shutil.copy(os.path.join(ccbhoma_root, 'dist/CommCare.jad'), build_dir)

add_jad_properties(os.path.join(build_dir, 'CommCare.jad'), {
  'Build-Number': build_number,
  'CommCare-Release': 'true',
  'Released-on': (date.today() + timedelta(days=1)).strftime('%Y-%b-%d %H:%M'),
})
