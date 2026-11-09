"""Passive supplement for the initial running collector; never controls the game."""
import json
import time
from pathlib import Path
from finish_capture import HERE, scan

session = Path((HERE / 'current_session.txt').read_text().strip())
last = None
totals = {'responses': 0, 'verified_success_spins': 0, 'published': 0, 'errors': 0}
offset = 0
while True:
    source = session / 'exchanges.jsonl'
    stamp = source.stat().st_mtime_ns if source.exists() else None
    if stamp != last:
        stats = scan(session, offset)
        offset = stats.pop('offset')
        for key in totals:
            totals[key] += stats[key]
        (session / 'validation.json').write_text(json.dumps(totals, indent=2) + '\n')
        print(json.dumps(totals), flush=True)
        last = stamp
    time.sleep(1)
