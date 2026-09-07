"""Reusable local base-generation -> tiled Real-ESRGAN -> 4K provider workflow."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.providers import service
from tools.providers.common import path, read_json, write_json


def run(request_file):
    request = read_json(path(request_file))
    if request.get('provider') != 'comfyui':
        raise ValueError('High-resolution tool accepts only explicit local ComfyUI requests')
    specification = read_json(path(request['image_request']))
    if specification['width'] != specification['height'] or specification['width'] != 1024:
        raise ValueError('4K square route requires a 1024-square base; compose/pad references explicitly first')
    directory, plan = service.prepare(request)
    source = service.execute(str(directory))
    output_id = specification.get('output_id',specification['asset']+'_4k')
    output = {**specification, 'id':output_id,'mode':'upscale',
              'workflow':'tools/imagegen/workflows/upscale_4k.api.json',
              'source_image':source['original_file'], 'width':4096,'height':4096,
              'upscale_model':'RealESRGAN_x4plus.pth',
              'upscale_source':'https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.1.0',
              'upscale_license':'BSD-3-Clause'}
    destination = directory/'upscale-request.json'
    write_json(destination,output)
    upscale = {**request,'name':output_id,'image_request':destination.relative_to(service.ROOT).as_posix()}
    directory, _ = service.prepare(upscale)
    return service.execute(str(directory))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('request')
    args = parser.parse_args()
    print(json.dumps(run(args.request),indent=2))
