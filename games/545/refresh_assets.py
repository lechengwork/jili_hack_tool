#!/usr/bin/env python3
"""Refresh the 545 entry and shared version manifest from the test CDN."""
import json
from pathlib import Path
import re
import urllib.request

HERE = Path(__file__).resolve().parent
ORIGIN = 'https://uat-wbgame.jlfafafa3.com/'

def fetch(rel):
    request = urllib.request.Request(ORIGIN + rel, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()

def save(rel, data):
    target = HERE / 'static' / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.download')
    temporary.write_bytes(data)
    temporary.replace(target)

if __name__ == '__main__':
    rel = 'astarte2/3.6/web-mobile/assets/versions.json'
    manifest = fetch(rel)
    version = json.loads(manifest)['bundle.js']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', version):
        raise ValueError('Invalid shared bundle version')
    bundle = 'astarte2/3.6/web-mobile/src/chunks/bundle.' + version + '.js'
    code = fetch(bundle)
    html = fetch('cc3x3/').decode('utf-8')
    html = html.replace('<head>', '<head>\n<meta charset="utf-8">', 1)
    save(bundle, code)
    save(rel, manifest)
    save('cc3x3/index.html', html.encode('utf-8'))
    print('Refreshed 545 entry; shared bundle ' + version + '; no credentials used.')
