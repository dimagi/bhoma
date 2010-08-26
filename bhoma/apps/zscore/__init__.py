from django.db.models import signals

def syncdb(app, created_models, verbosity=2, **kwargs):
    """Function used by syncdb signal"""
    app_name = app.__name__.rsplit('.', 1)[0]
    app_label = app_name.split('.')[-1]
    if app_label == "zscore":
        from bhoma.apps.zscore.loader import load_zscore
        load_zscore("static/zscore_data.csv")
    
signals.post_syncdb.connect(syncdb)