#!/usr/bin/env python3
"""Renders ``/observe:help`` — the plugin explaining itself, deterministically.

Why a script rather than skill prose: help written into a ``SKILL.md`` body is
re-worded by whichever model reads it, and goes stale the day a command is
added. Everything printed here is either measured — the version and the
documentation link from the manifest, the shipped command set from ``skills/``,
the project lines from the directory this ran in — or the one authored table
below, which is compared against ``skills/`` on every run and in
``tests/run_tests.py``.

The project lines matter more here than in most plugins: installing observe
activates nothing, so "what does this do" and "is any of it on in *this* repo"
are the same question, and answering only the first would be answering the
easier one.

Read-only by construction: no writes, no network. It has to work in a directory
that has never seen this plugin, because that is exactly where someone types
``/observe:help`` first.

    python3 scripts/help.py              # the block /observe:help prints
    python3 scripts/help.py --self-test  # fails if the table and skills/ disagree
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The one authored thing in this file: what each command is for, in the order
# someone meets them rather than alphabetically. A command added to skills/
# without a line here fails --self-test, which is what keeps this honest.
COMMANDS = [
    ("init", "Set this project up in one pass — pick the capabilities, name every subject to improve. Writes one config file, never code. Safe to re-run."),
    ("tldr", "End every meaningful turn with a closing summary. `on`, `off`, `status`, and `style <name>` for how it is written."),
    ("faq", "Archive a substantive question as a numbered markdown entry, deduplicated against the ones already there. `on`, `off`, `status`."),
    ("improve", "Name something to get better at; each subject gets its own growing log of what changed. Also `status`, `off <axis>`, `reminders off <axis>`."),
    ("help", "This text — what the plugin is for, what it ships, and where this project stands. Reads only; changes nothing."),
]

TAGLINE = (
    "an opt-in session observer: a closing TL;DR on every meaningful turn, FAQ capture "
    "of the questions worth keeping, and one improvement log per subject you name"
)


def manifest():
    try:
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def shipped_commands():
    """What the plugin ships right now, read from disk rather than believed."""
    skills = os.path.join(ROOT, "skills")
    if not os.path.isdir(skills):
        return []
    return sorted(name for name in os.listdir(skills)
                  if os.path.isfile(os.path.join(skills, name, "SKILL.md")))


def drift():
    shipped = shipped_commands()
    documented = [name for name, _ in COMMANDS]
    return (
        [c for c in documented if c not in shipped],
        [c for c in shipped if c not in documented],
    )


def switch(section):
    return "on" if isinstance(section, dict) and section.get("enabled") is True else "off"


def tldr_line(config):
    section = config.get("tldr")
    section = section if isinstance(section, dict) else {}
    state = switch(section)
    if state == "off":
        return "TL;DR: off — `/observe:tldr on` turns it on."
    style = lib_config.tldr_style(section)
    written = ", written in %s" % style["spec"]["label"] if style["id"] != "default" else ""
    return "TL;DR: on%s — every turn over %s characters ends with a summary." % (
        written, section.get("min_turn_chars", lib_config.DEFAULTS["tldr"]["min_turn_chars"]))


def faq_line(config, cwd):
    section = config.get("faq")
    section = section if isinstance(section, dict) else {}
    if switch(section) == "off":
        return "FAQ capture: off — `/observe:faq on` turns it on."
    directory = section.get("dir")
    if not (isinstance(directory, str) and directory.strip()):
        directory = lib_config.default_docs_dir(cwd, "faq")
    return "FAQ capture: on — entries go to `%s`." % directory


def improve_line(config, cwd):
    section = config.get("improve")
    section = section if isinstance(section, dict) else {}
    axes = section.get("axes")
    axes = axes if isinstance(axes, dict) else {}
    enabled = sorted(lib_config.enabled_axes(section))
    if not axes:
        return ("Improvement logs: nothing is observed yet — name a subject to start one, "
                "e.g. `/observe:improve how I work with Claude Code`.")
    directory = section.get("dir")
    if not (isinstance(directory, str) and directory.strip()):
        directory = lib_config.default_docs_dir(cwd, "improvements")
    if not enabled:
        return "Improvement logs: %d axis/axes recorded, none switched on. Logs live in `%s`." % (
            len(axes), directory)
    return "Improvement logs: %d of %d axes on (%s). Logs live in `%s`." % (
        len(enabled), len(axes), ", ".join(enabled), directory)


def project_lines(cwd):
    """The consuming project as it stands in this cwd.

    Installing this plugin activates nothing, so the honest answer to "what is
    running here" is usually "none of it" — and that has to be said in the
    words that also say how to change it.
    """
    config = lib_config.load_config(cwd)
    if config is None:
        if os.path.exists(os.path.join(cwd, lib_config.CONFIG_RELPATH)):
            return [
                "`%s` exists but could not be read, so every capability is off."
                % lib_config.CONFIG_RELPATH,
                "Fix or delete that file; nothing else here is affected by it.",
            ]
        return [
            "Nothing is activated here — there is no `%s`, and that is what every "
            "capability reads before doing anything." % lib_config.CONFIG_RELPATH,
            "`/observe:init` sets the project up in one pass, or switch one on by itself: "
            "`/observe:tldr on`, `/observe:faq on`, `/observe:improve <subject>`.",
        ]
    return [tldr_line(config), faq_line(config, cwd), improve_line(config, cwd)]


def render(cwd):
    m = manifest()
    missing, undocumented = drift()
    out = ["**%s %s** — %s." % (m.get("name", "observe"), m.get("version", "?"), TAGLINE), ""]
    out += ["**Installing activates nothing.** Every capability is off until a project switches "
            "it on, and everything written stays in that project.", "", "**Commands**"]
    out += ["- `/observe:%s` — %s" % (name, does) for name, does in COMMANDS]
    out += ["", "**In this project**"]
    out += ["- %s" % line for line in project_lines(cwd)]
    if m.get("homepage"):
        out += ["", "Full documentation: %s" % m["homepage"]]
    # Never silently correct a mismatch. A reader who is told the text is behind
    # can go look; a reader handed a quietly incomplete list cannot.
    if missing or undocumented:
        out += ["", "**⚠ This help text is out of date**"]
        out += ["- lists /observe:%s, which no longer ships" % c for c in missing]
        out += ["- /observe:%s ships but is not listed above" % c for c in undocumented]
    return "\n".join(out)


def self_test():
    missing, undocumented = drift()
    problems = ["help.py lists /observe:%s, but skills/%s/SKILL.md does not exist" % (c, c)
                for c in missing]
    problems += ["skills/%s/SKILL.md ships, but help.py never mentions /observe:%s" % (c, c)
                 for c in undocumented]
    if not manifest().get("version"):
        problems.append("plugin.json is unreadable or has no version — help would print a version of '?'")
    for problem in problems:
        print("FAIL: %s" % problem, file=sys.stderr)
    if problems:
        return 1
    print("help --self-test: OK (%d commands documented and shipped)" % len(COMMANDS))
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        sys.exit(self_test())
    try:
        print(render(os.getcwd()))
    except Exception:
        # Help is the one command someone runs when nothing else is working.
        print("**observe** — an opt-in session observer. `/observe:init` sets up a project; "
              "`/observe:tldr`, `/observe:faq` and `/observe:improve` are the capabilities. "
              "This help text could not be rendered in full.")
    sys.exit(0)
