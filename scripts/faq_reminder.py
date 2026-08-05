#!/usr/bin/env python3
"""UserPromptSubmit hook: remind the model to archive substantive questions.

Cheap heuristic only — a line outside fenced code blocks ends with a question
mark, and the prompt exceeds the configured length. Question marks inside
code (ternaries, SQL, URL query strings) do not count. The actual judgment
(substantive? reusable? duplicate?) belongs to the model via the faq skill;
this hook only injects context and never blocks.
Fail-safe: any error exits 0 silently.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_config

# Trailing punctuation a question line may carry after the question mark,
# e.g. markdown emphasis or a closing quote: 'Can we ship **today?**'.
TRAILING_PUNCTUATION = "\"')]}*_"


def has_question_line(prompt):
    """True if a line outside fenced code blocks ends with a question mark."""
    in_fence = False
    for line in prompt.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.rstrip(TRAILING_PUNCTUATION).endswith("?"):
            return True
    return False


def notice(data):
    """The reminder line for a question-shaped prompt, or None."""
    settings = lib_config.feature(lib_config.load_config(data.get("cwd")), "faq")
    if settings is None:
        return None
    prompt = data.get("prompt")
    if not isinstance(prompt, str):
        return None
    try:
        min_chars = int(settings.get("min_prompt_chars"))
    except (TypeError, ValueError):
        return None
    if len(prompt.strip()) <= min_chars or not has_question_line(prompt):
        return None
    faq_dir = settings.get("dir")
    if not isinstance(faq_dir, str) or not faq_dir.strip():
        faq_dir = lib_config.DEFAULTS["faq"]["dir"]
    return ("observe: this prompt looks like a question. If it is "
            "substantive and reusable (not session trivia), invoke the "
            "faq skill (/observe:faq) to archive it under '%s'." % faq_dir)


def main():
    data = lib_config.read_hook_input()
    if data is None:
        return
    line = notice(data)
    if not line:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": line,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
