#!/usr/bin/env python3
"""Print what the host project's observe configuration resolves to today.

Runs with the consuming project's cwd, reads `.claude/observe/config.json` if
there is one, layers it over the defaults in lib_config.py, and prints one
block per capability: whether it is on, what each knob resolves to, and whether
that value was configured or inferred. The `init` skill reads this before it
asks anything, so a project that is already set up is never re-interviewed.

Writes nothing, and fail-safe like the hooks: any error prints a single line
saying the state could not be read and exits 0.

    python3 resolve_config.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_config


def show(value):
    """One-line rendering of a config value, for a human to read."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "(none)"
    if isinstance(value, str):
        return '"%s"' % value
    return str(value)


def knob(section, name, key):
    """`key value (configured|default)` for one capability knob."""
    if key in section:
        return "%s %s (configured)" % (key, show(section[key]))
    return "%s %s (default)" % (key, show(lib_config.DEFAULTS[name][key]))


def section_of(config, name):
    """The capability's own section, and whether the project wrote one at all."""
    raw = config.get(name)
    if isinstance(raw, dict):
        return raw, True
    return {}, False


def switch(section, present):
    if not present:
        return "OFF (never activated)"
    return "ON" if section.get("enabled") is True else "OFF (switched off)"


def documents_dir(cwd, section, name, key="dir"):
    """Where this capability's documents go, plus where that value came from."""
    configured = section.get(key)
    if isinstance(configured, str) and configured.strip():
        return configured, "configured"
    return lib_config.default_docs_dir(cwd, name), "inferred"


def improve_lines(cwd, config):
    """The improve block: the two knobs, then one line per axis."""
    section, _ = section_of(config, "improve")
    axes = section.get("axes")
    axes = axes if isinstance(axes, dict) else {}
    enabled = [slug for slug, axis in axes.items()
               if isinstance(axis, dict) and axis.get("enabled") is True]

    if not axes:
        head = "no axes — nothing is observed"
    else:
        head = "%d %s, %d enabled" % (len(axes), "axis" if len(axes) == 1 else "axes", len(enabled))

    log_dir, log_source = documents_dir(cwd, section, "improvements")
    if log_source == "inferred":
        log_source = "inferred — the first axis records it"
    sessions = section.get("sessions", lib_config.DEFAULT_IMPROVE["sessions"])
    sessions_source = "configured" if "sessions" in section else "default"
    remind = section.get("remind", lib_config.DEFAULT_IMPROVE["remind"])
    remind_source = "configured" if "remind" in section else "default"
    if remind is True:
        remind_effect = ("a session starting with %s unreviewed sessions on an axis "
                         "offers that review" % show(sessions))
    else:
        remind_effect = "no axis ever offers a review on its own"

    lines = [
        "  improve   %s" % head,
        "              dir %s (%s) · sessions %s (%s)" % (log_dir, log_source, show(sessions), sessions_source),
        "              reminders %s (%s) — %s" % (
            "on" if remind is True else "off", remind_source, remind_effect),
    ]
    for slug, axis in sorted(axes.items()):
        if not isinstance(axis, dict):
            lines.append("              ??   %s — entry is not an object, so it is ignored" % slug)
            continue
        log_path = os.path.join(log_dir, "%s.md" % slug)
        state = "exists" if os.path.exists(os.path.join(cwd, log_path)) else "not created yet"
        parts = ['"%s"' % axis.get("title", slug)]
        if axis.get("preset"):
            parts.append("preset %s" % axis["preset"])
        if "remind" in axis:
            parts.append("reminders %s (its own, over the section's)"
                         % ("on" if axis.get("remind") is True else "off"))
        parts.append("log %s (%s)" % (log_path, state))
        lines.append("              %-4s %s — %s" % (
            "ON" if axis.get("enabled") is True else "OFF", slug, " · ".join(parts)))
        focus = axis.get("focus")
        if isinstance(focus, str) and focus.strip():
            lines.append("                   focus: %s" % focus.strip())
    return lines


def report(cwd):
    config = lib_config.load_config(cwd)
    lines = ["observe — what this project resolves to today", ""]

    path = lib_config.CONFIG_RELPATH
    if config is None:
        if os.path.exists(os.path.join(cwd, path)):
            lines.append("  config file        %s — present but unreadable, so nothing is activated" % path)
        else:
            lines.append("  config file        %s — absent, so nothing is activated" % path)
        config = {}
    else:
        version = config.get("configVersion")
        lines.append("  config file        %s — present (configVersion %s)"
                     % (path, version if version is not None else "unset"))

    has_docs = os.path.isdir(os.path.join(cwd, "docs"))
    lines.append("  documents go to    %s" % (
        "docs/ (the project has one)" if has_docs
        else "%s/ (the project has no docs/ directory)" % lib_config.CONFIG_DIR_RELPATH))
    lines.append("")

    tldr, tldr_present = section_of(config, "tldr")
    lines.append("  tldr      %s" % switch(tldr, tldr_present))
    lines.append("              %s · %s" % (knob(tldr, "tldr", "marker"), knob(tldr, "tldr", "min_turn_chars")))
    lines.append("              required %s · optional %s" % (
        knob(tldr, "tldr", "required_subsections").split(" ", 1)[1],
        knob(tldr, "tldr", "optional_subsections").split(" ", 1)[1]))

    faq, faq_present = section_of(config, "faq")
    faq_dir, faq_source = documents_dir(cwd, faq, "faq")
    if faq_source == "inferred":
        faq_source = "inferred — activation records it"
    lines.append("  faq       %s" % switch(faq, faq_present))
    lines.append("              dir %s (%s) · %s · %s" % (
        faq_dir, faq_source, knob(faq, "faq", "language"), knob(faq, "faq", "min_prompt_chars")))

    lines.extend(improve_lines(cwd, config))
    return "\n".join(lines)


def main():
    print(report(os.getcwd()))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("observe — the project's configuration could not be read; treat every capability as off.")
    sys.exit(0)
