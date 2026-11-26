#!/usr/bin/env python3
"""Verify archived input versions, LATEST, and the new version file manifest."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def main():
    baseline=json.loads((HERE/'BASELINE.json').read_text())
    for name, expected in baseline['preserved_git_blobs'].items():
        path=ROOT/name
        assert path.is_file(), 'Missing archived source: '+name
        assert git_blob(path.read_bytes())==expected, 'Changed archived source: '+name
    assert (ROOT/'LATEST').read_bytes()==b'v3.2\n', 'LATEST was modified without approval'
    manifest=json.loads((HERE/'FILE_MANIFEST.json').read_text())
    for name, expected in manifest.items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==expected, 'Changed candidate file: '+name
    print('PASS:',len(baseline['preserved_git_blobs']),'archived/control files unchanged;',len(manifest),'candidate SHA-256 values match; LATEST remains v3.2.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
