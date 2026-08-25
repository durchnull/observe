# Style: plain language (ISO 24495-1:2023)

What to do differently when a project sets `"style": "iso-24495-1"` in the
`tldr` section of `.claude/observe/config.json`. Read this only when writing a
TL;DR for such a project needs more than the rules the skill already states.

**ISO 24495-1:2023** — *Plain language — Part 1: Governing principles and
guidelines* — is a published international standard, sold by ISO and its member
bodies. This file does not reproduce it. It states the four principles the
standard is organised around, applies them to one small artefact — a closing
summary — and adds the practice that follows from them. Buy the standard from
[iso.org](https://www.iso.org/standard/78907.html) if you need its own wording,
its guidance on testing documents with readers, or a citable source.

## The four principles, applied to a TL;DR

Plain language is defined by what the *reader* can do with the text, not by a
word count or a readability score. The four principles say a reader:

| Principle | In a TL;DR |
| :--- | :--- |
| **Gets what they need** | Only what this reader has to know now. The turn above already carried the reasoning; the summary carries the outcome and what is left to do. |
| **Can find what they need** | The outcome comes first in the bullet — the qualifier, the caveat and the method come after it. Nothing that matters is buried mid-sentence. |
| **Can understand what they find** | One idea per sentence, everyday words, active voice, the actor named. A reader should not have to re-read a bullet to parse it. |
| **Can use what they find** | An actionable bullet is something a person can do: who does what, in the imperative, with the exact command, path or decision. |

The reader is one person: the user of this session. Not a stranger, not a
compliance auditor, not a future search engine.

## What this changes in practice

- **Short sentences, one idea each.** Aim under roughly 25 words. A bullet with
  two ideas is two bullets, or one bullet and a dropped idea.
- **Everyday words.** "Use" not "utilise", "start" not "initiate", "before" not
  "prior to". Where a plain word exists, it wins.
- **Active voice, actor named.** "The hook blocks the turn", not "the turn is
  blocked". A passive that hides who acts hides who has to act next.
- **Front-load the outcome.** "Two tests fail after the rename" beats "After the
  rename, which touched four files, two tests fail".
- **No hedging stack.** "This may possibly need" is "this needs" or it is not a
  finding worth a bullet.
- **No filler.** "Successfully completed the task" says nothing; delete it and
  state the result.
- **Expand an abbreviation the first time** unless the reader uses it daily. A
  project's own vocabulary counts as daily; a standard's number does not.
- **Numbers as digits**, with the unit: "3 files", "0.2.0", "200 characters".

## What plain language is not

**It is not lower precision.** The names of files, commands, flags, versions,
branches and figures are the part a reader acts on, and they stay verbatim —
`min_turn_chars`, `/observe:tldr on`, `0.2.0`, `docs/faq/`. Simplifying an
identifier is not plain language; it is a wrong answer with a friendly tone.
Everything *around* the exact names is what gets simpler.

**It is not shorter at the cost of the content.** A summary that drops a
decision the user has to make is not plain; it is incomplete. Plain language
removes the words that carry no information, not the information.

**It is not a different register for bad news.** A failed step, a skipped test,
a blocked push: name it in the same plain sentence you would use for a success.
Softening is a form of burying, and burying breaks the second principle.

## Before and after

> **Not:** In the interest of ensuring consistency across the plugin surface, a
> comprehensive refactoring of the configuration resolution layer was
> undertaken, which may potentially require subsequent validation.
>
> **Plain:** The config resolver now handles all four capabilities the same way.
> Run `python3 tests/run_tests.py` to check it.

> **Not:** It was determined that the aforementioned tests are currently
> non-passing subsequent to the implementation of the changes described above.
>
> **Plain:** Two tests fail after this change: `tldr_custom_marker_blocks` and
> `tldr_short_turn_is_exempt`.

## When the project also left a note

`tldr.style_notes` holds what no schema can — a house word, a term to avoid, a
reader to write for. It is the project's own sentence and it wins over a
preference in this file. It never wins over the exactness rule: a note asking
for simpler wording still leaves every identifier exact.
