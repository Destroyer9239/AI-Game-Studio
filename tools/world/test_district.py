import copy
import json
import unittest
from generate_district import ROOT, compose, TEMPLATES

class DistrictTests(unittest.TestCase):
    def setUp(self):self.spec=json.loads((ROOT/'tools/world/district_spec.json').read_text())
    def test_determinism(self):self.assertEqual(compose(self.spec),compose(copy.deepcopy(self.spec)))
    def test_seed_variation(self):
        first=compose(self.spec);self.spec['seed']+=100
        self.assertNotEqual(first['cells'][0]['buildings'],compose(self.spec)['cells'][0]['buildings'])
    def test_center_preserved(self):
        old=json.loads((ROOT/'game/world/city_block.json').read_text())
        self.assertEqual(compose(self.spec)['cells'][1]['buildings'],old['cells'][1]['buildings'])
    def test_all_archetypes(self):
        for archetype in TEMPLATES:
            self.spec['blocks'][0]['archetype']=archetype
            self.assertTrue(compose(self.spec)['cells'][0]['lots'])
    def test_road_connection(self):
        west,center=compose(self.spec)['cells']
        self.assertEqual(west['x']+west['road_sockets'][1][0],center['x']+center['road_sockets'][0][0])
    def test_budget_rejection(self):
        self.spec['budgets']['max_buildings']=1
        with self.assertRaises(ValueError):compose(self.spec)
    def test_duplicate_rejection(self):
        self.spec['blocks'][0]['id']='center'
        with self.assertRaises(ValueError):compose(self.spec)
    def test_unsupported_road(self):
        self.spec['road_width']=12
        with self.assertRaises(ValueError):compose(self.spec)

if __name__=='__main__':unittest.main()
