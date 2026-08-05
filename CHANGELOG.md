# Changelog

All notable changes to the `observe` plugin are documented here. This project
adheres to [Semantic Versioning](https://semver.org) and
[Keep a Changelog](https://keepachangelog.com).

`observe` is pre-1.0: while the major version is `0`, the config schema, its
location, and the skill surface may change in a minor release.

## [0.1.0] — 2026-08-08

### Added

- Initial release. Opt-in by construction: installing activates nothing — each
  capability turns on individually via an explicit `"enabled": true` in the host
  project's `.claude/observe/config.json`, and every skill doubles as its own
  toggle. Configuration lives beside the project's other Claude configuration;
  what the plugin writes to be *read* goes to the project's documentation
  directory.
- `/observe:init` — the setup interview: it reports what the project resolves
  to today, asks which capabilities it should use, and turns **every subject
  named into its own improvement axis**, so "my prompts, my English and error
  handling" becomes three axes with three logs rather than one broad one. It
  writes config, never code. Re-running it keeps every value already set, never
  deletes an axis or a log, and decides only the on/off switches it just asked
  about; `--dry-run` prints the file and stops. Backed by
  `scripts/resolve_config.py`, which prints the resolved state — capability by
  capability, configured values separated from inferred ones, the reminder
  switch among them — and writes nothing.
- `/observe:tldr` — `Stop` hook `scripts/check_tldr.py` plus the format skill:
  blocks a meaningful turn whose final assistant message lacks the configured
  TL;DR marker, or lacks a `required_subsections` label (default
  `**Informational**`) after it. `optional_subsections` (default `**Actionable**`)
  are named in the reminder but never enforced — an empty one is omitted, not
  written. Uses the documented `last_assistant_message` input with a
  transcript-JSONL fallback, honors `stop_hook_active` when sent, and blocks at
  most once per user prompt as loop protection. Turns at or under
  `min_turn_chars` (default 200) are exempt, so short replies are never padded.
- `/observe:faq` — `UserPromptSubmit` hook `scripts/faq_reminder.py` plus the
  capture skill: a one-line reminder when a prompt line outside fenced code
  blocks ends with a question mark and the prompt exceeds `min_prompt_chars`
  (question marks inside code — ternaries, SQL, URL query strings — do not
  trigger it); the skill judges whether the question is substantive and
  reusable, dedups against the configured FAQ dir, and writes
  `NNN-short-slug.md` entries with `id`/`date`/`question`/`topic`/`status`
  frontmatter, body in the configured language. Entries go to `docs/faq/`, or
  beside the config in a project without a `docs/`.
- `/observe:improve` — you name what to get better at, in your own words, and
  each subject becomes an **axis** with one growing log at
  `docs/improvements/<axis>.md`. Nothing is observed until an axis exists:
  `improve.axes` starts empty, and each axis is switched on and off on its own,
  so several can run at once. A review reads the recent evidence for one axis,
  reads what its log already says, and records only what changed — every habit
  marked `new`, `recurring`, `improving`, or `resolved`. Newest section first;
  older sections are never rewritten. `off` keeps the log.
- Improvement reviews come due on their own. A `SessionStart` hook,
  `scripts/improve_reminder.py`, counts per enabled axis how many sessions have
  been recorded since that axis's last review and opens a starting session with
  one line once the count reaches `improve.sessions`. Both halves are derived,
  never recorded — the last review is the newest `## YYYY-MM-DD` heading in the
  axis log, the evidence is the transcript timestamps — so nothing is written
  into the project and no stored marker can disagree with the log. The session
  being started is never counted as evidence of itself, transcripts as old as
  the last review are treated as already read, and resumed, compacted or forked
  sessions stay silent. The line offers a review and never starts one: a review
  reads several whole transcripts, so one that began on its own would spend the
  session it interrupted on work nobody asked for — the deliberate difference
  from the TL;DR and FAQ reminders, whose remedy is a few lines written on the
  spot.
- `improve.remind` (default `true`) switches that line off for every axis
  without switching off an axis. It defaults on because naming an axis is
  already the opt-in; a project that never names one is untouched.
- `/observe:improve reminders [on|off] [axis]` reads and sets that switch, so it
  is not a key you have to know about to reach. Given an axis it writes
  `remind` on that axis's own entry, which wins over the section in both
  directions — one noisy axis goes quiet without costing the reminders you
  wanted everywhere else, and one axis can keep offering while the rest are
  silent. `reminders off <axis>` is deliberately not `off <axis>`: the first
  keeps the axis observed and reviewable the moment you ask, the second stops
  observing it. `/observe:improve status` reports how many sessions have
  arrived since each axis's last review, and whether reminders are on.
- `reference/session-behaviour.md` — the catalogue of interaction habits an
  axis loads with `"preset": "session-behaviour"`: vague openers, drip-fed
  context, late corrections, over-broad asks, re-asked questions, manual
  repetition. Read only when such an axis is reviewed; any other axis runs on
  its own one-sentence `focus`.
- Both hook commands guard on `command -v python3`, so a machine without
  Python degrades to a silent no-op instead of a per-turn hook error.
- `tests/run_tests.py` plus a `tests/samples/` corpus covering no-config,
  not-activated (missing section, non-boolean `enabled`, a different capability
  active), garbage-input, and happy-path behavior for both hook scripts.
- CI validates both manifests, fails on a hardcoded machine path, on a
  network-capable import in a hook script, on a bundled `${CLAUDE_PLUGIN_ROOT}`
  path that does not resolve, and on shipped surface the README does not
  document.
