from __future__ import absolute_import

import itertools
import base64
import json
from django.core.cache import cache
import os.path

DEFAULT_NUM_SUGGESTIONS = 12

CACHE_TIMEOUT = 86400
CACHE_REFRESH_AFTER = 3600

def identity(x):
    return x

def groupby(it, keyfunc=identity, valfunc=identity, reducefunc=identity):
    grouped = {}
    for e in it:
        key = keyfunc(e)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(valfunc(e))
    return dict((k, reducefunc(vs)) for k, vs in grouped.iteritems())

def autocompletion(domain, key, max_results):
    if domain == 'firstname':
        return merge_autocompletes(max_results, (get_autocompletion('firstname-%s' % gender, key, max_results) for gender in ('male', 'female')))

    return get_autocompletion(domain, key, max_results)

def merge_autocompletes(max_results, *responses):
    response = {}

    all_suggestions = itertools.chain(r['suggestions'] for r in responses)
    grouped_suggestions = groupby(all_suggestions, lambda m: m['name'], lambda m: m['p'], sum)
    suggestions = [{'name': k, 'p': v} for k, v in grouped_suggestions.iteritems()]
    response['suggestions'] = sorted(suggestions, key=lambda m: -m['p'])[:max_results]

    hint_responses = [r['hinting'] for r in responses if 'hinting' in r]
    if hint_responses:
        freqs = [h['nextchar_freq'] for h in hint_responses]
        raw_freq_all = itertools.chain(fr.iteritems() for fr in freqs)
        freq_consolidated = groupby(raw_freq_all, lambda e: e[0], lambda e: e[1], sum)
        response['hinting'] = {'nextchar_freq': freq_consolidated}

        margins = [h['margin'] for h in hint_responses if 'margin' in h]
        if margins:
            response['hinting']['margin'] = max(margins)

    return response

def get_autocompletion(domain, key, maxnum):
    if not cacheget((domain, 'initialized')):
        init_cache(domain)

    response = cacheget((domain, 'results', key))
    if not response:
        print 'no response cached', (domain, 'results', key)
        rawdata = None
        lookup_key = key
        while rawdata == None and len(lookup_key) > 0:
            rawdata = cacheget((domain, 'raw', lookup_key))
            lookup_key = lookup_key[:-1]
        if rawdata == None:
            #prefix for which no matches exist
            rawdata = []
        response = get_response(domain, key, rawdata)
    response['suggestions'] = response['suggestions'][:maxnum]
    return response



def load_census_file(path):
    with open(path) as f:
        lines = f.readlines()
        for ln in lines:
            name = ln[:15].strip()
            prob = float(ln[15:20]) / 100.
            yield {'name': name, 'p': max(2e5 * prob, 1.)}

def load_raw_file(path):
    with open(path) as f:
        lines = f.readlines()
        for ln in lines:
            pcs = ln.split(';')
            name = pcs[0].strip()
            prob = int(pcs[1].strip())
            yield {'name': name, 'p': prob}

def get_matches(data, key, maxnum, matchfunc=None):
    if matchfunc == None:
        matchfunc = lambda key, name: name.startswith(key)

    #autocomplete suggestions
    matches = []
    for d in data:
        if matchfunc(key, d['name']):
            matches.append(d)
            if len(matches) == maxnum:
                break

    #next-char statistics for keyboard hinting
    alpha = {}
    total = 0
    for d in data:
        if d['name'].startswith(key) and not d['name'] == key:
            c = d['name'][len(key)]
            if c not in alpha:
                alpha[c] = 0
            alpha[c] += d['p']
            total += d['p']

    print sorted(list(alpha.iteritems()))

    return {'suggestions': matches, 'hinting': {'nextchar_freq': alpha, 'sample_size': total}}




def group(it, func):
    grouped = {}
    for e in it:
        key = func(e)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(e)
    return grouped

def init_cache(domain):
    IX_LEN = 3

    data = load_data(domain)
    for i in range(IX_LEN + 1):
        subdata = group(data, lambda e: e['name'][:i])
        for key, records in subdata.iteritems():
            if len(key) != i:
                continue
            print i, key
            cacheset((domain, 'results', key), get_matches(records, key, 20))
            if i == IX_LEN:
                cacheset((domain, 'raw', key), records)
    cacheset((domain, 'initialized'), True)

