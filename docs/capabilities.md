# How the capabilities work

The detail behind the three capabilities listed in the
[README](../README.md#capabilities): what each hook actually checks, what the
skills decide, and what gets written where. Every key named here is documented
with its default in the [configuration reference](configuration.md).

## TL;DR — `/observe:tldr`

The Stop hook prefers the documented `last_assistant_message` input field and falls
back to parsing the transcript JSONL for older CLI versions. When the marker is
missing it emits `{"decision": "block", "reason": ...}` so the model finishes the
turn with a proper summary. With `required_subsections` set (the default requires
`**Informational**`), a TL;DR also blocks unless each listed string appears after the
marker's last occurrence — the bullets are expected grouped under those labels.
`optional_subsections` (default `**Actionable**`) are only named in the reminder:
they hold what is left for the user to do, and when there is nothing, the
sub-section is omitted entirely rather than written empty — which is exactly why
their presence cannot be enforced. Turns at or under `min_turn_chars` are exempt, so a
one-line answer is never padded with boilerplate. Loop protection is built in: the
hook honors `stop_hook_active` when a CLI still sends it, and independently blocks
**at most once per user prompt** (a one-shot marker in the OS temp dir), so a
misbehaving turn can never loop. Any error exits silently — the hook can slip, but
never break a session.

Those keys govern the section's **shape**; `style` governs how the bullets are
**written**. `"iso-24495-1"` asks for plain language as ISO 24495-1:2023 frames
it — the reader gets what they need, finds it, understands it, and can use it —
while `"default"` asks only for outcomes and concrete values. The style travels
to both places a TL;DR is asked for: the hook appends its one-sentence reminder
to a block reason, and the skill injects the full contract from
`scripts/tldr_contract.py`, which prints what the project resolves to today with
its own marker and labels in the skeleton. Anything a style cannot express goes
in `style_notes` as free text and is passed through verbatim. The bundled
`reference/plain-language.md` holds the long form and is read only when a
summary needs more than the rules. The skill doubles as the on/off toggle and
as `/observe:tldr style <name>`.

## FAQ capture — `/observe:faq`

The hook applies only a cheap heuristic — a line outside fenced code blocks ends
with a question mark, and the prompt is longer than `min_prompt_chars` — and injects
a single context line; it never blocks. Question marks inside code (ternaries, SQL,
URL query strings) don't count, so pasted snippets don't trigger it. The `faq`
skill makes the actual call: archive only substantive, reusable questions (never
session trivia or secrets), grep the FAQ dir first and update an existing entry
instead of duplicating, otherwise create `NNN-short-slug.md` with the next free
number and frontmatter `id`, `date`, `question`, `topic`, `status`, followed by
the answer in the configured language. It normally fires on its own off the
prompt-time reminder above, but you can also invoke it directly with
`/observe:faq` right after asking a question.

## Improvement logs — `/observe:improve`

You choose the subjects. Each one is an **axis** with a slug, a title, and a
one-sentence `focus` recorded in the config — and one log file that grows,
`docs/improvements/<axis>.md`. Starting an axis is just saying what you want to
improve:

```text
/observe:improve how I work with Claude Code
/observe:improve the English phrasing of my prompts
/observe:improve error handling in the API layer
```

A review reads the last `N` (default 5) transcripts for the current project
from where Claude Code already stores them (under `~/.claude/projects/`), plus,
for an axis about a code domain, that code and its recent `git log`. Then it
does the part that makes the log worth keeping: **it reads what the log already
says.** A habit the log already records is not described again — its heading is
carried forward with a new marker.

| Marker | Means |
| :--- | :--- |
| `new` | not in the log before |
| `recurring` | in the log, and it happened again at a similar rate |
| `improving` | in the log, and measurably less frequent |
| `resolved` | in the log, and absent from this window entirely |

Each habit is written up with its evidence (dates and counts, never transcript
dumps), a concrete improvement you can copy, and the turns or tokens it cost.
Newest review section first; older sections are never rewritten. A window with
nothing worth recording writes nothing — the chat says so instead.

An axis about how you work with Claude Code can carry
`"preset": "session-behaviour"`, which loads a built-in catalogue of
interaction habits worth looking for — vague openers that needed clarification
rounds, context supplied one turn at a time, corrections that came only after
work went the wrong way, over-broad asks, questions re-asked across sessions,
multi-step requests retyped session after session. Every other axis runs on its
`focus` sentence alone.

`off` stops the observing and keeps the log — what you already learned is not
something a toggle should delete. The skill writes only the log file and the
config entry: it never changes your code, and never adopts an improvement for
you.

### Reviews come due on their own

Starting an axis is the whole setup. From then on the `SessionStart` hook
`scripts/improve_reminder.py` works out, per enabled axis, how much evidence
has arrived that no review has read — the sessions recorded since the newest
`## YYYY-MM-DD` heading in that axis's log — and once that reaches `sessions`
(default 5) a starting session opens with one line: how many sessions, since
which review, and the command.

Nothing is stored to make that work. The last review is read from the log, the
evidence from the transcript timestamps, so the count cannot drift out of step
with the log the way a recorded "last run" marker could. The session being
started is never counted as evidence of itself, and a resumed or compacted
session says nothing — an offer belongs at the start of fresh work.

Then it stops. Unlike the TL;DR and FAQ reminders, whose remedy is a few lines
written on the spot, a review reads several whole transcripts: one that started
by itself would spend the session it interrupted. So the line is an offer you
answer.

The offer has its own switch, separate from what is observed:

```text
/observe:improve reminders            # on or off, at what count, and any exceptions
/observe:improve reminders off        # stop offering, for every axis
/observe:improve reminders off game-sabotage   # stop offering for this one only
```

`reminders off <axis>` and `off <axis>` answer different questions. Switching an
axis off stops observing it. Switching its reminders off keeps it observed and
reviewable the moment you ask — you have just said you will pick the moment. An
axis's own setting wins over the section's in both directions, so one noisy axis
does not cost you the reminders you wanted everywhere else.
