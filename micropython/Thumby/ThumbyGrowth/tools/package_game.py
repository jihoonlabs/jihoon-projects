"""Build the device package; no Ollama, Docker or third-party modules needed."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def build(output):
    game = Path(__file__).resolve().parents[1]
    output = Path(output).resolve()
    files = {name: (game / name).read_bytes()
             for name in ('ThumbyGrowth.py', 'rules.py', 'README.txt')}
    for name in ('ThumbyGrowth.py', 'rules.py'):
        compile(files[name], name, 'exec')
    files['BUILD.json'] = (json.dumps({
        'game': 'ThumbyGrowth', 'device_directory': '/Games/ThumbyGrowth',
        'source_sha256': {name: hashlib.sha256(data).hexdigest()
                          for name, data in files.items()},
    }, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents an old downloaded release being overwritten.
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo('ThumbyGrowth/'+name, (2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ThumbyGrowth device ZIP')
    parser.add_argument('--output', type=Path, required=True)
    print(build(parser.parse_args().output))
