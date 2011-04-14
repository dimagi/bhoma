from fabric.api import *

'''
Bhoma central stuff
'''

def stop_central_server_scripts():
    sudo("/etc/init.d/bhoma-runscripts stop")

def start_central_server_scripts():
    sudo("/etc/init.d/bhoma-runscripts start")

def load_zones():
    sudo('python manage.py load_zones static/bhoma_clinic_zones.csv')
