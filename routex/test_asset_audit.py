"""Regression cases for manifest/native coverage without downloads or restoration."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from asset_audit import audit, validate_content


class AssetAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / 'demo/assets/game'
        self.bundle.mkdir(parents=True)

    def config(self, native=None, imports=None, packs=None):
        data = {'name': 'game', 'uuids': ['abc123def', 'pack00000'],
                'paths': {'0': ['checkname1', 0]}, 'types': ['cc.AudioClip'],
                'versions': {'native': native or [], 'import': imports or []}, 'packs': packs or {}}
        (self.bundle / 'config.aaaaa.json').write_text(json.dumps(data))

    def file(self, relative, data):
        p = self.root / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    def test_missing_random_audio_has_exact_original_extension_and_is_not_created(self):
        self.config(native=[0, '9926e'])
        name, ext = 'checkname1', 'soundext1'
        arrays = ','.join('[' + ','.join(map(str, map(ord, s))) + ']' for s in [name, ext])
        (self.bundle / 'index.aaaaa.js').write_text('var pairs=[' + arrays + '];')
        before = {p.relative_to(self.root) for p in self.root.rglob('*')}
        report = audit(self.root)
        row = report['declarations'][0]
        self.assertEqual(row['status'], 'missing')
        self.assertEqual(row['expected_path'], 'demo/assets/game/native/ab/abc123def.9926e.soundext1')
        self.assertFalse(report['inventory_no_known_missing_or_invalid'])
        self.assertEqual(before, {p.relative_to(self.root) for p in self.root.rglob('*')})

    def test_wrong_placeholder_cannot_pass_known_payload_validation(self):
        path = self.file('demo/assets/game/native/ab/abc123def.9926e.soundext1', b'ID3' + bytes(743))
        with self.assertRaisesRegex(ValueError, 'differs'):
            validate_content(path, '9926e')

    def test_packed_member_does_not_require_nonexistent_standalone_import(self):
        self.config(imports=[0, 'bbbbb', 1, 'aaaaa'], packs={'pack00000': [0]})
        self.file('demo/assets/game/import/pa/pack00000.aaaaa.json', b'[1,2,3]')
        report = audit(self.root)
        self.assertEqual(report['counts'].get('present'), 1)
        self.assertEqual(report['counts'].get('missing', 0), 0)
        self.assertEqual(report['declarations'][0]['kind'], 'import_pack')

    def test_original_filename_native_directory_is_not_a_missing_font(self):
        self.config(native=[0, 'aaaaa'])
        self.file('demo/assets/game/native/ab/abc123def.aaaaa/Font.ttf', b'\x00\x01\x00\x00' + bytes(20))
        report = audit(self.root)
        self.assertEqual(report['counts'].get('missing', 0), 0)
        self.assertEqual(report['declarations'][0]['files'][0]['status'], 'valid')

    def test_binary_pack_is_explicitly_uncovered(self):
        self.config(imports=[1, 'aaaaa'], packs={'pack00000': [0]})
        self.file('demo/assets/game/import/pa/pack00000.aaaaa.bin', b'original-binary')
        report = audit(self.root)
        self.assertTrue(any('not decoded' in r['reason'] for r in report['uncovered']))
        self.assertFalse(report['complete_acceptance_passed'])

    def test_invalid_extra_native_also_fails_inventory(self):
        self.config()
        self.file('demo/assets/game/native/ab/abc123def.abcde.bin', b'')
        report = audit(self.root)
        self.assertEqual(report['other_mirrored_media_counts'], {'invalid': 1})
        self.assertFalse(report['inventory_no_known_missing_or_invalid'])

    def test_external_http_origin_is_rejected_before_any_network(self):
        with self.assertRaisesRegex(ValueError, 'loopback'):
            audit(self.root, True, 'https://example.com')

    def test_loopback_http_checks_complete_bytes_and_mime(self):
        self.config(native=[0, 'aaaaa'])
        data = b'ID3' + b'captured audio payload'
        self.file('demo/assets/game/native/ab/abc123def.aaaaa.mp3', data)
        report = audit(self.root, check_http=True)
        self.assertEqual(report['http']['valid'], 1)
        self.assertEqual(report['http']['invalid'], 0)
        self.assertEqual(report['declarations'][0]['files'][0]['sha256'], hashlib.sha256(data).hexdigest())
        self.assertIn('NOT actual replay', report['http']['scope'])


if __name__ == '__main__':
    unittest.main()
