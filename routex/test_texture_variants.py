"""Regression checks for mixed Cocos revisions and orphan texture validation."""
import json,tempfile,unittest
from pathlib import Path
import texture_variants as textures

class TextureMetadataTests(unittest.TestCase):
 def test_pack_revision_follows_config_not_first_glob_result(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);bundle=root/'assets/cn';(bundle/'import/ab').mkdir(parents=True)
   (bundle.parent/'versions.json').write_text(json.dumps({'cn':'new'}))
   for revision,width,typed in [('old',10,False),('new',20,True)]:
    config={'name':'cn','uuids':['aa001122','abpack'],'versions':{'native':[0,revision+'tex'],'import':[1,revision+'pack']},'packs':{'abpack':['0']}}
    (bundle/('config.'+revision+'.json')).write_text(json.dumps(config))
    record={'fmt':'0_4_7@93','w':width,'h':width+1}
    pack={'type':'cc.ImageAsset','data':[[record]]}if typed else[1,0,0,[],0,[[record]]]
    (bundle/'import/ab'/('abpack.'+revision+'pack.json')).write_text(json.dumps(pack))
   targets,missing,binary=textures.declared_webps(root)
   by_name={p.name:r for p,r in targets.items()}
   self.assertFalse(missing);self.assertFalse(binary)
   self.assertEqual(by_name['aa001122.newtex.webp']['width'],20)
   self.assertTrue(by_name['aa001122.newtex.webp']['manifest_selected'])
   self.assertEqual(by_name['aa001122.oldtex.webp']['width'],10)
   self.assertIs(by_name['aa001122.oldtex.webp']['manifest_selected'],False)
   report=textures.audit(root)
   self.assertFalse(report['passed']);self.assertFalse(report['active_passed'])
   self.assertEqual(report['active_required_webp'],1)
   self.assertEqual(len(report['historical_asset_errors']),1)

 def test_existing_webp_without_metadata_is_not_silently_skipped(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);(root/'orphan.webp').write_bytes(b'not an image')
   report=textures.audit(root)
   self.assertEqual(report['required_webp'],1)
   self.assertFalse(report['passed'])
   self.assertIn('Invalid WebP',report['assets'][0]['error'])

if __name__=='__main__':unittest.main()
