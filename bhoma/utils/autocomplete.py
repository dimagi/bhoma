from touchforms.formplayer.autocomplete import csv_loader
from dimagi.utils.couch.database import get_db

def get_config():
    return {
        'firstname-male': {
            'static_file': 'zamnames_firstmale.csv',
            'static_loader': csv_loader,
            'dynamic_bonus': 10,
            'dynamic_inclusion_threshold': 3,
        },
        'firstname-female': {
            'static_file': 'zamnames_firstfemale.csv',
            'static_loader': csv_loader,
            'dynamic_bonus': 10,
            'dynamic_inclusion_threshold': 3,
        },
        'lastname': {
            'static_file': 'zamnames_last.csv',
            'static_loader': csv_loader,
            'dynamic_bonus': 10,
            'dynamic_inclusion_threshold': 3,
        },
        'village': {
            'static_file': 'zambia_all_places.csv',
            'static_loader': lambda path: csv_loader(path, 3),
            'resolution': 1000,
            'dynamic_bonus': 500,
            'split': True,
        },
    }

def couch_loader(domain, inclusion_threshold=None):
    db = get_db()
    data = db.view('patient/autocompl_index', startkey=[domain], endkey=[domain, {}], group=True)
    for row in data:
        if not inclusion_threshold or row['value'] >= inclusion_threshold:
            yield {'name': row['key'][1], 'p': row['value']}
