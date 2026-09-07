import copy,json,unittest
from pathlib import Path
from multiview_gate import evaluate,ROOT
class GateTests(unittest.TestCase):
    def setUp(self):
        self.package=json.loads((ROOT/'generated/references/canonical_fighter/package.json').read_text())
        self.review=json.loads((ROOT/'generated/references/canonical_fighter/visual_review.json').read_text())
    def test_reviewed_canonical_pass(self): self.assertEqual(evaluate(self.package,self.review)['status'],'PASS')
    def test_missing_review(self): self.assertEqual(evaluate(self.package)['status'],'NEEDS_REGENERATION')
    def test_contradiction(self):
        self.package['views']['front']['geometry_sha256']='different'
        self.assertEqual(evaluate(self.package,self.review)['status'],'REJECT')
    def test_markings(self):
        self.package['marking_audit']='UNREVIEWED_IMAGE'
        self.assertEqual(evaluate(self.package,self.review)['status'],'REJECT')
    def test_visual_failure(self):
        self.review['checks']['markings']='REJECT'
        self.assertEqual(evaluate(self.package,self.review)['status'],'REJECT')
if __name__=='__main__':unittest.main()
