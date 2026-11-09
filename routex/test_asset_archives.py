"""Verify ZIP-free checkout reconstruction and integrity enforcement."""
import json,tempfile,unittest,zipfile
from pathlib import Path
from asset_archives import prepare,materialize

class ArchiveTests(unittest.TestCase):
 def test_rebuild_without_original_zip(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);archive=root/'bundle.zip'
   with zipfile.ZipFile(archive,'w')as z:z.writestr('import/aa/original.cconb',b'original asset bytes')
   self.assertEqual(prepare(root),1);archive.unlink()
   self.assertEqual(materialize(root),1)
   with zipfile.ZipFile(archive)as z:self.assertEqual(z.read('import/aa/original.cconb'),b'original asset bytes')
   archive.unlink();(root/'import/aa/original.cconb').write_bytes(b'corrupted')
   with self.assertRaises(ValueError):materialize(root)
   self.assertFalse(archive.exists())
 def test_unsafe_archive_member_rejected(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td)
   with zipfile.ZipFile(root/'bundle.zip','w')as z:z.writestr('../outside.bin',b'bad')
   with self.assertRaises(ValueError):prepare(root)
if __name__=='__main__':unittest.main()
