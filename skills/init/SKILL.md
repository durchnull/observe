---
description: Interview this project and write .claude/observe/config.json — pick which observe capabilities it should use (the closing TL;DR, FAQ capture) and start one improvement axis per subject named, several in a single run. Idempotent, and it never deletes an axis or a log. Use when the user asks to set up or initialize observe, asks which capabilities this project should use, or names several things they want to get better at.
argument-hint: "[what to observe, e.g. \"tldr, faq, improve my prompts and error handling\"] [--dry-run]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, AskUserQuestion, Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_config.py":*)
---

# observe init — decide what this project observes

Installing observe activates nothing. This is the one interview that turns it
on: which capabilities this project should use, and what the user wants to get
better at. It writes **config, not code** — one file, `.claude/observe/config.json`,
and nothing is generated into `.claude/commands/`.

Everything here is also reachable one capability at a time (`/observe:tldr on`,
`/observe:faq on`, `/observe:improve <subject>`). This command exists so a
project can be set up in a single pass, and so several improvement subjects can
be named at once.

What this project resolves to right now:

!`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_config.py"`

## 1. Start from what is already there

The block above is the starting point — it already says whether a config file
exists, which capabilities are on, which axes exist, and which values are
configured rather than inferred. Do not re-derive any of it by reading the file
again.

**Re-running this command is safe and expected**, e.g. after a plugin update or
when a new subject comes up. The rules that make it safe:

- **Tuning knobs already in the file are never touched** — a project that set
  `marker`, `min_turn_chars`, `language`, `sessions`, or a `dir` keeps them.
- **Axes are never deleted, and neither are their logs.** An axis the user does
  not mention in this run is left exactly as it is.
- The `enabled` switches are the one thing this run does decide, because they
  are exactly what it asks about in §2.

If the block reports a config file that is **present but unreadable**, stop:
say so, name the path, and let the user fix or delete the file. Overwriting it
would silently discard whatever they had.

If the block did not run at all — a machine without `python3` gets a command
error there instead of a report — read `.claude/observe/config.json` yourself
and carry on, saying once that the resolver could not run.

## 2. Ask which capabilities this project should use

Skip anything `$ARGUMENTS` already answers. "tldr and faq", or "I want to
improve my prompts and my English", is an answer — re-asking it is rude and
slows down exactly the case this command exists for.

For the rest, ask **once**, as a single multi-select `AskUserQuestion`:

> Which capabilities should this project use?

| Option | Describe it as |
| :--- | :--- |
| **Closing TL;DR** | Every meaningful turn ends with a summary — an **Informational** block and an **Actionable** one. A long turn without it is blocked once with a reminder. This is the only capability felt on every single turn. |
| **FAQ capture** | Substantive questions get archived as numbered markdown entries you can read later. A question-shaped prompt gets a one-line reminder; nothing is ever blocked. |
| **Improvement logs** | You name subjects to get better at, and each one grows its own log of what changed. Needs at least one subject — §3. |

Name the cost as plainly as the benefit. Users switch TL;DR off again when
nobody told them it fires on every turn, and that is a bad first impression of
a plugin whose whole promise is that it stays out of the way until invited.

Do not ask where the documents should go — the block above already reports the
inferred directory. State it in the report instead; if the user then wants it
elsewhere, record their directory rather than the inferred one.

## 3. One axis per subject — several at once

**"I want to improve a, b and c" is three axes, not one.** Split the answer on
its commas and conjunctions and treat each fragment as its own subject. Never
merge two subjects into a broad axis to save a file: an axis's `focus` sentence
is what every future review is measured against, and a sentence covering two
subjects measures neither.

If improvement logs were chosen without any subject named, ask once — free
text, not a menu, because the wording is the user's to choose:

> Name each subject you want to get better at, one per line — how you work with
> Claude Code, the English in your prompts, error handling in the API layer,
> anything. There is no fixed list.

For **each** subject, derive the same four fields the `improve` skill derives
in its §3 — that skill is the authority on axes, so read
`${CLAUDE_PLUGIN_ROOT}/skills/improve/SKILL.md` rather than inventing a second
convention here:

1. **Slug** — 1–4 kebab-case words, filename-safe. It must be unique in this
   config: when two subjects slug the same way, lengthen the second rather than
   letting it overwrite the first. A slug matching an axis that already exists
   is that axis — switch it on, keep its recorded `focus`, and say so.
2. **Title** — the subject as a short human name.
3. **Focus** — one sentence naming what to look for and what "better" means
   here, in the user's own words wherever they gave them.
4. **Preset** — `"preset": "session-behaviour"` when the subject is how the
   user works with Claude Code; omit the key otherwise.

Then **read every axis back before writing** — slug, title, and focus sentence,
in one block — and let the user correct the wording. A focus sentence they do
not recognise is the one thing here that is expensive to get wrong, because
every review for that axis is measured against it.

## 4. Write the file, once

One Write for a new file, or one **surgical** Edit of an existing one — never a
wholesale reformat to add a key. Create `.claude/observe/` if it is missing.
With `--dry-run`, print the file that would be written and stop.

- Stamp `"configVersion": 1`.
- **Preserve every key already in the file**, including ones not described here
  — an unrecognized key belongs to a newer version of the plugin, not to you.
- **Omit what was not decided.** A capability the user did not choose gets
  `"enabled": false` only if its section already exists; otherwise leave the
  section out entirely. Absent already means off, and an absent knob stays
  inferable, so a later release can change a default without a migration.
- **Never record a tuning knob at its default value.** A pinned default is a
  value the project now owns and has to maintain. The documents directory is
  the one deliberate exception — next bullet.
- **Record the documents directory** when a capability that writes documents is
  activated — `faq.dir` when FAQ capture goes on, `improve.dir` when the first
  axis starts — using the directory the block above reports. Write it down
  rather than leaving it to be inferred each run: an inferred location would
  move an existing set of documents the day someone adds a `docs/`.
- **Deselecting improvement logs switches every existing axis off; it deletes
  nothing.** The logs stay, and so do the axis entries. Say this in the report
  so it is never a surprise.

Then create the log file for each **new** axis — header only, no review
section — in the shape `${CLAUDE_PLUGIN_ROOT}/skills/improve/SKILL.md` §7
specifies. An axis that already had a log keeps it untouched.

## 5. Report

Short, in this order:

1. The file path, and whether it was **created** or **updated in place**.
2. One line per capability: on or off, and where its documents go.
3. One line per axis: slug, title, on or off, log path, and whether the log was
   just created or already existed. Say explicitly which axes were left alone.
4. Anything preserved rather than proposed — the values this run did not touch.
5. What happens next, in one sentence: the hooks are live in new sessions, and
   `/observe:improve` runs a review when there is something to review.

Do not run a review here, do not write into the project's code, and do not
adopt anything on the user's behalf. This command sets up; the capabilities do
the rest on their own.
