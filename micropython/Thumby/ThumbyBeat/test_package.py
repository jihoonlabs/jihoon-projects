import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
import package_game  # noqa: E402


class TestPackage(unittest.TestCase):
    def test_zip_has_only_device_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = package_game.build(Path(tmp) / 'ThumbyBeat.zip')
            with zipfile.ZipFile(out) as archive:
                names = sorted(archive.namelist())
                build = json.loads(archive.read('ThumbyBeat/BUILD.json'))
        import charts
        songs = ['ThumbyBeat/%s.py' % meta[0] for meta in charts.META]
        expect = ['ThumbyBeat/BUILD.json', 'ThumbyBeat/ThumbyBeat.py',
                  'ThumbyBeat/charts.py', 'ThumbyBeat/pat.py',
                  'ThumbyBeat/rules.py'] + songs
        self.assertEqual(names, sorted(expect))
        self.assertNotIn('ThumbyBeat/fake_thumby.py', names)
        self.assertEqual(build['device_directory'], '/Games/ThumbyBeat')


if __name__ == '__main__':
    unittest.main()
