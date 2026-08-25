"""Shared helpers for observe hook scripts.

Locates and parses the host project's `.claude/observe/config.json`. Every
capability is opt-in: no config file, a missing capability section, or a section
without an explicit `"enabled": true` all resolve to "capability off". Every
helper is also fail-safe: a missing file, bad JSON, or a wrong type resolves to
"capability off" instead of raising — a hook script must never break a session.
"""

import json
import os
import sys

CONFIG_DIR_RELPATH = os.path.join(".claude", "observe")
CONFIG_RELPATH = os.path.join(CONFIG_DIR_RELPATH, "config.json")

# Nothing is active by default. A capability turns on only when its section
# in the config carries an explicit "enabled": true; the remaining keys are
# tuning knobs that fall back to these values.
DEFAULTS = {
    "tldr": {
        "enabled": False,
        "marker": "## TL;DR",
        "min_turn_chars": 200,
        "required_subsections": ["**Informational**"],
        "optional_subsections": ["**Actionable**"],
        # How the bullets are written, over and above the shape the marker and
        # the sub-section labels give them. See TLDR_STYLES below.
        "style": "default",
        "style_notes": "",
    },
    "faq": {
        "enabled": False,
        # FAQ entries are documents a person reads, so they go where a project
        # keeps documents - not into .claude/, which holds its configuration.
        # `/observe:faq on` records the project's actual choice here; this is
        # what a config without a `dir` falls back to.
        "dir": "docs/faq/",
        "language": "en",
        "min_prompt_chars": 60,
    },
}

# `improve` is deliberately absent from DEFAULTS: it has no single on/off
# switch. It is a set of user-chosen axes, each enabled on its own, so "is it
# active" is a per-axis question feature() cannot answer — which is also why
# `remind` defaults to true rather than false. Naming an axis is already the
# opt-in; a second switch to flip afterwards would only be a way to forget.
# These knobs still need one source of truth for resolve_config.py to report,
# so they live here, apart from the capabilities feature() can speak for.
# `dir` has no static default at all - it is inferred by default_docs_dir().
DEFAULT_IMPROVE = {
    "sessions": 5,
    "remind": True,
}

# The output styles `tldr.style` can name. The shape of a TL;DR — its marker
# and its sub-section labels — is already configurable; a style governs the
# other half, how the bullets under those labels are written. Each entry is
# self-contained: `reminder` is the clause the Stop hook appends to a block
# reason (kept to one sentence, because it is read on a blocked turn), `rules`
# is what the skill states as the contract, and `reference` names a bundled
# file with the full guidance, read only when a style needs more than its rules.
TLDR_STYLES = {
    "default": {
        "label": "default",
        "summary": "Concise outcome bullets; no further constraint on the wording.",
        "reminder": "",
        "rules": [
            "Bullets state outcomes and concrete values (amounts, filenames, versions).",
            "No filler such as \"successfully completed the task\".",
        ],
        "reference": None,
    },
    "iso-24495-1": {
        "label": "plain language (ISO 24495-1:2023)",
        "summary": ("The four governing principles of ISO 24495-1:2023 applied to a summary: "
                    "the reader gets what they need, finds it, understands it, and can use it."),
        "reminder": ("Write it in plain language (ISO 24495-1:2023): short sentences, everyday "
                     "words, active voice, the outcome first, and one fact per bullet — but keep "
                     "file names, commands, flags and figures exact."),
        "rules": [
            "Relevant — only what this reader needs to act; drop what the turn above already settled.",
            "Findable — outcome first in each bullet, the qualifier after it; never bury the point mid-sentence.",
            "Understandable — one idea per sentence, roughly 25 words or fewer; everyday words; active voice with the actor named.",
            "Usable — an Actionable bullet says who does what, in the imperative, with the exact command or decision.",
            "Exactness is not simplified away: file names, commands, flags, versions and figures stay verbatim.",
            "Expand an abbreviation the first time unless the reader already uses it daily.",
        ],
        "reference": "reference/plain-language.md",
    },
}

