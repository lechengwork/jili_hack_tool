"""Ensure repairs never guess missing native extensions or overwrite existing data."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import repair_asset_gaps as repairer

GOLD = (repairer.ROOT / repairer.SOURCE_746).read_bytes()


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'games/545'
        self.static = self.game / 'static'
        self.static.mkdir(parents=True)
        source = self.root / repairer.SOURCE_746
        source.parent.mkdir(parents=True); source.write_bytes(GOLD)
        self.row = {'status': 'missing', 'kind': 'native', 'config': 'game/config.aaaaa.json',
                    'uuid': 'abc123def', 'version': '9926e',
                    'expected_path': 'game/native/ab/abc123def.9926e.soundext1',
                    'extension_evidence': ['game/index.aaaaa.js']}
        cfg = self.static / self.row['config']; cfg.parent.mkdir(parents=True)
        cfg.write_text(json.dumps({'uuids': ['abc123def'], 'versions': {}, 'packs': {}}))
        for target, value in [('ROOT', self.root), ('git_sources', lambda: {})]:
            p = patch.object(repairer, target, value); p.start(); self.addCleanup(p.stop)
        p = patch.object(repairer.subprocess, 'check_output', return_value=''); p.start(); self.addCleanup(p.stop)

    def run_repair(self, fetch=False):
        (self.game / 'asset_validation.json').write_text(json.dumps({'declarations': [self.row]}))
        repairer.repair(['545'], fetch)
        return json.loads((self.game / 'asset_repairs.json').read_text())

    def test_exact_declared_silent_asset_uses_original_bytes(self):
        r = self.run_repair()
        self.assertEqual(r['restored'], 1)
        self.assertEqual((self.static / self.row['expected_path']).read_bytes(), GOLD)
        self.assertEqual(r['outcomes'][0]['sha256'], repairer.SHARED_SHA)

    def test_existing_different_file_is_preserved_and_flagged(self):
        p = self.static / self.row['expected_path']; p.parent.mkdir(parents=True); p.write_bytes(b'colleague-edited')
        r = self.run_repair()
        self.assertEqual(p.read_bytes(), b'colleague-edited')
        self.assertEqual(r['outcomes'][0]['status'], 'existing_conflict')

    def test_unknown_native_extension_is_not_filled_with_silent_audio(self):
        del self.row['expected_path']
        self.row['expected_prefix'] = 'game/native/ab/abc123def.9926e'
        r = self.run_repair()
        self.assertEqual(r['restored'], 0)
        self.assertEqual(len(r['unconfirmed']), 1)

    def test_verified_history_survives_later_empty_gap_inventory(self):
        self.run_repair()
        (self.game / 'asset_validation.json').write_text(json.dumps({'declarations': []}))
        repairer.repair(['545'])
        result = json.loads((self.game / 'asset_repairs.json').read_text())
        self.assertEqual(result['restored'], 1)
        self.assertEqual(result['outcomes'][0]['sha256'], repairer.SHARED_SHA)

    def test_source_content_must_match_verified_original(self):
        (self.root / repairer.SOURCE_746).write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'payload changed'):
            self.run_repair()

    def test_target_traversal_is_rejected(self):
        self.row['expected_path'] = '../../outside.mp3'
        with self.assertRaisesRegex(ValueError, 'outside static root'):
            self.run_repair()
        self.assertFalse((self.root / 'outside.mp3').exists())

    def test_unavailable_import_is_reported_without_extension_probing(self):
        self.row = {'status': 'missing', 'kind': 'import', 'config': 'game/config.aaaaa.json',
                    'uuid': 'abc123def', 'version': 'aaaaa', 'expected_prefix': 'game/import/ab/abc123def.aaaaa'}
        with patch.object(repairer.urllib.request, 'urlopen', side_effect=urllib.error.URLError('original 404')) as request:
            r = self.run_repair(True)
        self.assertEqual(request.call_count, 1)
        self.assertTrue(request.call_args.args[0].full_url.endswith('abc123def.aaaaa.json'))
        self.assertEqual(r['restored'], 0)
        self.assertEqual(r['failed_or_unavailable'], 1)


if __name__ == '__main__':
    unittest.main()
