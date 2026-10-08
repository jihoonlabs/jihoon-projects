"""Zipapp entry: concise terminal status, detailed unique report in cwd."""
import contextlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest
import uuid
import zipfile

import test_phone_intake


def main():
    log = io.StringIO()
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_phone_intake)
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    with zipfile.ZipFile(sys.argv[0]) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    report = {
        "manifest": manifest, "python": platform.python_version(),
        "tests": result.testsRun, "success": result.wasSuccessful() and result.testsRun > 0,
        "log": log.getvalue(),
    }
    name = "phone_" + uuid.uuid4().hex[:8] + ".json"
    try:
        with Path(name).open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
    except OSError:
        print("ERROR REPORT")
        return 2
    print(("PASS " if report["success"] else "FAIL ") + str(result.testsRun))
    print(name)
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
