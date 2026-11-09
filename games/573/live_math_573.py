"""Write verified game-specific SPIN results immediately, without a finish step."""
import ctypes
import errno
import sys
import json
import os
from pathlib import Path
import tempfile


def _write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) == value:
            return
        raise FileExistsError('Existing math JSON differs; preserved: ' + str(path))
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '.', delete=False) as f:
            temporary = Path(f.name)
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        # RENAME_EXCL makes publication atomic without replacing an editor's file.
        if sys.platform != 'darwin':
            raise RuntimeError('573 capture requires atomic no-replace rename on macOS')
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(os.fsencode(temporary), os.fsencode(path), 4):
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code), str(path))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def export_spin(decoded, game_dir, session, decode, encode):
    """Return None for non-SPIN/error/unverified replies, else an ok/error report.

    Unknown schemas stay in the raw capture and math_errors.jsonl; they must not
    become plausible-looking math JSON. Existing edited math is never overwritten.
    Call under the collector lock (or after capture stops during finish).
    """
    if decoded.get('type') != 0 or decoded.get('ret') != 0 or decoded.get('_sig_ok') is not True:
        return None
    game_dir, session = Path(game_dir), Path(session)
    payload = bytes(decoded['raw'])
    try:
        result = decode(payload)
        rid = result['roundIndexV2']
        if not rid.isdigit() or not rid.endswith(game_dir.name):
            raise ValueError('Round ID does not match game directory')
        if encode(result) != payload:
            raise ValueError('Math codec did not preserve the complete SPIN payload')
        _write_json(session / 'math' / (rid + '.json'), result)
        target = game_dir / 'math' / (rid + '.json')
        _write_json(target, result)
        return {'ok': True, 'round_id': rid, 'path': str(target)}
    except Exception as error:
        report = {'ok': False, 'idx': decoded.get('idx'),
                  'error': type(error).__name__ + ': ' + str(error),
                  'payload_hex': payload.hex()}
        session.mkdir(parents=True, exist_ok=True)
        log = 'math_conflicts.jsonl' if isinstance(error, FileExistsError) else 'math_errors.jsonl'
        with (session / log).open('a', encoding='utf-8') as f:
            f.write(json.dumps(report, ensure_ascii=False) + '\n')
        return report


def format_status(report):
    if report is None:
        return ''
    if report['ok']:
        return ' math=OK file=' + report['path']
    return ' math=ERROR ' + report['error'] + ' (raw retained; see session/math_errors.jsonl or math_conflicts.jsonl)'
