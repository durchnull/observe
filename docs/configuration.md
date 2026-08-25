# Configuration reference

Every key `.claude/observe/config.json` accepts. The
[README](../README.md#the-config-file) shows the file's shape and where it lives;
this is the full reference for each key.

Every key is optional. A key you leave out is inferred, which is why a plugin
update never hard-fails on an older file — and why `/observe:init` records only
what you actually chose instead of pinning defaults you would then own.

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `tldr.enabled` | `false` | Enforce the closing TL;DR on every meaningful turn. |
| `tldr.marker` | `"## TL;DR"` | Substring the final assistant message must contain. |
| `tldr.min_turn_chars` | `200` | Turns whose final message is this many characters or shorter are exempt — short conversational replies are never padded. `0` enforces on every turn. |
| `tldr.required_subsections` | `["**Informational**"]` | Literal strings that must each appear after the marker — the TL;DR bullets are grouped under these labels. `[]` accepts a flat TL;DR. |
| `tldr.optional_subsections` | `["**Actionable**"]` | Labels the reminder names as add-only-when-non-empty. Never enforced: an optional sub-section with nothing in it is omitted, not written. |
| `tldr.style` | `"default"` | How the bullets are **written**, where the keys above govern the section's shape. `"default"` asks only for outcomes, concrete values and no filler. `"iso-24495-1"` asks for plain language as [ISO 24495-1:2023](https://www.iso.org/standard/78907.html) frames it — short sentences, everyday words, active voice, outcome first, with file names, commands, flags and figures kept exact. `plain`, `plain language` and `ISO 24495-1:2023` are accepted spellings of the same style; a value naming no style resolves to `default` and is reported as unrecognized. `/observe:tldr style <name>` sets it. |
| `tldr.style_notes` | `""` | Free text for what a style cannot hold — a house word, a term to avoid, the reader to write for. Passed through verbatim into the skill's contract and into the hook's reminder (capped at 300 characters there), and it wins over a preference in the style's own guidance. It never overrides exactness: identifiers stay identifiers. |
| `faq.enabled` | `false` | Remind the model to archive substantive questions. |
| `faq.dir` | `"docs/faq/"` | Directory (project-relative) for FAQ entries. `/observe:faq on` records the project's own: `docs/faq/` when it has a `docs/`, otherwise `.claude/observe/faq/`. |
| `faq.language` | `"en"` | Language of FAQ file *content*; frontmatter keys stay English. |
| `faq.min_prompt_chars` | `60` | A prompt must exceed this length (and contain a question line) to trigger the reminder. |
| `improve.dir` | `"docs/improvements/"` | Directory (project-relative) for the per-axis logs, one `<axis>.md` each. Recorded when the first axis starts: `docs/improvements/` when the project has a `docs/`, otherwise `.claude/observe/improvements/`. |
| `improve.sessions` | `5` | How many recent transcripts a review reads, and how many unreviewed sessions make an axis due. `/observe:improve <axis> 20` overrides the reading count for one run. |
| `improve.remind` | `true` | Whether a starting session offers a review that has come due. On by default because naming an axis is already the opt-in; the offer is one line and never starts a review by itself. `false` silences it for every axis. |
| `improve.axes` | `{}` | One entry per subject you chose. **Empty by default — nothing is observed until you name something.** Each carries `enabled`, `title`, a one-sentence `focus`, and optionally `preset`. |
| `improve.axes.<axis>.focus` | — | The sentence every review of that axis is measured against: what to look for, and what "better" means here. |
| `improve.axes.<axis>.preset` | unset | `"session-behaviour"` loads the bundled catalogue of interaction habits to look for. Any other axis runs on its `focus` alone. |
| `improve.axes.<axis>.remind` | unset | Overrides `improve.remind` for this axis alone, in both directions — so one noisy axis can go quiet while the rest still offer reviews, or one axis can keep offering while the section is off. Unset means the section decides. |

To see what a project resolves to today — which capabilities are on, which axes
exist, and which values are configured rather than inferred — the bundled
`scripts/resolve_config.py` prints exactly that and writes nothing;
`/observe:init` shows its report before it asks anything.
