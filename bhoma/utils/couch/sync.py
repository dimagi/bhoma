from django.conf import settings
from couchdbkit.client import Server
from bhoma import const


def pull_from_national_to_clinic():
    server = Server()
    source = settings.BHOMA_NATIONAL_DATABASE
    target = settings.BHOMA_COUCH_DATABASE
    filter = const.FILTER_CLINIC
    query_params = { "clinic_id": settings.BHOMA_CLINIC_ID }
    return replicate(server, source, target, filter, query_params)

def push_from_clinic_to_national():
    server = Server()
    source = settings.BHOMA_COUCH_DATABASE
    target = settings.BHOMA_NATIONAL_DATABASE
    return replicate(server, source, target)


def replicate(server, source, target, filter="", query_params={}):
    replication_params = {"source": source, 
                          "target": target,
                          "filter": filter, 
                          "query_params": query_params
    }
    result = server.res.post('/_replicate', payload=replication_params)
    return result