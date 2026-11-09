#!/usr/bin/env python3
"""Fetch one fresh Go Rush URL using the registry's dedicated capture account."""
import json,sys
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT))
import jili_login
if __name__=='__main__':
    registry=json.loads((ROOT/'account_registry.json').read_text())
    jili_login.CONFIG_PATH=ROOT/registry['capture_reservation']['private_config']
    r=jili_login.login('224',verbose=False);u=urlsplit(r['game_url'])
    if u.hostname!='uat-wbgame.jlfafafa3.com' or u.path!='/aviator/index.html' or parse_qs(u.query).get('gameID')!=['224']:raise ValueError('Unexpected Go Rush destination')
    p=HERE/'login_session.local.json';p.touch(mode=0o600,exist_ok=True);p.chmod(0o600);p.write_text(json.dumps(r,ensure_ascii=False)+'\n')
    print('LoginGame OK gameID=224 path=/aviator/index.html; fresh URL saved privately')
