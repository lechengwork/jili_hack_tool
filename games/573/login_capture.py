"""Create a fresh 573 login without changing shared config or reusing keys."""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
import jili_login

if __name__ == '__main__':
    # The previously reserved capture account, isolated from shared math accounts.
    jili_login.CONFIG_PATH = HERE.parent / '200' / 'capture_config.local.json'
    result = jili_login.login('573', verbose=False)
    url = urlsplit(result['game_url'])
    if url.hostname != 'uat-wbgame.jlfafafa3.com' or parse_qs(url.query).get('gameID') != ['573']:
        raise ValueError('Unexpected 573 launch destination')
    target = HERE / 'login_session.local.json'
    target.touch(mode=0o600, exist_ok=True)
    target.chmod(0o600)
    target.write_text(json.dumps(result, ensure_ascii=False) + '\n')
    print('LoginGame OK player=%s path=%s gameID=573' % (result['player_id'], url.path))
