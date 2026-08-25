---
description: End every meaningful turn with a closing "## TL;DR" section — an **Informational** block with the outcome and concrete values, plus an **Actionable** block with the user's open todos, omitted when empty — or manage the capability with on/off/status/style. Use when a Stop-hook reminder asks for the TL;DR, when the user asks for one, or when the user asks to turn TL;DR enforcement on or off or to change how it is written.
argument-hint: "[on|off|status|style <name>]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tldr_contract.py":*)
---

# Closing TL;DR

End meaningful turns with a summary the user can act on without rereading the
turn. When this capability is active, a Stop hook enforces it: a long turn
that ends without the marker is blocked once with a reminder.

**Everything about the section is the project's to set** — the marker, the
sub-section labels, the length that counts as meaningful, and the style the
bullets are written in. What this project resolves to right now:

!`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tldr_contract.py"`

## 0. Activation and style — `on`, `off`, `status`, `style <name>`

This capability is **off by default**. When `$ARGUMENTS` is one of these,
manage the configuration and stop. Every edit is surgical: set the one key and
preserve every other key and section.

- `status` — report the block above in one or two lines: on or off, and the
  style it resolves to. Do not read the config file again; the block is it.
- `on` — create or surgically edit `.claude/observe/config.json`: set
  `"enabled": true` inside the `tldr` section. If the file does not exist,
  create it as `{"configVersion": 1, "tldr": {"enabled": true}}`. Confirm in one
  line.
- `off` — set `"enabled": false` in the `tldr` section if the file and section
  exist (a missing file or section already means off). Confirm in one line.
- `style <name>` — set `"style"` in the `tldr` section to the canonical id from
  the table below, creating the file or the section if needed. Confirm in one
  line, naming the style. `style` with no name reports the current one instead
  of changing it.

Never record a knob at its default value: switching the style back to the
plugin's default means **removing** the `style` key, not writing
`"style": "default"`. A pinned default is a value the project then owns.

### The styles

| `tldr.style` | The bullets are written… |
| :--- | :--- |
| `default` | Concise: outcomes and concrete values, no filler. No further constraint on the wording. |
| `iso-24495-1` | In **plain language** as ISO 24495-1:2023 frames it — the reader gets what they need, finds it, understands it, and can use it. Short sentences, everyday words, active voice, outcome first; file names, commands, flags and figures stay exact. |

The plugin also accepts what a person would plausibly type — `plain`,
`plain language`, `ISO 24495-1:2023` all resolve to `iso-24495-1` — but write
the canonical id into the config. A value that names no style at all resolves
to `default` and is reported as unrecognized: a typo in a wording knob never
costs the summary itself.

`tldr.style_notes` is the free-text companion for what no style can hold — a
house word, a term to avoid, the reader to write for. It is passed through
verbatim, in the block above and in the hook's reminder, and it wins over a
preference in the style's own guidance.

## The format

The block above already prints this project's skeleton, with its marker and its
labels in it. Copy that shape. The defaults, when nothing is configured:

```markdown
## TL;DR

**Informational**
- The outcome: what happened or what was found, with concrete values (amounts, filenames, versions), not vague summaries.
- 1-4 bullets total; each one something the user would repeat to a colleague.

**Actionable**
- Todos left for the user: decisions to make, commands to run, authorizations to give.
- Omit this whole block when nothing is left — an empty section is omitted, never written.
```

Rules that hold whatever the style:

- The TL;DR is a **summary, not a substitute**: the reasoning stays in the
  message above it.
- A **meaningful** turn is one whose final message exceeds the configured
  `min_turn_chars` (default 200). Short conversational replies are exempt —
  never pad a one-line answer with a summary.
- Bullets state outcomes and concrete values; no filler like "successfully
  completed the task".

## Writing in the configured style

The block above lists the active style's rules; they are the contract, and for
most turns they are all you need. When a summary needs more than they say —
a bullet that will not come apart into one idea, a term you are unsure counts
as plain — read the style's full guidance, which the block names:
`${CLAUDE_PLUGIN_ROOT}/reference/plain-language.md` for `iso-24495-1`. The
`default` style has no reference: it is the shape rules above and nothing more.

Plain language is **never** a licence to blur a name. `min_turn_chars`,
`/observe:tldr on`, `1.4.2`, `docs/faq/` stay exactly as written; the words
around them get simpler. A simplified identifier is a wrong answer in a
friendly tone.

## How enforcement works

The plugin's Stop hook checks the turn's final assistant message. When the
capability is active and a meaningful turn lacks the marker (or lacks a
required block label after it), it blocks the stop **once** with a reminder,
then never again for the same prompt — a misbehaving turn can never loop. The
reminder names the configured style and the project's notes, so a blocked turn
is told how to write the summary, not just that one is missing. When the
capability is off, the hook is a silent no-op.
