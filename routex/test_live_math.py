"""Offline regression tests for immediate 518/807 math export (no finish/server)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from live_math import export_spin

ROOT = Path(__file__).resolve().parent.parent


def adapter(gid):
    spec = importlib.util.spec_from_file_location('adapter_' + gid, ROOT / 'games' / gid / 'math_adapter.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LiveMathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def row(self, payload, **changes):
        return dict(type=0, ret=0, _sig_ok=True, raw=list(payload), idx=1, **changes)

    def fixture(self, gid):
        codec = adapter(gid)
        vector = json.loads((ROOT / 'games' / gid / 'math/roundtrip_vectors.jsonl').read_text().splitlines()[0])
        return codec, bytes.fromhex(vector['response_payload_hex'])

    def test_all_observed_payloads_are_immediately_readable_and_reversible(self):
        for gid in ['518', '807']:
            codec = adapter(gid)
            game, session = self.root / gid, self.root / ('session-' + gid)
            vectors = ROOT / 'games' / gid / 'math/roundtrip_vectors.jsonl'
            for line in vectors.read_text().splitlines():
                payload = bytes.fromhex(json.loads(line)['response_payload_hex'])
                report = export_spin(self.row(payload), game, session, codec.wire_to_math, codec.math_to_wire)
                self.assertTrue(report['ok'], report)
                for directory in [game / 'math', session / 'math']:
                    sample = json.loads((directory / (report['round_id'] + '.json')).read_text())
                    self.assertEqual(codec.math_to_wire(sample), payload)

    def test_heartbeat_failed_and_unverified_spins_create_no_math(self):
        codec, payload = self.fixture('807')
        for changes in [{'type': 2}, {'ret': 304}, {'_sig_ok': False}]:
            row = self.row(payload); row.update(changes)
            self.assertIsNone(export_spin(row, self.root / '807', self.root / 'session', codec.wire_to_math, codec.math_to_wire))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_unknown_schema_is_retained_and_next_valid_spin_still_exports(self):
        codec, payload = self.fixture('807')
        unknown = payload + codec.field(127, 0, codec.varint(1))
        game, session = self.root / '807', self.root / 'session'
        report = export_spin(self.row(unknown), game, session, codec.wire_to_math, codec.math_to_wire)
        self.assertFalse(report['ok'])
        evidence = json.loads((session / 'math_errors.jsonl').read_text())
        self.assertEqual(evidence['payload_hex'], unknown.hex())
        self.assertFalse((game / 'math').exists())
        self.assertTrue(export_spin(self.row(payload), game, session, codec.wire_to_math, codec.math_to_wire)['ok'])

    def test_duplicate_and_finish_backfill_do_not_overwrite_edited_math(self):
        for gid in ['518', '807']:
            codec, payload = self.fixture(gid)
            game, session = self.root / gid, self.root / ('session-' + gid)
            report = export_spin(self.row(payload), game, session, codec.wire_to_math, codec.math_to_wire)
            path = Path(report['path']); before = path.stat().st_mtime_ns
            self.assertTrue(export_spin(self.row(payload), game, session, codec.wire_to_math, codec.math_to_wire)['ok'])
            self.assertEqual(path.stat().st_mtime_ns, before)
            edited = json.loads(path.read_text()); edited['postMoney'] += 1
            path.write_text(json.dumps(edited))
            self.assertFalse(export_spin(self.row(payload), game, session, codec.wire_to_math, codec.math_to_wire)['ok'])
            self.assertEqual(json.loads(path.read_text()), edited)
            saved = json.loads((session / 'math' / path.name).read_text())
            self.assertEqual(codec.math_to_wire(saved), payload)


if __name__ == '__main__':
    unittest.main()