# What a project may write in `tldr.style` and still be understood. Keys are
# normalized (lowercased, everything but a-z0-9 dropped), so "ISO 24495-1:2023",
# "iso-24495-1" and "plain language" all land on the same style. An alias is a
# convenience for a hand-edited config; the canonical ids above are what the
# skill writes and what the documentation names.
TLDR_STYLE_ALIASES = {
    "": "default",
    "default": "default",
    "standard": "default",
    "none": "default",
    "iso": "iso-24495-1",
    "iso24495": "iso-24495-1",
    "iso244951": "iso-24495-1",
    "iso2449512023": "iso-24495-1",
    "plain": "iso-24495-1",
    "plainlanguage": "iso-24495-1",
    "plainenglish": "iso-24495-1",
}

DEFAULT_TLDR_STYLE = "default"


def default_docs_dir(cwd, name):
    """Where to propose putting a project's `name` documents when it has not chosen.

    Inferred once, when the capability is switched on, and written into the
    config — a value that kept re-inferring would move an existing set of
    documents the day someone adds a docs/.
    """
    if isinstance(cwd, str) and cwd and os.path.isdir(os.path.join(cwd, "docs")):
        return os.path.join("docs", name) + "/"
    return os.path.join(CONFIG_DIR_RELPATH, name) + "/"


def read_hook_input():
    """Parse the hook input JSON from stdin. Returns a dict, or None on any failure."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def load_config(cwd):
    """Read the project's observe config. Returns a dict, or None if absent or unreadable."""
    if not isinstance(cwd, str) or not cwd:
        return None
    try:
        with open(os.path.join(cwd, CONFIG_RELPATH), encoding="utf-8") as fh:
            config = json.load(fh)
    except Exception:
        return None
    return config if isinstance(config, dict) else None


def feature(config, name):
    """Merged settings for one capability, or None when it is not activated."""
    if not isinstance(config, dict):
        return None
    section = config.get(name, {})
    if not isinstance(section, dict):
        return None
    merged = dict(DEFAULTS[name])
    merged.update(section)
    return merged if merged.get("enabled") is True else None


def tldr_style(settings):
    """The output style a tldr settings dict resolves to.

    Returns `{"id", "spec", "written", "known"}`. `written` is what the project
    actually put in the file and `known` whether it named a style at all, so a
    caller can report "that is not a style I know" instead of silently
    substituting. An unrecognized or malformed value resolves to the default
    style rather than switching the capability off: a typo in a wording knob
    must never cost the summary itself.
    """
    raw = settings.get("style") if isinstance(settings, dict) else None
    written = raw if isinstance(raw, str) else None
    key = "".join(ch for ch in (written or "").lower() if ch.isalnum())
    known = key in TLDR_STYLE_ALIASES
    style_id = TLDR_STYLE_ALIASES.get(key, DEFAULT_TLDR_STYLE)
    return {"id": style_id, "spec": TLDR_STYLES[style_id],
            "written": written, "known": known}


def tldr_style_notes(settings):
    """The project's free-text wording notes, stripped — "" when it wrote none.

    A schema cannot hold "we say 'deploy', never 'ship'". This key can, and both
    the hook reminder and the skill contract pass it through verbatim.
    """
    notes = settings.get("style_notes") if isinstance(settings, dict) else None
    return notes.strip() if isinstance(notes, str) else ""


def improve_settings(config):
    """The improve section over its defaults, or None when the project has none.

    Unlike feature(), this says nothing about whether anything is observed —
    that is enabled_axes()' answer, one axis at a time.
    """
    if not isinstance(config, dict):
        return None
    section = config.get("improve")
    if not isinstance(section, dict):
        return None
    merged = dict(DEFAULT_IMPROVE)
    merged.update(section)
    return merged


def enabled_axes(section):
    """`{slug: axis}` for every axis switched on — empty when none is."""
    if not isinstance(section, dict):
        return {}
    axes = section.get("axes")
    if not isinstance(axes, dict):
        return {}
    return {slug: axis for slug, axis in axes.items()
            if isinstance(slug, str) and slug.strip()
            and isinstance(axis, dict) and axis.get("enabled") is True}


def reminds(section, axis):
    """Whether this axis offers a review of its own accord.

    The axis's own `remind` wins where it has one, so a single noisy axis is
    silenced without silencing the rest; otherwise the improve section decides
    for all of them. Anything but an explicit true reads as off: for a switch
    that is on by default, the safe direction of a malformed value is silence.
    """
    if isinstance(axis, dict) and "remind" in axis:
        return axis.get("remind") is True
    return isinstance(section, dict) and section.get("remind") is True
