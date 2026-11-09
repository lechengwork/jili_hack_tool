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
            raise RuntimeError('224 capture requires atomic no-replace rename on macOS')
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
