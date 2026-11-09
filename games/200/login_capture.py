#!/usr/bin/env python3
"""Get a fresh Pappu launch using this game's private capture account config."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
import jili_login

if __name__ == '__main__':
    jili_login.CONFIG_PATH = HERE / 'capture_config.local.json'
    result = jili_login.login('200', verbose=False)
    target = HERE / 'login_session.local.json'
    target.write_text(json.dumps(result, ensure_ascii=False) + '\n')
    target.chmod(0o600)
    from urllib.parse import urlsplit, parse_qs
    url = urlsplit(result['game_url'])
    if url.hostname != 'uat-wbgame.jlfafafa3.com' or url.path != '/pappu/index.html' or parse_qs(url.query).get('gameID') != ['200']:
        raise ValueError('Unexpected Pappu launch destination')
    print('LoginGame OK player=%s path=%s gameID=200' % (result['player_id'], url.path))
