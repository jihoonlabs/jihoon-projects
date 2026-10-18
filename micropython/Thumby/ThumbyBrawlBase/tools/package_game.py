"""Build a ZIP containing only the files needed on a Thumby device."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


GAME_FILES = ('ThumbyBrawlBase.py', 'campaign.py', 'rules.py', 'scene_art.py')
GAME_NAME = 'ThumbyBrawlBase'


def build(output):
    game = Path(__file__).resolve().parents[1]
    output = Path(output).resolve()
    files = {name: (game / name).read_bytes() for name in GAME_FILES}
    for name in GAME_FILES:
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
            info = zipfile.ZipInfo(GAME_NAME + '/' + name, (2026, 10, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Thumby Brawl Base device ZIP')
    parser.add_argument('--output', type=Path, required=True)
    print(build(parser.parse_args().output))
