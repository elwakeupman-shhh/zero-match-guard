# zero-match-guard

Make a check that examined **nothing** fail, instead of passing.

A verification step that finds nothing looks exactly like a verification step that
finds nothing wrong. Both print `PASS`. Both exit `0`. Only one of them did anything.

```bash
# A scanner given a glob that matches no files:
python zero_match_guard.py --paths "build/*.mp4" -- ./scan.sh build/
# [guard] BLOCK: matched 0 file(s), need at least 1 - refusing to report PASS
# exit 3
```

## Why

This is a real bug shape, not a hypothetical. A scanner expanded
`glob(path + "/**/*")` on arguments that were already files. The expansion
returned nothing, so it scanned zero files, found zero problems, and printed
`PASS`. The release script trusted it for two months.

Nothing errored. The log even said `files scanned: 0` - and that line was read
past every time, because the word next to it was `PASS`.

Three properties make this class of bug durable:

1. **The output is indistinguishable from the good case.**
2. **It fails open** - the guard stops blocking, which is silent by definition.
3. **It gets more trusted over time** - every green run is evidence it works.

## Install

There is nothing to install. One file, standard library only, Python 3.8+.

```bash
# Replace OWNER with the account that hosts this repository:
curl -O https://raw.githubusercontent.com/OWNER/zero-match-guard/main/zero_match_guard.py

# Or just copy the single file into your repo - that is the intended way to use it.
cp zero_match_guard.py path/to/your/project/
```

## Usage

Guard by the files you expect the check to touch:

```bash
python zero_match_guard.py --paths "dist/**/*.js" --min-count 5 -- npm run lint
```

Guard by the count the check prints about itself:

```bash
python zero_match_guard.py --count-from 'files scanned: (\d+)' -- ./scan.sh
```

If the check's output has no such count, that is itself a failure - a check that
cannot say how much it examined is not evidence.

## In CI

The failure this guards against is most expensive in CI, where nobody reads the log
until something has already shipped.

```yaml
# .github/workflows/check.yml
- name: Lint (guarded)
  run: |
    python zero_match_guard.py --paths "dist/**/*.js" --min-count 1 -- npm run lint

- name: Secret scan (guarded by the scanner's own count)
  run: |
    python zero_match_guard.py --count-from 'files scanned: (\d+)' --min-count 1 -- ./scan.sh
```

The job now fails when the lint step matched no files, instead of reporting a green
check for work it never did.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Ran, examined enough inputs, passed |
| `1` | Ran and reported a problem (the check's own failure) |
| `2` | A literal path given to the check does not exist |
| `3` | Examined zero inputs, or fewer than `--min-count` |

`1` and `3` are deliberately different. "Found a problem" and "could not do my
job" are different states, and collapsing them into "non-zero" throws away the
one signal that catches this bug.

## Where this hides

| Check | Silent-zero failure |
|---|---|
| Test runner | Pattern matches no tests; `0 passed` is green in several runners |
| Linter | Ignore file swallows the whole tree |
| Backup verify | Compares a manifest that is itself empty |
| Grep guard in CI | Typo in the pattern; nothing matches; the gate opens |
| Schema check | Config fails to parse, exception swallowed, empty dict validates |

## Test

```bash
python test_guard.py
```

The last case is the one nobody writes: feed the checker an input that matches
nothing, and assert that it **fails**.

## License

MIT
