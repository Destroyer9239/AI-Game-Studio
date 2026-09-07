"""Build a selectively mapped, periodic concrete material with Pillow/NumPy.

Run with the configured Comfy portable Python. No model or package installation.
AI color is appearance only; relief is an explicitly authored periodic signal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def periodic_color(array, band=256):
    """Smoothly reconcile opposite edge bands; exact edge equality is testable."""
    result = array.astype(np.float32).copy()
    for axis in (0, 1):
        view = np.swapaxes(result, 0, axis)
        for i in range(band):
            weight = 0.5 * (1 + np.cos(np.pi * i / band))
            average = (view[i] + view[-1-i]) * .5
            view[i] = view[i] * (1-weight) + average * weight
            view[-1-i] = view[-1-i] * (1-weight) + average * weight
    return np.clip(result, 0, 255).astype(np.uint8)


def build(source, destination, size=4096, include_height=False):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_relative_to(ROOT) or not destination.is_relative_to(ROOT):
        raise ValueError('Material paths must remain in project')
    original = Image.open(source).convert('RGB')
    if original.size != (size, size):
        raise ValueError('Expected a square, already upscaled source; no silent resize')
    # Crop the inner panel before upscale in future requests; this demonstration
    # retains generated seams as color only, never inventing seam depth.
    color = periodic_color(np.asarray(original), max(8, size // 16))
    destination.mkdir(parents=True, exist_ok=True)
    prefix = destination.name
    files = {}
    def save(role, data):
        target = destination / f'{prefix}_{role}.png'
        Image.fromarray(data).save(target, optimize=True)
        files[role] = {'path': target.relative_to(ROOT).as_posix(),
                       'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                       'resolution': [size, size]}
    save('basecolor', color)
    # Periodic artist-authored 0.15 mm relief, unrelated to image luminance.
    phase = np.linspace(0, 2*np.pi, size, dtype=np.float32)
    height = (.5 + .25*np.sin(phase[None, :]*37)*np.sin(phase[:, None]*41)
              + .125*np.cos(phase[None, :]*83 + phase[:, None]*71))
    height[-1, :] = height[0, :]
    height[:, -1] = height[:, 0]
    dx = (np.roll(height, -1, 1)-np.roll(height, 1, 1))*.00015/(4/size)
    dy = (np.roll(height, -1, 0)-np.roll(height, 1, 0))*.00015/(4/size)
    normal = np.stack((-dx, dy, np.ones_like(height)), axis=2)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    normal = np.round((normal*.5+.5)*255).astype(np.uint8)
    normal[-1, :] = normal[0, :]
    normal[:, -1] = normal[:, 0]
    save('normal', normal)
    if include_height:
        save('height', np.round(height*65535).astype(np.uint16))
    save('roughness', np.full((size,size), round(.82*255), dtype=np.uint8))
    preview = Image.new('RGB', (1536,1536))
    tile = Image.fromarray(color).resize((512,512))
    for y in range(3):
        for x in range(3):
            preview.paste(tile,(512*x,512*y))
    preview.save(destination/'tiling_preview.png')
    report = {'schema_version':1, 'id':prefix, 'category':'concrete/weathered',
              'source':source.relative_to(ROOT).as_posix(),
              'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'maps':files, 'metallic':0, 'roughness':.82, 'tile_meters':2,
              'normal_convention':'OpenGL +Y tangent space',
              'relief':'Authored periodic microrelief, 0.15 mm range; not inferred physical geometry',
              'omitted_maps':{'ao':'No geometry bake', 'metallic':'Dielectric constant 0', 'emission':'Non-emissive'},
              'color_processing':'256 px smooth opposite-edge reconciliation; generated panel joints remain color only',
              'review':'Pending visual tiled and Godot review',
              'source_provenance':'generated/manifests/industrial_concrete_4k.json'}
    (destination/'material.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    validate(destination)
    print('MATERIAL_FACTORY_PASS: '+str(destination))
    return report


def validate(destination):
    destination = Path(destination)
    package = json.loads((destination/'material.json').read_text())
    for role, record in package['maps'].items():
        target = ROOT/record['path']
        if hashlib.sha256(target.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Material hash mismatch: '+role)
        with Image.open(target) as image:
            pixels = np.asarray(image)
            if list(image.size) != record['resolution']:
                raise ValueError('Material resolution mismatch')
        if not np.array_equal(pixels[0],pixels[-1]) or not np.array_equal(pixels[:,0],pixels[:,-1]):
            raise ValueError('Opposite texture edges differ: '+role)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source')
    parser.add_argument('--destination',default='game/assets/textures/industrial_concrete')
    parser.add_argument('--validate',action='store_true')
    parser.add_argument('--height',action='store_true',help='Optional 16-bit source map; not used by the current GLB')
    args = parser.parse_args()
    if args.validate:
        validate(ROOT/args.destination)
        print('MATERIAL_VALIDATION_PASS')
    else:
        build(ROOT/args.source,ROOT/args.destination,include_height=args.height)
