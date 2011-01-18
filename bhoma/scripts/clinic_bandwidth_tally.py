import re
import math
from datetime import datetime, timedelta
import sys

def parse_file(path):
    with open(path) as f:
        raw = [l.strip() for l in f.readlines() if l.strip()]

    data = []
    ts = None
    for i, ln in enumerate(raw):
        if ln == '==START==':
            ts = datetime.fromtimestamp(float(raw[i + 1]))
        elif ln == '==END==':
            ts = None
                
        pcs = ln.split(';')
        if len(pcs) != 5:
            continue

        proc = pcs[0]
        up = float(pcs[3])
        down = float(pcs[4])
        if up + down == 0:
            continue

        data.append({
            'p': proc,
            'u': up,
            'd': down,
            't': ts,
        })
    return data

def fdelta(delta):
    return 86400. * delta.days + delta.seconds + 1.0e-6 * delta.microseconds

def to_bucket(ts, res):
    s = fdelta(ts - datetime(1970, 1, 1))
    return int(math.floor(s / fdelta(res)))

def to_ts(bucket, res):
    return datetime.utcfromtimestamp(bucket * fdelta(res))

def get_time_limits(data):
    mintime = min(k['t'] for k in data)
    maxtime = max(k['t'] for k in data)
    return (mintime, maxtime)

def get_time_buckets(data, res):
    mintime, maxtime = get_time_limits(data)

    buckets = []
    b = to_bucket(mintime, res)
    while to_ts(b, res) < maxtime:
        buckets.append(b)
        b += 1
    return buckets

def time_partition(data, res):
    partitioned = dict((b, (lambda: [])()) for b in get_time_buckets(data, res))

    for d in data:
        partitioned[to_bucket(d['t'], res)].append(d)

    return partitioned

def proc_partition(data):
    partitioned = {}
    for d in data:
        proc = d['p']
        if proc not in partitioned:
            partitioned[proc] = []
        partitioned[proc].append(d)
    return partitioned

def tally(raw, key=lambda r: r['p']):
    data = {}
    for r in raw:
        x = key(r)
        if x not in data:
            data[x] = [0, 0]
        data[x][0] += r['u']
        data[x][1] += r['d']

    results = [{'p': k, 'u': v0, 'd': v1} for k, (v0, v1) in data.iteritems()]
    results.sort(key=lambda k: -(k['u'] + k['d']))
    return results

def print_results_by_time(results, bucket, res, timelimits=None):
    print 'data usage: %s to %s' % (to_ts(bucket, res) if bucket else timelimits[0], to_ts(bucket + 1, res) if bucket else timelimits[1])

    def println(proc, up, down):
        return '%s  %7dK up  %7dK down' % (('%s:' % proc).ljust(45), up, down)

    misc = {'u': 0, 'd': 0}
    total = {'u': 0, 'd': 0}
    for r in results:
        total['u'] += r['u']
        total['d'] += r['d']
        if r['u'] + r['d'] < 20.:
            misc['u'] += r['u']
            misc['d'] += r['d']
        else:
            print println(r['p'], round(r['u']), round(r['d']))
    if misc['u'] + misc['d'] > 0:
        print println('misc', round(misc['u']), round(misc['d']))
    print println('total', round(total['u']), round(total['d']))
    print

def print_results_by_proc(results, proc, buckets, res):
    results = dict((r['p'], r) for r in results)

    print 'data usage: %s' % proc

    def println(proc, up, down):
        return '%s  %7dK up  %7dK down' % (('%s>' % proc).ljust(20), up, down)

    total = {'u': 0, 'd': 0}
    for b in buckets:
        try:
            r = results[b]
        except KeyError:
            r = {'u': 0, 'd': 0}

        total['u'] += r['u']
        total['d'] += r['d']
        print println(str(to_ts(b, res)), round(r['u']), round(r['d']))
    print println('total', round(total['u']), round(total['d']))
    print

if __name__ == "__main__":

    PATH = sys.argv[1]
    try:
        RES = eval('timedelta(%s)' % sys.argv[2])
        bucketed = True
    except IndexError:
        RES = timedelta(days=9999)
        bucketed = False

    data = parse_file(PATH)
    results = tally(data)

    if bucketed:
        pdata = time_partition(data, RES)
        presults = dict((k, tally(v)) for k, v in pdata.iteritems())
        for k in sorted(presults.keys()):
            print_results_by_time(presults[k], k, RES)

        procs_of_interest = [r['p'] for r in results if r['u'] + r['d'] > 20.]
        prdata = dict((k, v) for k, v in proc_partition(data).iteritems() if k in procs_of_interest)
        prresults = dict((k, tally(v, lambda r: to_bucket(r['t'], RES))) for k, v in prdata.iteritems())
        for k in sorted(prresults.keys()):
            print_results_by_proc(prresults[k], k, get_time_buckets(data, RES), RES)
    else:
        print_results_by_time(results, None, RES, get_time_limits(data))
