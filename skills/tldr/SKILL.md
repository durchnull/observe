---
description: End every meaningful turn with a closing "## TL;DR" section — an **Informational** block with the outcome and concrete values, plus an **Actionable** block with the user's open todos, omitted when empty — or manage the capability with on/off/status. Use when a Stop-hook reminder asks for the TL;DR, when the user asks for one, or when the user asks to turn TL;DR enforcement on or off.
argument-hint: "[on|off|status]"
---

# Closing TL;DR

End meaningful turns with a summary the user can act on without rereading the
turn. When this capability is active, a Stop hook enforces it: a long turn
that ends without the marker is blocked once with a reminder.

## 0. Activation — `on`, `off`, `status`

This capability is **off by default**. When `$ARGUMENTS` is one of these words,
manage the activation and stop:

- `status` — read `.claude/observe/config.json` at the project root; report in one
  line whether `tldr.enabled` is `true`.
- `on` — create or surgically edit `.claude/observe/config.json`: set
  `"enabled": true` inside the `tldr` section, preserving every other key and
  section. If the file does not exist, create it as
  `{"configVersion": 1, "tldr": {"enabled": true}}`. Confirm in one line.
- `off` — set `"enabled": false` in the `tldr` section if the file and section
  exist (a missing file or section already means off). Confirm in one line.

## The format

The turn's final message ends with (defaults shown; the marker and labels are
configurable in `.claude/observe/config.json`):

```markdown
## TL;DR

**Informational**
- The outcome: what happened or what was found, with concrete values (amounts, filenames, versions), not vague summaries.
- 1-4 bullets total; each one something the user would repeat to a colleague.

**Actionable**
- Todos left for the user: decisions to make, commands to run, authorizations to give.
- Omit this whole block when nothing is left — an empty section is omitted, never written.
```

Rules:

- The TL;DR is a **summary, not a substitute**: the reasoning stays in the
  message above it.
- A **meaningful** turn is one whose final message exceeds the configured
  `min_turn_chars` (default 200). Short conversational replies are exempt —
  never pad a one-line answer with a summary.
- Bullets state outcomes and concrete values; no filler like "successfully
  completed the task".

## How enforcement works

The plugin's Stop hook checks the turn's final assistant message. When the
capability is active and a meaningful turn lacks the marker (or lacks a
required block label after it), it blocks the stop **once** with a reminder,
then never again for the same prompt — a misbehaving turn can never loop. When
the capability is off, the hook is a silent no-op.
