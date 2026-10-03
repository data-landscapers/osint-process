"""Run every scripts/tests/test-*.py and report one line each; exit 1 if any fails.

A change to a script any test imports runs this before its commit.

Run: python scripts/tests/run-all.py
"""
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
env = dict(os.environ, PYTHONIOENCODING="utf-8")
failed = []
for t in sorted(HERE.glob("test-*.py")):
    r = subprocess.run([sys.executable, str(t)], cwd=HERE.parents[1], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    print(("ok    " if r.returncode == 0 else "FAIL  ") + t.name)
    if r.returncode != 0:
        failed.append(t.name)
        print("\n".join("      " + l for l in (r.stdout + r.stderr).strip().splitlines()[-8:]))
print(f"\n{len(failed)} of {len(list(HERE.glob('test-*.py')))} failed")
sys.exit(1 if failed else 0)
