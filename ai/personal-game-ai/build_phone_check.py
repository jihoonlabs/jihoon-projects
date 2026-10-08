"""Build a self-contained offline check.pyz without copying user artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    sources = {name: (base / name).read_bytes() for name in
               ("request_intake.py", "test_phone_intake.py", "phone_runner.py")}
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sources.items()}
    # Exclusive creation prevents accidental replacement of an existing bundle.
    with args.output.open("xb") as stream, zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sources.items():
            archive.writestr("__main__.py" if name == "phone_runner.py" else name, data)
        archive.writestr("manifest.json", json.dumps(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
