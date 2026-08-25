#!/usr/bin/env python3
"""Print the TL;DR contract the host project resolves to today.

Runs with the consuming project's cwd, reads `.claude/observe/config.json` if
there is one, layers it over the defaults in lib_config.py, and prints the whole
contract in one block: whether the capability is on, what each knob resolves to,
the skeleton to copy with this project's own marker and labels in it, and the
rules of the configured output style. The `tldr` skill injects this, so the
format it states is the project's, never the plugin's defaults recited from the
skill body.

Writes nothing, and fail-safe like the hooks: any error prints the default
contract and exits 0, because a summary that goes unwritten is worse than one
written to a default shape.

    python3 tldr_contract.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_config

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def source(section, key):
    return "configured" if key in section else "default"


def value(section, key):
    if key in section:
        return section[key]
    return lib_config.DEFAULTS["tldr"][key]


def labels(section, key):
    """The label list for `key`, dropping anything that is not a usable string."""
    raw = value(section, key)
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str) and item.strip()]


def style_origin(section, style):
    """Where the style came from — and whether the project's value was understood."""
    if "style" not in section:
        return "default"
    return "configured" if style["known"] else "configured, but unrecognized"


def skeleton(marker, required, optional):
    """The section to copy, wearing this project's marker and labels."""
    lines = ["", marker, ""]
    if not required and not optional:
        lines += ["- One bullet per outcome, with the concrete values.", ""]
        return lines
    for label in required:
        lines += [
            label,
            "- The outcome: what happened or what was found, with concrete values",
            "  (amounts, filenames, versions) — never a vague summary.",
            "",
        ]
    for label in optional:
        lines += [
            label,
            "- What is left for the user: decisions, commands to run, authorizations.",
            "- Omit this whole block when there is nothing — never write it empty.",
            "",
        ]
    return lines


def report(cwd):
    config = lib_config.load_config(cwd)
    section = config.get("tldr") if isinstance(config, dict) else None
    present = isinstance(section, dict)
    section = section if present else {}

    if not present:
        state = "OFF — this project has never activated it (`/observe:tldr on`)"
    elif section.get("enabled") is True:
        state = "ON"
    else:
        state = "OFF — switched off in this project (`/observe:tldr on`)"

    marker = value(section, "marker")
    marker = marker if isinstance(marker, str) and marker.strip() else lib_config.DEFAULTS["tldr"]["marker"]
    required = labels(section, "required_subsections")
    optional = labels(section, "optional_subsections")
    style = lib_config.tldr_style(section)
    spec = style["spec"]
    notes = lib_config.tldr_style_notes(section)

    lines = [
        "TL;DR — what this project resolves to today",
        "",
        "  state       %s" % state,
        "  marker      %r (%s)" % (marker, source(section, "marker")),
        "  meaningful  a final message longer than %s characters (%s)"
        % (value(section, "min_turn_chars"), source(section, "min_turn_chars")),
        "  required    %s (%s)" % (", ".join(required) if required else "(none — a flat TL;DR passes)",
                                   source(section, "required_subsections")),
        "  optional    %s (%s)" % (", ".join(optional) if optional else "(none)",
                                   source(section, "optional_subsections")),
        "  style       %s (%s)" % (spec["label"], style_origin(section, style)),
    ]
    if "style" in section and not style["known"]:
        lines.append("              %r is not a style this plugin knows, so the default is used"
                     " — valid values: %s"
                     % (section["style"], ", ".join(sorted(lib_config.TLDR_STYLES))))
    elif style["written"] not in (None, style["id"]):
        lines.append("              written as %r in the config" % style["written"])

    lines += ["", "  Write the closing section like this:"]
    lines += ["  %s" % line if line else "" for line in skeleton(marker, required, optional)]

    lines += ["  Style — %s:" % spec["label"]]
    lines += ["  - %s" % rule for rule in spec["rules"]]
    if spec["reference"]:
        lines += [
            "",
            "  Full guidance, when a summary needs more than those rules:",
            "  %s" % os.path.join(PLUGIN_ROOT, spec["reference"]),
        ]
    if notes:
        lines += ["", "  This project also asks, in its own words:", "  %s" % notes]
    lines += [
        "",
        "  The TL;DR is a summary, not a substitute: the reasoning stays above it.",
        "  A short conversational reply is exempt — never pad a one-line answer.",
    ]
    return "\n".join(lines)


def main():
    print(report(os.getcwd()))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("TL;DR — this project's configuration could not be read. Close the turn with a "
              "'## TL;DR' section: an **Informational** block with the outcome and concrete "
              "values, and an **Actionable** block with what is left to do, omitted when empty.")
    sys.exit(0)
