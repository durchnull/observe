# Preset: Claude session behaviour

What to look for when reviewing an axis about how the user works with Claude
Code. Read this only when the axis being reviewed carries
`"preset": "session-behaviour"`.

The subject is the **user's** side of the exchange, not the model's. The
question is always: what would have reached the same goal in fewer turns and
fewer tokens? A one-off is noise; twice or more is a pattern.

## Habits worth looking for

- **Vague openers** — a first prompt that needed one or more clarification
  rounds before work could start: a missing goal, a missing file, or a
  constraint the user knew all along.
- **Drip-fed context** — paths, error messages, or requirements supplied one
  turn at a time in answer to questions, when one complete prompt would have
  carried them all.
- **Late corrections** — preferences or constraints stated only after work went
  the wrong way ("actually, don't touch X", "we always do Y here"). These are
  candidates for stating up front, or for the project's `CLAUDE.md`.
- **Over-broad asks** — one prompt bundling several unrelated goals, forcing
  long turns and follow-up untangling.
- **Re-asked questions** — something a previous session already answered.
  Recurring ones are candidates for the FAQ capability.
- **Manual repetition** — the same multi-step request typed out session after
  session, when a skill, command, or saved note would compress it to one line.

## What a good improvement looks like

Concrete enough to copy. Not "give more context up front" but the sentence
itself: *instead of "the tests are broken", open with "`tests/test_parser.py`
fails at `test_quoted_header` with `AssertionError: expected 'a.txt', got
None` — quoted filenames should come back unquoted."*

Where a habit points at a durable fix rather than a phrasing change — a
`CLAUDE.md` line, a skill, an FAQ entry — say which, and say it as the concrete
text to add.

## What not to report

- The model's mistakes. This axis observes the user's side; a review that
  turns into a critique of Claude's turns has drifted off it.
- Anything the log already records unchanged — carry the heading forward with
  its new marker instead.
- Style preferences with no cost attached. Every habit reported here must come
  with the turns or tokens it actually cost.
