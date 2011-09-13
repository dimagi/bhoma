import logging

def get_server_domain(domain, use_tunnel=False, tunnel_port=None):
    return 'localhost:%d' % tunnel_port if use_tunnel else domain

def get_server_url(server_root, username, password):
    if username and password:
        return "http://%(user)s:%(pass)s@%(server)s" % \
            {"user": username,
             "pass": password, 
             "server": server_root }
    else:
        return "http://%(server)s" % {"server": server_root }

def is_clinic(clinic_id):
    """
    An extremely low-tech way to guess if something is a clinic.
    This is pretty poor to rely on, and will break if clinic
    id formats change... 
    """
    try:
        # clinic ids are 7 digits long
        return int(clinic_id) > 999999
    except Exception:
        return False
    
def get_dynamic_db_settings(server_root, username, password, dbname, installed_apps, clinic_id):
    """
    Get dynamic database settings.  Other apps can use this if they want to change
    settings
    """
    # this is hacky. exclude some known, unused apps from syncing with couch
    # at clinics, since we don't want to stress the couch process and hardware
    app_excludes = () if not is_clinic(clinic_id) else ("couchexport")
    db_app_prefixes = ('bhoma', 'touchforms', "couchversion", "djangocouch", "couchlog", "couchexport")
    
    server = get_server_url(server_root, username, password)
    database = "%(server)s/%(database)s" % {"server": server, "database": dbname}
    couchdbs = [(app, database) for app in installed_apps \
                if any(app.startswith(prefix) for prefix in db_app_prefixes) \
                and app not in app_excludes]
    posturl = "http://%s/%s/_design/xforms/_update/xform/" % (server_root, dbname)
    return {"BHOMA_COUCH_SERVER":  server, # old
            "BHOMA_COUCH_DATABASE": database, # old
            "COUCH_SERVER":  server, # new 
            "COUCH_DATABASE": database, # new
            "COUCHDB_DATABASES": couchdbs,
            "XFORMS_POST_URL": posturl }
            
