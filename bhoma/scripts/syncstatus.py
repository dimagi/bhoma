import sys

#must match values in couchinventory.py
DOCID_HASH_LEN = 7
REV_HASH_LEN = 2

def chunker(it, n):
    chunk = []
    for e in it:
        chunk.append(e)
        if len(chunk) == n:
            yield chunk
            chunk = []
    if len(chunk) > 0:
        yield chunk

def loaddb(f):
    raw = f.read()
    f.close()

    reclen = DOCID_HASH_LEN + REV_HASH_LEN
    if len(raw) % reclen != 0:
        raise RuntimeError('file corrupted')

    recs = [''.join(ch) for ch in chunker(raw, 9)]
    return [{'id': rec[:DOCID_HASH_LEN], 'rev': rec[DOCID_HASH_LEN:]} for rec in recs]

def compare(srcdata, dstdata):
    def idset(data):
        return set(rec['id'] for rec in data)

    def recdict(data):
        return dict((rec['id'], rec['rev']) for rec in data)

    src_idset = idset(srcdata)
    dst_idset = idset(dstdata)
    src_dict = recdict(srcdata)
    dst_dict = recdict(dstdata)

    total = len(srcdata)
    total_missing = len(src_idset - dst_idset)
    total_conflicted = len([id_ for id_ in src_idset & dst_idset if src_dict[id_] != dst_dict[id_]])

    return {'total': total, 'missing': total_missing, 'conflict': total_conflicted, 'synced': total - total_missing - total_conflicted}

if __name__ == "__main__":

    if len(sys.argv) != 3:
        raise RuntimeError('two arguments required: srcdump dstdump')

    def argfile(path):
        return open(path) if path != '-' else sys.stdin

    src = argfile(sys.argv[1])
    dst = argfile(sys.argv[2])

    if src == sys.stdin and dst == sys.stdin:
        raise RuntimeError('only one file may use stdin!')

    srcdata = loaddb(src)
    dstdata = loaddb(dst)
    stats = compare(srcdata, dstdata)

    print '%.2f%% synced (%d of %d records)' % (100. * stats['synced'] / stats['total'], stats['synced'], stats['total'])
    print '%d records unsynced (%d new; %d conflicting)' % (stats['missing'] + stats['conflict'], stats['missing'], stats['conflict'])