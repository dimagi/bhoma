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
    server = get_server_url(server_root, username, password)
    database = "%(server)s/%(database)s" % {"server": server, "database": dbname}
    couchdbs = [(app, database) for app in installed_apps if app.startswith("bhoma")]
    posturl = "http://%s/%s/_design/xforms/_update/xform/" % (server_root, dbname)
    return {"BHOMA_COUCH_SERVER":  server,
            "BHOMA_COUCH_DATABASE": database,
            "COUCHDB_DATABASES": couchdbs,
            "XFORMS_POST_URL": posturl }
            

