"""Technical acceptance for the authored hero surface set.

Checks the properties a tiling PBR surface must have to be usable: declared
resolution, periodic wrap, unit-length tangent-space normals, declared value
ranges and truthful provenance. Artistic quality is reviewed separately.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[2]
SURFACES = ROOT / 'game/assets/textures/hero_surfaces'
# name -> accepted Pillow modes for that role
MAPS = {'normal': ('RGB',), 'roughness': ('L', 'RGB'), 'aggregate': ('L', 'RGB')}
METADATA_FIELDS = {
    'source': str, 'seed': int, 'resolution': int, 'repeat_m': (int, float),
    'height_amplitude_m': (int, float), 'normal': str, 'roughness': str,
    'maps': str, 'credits': int,
}


def read_map(directory, name):
    """Return one surface map as float 0..1 with a trailing channel axis."""
    path = Path(directory) / (name + '.png')
    if not path.is_file():
        raise FileNotFoundError('Missing surface map: ' + str(path))
    with Image.open(path) as image:
        image.load()
        if image.format != 'PNG':
            raise ValueError('%s is %s, not PNG' % (path.name, image.format))
        if image.mode not in MAPS[name]:
            raise ValueError('%s uses unsupported mode %s' % (path.name, image.mode))
        data = np.asarray(image, dtype=np.float64) / 255.0
    return data if data.ndim == 3 else data[:, :, None]


def read_metadata(directory):
    """Return validated provenance metadata for a surface set."""
    path = Path(directory) / 'material.json'
    if not path.is_file():
        raise FileNotFoundError('Missing provenance: ' + str(path))
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise TypeError('material.json must hold an object')
    for field, kind in METADATA_FIELDS.items():
        if field not in data:
            raise KeyError('material.json is missing ' + field)
        if isinstance(data[field], bool) or not isinstance(data[field], kind):
            raise TypeError('material.json field %s has the wrong type' % field)
    if data['resolution'] < 1 or data['repeat_m'] <= 0 or data['height_amplitude_m'] <= 0:
        raise ValueError('material.json declares a non-physical surface')
    if data['credits'] != 0:
        raise ValueError('Hero surfaces must record zero external credits')
    return data


def declared_range(text):
    """Pull the low/high pair out of a declared range such as 'authored .63-.87'."""
    numbers = [float(part) for part in text.replace('-', ' ').split() if part.replace('.', '', 1).isdigit()]
    if len(numbers) != 2:
        raise ValueError('Roughness provenance must declare a low-high range: ' + text)
    return min(numbers), max(numbers)


def wrap_step(channel):
    """Largest value step across the tiling seam, per axis."""
    return max(np.abs(channel[-2] - channel[0]).max(), np.abs(channel[:, -2] - channel[:, 0]).max())


def interior_step(channel):
    """Largest neighbouring value step inside the map, per axis."""
    return max(np.abs(np.diff(channel, axis=0)).max(), np.abs(np.diff(channel, axis=1)).max())


class HeroSurfaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = read_metadata(SURFACES)
        cls.maps = {name: read_map(SURFACES, name) for name in MAPS}

    def test_declared_resolution(self):
        size = self.metadata['resolution']
        self.assertEqual(size, 1024)
        for name, data in self.maps.items():
            self.assertEqual(data.shape[:2], (size, size), name)

    def test_import_records_exist(self):
        for name in MAPS:
            record = SURFACES / (name + '.png.import')
            self.assertTrue(record.is_file(), record)
            self.assertIn('hero_surfaces/%s.png' % name, record.read_text())

    def test_periodic_edges(self):
        for name, data in self.maps.items():
            self.assertTrue(np.array_equal(data[0], data[-1]), name + ' row wrap')
            self.assertTrue(np.array_equal(data[:, 0], data[:, -1]), name + ' column wrap')

    def test_seam_is_continuous(self):
        # A duplicated edge alone does not prove tiling: the step across the
        # wrap must be no larger than the largest step inside the map.
        for name, data in self.maps.items():
            for channel in range(data.shape[2]):
                plane = data[:, :, channel]
                self.assertLessEqual(wrap_step(plane), interior_step(plane) + 1e-9,
                                     '%s channel %d discontinuous across the seam' % (name, channel))

    def test_normal_vectors_are_unit_length(self):
        vectors = self.maps['normal'] * 2 - 1
        lengths = np.linalg.norm(vectors, axis=2)
        self.assertLess(np.max(np.abs(lengths - 1)), .015, 'normal magnitudes drift from unit length')

    def test_normal_is_tangent_space(self):
        vectors = self.maps['normal'] * 2 - 1
        self.assertGreater(vectors[:, :, 2].min(), .5, 'normal Z must stay outward in tangent space')
        self.assertEqual(self.metadata['normal'], 'OpenGL')

    def test_normal_slope_matches_declared_amplitude(self):
        # Slope implied by the map must be reachable from the declared
        # microrelief height over one declared texture repeat.
        vectors = self.maps['normal'] * 2 - 1
        slope = np.hypot(vectors[:, :, 0], vectors[:, :, 1]) / np.maximum(vectors[:, :, 2], 1e-9)
        texel_m = self.metadata['repeat_m'] / self.metadata['resolution']
        self.assertLessEqual(slope.max(), 2 * self.metadata['height_amplitude_m'] / texel_m,
                             'normals imply more relief than the declared height amplitude')

    def test_roughness_within_declared_range(self):
        low, high = declared_range(self.metadata['roughness'])
        values = self.maps['roughness']
        self.assertGreaterEqual(values.min(), low - 1 / 255)
        self.assertLessEqual(values.max(), high + 1 / 255)

    def test_data_maps_are_single_channel(self):
        # Roughness and the aggregate tint field carry data, not colour.
        for name in ('roughness', 'aggregate'):
            data = self.maps[name]
            for channel in range(1, data.shape[2]):
                self.assertTrue(np.array_equal(data[:, :, 0], data[:, :, channel]), name + ' is not greyscale')

    def test_provenance(self):
        self.assertEqual(self.metadata['height_amplitude_m'], .00012)
        self.assertEqual(self.metadata['repeat_m'], 2)
        self.assertEqual(self.metadata['seed'], 7182)
        self.assertEqual(self.metadata['credits'], 0)
        self.assertIn('original', self.metadata['source'])


class SurfaceValidatorRejections(unittest.TestCase):
    """The loaders must fail loudly on the ways a surface set can be broken."""

    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix='hero_surface_'))
        for name in MAPS:
            shutil.copy(SURFACES / (name + '.png'), self.directory / (name + '.png'))
        shutil.copy(SURFACES / 'material.json', self.directory / 'material.json')
        self.addCleanup(shutil.rmtree, self.directory, True)

    def write_metadata(self, mutate):
        data = json.loads((self.directory / 'material.json').read_text())
        mutate(data)
        (self.directory / 'material.json').write_text(json.dumps(data))

    def test_valid_copy_is_accepted(self):
        read_metadata(self.directory)
        for name in MAPS:
            read_map(self.directory, name)

    def test_missing_map_rejected(self):
        (self.directory / 'normal.png').unlink()
        with self.assertRaises(FileNotFoundError):
            read_map(self.directory, 'normal')

    def test_missing_metadata_rejected(self):
        (self.directory / 'material.json').unlink()
        with self.assertRaises(FileNotFoundError):
            read_metadata(self.directory)

    def test_non_image_payload_rejected(self):
        (self.directory / 'normal.png').write_bytes(b'not an image at all')
        with self.assertRaises(UnidentifiedImageError):
            read_map(self.directory, 'normal')

    def test_wrong_image_format_rejected(self):
        with Image.open(SURFACES / 'normal.png') as image:
            image.convert('RGB').save(self.directory / 'normal.png', format='BMP')
        with self.assertRaises(ValueError):
            read_map(self.directory, 'normal')

    def test_wrong_channel_layout_rejected(self):
        with Image.open(SURFACES / 'normal.png') as image:
            image.convert('L').save(self.directory / 'normal.png', format='PNG')
        with self.assertRaises(ValueError):
            read_map(self.directory, 'normal')

    def test_malformed_json_rejected(self):
        (self.directory / 'material.json').write_text('{ this is not json')
        with self.assertRaises(json.JSONDecodeError):
            read_metadata(self.directory)

    def test_missing_metadata_field_rejected(self):
        self.write_metadata(lambda data: data.pop('height_amplitude_m'))
        with self.assertRaises(KeyError):
            read_metadata(self.directory)

    def test_wrong_metadata_type_rejected(self):
        self.write_metadata(lambda data: data.update(resolution='1024'))
        with self.assertRaises(TypeError):
            read_metadata(self.directory)

    def test_non_physical_metadata_rejected(self):
        self.write_metadata(lambda data: data.update(repeat_m=0))
        with self.assertRaises(ValueError):
            read_metadata(self.directory)

    def test_recorded_external_credits_rejected(self):
        self.write_metadata(lambda data: data.update(credits=3))
        with self.assertRaises(ValueError):
            read_metadata(self.directory)


if __name__ == '__main__':
    unittest.main(verbosity=2)
