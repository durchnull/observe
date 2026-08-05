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
