"""Offline tests only; no model, server or image inference is involved."""
import copy
import json
import unittest
from submit_image import ROOT, build_workflow, project_path


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((ROOT / "tools/imagegen/requests/test_fighter_concept.json").read_text())

    def test_typed_parameters_and_links(self):
        workflow = build_workflow(self.request)
        self.assertEqual(workflow["4"]["inputs"]["width"], 1024)
        self.assertEqual(workflow["5"]["inputs"]["seed"], 94721)
        self.assertEqual(workflow["5"]["inputs"]["model"], ["1", 0])
        self.assertEqual(workflow["2"]["inputs"]["text"], self.request["prompt"])

    def test_path_escape(self):
        with self.assertRaises(ValueError):
            project_path("../outside.json")

    def test_request_constraints(self):
        for key, value in [("width", 999), ("height", 4096), ("seed", -1),
                           ("asset", "../bad"), ("kind", "unknown"),
                           ("tileable_required", True), ("alpha_required", True)]:
            with self.subTest(key=key):
                request = copy.deepcopy(self.request)
                request[key] = value
                with self.assertRaises(ValueError):
                    build_workflow(request)


if __name__ == "__main__":
    unittest.main()
