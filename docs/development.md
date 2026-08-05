# Working on this plugin

Two commands cover the whole check:

```bash
python3 tests/run_tests.py          # hook-contract tests (stdlib only, no network)
claude plugin validate . --strict   # manifest + frontmatter + hooks.json
```

## What the tests cover

`tests/samples/` holds representative hook-input JSON for every case: no config,
capability not activated (missing section, `enabled` absent or non-boolean, a
*different* capability active), happy path — and for the Stop hook: marker present,
marker missing, a flat TL;DR without the required sub-section, an optional
sub-section omitted, `stop_hook_active`, the short-turn exemption, and the
transcript fallback. The FAQ samples also cover the false-positive guards
(question marks inside fenced code, or mid-line only).

The `SessionStart` cases build their own evidence: a session directory whose
transcript timestamps are set per case, and an axis log carrying a review
heading, which together decide whether a review is due. They cover the counting
rules that keep the reminder honest — the session being started is not evidence
of itself, transcripts as old as the last review were already read, the newest
heading in a log wins over the first one, a resumed session stays quiet — plus
the `remind` switch and a missing session directory.

The `resolve_config.py` cases build their fixture projects inline instead — a bare
repo, one with a `docs/` directory, one already configured, and one whose config
file is broken — and assert that the resolver writes nothing into any of them.

## Trying a change

Load the checkout directly, without installing:

```bash
claude --plugin-dir /path/to/observe
```

Then `/reload-plugins` after each edit, and run the skill you changed.
