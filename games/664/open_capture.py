#!/usr/bin/env python3
"""Open a dedicated capture profile. Browser certificate checks remain enabled."""
import json
import argparse
from pathlib import Path
import subprocess
from urllib.parse import urlsplit,parse_qs

HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--profile',help='Reuse an existing capture profile after its Chrome exits')
    args=ap.parse_args()
    result=json.loads((HERE/'login_session.local.json').read_text())
    u=urlsplit(result['game_url'])
    if u.hostname!='uat-wbgame.jlfafafa3.com' or u.path not in ('/lj500/','/lj500/index.html') or parse_qs(u.query).get('gameID')!=['664']:
        raise ValueError('Refusing unexpected launch URL')
    session=Path((HERE/'current_session.txt').read_text().strip())
    profile=Path(args.profile).resolve() if args.profile else session/'chrome-profile'
    (session/'chrome_profile.txt').write_text(str(profile)+'\n')
    process=subprocess.Popen([
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '--user-data-dir='+str(profile),
        '--host-resolver-rules=MAP uat-wbgame.jlfafafa3.com 127.0.0.1:8664',
        '--disable-quic','--no-first-run','--no-default-browser-check',
        '--disable-features=ChromeWhatsNewUI',result['game_url'],
    ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    (session/'chrome.pid').write_text(str(process.pid)+'\n')
    print('Lucky Jaguar 500 capture Chrome pid=%s player=%s; certificate validation enabled' % (process.pid,result['player_id']),flush=True)
    process.wait()
