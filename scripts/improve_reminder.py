#!/usr/bin/env python3
"""SessionStart hook: say when an axis has collected enough new evidence.

Every value is derived, none is recorded: the last review is the newest
`## YYYY-MM-DD` heading in that axis's log, and the evidence since then is the
session transcripts modified after that date. No state file, so there is
nothing to migrate into a project and nothing that can disagree with the log.

The injected line is an *offer*. Unlike the TL;DR and FAQ reminders, whose
remedy is a few lines written on the spot, a review reads several whole
transcripts — performing one unasked would spend the session it opened. So
this hook reports that a review is worth running and stops there.

Fires at the start of fresh work only, where the previous sessions are complete
on disk. Fail-safe: any error exits 0 silently.
"""

import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_config

# A resumed, compacted or forked session continues work already in progress;
# only a fresh start is a moment where an offer is not an interruption.
FRESH_START = ("startup", "clear")

# One review section per heading, as the improve skill writes them:
# `## 2026-08-03 — 5 sessions`.
REVIEW_HEADING = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\b")


def sessions_dir(data):
    """The directory Claude Code keeps this project's transcripts in.

    Taken from `transcript_path` rather than rebuilt from cwd: the mapping from
    a project path to its session directory is Claude Code's own, and a guess
    at it would silently count nothing.
    """
    path = data.get("transcript_path")
    if not isinstance(path, str) or not path:
        return None
    directory = os.path.dirname(path)
    return directory if os.path.isdir(directory) else None


def newest_review(log_path):
    """Date of the most recent review in an axis log, or None if never reviewed."""
    newest = None
    try:
        with open(log_path, encoding="utf-8") as fh:
            in_fence = False
            for line in fh:
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                match = REVIEW_HEADING.match(stripped)
                if not match:
                    continue
                try:
                    seen = datetime.date.fromisoformat(match.group(1))
                except ValueError:
                    continue
                if newest is None or seen > newest:
                    newest = seen
    except OSError:
        return None
    return newest


def sessions_since(directory, since, current):
    """Transcripts modified after `since` (all of them when it is None).

    Strictly after, by date: a transcript touched on the day of the review is
    assumed to be one the review read. The session being started is excluded —
    it is evidence of nothing yet.
    """
    try:
        names = os.listdir(directory)
    except OSError:
        return 0
    count = 0
    for name in names:
        if not name.endswith(".jsonl") or name == current:
            continue
        try:
            modified = datetime.date.fromtimestamp(
                os.path.getmtime(os.path.join(directory, name)))
        except OSError:
            continue
        if since is None or modified > since:
            count += 1
    return count


def due_axes(data, settings, axes):
    """One phrase per axis whose unreviewed evidence has reached the threshold."""
    directory = sessions_dir(data)
    if directory is None:
        return []
    try:
        threshold = int(settings.get("sessions"))
    except (TypeError, ValueError):
        threshold = lib_config.DEFAULT_IMPROVE["sessions"]
    if threshold < 1:
        return []

    cwd = data.get("cwd")
    log_dir = settings.get("dir")
    if not isinstance(log_dir, str) or not log_dir.strip():
        log_dir = lib_config.default_docs_dir(cwd, "improvements")
    current = os.path.basename(data.get("transcript_path") or "")

    due = []
    for slug, axis in sorted(axes.items()):
        last = newest_review(os.path.join(cwd, log_dir, "%s.md" % slug))
        count = sessions_since(directory, last, current)
        if count < threshold:
            continue
        title = axis.get("title")
        if not isinstance(title, str) or not title.strip():
            title = slug
        if last is None:
            due.append('%d sessions and no review yet of "%s" (/observe:improve %s)'
                       % (count, title, slug))
        else:
            due.append('%d sessions since the "%s" review of %s (/observe:improve %s)'
                       % (count, title, last.isoformat(), slug))
    return due


def notice(data):
    """The reminder line for this session, or None."""
    if data.get("source") not in FRESH_START:
        return None
    settings = lib_config.improve_settings(lib_config.load_config(data.get("cwd")))
    if settings is None:
        return None
    # Silenced axes drop out before any file is read, so a project that switched
    # reminders off costs nothing at all at session start.
    axes = {slug: axis for slug, axis in lib_config.enabled_axes(settings).items()
            if lib_config.reminds(settings, axis)}
    if not axes:
        return None
    due = due_axes(data, settings, axes)
    if not due:
        return None
    return ("observe: %s. Mention this in one line and let the user decide — a "
            "review reads whole transcripts, so never run one unasked."
            % "; ".join(due))


def main():
    data = lib_config.read_hook_input()
    if data is None:
        return
    line = notice(data)
    if not line:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": line,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
