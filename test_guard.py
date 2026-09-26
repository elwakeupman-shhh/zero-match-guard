#!/usr/bin/env python3
"""Self-test. Run: python test_guard.py

The last case is the one nobody writes: feed the checker an input that matches
nothing and assert that it FAILS.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "zero_match_guard.py")
PY = sys.executable


def run(args):
    r = subprocess.run([PY, GUARD] + args, capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        real = os.path.join(d, "a.txt")
        open(real, "w").write("x")

        cases = [
            ("passes when it examined a real file",
             ["--paths", real, "--", PY, "-c", "print('ok')"], 0),
            ("BLOCKS when the glob matched nothing",
             ["--paths", os.path.join(d, "*.mp4"), "--", PY, "-c", "print('ok')"], 3),
            ("BLOCKS when a literal path does not exist",
             ["--paths", os.path.join(d, "nope.txt"), "--", PY, "-c", "print('ok')"], 2),
            ("propagates the check's own failure",
             ["--paths", real, "--", PY, "-c", "import sys; sys.exit(1)"], 1),
            ("BLOCKS when the check reports zero examined",
             ["--count-from", r"scanned: (\d+)", "--",
              PY, "-c", "print('files scanned: 0'); print('PASS')"], 3),
            ("passes when the check reports a real count",
             ["--count-from", r"scanned: (\d+)", "--",
              PY, "-c", "print('files scanned: 3'); print('PASS')"], 0),
        ]
        for name, args, want in cases:
            got, out = run(args)
            ok = got == want
            fails += not ok
            print(f"[{'PASS' if ok else 'FAIL'}] {name} (exit {got}, want {want})")
            if not ok:
                print("        output:", out.strip()[:200])

    print(f"\n{len(cases) - fails}/{len(cases)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
