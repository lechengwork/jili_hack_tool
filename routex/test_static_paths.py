"""URL-encoded native filenames must work without allowing root escapes."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

with tempfile.TemporaryDirectory() as isolated:
    with patch.dict(os.environ, {'STATIC': isolated, 'REPLAY': isolated+'/none',
                                'RESPONSES': isolated+'/none', 'INIT_SEQ': isolated+'/none',
                                'INJECT_BUNDLE': '0', 'CAPTURE': '0'}):
        import server


class StaticPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'static'; self.root.mkdir()
        self.other = Path(self.temp.name) / 'static-other'; self.other.mkdir()
        for name in ('STATIC_ROOT', 'SHARED_ROOT'):
            p = patch.object(server, name, str(self.root)); p.start(); self.addCleanup(p.stop)

    def test_space_and_unicode_font_names(self):
        for name in ('Chanakya Regular.ttf', '中文字型.ttf'):
            path = self.root / name; path.write_bytes(b'original font')
            self.assertEqual(server.resolve_static('/'+quote(name)), str(path.resolve()))

    def test_encoded_traversal_and_sibling_prefix_escape_are_rejected(self):
        (self.other/'secret.ttf').write_bytes(b'outside')
        self.assertIsNone(server.resolve_static('/%2e%2e/static-other/secret.ttf'))

    def test_symlink_outside_root_is_rejected(self):
        (self.other/'font.ttf').write_bytes(b'outside')
        (self.root/'external').symlink_to(self.other, target_is_directory=True)
        self.assertIsNone(server.resolve_static('/external/font.ttf'))

    def test_url_is_decoded_once(self):
        literal = self.root/'font%20name.ttf'; literal.write_bytes(b'literal percent')
        self.assertEqual(server.resolve_static('/font%2520name.ttf'), str(literal.resolve()))
        self.assertIsNone(server.resolve_static('/font%20name.ttf'))

    def test_missing_and_nul_paths_stay_missing(self):
        self.assertIsNone(server.resolve_static('/missing.ttf'))
        self.assertIsNone(server.resolve_static('/%00font.ttf'))


if __name__ == '__main__':
    unittest.main()
