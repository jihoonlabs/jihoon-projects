"""Build a ZIP containing only the files needed on a Thumby device."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


BASE_FILES = ('ThumbyBeat.py', 'rules.py', 'charts.py', 'pat.py')
GAME_NAME = 'ThumbyBeat'


def game_files(game):
    # One module per song (s_*.py) is loaded on demand on the device.
    songs = sorted(path.name for path in game.glob('s_*.py'))
    return BASE_FILES + tuple(songs)


def build(output):
    game = Path(__file__).resolve().parents[1]
    output = Path(output).resolve()
    names = game_files(game)
    files = {name: (game / name).read_bytes() for name in names}
    for name in names:
        compile(files[name], name, 'exec')
    files['BUILD.json'] = (json.dumps({
        'game': GAME_NAME,
        'device_directory': '/Games/' + GAME_NAME,
        'source_sha256': {name: hashlib.sha256(data).hexdigest()
                          for name, data in files.items()},
    }, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(GAME_NAME + '/' + name, (2026, 11, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Thumby Beat device ZIP')
    parser.add_argument('--output', type=Path, required=True)
    print(build(parser.parse_args().output))
