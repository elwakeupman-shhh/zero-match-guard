#!/usr/bin/env python3
"""zero-match-guard: make a check that examined nothing fail instead of pass.

A verification step that finds nothing looks exactly like a verification step
that finds nothing wrong. Both print PASS. Both exit 0. Only one of them did
anything.

This wraps any check command and refuses to report success when the check
matched zero inputs.

Exit codes:
    0  check ran, examined >= min-count inputs, and passed
    1  check ran and reported a problem (the check's own failure)
    2  a path given to the check does not exist
    3  the check examined zero inputs (or fewer than --min-count)

No third-party dependencies. Standard library only. Python 3.8+.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

__version__ = "1.0.0"


def expand(patterns):
    """Expand patterns to real files. Returns (files, missing_literals)."""
    files, missing = [], []
    for p in patterns:
        if os.path.isfile(p):
            files.append(p)
            continue
        hits = [h for h in glob.glob(p, recursive=True) if os.path.isfile(h)]
        if hits:
            files.extend(hits)
        elif not glob.has_magic(p):
            # A literal path that does not exist is an error, not an empty match.
            missing.append(p)
    return sorted(set(files)), missing


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="zero-match-guard",
        description="Fail a check that examined nothing, instead of passing it.")
    ap.add_argument("--min-count", type=int, default=1,
                    help="minimum inputs the check must examine (default: 1)")
    ap.add_argument("--count-from", default="",
                    help="regex with one group capturing the count the check "
                         "printed, e.g. 'files scanned: (\\d+)'. When given, the "
                         "count comes from the check's own output instead of "
                         "from the expanded file list.")
    ap.add_argument("--paths", nargs="*", default=[],
                    help="paths or globs the check will examine")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("command", nargs=argparse.REMAINDER,
                    help="-- the check command to run")
    a = ap.parse_args(argv)

    cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
    if not cmd:
        ap.error("no command given (put it after --)")

    files, missing = expand(a.paths)
    if missing:
        print(f"[guard] BLOCK: path does not exist: {', '.join(missing)}",
              file=sys.stderr)
        return 2

    if a.paths and not a.count_from and len(files) < a.min_count:
        print(f"[guard] BLOCK: matched {len(files)} file(s), "
              f"need at least {a.min_count} — refusing to report PASS",
              file=sys.stderr)
        return 3

    r = subprocess.run(cmd, capture_output=True, text=True)
    out = (r.stdout or "") + (r.returncode and (r.stderr or "") or "")
    if not a.quiet:
        sys.stdout.write(r.stdout or "")
        sys.stderr.write(r.stderr or "")

    if a.count_from:
        m = re.search(a.count_from, out)
        if not m:
            print(f"[guard] BLOCK: could not find a count matching "
                  f"{a.count_from!r} in the check output — "
                  f"cannot prove it examined anything", file=sys.stderr)
            return 3
        n = int(m.group(1))
        if n < a.min_count:
            print(f"[guard] BLOCK: the check examined {n} input(s), "
                  f"need at least {a.min_count}", file=sys.stderr)
            return 3
        examined = n
    else:
        examined = len(files)

    if r.returncode != 0:
        print(f"[guard] check failed (exit {r.returncode}) "
              f"after examining {examined} input(s)", file=sys.stderr)
        return 1

    print(f"[guard] PASS — examined {examined} input(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
