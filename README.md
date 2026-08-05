# observe

[![ci](https://img.shields.io/github/actions/workflow/status/durchnull/observe/ci.yml?branch=main&label=ci)](https://github.com/durchnull/observe/actions/workflows/ci.yml)
[![version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fdurchnull%2Fobserve%2Fmain%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version&prefix=v)](CHANGELOG.md)
[![license](https://img.shields.io/github/license/durchnull/observe)](LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-D97757?logo=claude&logoColor=white)](https://code.claude.com/docs/en/plugins)

A Claude Code plugin that observes and assists your own working style, one
opt-in capability at a time.

It closes every meaningful turn with a **TL;DR**, archives your substantive
questions as **FAQ** entries, and keeps an **improvement log** for each subject
you decide to get better at — how you work with Claude, the English in your
prompts, one corner of your codebase, whatever you name.

**Installing activates nothing.** Every capability is off until you switch it
on, per project — `/observe:init` asks once and sets the whole project up, or
you turn each capability on by itself. Configuration lives under
`.claude/observe/` there, beside the rest of the project's Claude
configuration; what the plugin writes for you to *read* — FAQ entries,
improvement logs — goes to the project's documentation directory
(`docs/faq/`, `docs/improvements/`).

> **Pre-1.0:** while the major version is `0`, a release may rename or remove
> config keys, skills, or file formats without warning, and the FAQ entries and
> improvement logs this plugin writes into your project can be lost or need
> fixing up by hand on update. It ships as-is, with no warranty (see
> [LICENSE](LICENSE)).

## Capabilities

| Skill | Mechanism | When active |
| :--- | :--- | :--- |
| `/observe:tldr` | `Stop` hook (`scripts/check_tldr.py`) + skill | Every meaningful turn ends with a `## TL;DR` section — an **Informational** block (outcomes, concrete values) and an **Actionable** block (your open todos, omitted when empty). A long turn without it is blocked once with a reminder. |
| `/observe:faq` | `UserPromptSubmit` hook (`scripts/faq_reminder.py`) + skill | Question-shaped prompts get a one-line reminder; the model judges whether the question is substantive and reusable, then archives it as a numbered markdown file under `docs/faq/`, deduplicating against existing entries. |
| `/observe:improve` | `SessionStart` hook (`scripts/improve_reminder.py`) + skill | You name what to get better at — one **axis** per subject. A review reads the recent evidence for that axis, compares it against what the axis's log already says, and appends what changed: `new`, `recurring`, `improving`, `resolved`. One growing log per axis under `docs/improvements/`. No axis exists until you start one; once one does, a session offers the review when a window of evidence has come in. |

A fourth skill, `/observe:init`, is not a capability but the setup interview for
all three — see [Activation](#activation).

How each one works underneath — the hook contracts, the FAQ heuristic, the review
markers — is in [docs/capabilities.md](docs/capabilities.md).

## Install

```text
/plugin marketplace add durchnull/claude-plugins
/plugin install observe@durchnull
```

To take this plugin on its own, add its repo directly instead — it carries its own `durchnull`
marketplace definition:

```text
/plugin marketplace add durchnull/observe
/plugin install observe@durchnull
```

Both routes register a marketplace named `durchnull`, and adding one replaces the other, so prefer
the catalog whenever you want more than one durchnull plugin at a time.

Or try it from a checkout without installing:

```bash
claude --plugin-dir /path/to/observe
```

Enabling it for every project is safe: until a project activates a capability in
its `.claude/observe/config.json`, all three hooks exit silently and nothing is
written. Setting the plugin by hand instead of installing it, and what happens on
a machine without Python, are in [docs/install.md](docs/install.md).

## Activation

Nothing is active by default. `/observe:init` is the one command that sets a
project up:

```text
/observe:init
```

It reports what the project resolves to today, asks which of the three
capabilities it should use, and turns **every subject you name into its own
improvement axis** — "I want to improve my prompts, my English and error
handling" is three axes with three logs, not one broad one. Answer it in the
invocation to skip the questions:

```text
/observe:init tldr, faq, improve how I work with Claude and the English in my prompts
```

Re-running it is safe and expected: it keeps every value you already set, never
deletes an axis or its log, and only decides the on/off switches it just asked
about. `--dry-run` prints the config file it would write and stops.

Or switch each capability on by itself, in the project where you want it:

```text
/observe:tldr on
/observe:faq on
/observe:improve how I work with Claude Code
```

`tldr` and `faq` are single switches, each also taking `off` and `status`.
`improve` has nothing to switch on globally: you start an axis by saying what
you want to improve, in your own words, and each axis is on or off on its own.
Starting one is the whole setup — once a window of sessions has gone by
unreviewed, a starting session says so in one line and you decide whether to
run the review then.

```text
/observe:improve the English phrasing of my prompts   # start another axis
/observe:improve status                               # what is being observed
/observe:improve off english-phrasing                 # stop; the log stays
/observe:improve reminders off english-phrasing       # keep it, but ask me first
/observe:improve                                      # review every active axis
```

The last two are different switches: `off` stops observing an axis, while
`reminders off` keeps it observed and reviewable on demand and only stops the
offer. Either takes an axis or applies to all of them.

### The config file

`/observe:init` and the toggles edit
`.claude/observe/config.json` at the project root; you can maintain that file by hand
instead — `tldr` and `faq` are active only when their section carries an explicit
`"enabled": true`, and an `improve` axis only when its own entry does. A file with
all three capabilities on, leaving every tuning key at its default:

```json
{
  "configVersion": 1,
  "tldr": { "enabled": true },
  "faq": { "enabled": true, "dir": "docs/faq/" },
  "improve": {
    "dir": "docs/improvements/",
    "axes": {
      "session-behaviour": {
        "enabled": true,
        "title": "Claude session behaviour",
        "focus": "How I phrase requests, supply context up front, and scope asks.",
        "preset": "session-behaviour"
      }
    }
  }
}
```

Every key but `enabled` is optional and falls back to the default shown above.
The full key-by-key reference — every default, what each one changes — is in
[docs/configuration.md](docs/configuration.md). To see what a project resolves to
today — which capabilities are on, which axes exist, and which values are
configured rather than inferred — the bundled `scripts/resolve_config.py` prints
exactly that and writes nothing; `/observe:init` shows its report before it asks
anything.

## Privacy

Everything stays local. The scripts are Python 3 stdlib only — the hooks read their
input from stdin, the resolver reads the project's own config file, and none of them
makes **any network call** (CI fails the build if a network-capable
module is ever imported). The plugin writes only inside the host project, and only
what you activated: the config file `/observe:init` and the toggles maintain
(`.claude/observe/config.json`),
FAQ entries, and the improvement logs, each under its configured dir. Transcripts
are read on demand by `/observe:improve` from where Claude Code already stores
them; nothing is copied or uploaded. An improvement log holds findings and at
most one short quoted line per habit — never a transcript dump.

## Development

```bash
python3 tests/run_tests.py          # hook-contract tests (stdlib only, no network)
claude plugin validate . --strict   # manifest + frontmatter + hooks.json
```

What those tests cover, and how to try a change against a real session, is in
[docs/development.md](docs/development.md).

## License

[MIT](LICENSE) © David Friedrich.

The license covers the code, not the name. It grants no right to use **durchnull** as the
name of a derived or redistributed work — fork it freely, under a name of your own.
