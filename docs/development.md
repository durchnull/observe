# Working on this plugin

Two commands cover the whole check:

```bash
python3 tests/run_tests.py          # hook-contract tests (stdlib only, no network)
python3 scripts/help.py --self-test # /observe:help lists exactly what skills/ ships
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

The `tldr.style` cases sit with the Stop hook: every spelling a project might
write resolves to the same style, a style the plugin does not know still blocks
with the default wording rather than switching the hook off, and the project's
free-text `style_notes` reach the reminder but are capped there.

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

`help.py` is checked from both ends: its own `--self-test` fails when the authored
command table and `skills/` disagree, and the suite renders it in a bare project,
in a fully configured one, and over a config file that is not valid JSON — the
three states someone actually types `/observe:help` in.

`tldr_contract.py` gets the same treatment, plus one rule of its own: the `tldr`
skill **injects** it, and an injected command that fails aborts the whole skill
invocation. So every case asserts it exits 0 and prints a usable contract —
including over a config file that is not valid JSON.

## Trying a change

Load the checkout directly, without installing:

```bash
claude --plugin-dir /path/to/observe
```

Then `/reload-plugins` after each edit, and run the skill you changed.
