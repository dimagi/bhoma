import logging
def get_server_url(server_root, username, password):
    if username and password:
        return "http://%(user)s:%(pass)s@%(server)s" % \
            {"user": username,
             "pass": password, 
             "server": server_root }
    else:
        return "http://%(server)s" % {"server": server_root }

def get_dynamic_db_settings(server_root, username, password, dbname, installed_apps):
    """
    Get dynamic database settings.  Other apps can use this if they want to change
    settings
    """
    db_app_prefixes = ('bhoma', 'touchforms', "couchversion", "djangocouch", "couchlog")
    server = get_server_url(server_root, username, password)
    database = "%(server)s/%(database)s" % {"server": server, "database": dbname}
    couchdbs = [(app, database) for app in installed_apps if any(app.startswith(prefix) for prefix in db_app_prefixes)]
    posturl = "http://%s/%s/_design/xforms/_update/xform/" % (server_root, dbname)
    return {"BHOMA_COUCH_SERVER":  server, # old
            "BHOMA_COUCH_DATABASE": database, # old
            "COUCH_SERVER":  server, # new 
            "COUCH_DATABASE": database, # new
            "COUCHDB_DATABASES": couchdbs,
            "XFORMS_POST_URL": posturl }
            

def get_commit_id():
    REV_HASH_LENGTH = 12

    # This command is never allowed to fail since it's called in settings
    try:
        import os
        return os.popen("git log --format=%H -1").readlines()[0].strip()[:REV_HASH_LENGTH].lower()
    except Exception:
        logging.exception('failed to fetch revision hash')
        return None
