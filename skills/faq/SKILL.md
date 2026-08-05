---
description: Archive a substantive, reusable question the user asked as a numbered markdown FAQ entry in the host project's documentation directory (docs/faq/ by default), deduplicating against existing entries — or manage the capability with on/off/status. Use when an observe reminder flags a question-shaped prompt, when the user asks to save a question to the FAQ, or when the user asks to turn FAQ capture on or off.
argument-hint: "[on|off|status]"
---

# FAQ capture

Archive one user question as one markdown file in the project's FAQ directory —
or update the existing entry that already covers it. Answer the user's question
first, as you normally would; capture is a small follow-up, not a detour.

## 0. Activation — `on`, `off`, `status`

This capability is **off by default**. When `$ARGUMENTS` is one of these words,
manage the activation and stop:

- `status` — read `.claude/observe/config.json` at the project root; report in one
  line whether `faq.enabled` is `true`.
- `on` — create or surgically edit `.claude/observe/config.json`: set
  `"enabled": true` inside the `faq` section, preserving every other key and
  section. Unless the section already names a `dir`, record one in the same
  edit: `docs/faq/` when the project has a `docs/` directory, otherwise
  `.claude/observe/faq/`. Write it down rather than leaving it to be inferred
  each time — an inferred location would move an existing FAQ the day someone
  adds a `docs/`. If the file does not exist, create it as
  `{"configVersion": 1, "faq": {"enabled": true, "dir": "<the dir>"}}`.
  Confirm in one line, naming the directory.
- `off` — set `"enabled": false` in the `faq` section if the file and section
  exist (a missing file or section already means off). Confirm in one line.

## 1. Resolve the configuration

Read `.claude/observe/config.json` at the project root. Unless `faq.enabled` is
`true`, say in one line that FAQ capture is not activated in this project
(activate with `/observe:faq on`) and stop. Use the `faq` section:
`dir` (default `docs/faq/`), `language` (default `en`).

## 2. Decide whether the question is worth archiving

Archive only questions that are **substantive** (about the project, its stack,
its conventions, or a technique — something with a durable answer) and
**reusable** (the user, or a teammate, could plausibly hit it again). Skip:

- session trivia ("what did the test print?", "can you fix this?", "where were we?")
- questions whose answer is this session's transient state
- anything containing secrets, credentials, or personal data

When you skip, skip silently — no announcement needed.

## 3. Deduplicate before creating

List the configured FAQ directory and search the existing entries (filenames,
`question:` frontmatter, headings — a case-insensitive grep for the question's
key terms) for one that already covers this question. If one does:
**update it instead of duplicating** — refresh the answer where it is stale,
set `date` to today, keep `id` and the filename. Say which entry you updated.

## 4. Otherwise create a new entry

Filename: `NNN-short-slug.md` in the configured dir — `NNN` is the next free
number, zero-padded to three digits (scan existing `NNN-*.md` files, take the
highest + 1, starting at `001`), and the slug is 3-6 kebab-case words from the
question. Create the directory if it does not exist yet.

File shape — frontmatter **keys stay English** regardless of language; the
body prose is written in the configured `faq.language`:

```markdown
---
id: 7
date: 2026-07-31
question: How do release tags interact with marketplace version pins?
topic: releases
status: answered
---

The answer, written for a future reader with no session context: state the
answer first, then the reasoning or steps, in the configured language.
```

- `id`: the entry number as an integer (matches `NNN`)
- `date`: today, ISO `YYYY-MM-DD`
- `question`: one line, the user's question condensed but faithful (original wording's language is fine)
- `topic`: one short kebab-case noun, e.g. `releases`, `hooks`, `testing`
- `status`: `answered`, or `open` if the question is archived without a settled answer

## 5. Report

One line: the file you created or updated, and its question. Then return to
whatever the session was doing.
