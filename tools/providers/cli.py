"""Provider command interface. Planning/configuration are offline by default."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.providers import service
from tools.providers.common import path, read_json, create_approval, sanitized

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('providers', 'status', 'plan', 'create', 'process', 'execute', 'approve', 'poll', 'fetch', 'balance', 'usage', 'quote', 'validate', 'preview', 'launch', 'multiview'))
    parser.add_argument('--request')
    parser.add_argument('--provider', default='auto')
    parser.add_argument('--job')
    parser.add_argument('--approval')
    parser.add_argument('--user-reference')
    parser.add_argument('--max-cost', type=float)
    parser.add_argument('--unit', default='credits')
    parser.add_argument('--wait', type=int, default=0)
    parser.add_argument('--quality', choices=tuple(service.registry_quality()))
    parser.add_argument('--asset')
    parser.add_argument('--source')
    parser.add_argument('--repair', action='store_true')
    args = parser.parse_args()
    if args.action in ('providers', 'status'):
        result = service.registry()
        for name in ('meshy', 'higgsfield', 'comfyui'):
            result['providers'][name]['configuration'] = service.adapter(name).configured()
        if args.action == 'status':
            result['providers']['comfyui']['health'] = service.adapter('comfyui').health()
    elif args.action in ('plan', 'create', 'multiview'):
        request = read_json(path(args.request))
        if args.provider != 'auto':
            request['provider'] = args.provider
        if args.quality:
            request['quality'] = args.quality
        if args.action == 'multiview':
            from tools.providers.multiview import scaffold
            result = scaffold(request)
        else:
            directory, plan = service.prepare(request)
            result = {'job': str(directory.relative_to(service.ROOT)).replace('\\', '/'), 'plan': sanitized(plan)}
            if args.action == 'create' and not plan['paid']:
                result['result'] = service.execute(str(directory))
            elif args.action == 'create':
                result['status'] = 'AWAITING_EXPLICIT_PAID_APPROVAL'
    elif args.action == 'process':
        _, plan = service.load_plan(args.job)
        service.check_inputs(plan)
        result = service.process_model(plan, path(args.source or plan['asset']['source_file']), repair=args.repair)
    elif args.action in ('validate', 'preview', 'launch'):
        from tools.providers.common import asset_id
        if args.action == 'validate' and not args.asset:
            result = {'output': service.studio('validate', 'test_fighter')}
        else:
            name = asset_id(args.asset or 'test_fighter')
            result = {'output': service.studio('test-asset' if args.action == 'validate' else args.action, name)}
    elif args.action == 'execute':
        result = service.execute(args.job, args.approval)
    elif args.action == 'approve':
        if not args.user_reference or args.max_cost is None or not args.approval:
            raise ValueError('Record an actual explicit user approval reference, cost ceiling and ignored receipt path')
        _, plan = service.load_plan(args.job)
        create_approval(plan, args.approval, args.user_reference, args.max_cost, args.unit)
        result = {'status': 'APPROVAL_RECORDED', 'note': 'This command may only be called after explicit user authorization for the displayed plan.'}
    elif args.action == 'poll':
        if not 0 <= args.wait <= 300:
            raise ValueError('Poll wait must be 0–300 seconds')
        result = service.poll(args.job, args.wait)
    elif args.action == 'fetch':
        result = service.fetch(args.job)
    elif args.action == 'quote':
        _, plan = service.load_plan(args.job)
        result = service.adapter('higgsfield').quote(plan) if plan['provider'] == 'higgsfield' else plan['cost']
    else:
        if args.provider != 'meshy':
            raise ValueError('Balance/usage currently implemented only for Meshy')
        result = getattr(service.adapter('meshy'), args.action)()
    print(json.dumps(sanitized(result), indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'FAIL', 'error': sanitized(str(error))}))
        sys.exit(1)