def get_response(domain, key, data):
    response = get_matches(data, key, 20)
    cacheset((domain, 'results', key), response)
    return response

def load_data(domain):
    rootdir = 'data/census'

    DATASET = 'us'

    if domain == 'village':
        if DATASET == 'zam':
            path = 'zamvillage'
        else:
            path = 'usplaces'
        data = load_raw_file(os.path.join(rootdir, path))
    else:
        if DATASET == 'zam':
            path = {
                'firstname-male': 'zamnamesfirstmale',
                'firstname-female': 'zamnamesfirstfemale',
                'lastname': 'zamnameslast'
                }[domain]
            loadfunc = load_raw_file
        else:
            path = {
                'firstname-male': 'dist.male.first',
                'firstname-female': 'dist.female.first',
                'lastname': 'dist.all.last'
                }[domain]
            loadfunc = load_census_file
        data = loadfunc(os.path.join(rootdir, path))
    data = list(data)
    data.sort(key=lambda v: -v['p'])
    return data


### UTILITY FUNCTIONS FOR DEALING WITH MEMCACHED ###

def enc(data):
    return base64.b64encode(json.dumps(data))

def dec(data):
    return json.loads(base64.b64decode(data))

def cacheget(key):
    data = cache.get(enc(key))
    if data == None:
        return None
    else:
        return dec(data)

def cacheset(key, val):
    cache.set(enc(key), enc(val), CACHE_TIMEOUT)

### FUNCTIONS TO AID IN FUZZY MATCHING -- currently unused ###

def damerau_levenshtein_dist(s1, s2, thresh=9999):
    """compute the damerau-levenshtein distance between two strings"""
    if abs(len(s1) - len(s2)) > thresh:
        return None

    metric = compute_levenshtein(s1, s2, thresh)[-1][-1]
    return metric if metric <= thresh and metric >= 0 else None

def damlev_prefix_dist(prefix, target, thresh=9999):
    """compute the minimum damerau-levenshtein distance between target and all strings starting with prefix"""
    arr = compute_levenshtein(prefix, target, thresh, False)
    ixs = [k for k in arr[-1] if k >= 0]
    return min(ixs) if ixs else None

def munching_index_order(d1, d2, thresh):
    dmin = min(d1, d2)
    dmax = max(d1, d2)
    thresh = min(thresh, dmax)

    def ixround(a):
        for b in range(thresh):
            i = d1 - 1 - a
            j = d2 - 1 - a - thresh + b
            yield i, j

            i = d1 - 1 - a - thresh + b
            j = d2 - 1 - a
            yield i, j

        i = d1 - 1 - a
        j = d2 - 1 - a
        yield i, j

    for a in range(dmin - 1, -1, -1):
        yield [(i, j) for i, j in ixround(a) if i >= 0 and j >= 0]

def typewriter_index_order(d1, d2, thresh):
    for i in range(d1):
        yield [(i, j) for j in range(d2)]

def compute_levenshtein(s1, s2, thresh=9999, exact=True):
    d1 = len(s1) + 1
    d2 = len(s2) + 1
    arr = [[-1 for j in range(d2)] for i in range(d1)]

    def offset(i, j):
        return abs((d1 - d2) - (i - j)) if exact else 0

    def getarr(i, j):
        return arr[i][j] if offset(i, j) <= thresh else thresh + 1

    index_iterator = munching_index_order if exact else typewriter_index_order
    for ixround in index_iterator(d1, d2, thresh):
        for i, j in ixround:
            if i == 0:
                arr[i][j] = j
            elif j == 0:
                arr[i][j] = i
            else:
                cost = 0 if (s1[i - 1] == s2[j - 1]) else 1
                arr[i][j] = min(
                    getarr(i - 1, j) + 1,   #deletion
                    getarr(i, j - 1) + 1,   #insertion
                    getarr(i - 1, j - 1) + cost   #substitution
                )
                if i > 1 and j > 1 and (s1[i - 1], s1[i - 2]) == (s2[j - 2], s2[j - 1]):
                    arr[i][j] = min(
                        getarr(i, j),
                        getarr(i - 2, j - 2) + cost   #transposition
                    )

        if min(arr[i][j] + offset(i, j) for i, j in ixround) > thresh:
            break

    return arr

