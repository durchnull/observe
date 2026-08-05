---
description: Observe and log improvement along the axes this project chose — how the user works with Claude Code, the phrasing of their prompts, a specific code domain, anything they name. Reviews recent evidence for one axis and writes a dated finding into docs/improvements/<axis>.md, marking each habit new, recurring, improving or resolved; also starts an axis, lists them, and switches them on and off. Use when the user asks to observe or improve something, asks for an improvement review, asks what is being observed, or asks to start or stop observing an axis.
argument-hint: "[status | <what to improve> | on|off <axis> | <axis> [N]]"
---

# Improvement observations

The user picks what to get better at. Each subject is an **axis** — "how I work
with Claude Code", "the English in my prompts", "error handling in the API
layer" — and each active axis has one growing log file. A review reads recent
evidence for one axis, compares it against what that log already says, and
appends what changed: a habit seen for the first time, one that came back, one
that is fading, one that is gone.

The log is the point. A review that re-reports yesterday's findings is noise;
a review that says "this one is now recurring, that one has stopped" is a
record of improvement.

## 0. Nothing is observed until the user names an axis

There are **no default axes**. Installing observe and even switching this
capability on observes nothing — the `improve.axes` object starts empty, and an
axis is observed only while its entry carries an explicit `"enabled": true`.

Configuration lives in `.claude/observe/config.json` at the project root:

```json
{
  "configVersion": 1,
  "improve": {
    "dir": "docs/improvements/",
    "sessions": 5,
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

- `dir` — where the logs go, project-relative. Default `docs/improvements/`;
  in a project without a `docs/` directory, `.claude/observe/improvements/`.
- `sessions` — how many recent transcripts a review reads, and the number of
  unreviewed sessions that makes an axis due. Default `5`.
- `remind` — whether a starting session offers a review that has come due
  (§2). Default `true`; write it only to switch reminders off.
- `axes.<slug>` — one entry per axis. `title` is the human name, `focus` is one
  sentence saying what to look for, `preset` is optional (see §5). An entry may
  carry its own `remind`, which wins over the section's for that axis (§4b).

## 1. Read `$ARGUMENTS`

Resolve in this order and stop at the first match:

| `$ARGUMENTS` | Do |
| :--- | :--- |
| empty | §6, once per **enabled** axis. If none is enabled, say so in one line, name what `/observe:improve <what to improve>` would start, and stop. |
| `status` | §4 |
| starts with `reminders` or `remind` | §4b — the rest is `on`/`off`, optionally followed by an axis. This row sits above the ones below deliberately: without it `reminders off` reads as a subject and starts an axis by that name. |
| starts with `on ` or `off ` | §4, for the axis named after the word |
| exactly `off` | §4 — switch every axis off |
| names an existing axis (its slug, or its title case-insensitively), optionally followed by an integer | §6 for that axis only, reading that many transcripts |
| anything else | §3 — the user is describing something new to improve |

## 2. Gate a review

A review runs only for an axis whose entry is `"enabled": true`. When the user
names an axis that exists but is switched off, say so in one line, offer
`/observe:improve on <axis>`, and stop — do not review it and do not switch it
on unasked.

**A review is due on its own, but never runs on its own.** The `SessionStart`
hook `${CLAUDE_PLUGIN_ROOT}/scripts/improve_reminder.py` counts, per enabled
axis, the sessions recorded since that axis's last review — the newest
`## YYYY-MM-DD` heading in its log — and injects one line when that reaches
`sessions`. Naming an axis is the only opt-in it needs; §4b switches the line
off, for one axis or for all.

That line is an offer, and stays one. Put it to the user in a sentence and let
them answer. Do **not** start a review because a reminder appeared: a review
reads whole transcripts, so one that begins unasked spends the session it
interrupted on work the user did not ask for. This is the difference from the
TL;DR and FAQ reminders, whose remedy is a few lines written on the spot.

## 3. Start observing something new

The user's words are the subject: "correct English phrasing for better
prompting", "how I work with Claude", "the way this repo handles migrations".
Turn that into an axis and confirm it in the same turn:

1. **Slug** — 1–4 kebab-case words, filename-safe, from the subject.
2. **Title** — the subject as a short human name.
3. **Focus** — one sentence naming what to look for and what "better" means
   here. Write it in the user's words where you can; this sentence is what
   every future review is measured against, so vagueness is expensive.
4. **Preset** — if the subject is how the user works with Claude Code, set
   `"preset": "session-behaviour"` (see §5). Otherwise omit the key.
5. Surgically edit `.claude/observe/config.json`: add the axis under
   `improve.axes` with `"enabled": true`, preserving every other key and
   section. If `improve.dir` is absent, record it in the same edit —
   `docs/improvements/` when the project has a `docs/` directory, otherwise
   `.claude/observe/improvements/`. Write it down rather than leaving it to be
   inferred each time: an inferred location would move existing logs the day
   someone adds a `docs/`. If the file does not exist, create it as
   `{"configVersion": 1, "improve": {"dir": "<the dir>", "axes": {…}}}`.
