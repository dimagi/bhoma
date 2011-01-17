import re
from datetime import datetime, timedelta
import sys
import os
import os.path

LOGFILE = '/var/log/bhoma/reversessh.log'
WINDOW = timedelta(minutes=20)
BUFFER = timedelta(minutes=3)

def fdelta(delta):
    return 86400. * delta.days + delta.seconds + 1.0e-6 * delta.microseconds

def partition(data, keyfunc):
    grouped = {}
    for e in data:
        key = keyfunc(e)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(e)
    return grouped

def parse_logfile(basepath=LOGFILE):
    logdir, logfile = os.path.split(basepath)
    paths = [os.path.join(logdir, p) for p in os.listdir(logdir) if p.startswith(logfile)]

    lines = []
    for p in paths:
        with open(p) as f:
            lines.extend(f.readlines())
    
    data = []
    for l in lines:
        match = re.match('^(?P<stamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*:INFO:(?P<site>[^ ]+).*(?P<status>up|down)$', l)
        if match:
            stamp = datetime.strptime(match.group('stamp'), '%Y-%m-%d %H:%M:%S')
            site = match.group('site')
            up = (match.group('status') == 'up')
            data.append((stamp, site, up))
    return data

def tally(data, start, end, window=WINDOW):
    persite = partition(data, lambda e: e[1])
    return dict((site, tally_site(reports, start, end, window)) for site, reports in persite.iteritems())

def midp(date1, date2):
    return date1 + (date2 - date1) / 2

def tally_site(reports, start, end, window):
    halfrange = window / 2 + BUFFER
    reports = [r for r in reports if r[0] >= start - halfrange and r[0] <= end + halfrange]
    reports.sort(key=lambda e: e[0])

    totals = {'up': 0., 'down': 0.}
    for i, r in enumerate(reports):
        prev = reports[i - 1][0] if i > 0 else None
        next = reports[i + 1][0] if i < len(reports) - 1 else None

        interval_start = max(r[0] - halfrange, start, midp(r[0], prev) if prev else datetime(1970, 1, 1))
        interval_end = min(r[0] + halfrange, end, midp(r[0], next) if next else datetime(2030, 1, 1))

        totals['up' if r[2] else 'down'] += max(fdelta(interval_end - interval_start), 0.)

    total_interval = fdelta(end - start)
    return (totals['up'] / total_interval, totals['down'] / total_interval)
        
def print_tallies(tallies, start, end):
    print 'remote tunnel uptime\n\nstart: %s\nend:   %s\n' % tuple(x.strftime('%Y-%m-%d %H:%M:%S') for x in (start, end))

    for site in sorted(tallies.keys()):
        up = tallies[site][0]
        down = tallies[site][1]
        unkn = abs(1. - up - down)

        def fmtpct(x):
            return ('%.1f%%' % (100.*x)).rjust(6)

        print '%s  %s up  %s down  %s unknown' % (site.ljust(max(len(s) for s in tallies.keys()) + 3), fmtpct(up), fmtpct(down), fmtpct(unkn))

if __name__ == "__main__":

    if len(sys.argv) == 1:
        start = datetime.now() - timedelta(days=1)
        end = datetime.now()
    elif len(sys.argv) == 2:
        start = datetime.now() - timedelta(hours=float(sys.argv[1]))
        end = datetime.now()
    else:
        start = datetime.strptime(sys.argv[1], '%Y%m%d%H%M')
        end = datetime.strptime(sys.argv[2], '%Y%m%d%H%M')

    rawdata = parse_logfile()
    tallies = tally(rawdata, start, end)
    print_tallies(tallies, start, end)

