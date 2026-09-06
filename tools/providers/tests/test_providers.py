import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.providers import service
from tools.providers.common import path, read_json, write_json, create_approval, consume_approval, digest, public_https, reject_secrets, download
from tools.providers.meshy import adapter as meshy
from tools.providers.higgsfield import adapter as higgsfield

class ProviderTests(unittest.TestCase):
    def request(self, **changes):
        request = {'name': 'unit_test_asset', 'asset_type': 'organic', 'operation': 'generate_3d', 'provider': 'meshy', 'prompt': 'Original creature'}
        request.update(changes)
        return request

    def test_auto_never_defaults_mechanical_to_paid(self):
        name, reason = service.select_provider(self.request(provider='auto', asset_type='spacecraft'))
        self.assertEqual(name, 'blender')
        self.assertIn('no paid fallback', reason)

    def test_unsupported_provider_and_capability(self):
        with self.assertRaises(ValueError): service.adapter('tripo')
        with self.assertRaises(ValueError): service.prepare(self.request(provider='meshy', operation='generate_video'))

    def test_offline_planning_without_credentials(self):
        with patch.dict(os.environ, {}, clear=True), patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('Network forbidden')):
            directory, plan = service.prepare(self.request())
            self.assertFalse(meshy.configured()['api_key_present'])
            self.assertEqual(plan['cost']['amount'], 20)
            self.assertEqual(plan['request']['body']['mode'], 'preview')
            self.assertFalse(plan['automatic_followup_paid_tasks'])

    def test_meshy_image_and_multi_image(self):
        one = meshy.build(self.request(source_images=['https://example.com/front.png']))
        two = meshy.build(self.request(source_images=['https://example.com/front.png', 'https://example.com/side.png']))
        self.assertTrue(one['route'].endswith('/image-to-3d'))
        self.assertTrue(two['route'].endswith('/multi-image-to-3d'))
        self.assertTrue(two['body']['enable_pbr'])
        self.assertEqual(two['cost']['amount'], 30)
        with self.assertRaises(ValueError): meshy.build(self.request(source_images=['https://example.com/a.png'] * 5))

    def test_meshy_specialized_operations(self):
        for operation, expected in [('remesh', 5), ('retexture', 10), ('rig', 5)]:
            built = meshy.build(self.request(operation=operation, asset_type='humanoid', options={'input_task_id': 'known-task'}))
            self.assertEqual(built['cost']['amount'], expected)
        animation = meshy.build(self.request(operation='animate', options={'rig_task_id': 'known-rig', 'action_id': 92}))
        self.assertEqual(animation['route'], '/openapi/v1/animations')
        refine = meshy.build(self.request(method='refine', options={'input_task_id': 'known-preview'}))
        self.assertEqual(refine['body']['mode'], 'refine')
        with self.assertRaises(ValueError): meshy.build(self.request(operation='rig', asset_type='spacecraft', options={'input_task_id': 'known'}))

    def test_higgsfield_documented_cli_models(self):
        self.assertEqual(higgsfield.build(self.request(provider='higgsfield'))['model'], 'tripo_3d')
        self.assertEqual(higgsfield.build(self.request(operation='generate_image'))['model'], 'nano_banana_2')
        self.assertEqual(higgsfield.build(self.request(operation='generate_video'))['model'], 'seedance_2_0')
        with patch('shutil.which', return_value=None):
            self.assertFalse(higgsfield.configured()['cli_available'])

    def test_approval_required_before_any_submission(self):
        directory, _ = service.prepare(self.request())
        with patch.object(meshy, 'submit', side_effect=AssertionError('Must not submit')):
            with self.assertRaisesRegex(ValueError, 'approval'):
                service.execute(str(directory))

    def test_bound_approval_single_submission_and_task_tracking(self):
        directory, plan = service.prepare(self.request())
        receipt = 'generated/approvals/test-' + uuid.uuid4().hex + '.json'
        create_approval(plan, receipt, 'UNIT TEST ONLY — not a real generation approval', 20, 'credits')
        with patch.object(meshy, 'headers', return_value={}), patch.object(meshy, 'submit', return_value='mock-task-id') as submit:
            state = service.execute(str(directory), receipt)
            self.assertEqual(state['task_id'], 'mock-task-id')
            with self.assertRaises(FileExistsError): service.execute(str(directory), receipt)
            self.assertEqual(submit.call_count, 1)
        with patch.object(meshy, 'status', return_value={'status': 'SUCCEEDED', 'consumed_credits': 20, 'model_urls': {}}):
            service.poll(str(directory))
        self.assertEqual(read_json(directory / 'state.json')['consumed_credits'], 20)

    def test_changed_plan_and_under_budget_rejected(self):
        directory, plan = service.prepare(self.request())
        receipt = 'generated/approvals/test-' + uuid.uuid4().hex + '.json'
        with self.assertRaises(ValueError): create_approval(plan, receipt, 'UNIT TEST', 1, 'credits')
        create_approval(plan, receipt, 'UNIT TEST', 20, 'credits')
        changed = copy.deepcopy(plan)
        changed['request']['body']['prompt'] = 'Different operation'
        with self.assertRaises(ValueError): consume_approval(changed, receipt, directory)

    def test_uncertain_submission_is_not_retried(self):
        directory, plan = service.prepare(self.request())
        receipt = 'generated/approvals/test-' + uuid.uuid4().hex + '.json'
        create_approval(plan, receipt, 'UNIT TEST', 20, 'credits')
        with patch.object(meshy, 'headers', return_value={}), patch.object(meshy, 'submit', side_effect=TimeoutError('mock timeout')) as submit:
            with self.assertRaises(TimeoutError): service.execute(str(directory), receipt)
            with self.assertRaises(FileExistsError): service.execute(str(directory), receipt)
            self.assertEqual(submit.call_count, 1)
        self.assertIn('UNKNOWN', read_json(directory / 'state.json')['status'])

    def test_secret_and_media_protection(self):
        with self.assertRaises(ValueError): reject_secrets({'api_key': 'unit-test-placeholder'})
        with self.assertRaises(ValueError): public_https('https://127.0.0.1/internal')
        with self.assertRaises(ValueError): public_https('http://example.com/a.glb')
        with self.assertRaises(ValueError): path('../outside')

    def test_missing_credentials_block_before_submission(self):
        directory, plan = service.prepare(self.request())
        receipt = 'generated/approvals/test-' + uuid.uuid4().hex + '.json'
        create_approval(plan, receipt, 'UNIT TEST ONLY', 20, 'credits')
        with patch.dict(os.environ, {}, clear=True), patch.object(meshy, 'submit', side_effect=AssertionError('No submit')):
            with self.assertRaisesRegex(ValueError, 'MESHY_API_KEY'): service.execute(str(directory), receipt)
        self.assertFalse((directory / 'submission.lock').exists())
        directory, plan = service.prepare(self.request(provider='higgsfield'))
        with patch('shutil.which', return_value=None), patch.object(higgsfield, 'submit', side_effect=AssertionError('No submit')):
            with self.assertRaisesRegex(ValueError, 'not installed'): service.execute(str(directory), receipt)

    def test_quality_and_available_provider_selection(self):
        req = self.request(provider='auto', quality='hero', complexity='high', cost_policy='consider_paid', asset_type='spacecraft')
        with patch.object(meshy, 'configured', return_value={'api_key_present': False}), patch.object(higgsfield, 'configured', return_value={'cli_available': True}):
            directory, plan = service.prepare(req)
            self.assertEqual(plan['provider'], 'higgsfield')
            self.assertGreater(plan['asset']['cleanup']['lod_ratio'], 0)
            self.assertTrue(plan['paid'])
        with self.assertRaises(ValueError): service.prepare(self.request(quality='ultra_unbounded'))
        with self.assertRaises(ValueError): service.prepare(self.request(quality='hero', cleanup={'lod_ratio': 0}))

    def test_image_edit_and_changed_reference(self):
        file = path('generated/provider-fixtures/unit-reference.png')
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b'unit-test-image')
        req = self.request(provider='higgsfield', operation='edit_image', source_images=[file.relative_to(service.ROOT).as_posix()])
        directory, plan = service.prepare(req)
        self.assertIn('--image', plan['request']['arguments'])
        file.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed'): service.execute(str(directory))

    def test_multiview_manifest_archives_references(self):
        file = path('generated/provider-fixtures/reference-provenance.png')
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b'unit-test-reference')
        name = 'unit_reference_' + uuid.uuid4().hex[:8]
        directory, plan = service.prepare(self.request(name=name, reference_views={'front': file.relative_to(service.ROOT).as_posix()}))
        self.assertEqual(plan['request']['method'], 'image')
        record = service.manifest(plan, file)
        self.assertEqual(path(record['reference_images'][0]['path']).read_bytes(), file.read_bytes())
        self.assertEqual(record['quality_tier'], 'standard')

    def test_download_glb_guard_and_fetch_handoff(self):
        binary = path('game/assets/models/provider_cleanup_probe.glb').read_bytes()
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value = binary
        destination = path('generated/provider-fixtures/mock-download.glb')
        with patch('tools.providers.common.public_https'), patch('tools.providers.common.build_opener', return_value=opener):
            self.assertEqual(download('https://example.com/model.glb', destination).read_bytes(), binary)
            opener.open.return_value.__enter__.return_value.read.return_value = b'<html>not a model</html>'
            with self.assertRaisesRegex(ValueError, 'Expected GLB'): download('https://example.com/model.glb', destination)
        directory, plan = service.prepare(self.request())
        response = {'status': 'SUCCEEDED', 'model_urls': {'glb': 'https://example.com/model.glb'}}
        with patch.object(service, 'poll', return_value=response), patch.object(service, 'download', return_value=destination), patch.object(service, 'process_model', return_value={'status': 'MOCK_CLEANUP'}) as process:
            self.assertEqual(service.fetch(str(directory))['status'], 'MOCK_CLEANUP')
            process.assert_called_once_with(plan, destination)

    def test_higgsfield_cli_bridge_without_spending(self):
        _, plan = service.prepare(self.request(provider='higgsfield'))
        runner = MagicMock(return_value=json.dumps({'id': 'mock-job'}))
        with patch.object(higgsfield, 'executable', return_value='mock-higgsfield'):
            self.assertEqual(higgsfield.submit(plan, runner), 'mock-job')
            self.assertEqual(runner.call_args.args[0][1:4], ['generate', 'create', 'tripo_3d'])
            self.assertNotIn('--wait', runner.call_args.args[0])
            runner.return_value = json.dumps({'status': 'completed'})
            self.assertEqual(higgsfield.status(plan, 'mock-job', runner)['status'], 'completed')

if __name__ == '__main__':
    unittest.main()
