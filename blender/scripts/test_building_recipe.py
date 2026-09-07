"""Recipe regression: determinism, batching, integration contracts, archetypes.

Runs entirely on the throwaway `unit_building_recipe` id so accepted building
sources and manifests are never rewritten by a test run.
"""
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_building import build, validate, ROOT

CHECKS = 0
# Named modules other systems bind to; batching must never absorb them.
CONTRACTS = ['Foundation', 'Structural_Shell', 'Entrance_Glass', 'Entrance_Canopy',
             'Entrance_Light', 'Roof_Parapet', 'Building-colonly']
MATERIALS = {'Warm_Mineral_Facade', 'Charcoal_Trim', 'Blue_Glazing', 'Warm_Window_Light',
             'Cyan_Wayfinding', 'Foundation', 'Painted_Accent'}


def check(value, label):
    global CHECKS
    CHECKS += 1
    if not value:
        raise AssertionError(label)


def scene_inventory():
    """Deterministic fingerprint of the built scene, after batching and joins."""
    rows = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        rows.append((
            obj.name,
            len(obj.data.vertices),
            len(obj.data.polygons),
            tuple(m.name for m in obj.data.materials),
            tuple(round(v, 5) for v in obj.location),
            tuple(round(v, 5) for v in obj.dimensions),
            len(obj.data.uv_layers),
        ))
    rows.sort()
    return rows


def run(spec):
    build(spec)
    manifest = json.loads((ROOT / f"generated/manifests/{spec['id']}_recipe.json").read_text())
    return manifest, scene_inventory()


base = json.loads((ROOT / 'tools/world/foundry_building.json').read_text())
base['id'] = 'unit_building_recipe'

# --- deterministic recipe and geometry -------------------------------------
first, first_scene = run(base)
second, second_scene = run(base)
check(first['recipe_sha256'] == second['recipe_sha256'], 'recipe hash is deterministic')
check(first_scene == second_scene, 'batched geometry is deterministic')
check(len([p for p in second['placements'] if p['name'] == 'Entrance_Glass']) == 1, 'single entrance')
check(next(p for p in second['placements'] if p['name'] == 'Entrance_Glass')['position'][0] == 0, 'entrance is centred')

# --- integration contracts survive material batching -----------------------
names = [row[0] for row in second_scene]
for contract in CONTRACTS:
    check(contract in names, 'integration contract preserved: ' + contract)
collision = bpy.context.scene.objects['Building-colonly']
check(collision.hide_render, 'collision proxy stays out of renders')
check(collision.dimensions.z >= base['floors'] * 3.2, 'collision proxy covers the full shell')

batches = [name for name in names if name.startswith('Batch_')]
check(batches, 'material batching produced joined modules')
for name in batches:
    check(name[len('Batch_'):] in MATERIALS, 'batch is named after an authored material: ' + name)
check(len(names) < len(second['placements']) / 3, 'batching collapses modules into few objects')
for row in second_scene:
    check(len(row[3]) == 1, 'every object keeps exactly one material slot: ' + row[0])
    check(row[3][0] in MATERIALS, 'authored material naming preserved: ' + str(row[3]))
    check(row[6] == 1, 'every object carries its planar UV layer: ' + row[0])
    check(row[1] > 0 and row[2] > 0, 'no empty mesh survives batching: ' + row[0])

# --- planar UV projection keeps the declared two-metre repeat --------------
shell = bpy.context.scene.objects['Structural_Shell']
uvs = [tuple(loop.uv) for loop in shell.data.uv_layers.active.data]
check(all(all(abs(v) < 1e4 for v in uv) for uv in uvs), 'shell UVs are finite')
span = max(u for u, _ in uvs) - min(u for u, _ in uvs)
check(abs(span - base['footprint'][0] / 2) < .01, 'shell UV span matches a two-metre repeat')

# --- seed and quality still change the recipe ------------------------------
changed = dict(base, seed=base['seed'] + 1)
third, _ = run(changed)
check(second['recipe_sha256'] != third['recipe_sha256'], 'seed changes the recipe')
distant, distant_scene = run(dict(changed, quality='DISTANT'))
check(len(distant['placements']) < len(second['placements']) / 4, 'DISTANT recipe is far cheaper')
check(len(distant_scene) <= len(second_scene), 'DISTANT recipe never adds objects')

# --- the three shipped architectural styles --------------------------------
signatures = {'foundry_building': 'Exhaust_Stack', 'market_building': 'Store_Awning', 'relay_building': 'Vertical_Sun_Fin'}
for asset, signature in signatures.items():
    spec = json.loads((ROOT / f'tools/world/{asset}.json').read_text())
    spec['id'] = 'unit_building_recipe'
    style, style_scene = run(spec)
    repeat, repeat_scene = run(spec)
    check(style['recipe_sha256'] == repeat['recipe_sha256'], asset + ' recipe is deterministic')
    check(style_scene == repeat_scene, asset + ' batched geometry is deterministic')
    placed = [p['name'] for p in style['placements']]
    check(any(name.startswith(signature) for name in placed), asset + ' keeps its ' + signature + ' silhouette')
    check('Entrance_Glass' in placed, asset + ' keeps a reachable entrance module')
    check(style['navigation_hooks']['front_entrance'][1] > 0, asset + ' publishes a front entrance hook')
    other = [s for a, s in signatures.items() if a != asset]
    check(not any(name.startswith(tuple(other)) for name in placed), asset + ' does not borrow another style')

# --- specification validation ----------------------------------------------
for key, value in [('id', '../unsafe'), ('floors', 100), ('archetype', 'unknown'),
                   ('quality', 'MAXIMUM'), ('footprint', [4, 10]), ('footprint', [12, 90])]:
    bad = {**base, key: value}
    try:
        validate(bad)
    except ValueError:
        CHECKS += 1
    else:
        raise AssertionError('Invalid specification accepted: %s=%s' % (key, value))

print('BUILDING_RECIPE_TESTS_PASS: %d checks' % CHECKS)
