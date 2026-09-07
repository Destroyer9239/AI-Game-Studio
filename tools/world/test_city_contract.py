"""Read-only world/district/chunk/lot contract validation, no asset regeneration."""
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def validate(spec):
    assert spec['schema_version']==1
    assert spec['load_radius']<spec['unload_radius'] and spec['max_loaded']<=3
    ids=[c['id'] for c in spec['cells']]; assert len(ids)==len(set(ids))
    rules=spec['district_rules'][spec['district']]
    assert 4<=rules['road_width']<=16
    occupied=[]
    for cell in spec['cells']:
        names=[b['id'] for b in cell['buildings']];assert len(names)==len(set(names))
        for lot in cell['buildings']:
            recipe=json.loads((ROOT/f"tools/world/{lot['asset']}.json").read_text())
            assert recipe['archetype'] in ['industrial','commercial','office','residential','civic','warehouse','utility','spaceport']
            assert rules['height_range'][0]<=recipe['floors']<=rules['height_range'][1]
            x,_,z=lot['position']; assert abs(x)<32 and abs(z)<32
            assert lot['yaw']==(180 if z<0 else 0), 'Entrance must face street'
            assert abs(z)-lot['front_offset']>rules['road_width']/2+4, 'Facade overlaps sidewalk'
            assert lot['id'] not in occupied;occupied.append(lot['id'])
    return len(occupied)
class CityContract(unittest.TestCase):
    def setUp(self):self.spec=json.loads((ROOT/'game/world/city_block.json').read_text())
    def test_existing_block(self):self.assertEqual(validate(self.spec),4)
    def test_bad_door(self):
        self.spec['cells'][1]['buildings'][0]['yaw']=0
        with self.assertRaises(AssertionError):validate(self.spec)
    def test_duplicate_lot(self):
        self.spec['cells'][1]['buildings'].append(self.spec['cells'][1]['buildings'][0])
        with self.assertRaises(AssertionError):validate(self.spec)
    def test_sidewalk_overlap(self):
        self.spec['cells'][1]['buildings'][0]['position'][2]=-6
        with self.assertRaises(AssertionError):validate(self.spec)
    def test_height_rule(self):
        self.spec['district_rules']['industrial']['height_range']=[1,1]
        with self.assertRaises(AssertionError):validate(self.spec)
if __name__=='__main__':unittest.main()