6. Create the log file (§7's header, no review section yet).

Report in two lines: the axis you started, the focus sentence you recorded, the
log path, and that a later session will offer the first review once `sessions`
of evidence have accumulated — starting an axis is all the setup there is. If
the subject is already covered by an existing axis, say so and offer to review
or re-enable it instead of creating a near-duplicate.

## 4. `status`, `on <axis>`, `off <axis>`

- `status` — list every axis: title, slug, on or off, log path, the date of its
  most recent review (read the log's top section), and how many sessions have
  been recorded since — the `*.jsonl` files in this project's session directory
  (§6a) modified after that date. One line each, and one closing line saying
  whether reminders are on and at what count they speak. When `improve.axes` is
  empty or absent, say that nothing is being observed and name the command that
  starts one.
- `on <axis>` — set `"enabled": true` for that axis. If no axis matches the
  name, treat it as §3 instead — the user is naming something new.
- `off <axis>` — set `"enabled": false`. Bare `off` switches every axis off.
  Never delete an axis or its log on `off`: switching off stops the observing,
  and the record of what was already learned stays. Deleting is the user's own
  call, made explicitly.

Confirm each change in one line.

## 4b. `reminders on|off [axis]`

Switches §2's offer without touching what is observed. An axis whose reminders
are off is still reviewed the moment the user asks for it — the two switches
answer different questions: `off <axis>` means *stop observing this*, `reminders
off <axis>` means *I will decide when to review this myself*.

- `reminders` alone — report the state and stop: on or off overall, at what
  count it speaks (`sessions`), and any axis that overrides it.
- `reminders off` — set `"remind": false` on the `improve` section.
- `reminders on` — set `"remind": true` there. Since `true` is the default,
  prefer removing the key when it is the only thing switching reminders off; a
  config that records only what the user chose stays honest about the default.
- `reminders on|off <axis>` — set `remind` on that axis's own entry instead,
  which wins over the section for that axis alone. Use this when one axis is
  noisy and the rest are wanted; do not silence everything to quiet one.

If no axis matches a name given here, say so and stop. Never fall through to §3
— the user is adjusting a switch, not naming a new subject to improve.

Confirm in one line, and say what it means concretely: which axes will still
offer a review, and which now wait to be asked.

## 5. The `session-behaviour` preset

An axis about how the user works with Claude Code has a catalogue of habits
worth looking for that would be tedious to re-derive. When the axis being
reviewed carries `"preset": "session-behaviour"`, read
`${CLAUDE_PLUGIN_ROOT}/reference/session-behaviour.md` and use it as §6's
list of what to look for. Read it only then — an axis about a code domain has
no use for it.

Any other axis is driven by its own `focus` sentence alone.

## 6. Review one axis

### 6a. Gather the evidence

The default source is this project's recent sessions. Claude Code stores them
under `~/.claude/projects/<project-dir>/`, where `<project-dir>` is the
project's absolute path with path separators replaced by dashes. Take the `N`
most recently modified `*.jsonl` files there — `N` from `$ARGUMENTS` if it is a
number, otherwise `improve.sessions`, otherwise 5. Skip sidechain entries. If
the directory holds no transcripts, say so and stop; do not guess.

Read for what the axis's `focus` names, not everything:

- an axis about **how the user works or writes** — read the user's messages and
  how each exchange unfolded from them
- an axis about a **code domain** — read the sessions for work that touched it,
  then read that code and its recent `git log` directly; the sessions say what
  was attempted, the code says what it became

### 6b. Read the existing log first

Read `<dir>/<slug>.md` before writing anything. For every habit it already
records, decide which of these the new evidence shows:

| Marker | Means |
| :--- | :--- |
| `new` | not in the log before |
| `recurring` | in the log, and it happened again at a similar rate |
| `improving` | in the log, and measurably less frequent |
| `resolved` | in the log, and absent from this window entirely |

A habit seen once is noise; twice or more is a pattern. Do not re-describe a
habit the log already describes — carry its heading forward, change the marker,
and write only what is different this time.

### 6c. Write the entry

Append a new section to the log **directly under the intro paragraph**, so the
newest review is the first thing a reader sees. Per habit:

- **The habit** — one sentence, described without blame. Reuse the existing
  heading verbatim when the log already has one.
- **The evidence** — which sessions and how often (dates and counts, never
  transcript dumps; at most one short quoted line).
- **The improvement** — something concrete the user can copy: the rewritten
  opening sentence, the constraint stated up front, the shape the code should
  have had.
- **The gain** — stated plainly and honestly: "~4 extra turns across 3
  sessions", "three round-trips of clarification".

If the window shows nothing worth recording, write no section. Say so in the
chat instead — an empty review is a real result, and padding the log with
"nothing found" entries makes it unreadable.

## 7. The log file

`<dir>/<slug>.md`, created on first use:

```markdown
---
axis: session-behaviour
title: Claude session behaviour
focus: How I phrase requests, supply context up front, and scope asks.
started: 2026-08-03
---

# Claude session behaviour

What this log observes: <the focus sentence, expanded to a sentence or two —
what "better" means on this axis>.

## 2026-08-03 — 5 sessions

### Context supplied one turn at a time — recurring

**Evidence** — 6 times across 4 sessions (Jul 29, Jul 31, Aug 1, Aug 3): the
file path arrived only after being asked for.

**Improvement** — open with the path and the error text in the first message:
"in src/parser.py, `parse_header` returns None for a quoted filename; expected
the unquoted string."

**Gain** — ~5 clarification turns.
```

- Frontmatter keys stay English; the prose follows the language the user writes
  in.
- One `##` section per review: `## YYYY-MM-DD — N sessions`.
- One `###` per habit, with the marker after an em dash.
- Never rewrite or delete an older section. The log is a record of what was
  true when it was written; a habit that changed gets a new entry with a new
  marker, not an edited old one.

## 8. Report

One short message: the axis reviewed, how many sessions, the counts by marker
("2 recurring, 1 new, 1 resolved"), the single highest-leverage change in one
sentence, and the log path. The detail belongs in the log, not in the chat.

This skill writes only the log file and the config entry. It never changes the
project's code, and never adopts an improvement on the user's behalf.
