#!/usr/bin/env python3
"""Stop hook: require the configured TL;DR marker in the final assistant message.

Reads the hook input from stdin. When the tldr capability is activated and the
turn's final assistant text lacks the configured marker — or lacks one of the
configured required sub-section labels after it — prints a
`{"decision": "block", "reason": ...}` JSON so the model finishes the turn
properly. Fail-safe: on any error it exits 0 with no output, and it blocks at
most once per user prompt so a misbehaving turn can never loop.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_config


def last_assistant_text_from_transcript(path):
    """Text of the last assistant message in the transcript JSONL, or None.

    Fallback for CLI versions that do not send `last_assistant_message` —
    the docs warn the transcript file may lag the in-memory conversation.
    """
    text = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if not isinstance(entry, dict) or entry.get("type") != "assistant":
                continue
            if entry.get("isSidechain"):
                continue
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            parts = []
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text") or "")
            if any(part.strip() for part in parts):
                text = "\n".join(parts)
    return text


def config_labels(settings, key):
    """List of non-empty string labels under `key`; [] on any other shape."""
    value = settings.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def already_blocked(session_id, prompt_id):
    """One-shot guard: True if this prompt was blocked before; records the block otherwise.

    `stop_hook_active` disappeared from the hooks reference (2026-07 check), so
    loop protection cannot rely on it — a marker file per (session, prompt) in
    the OS temp dir caps this hook at a single block per user prompt.
    """
    marker_dir = os.path.join(tempfile.gettempdir(), "claude-observe")
    name = "%s-%s.blocked" % (session_id or "unknown-session", prompt_id or "no-prompt-id")
    marker_path = os.path.join(marker_dir, name)
    if os.path.exists(marker_path):
        return True
    try:
        os.makedirs(marker_dir, exist_ok=True)
        with open(marker_path, "w", encoding="utf-8") as fh:
            fh.write("1\n")
    except Exception:
        pass
    return False


def main():
    data = lib_config.read_hook_input()
    if data is None:
        return
    # No longer documented, but honored if an older CLI still sends it.
    if data.get("stop_hook_active"):
        return
    settings = lib_config.feature(lib_config.load_config(data.get("cwd")), "tldr")
    if settings is None:
        return
    marker = settings.get("marker")
    if not isinstance(marker, str) or not marker.strip():
        return

    text = data.get("last_assistant_message")
    if not isinstance(text, str) or not text.strip():
        transcript_path = data.get("transcript_path")
        if not isinstance(transcript_path, str) or not transcript_path:
            return
        text = last_assistant_text_from_transcript(transcript_path)
    if not text:
        # No evidence either way — never block on a message we could not read.
        return
    try:
        min_turn = int(settings.get("min_turn_chars"))
    except (TypeError, ValueError):
        return
    if len(text.strip()) <= min_turn:
        # Short conversational replies are exempt — a one-line answer should
        # not be padded with a summary. Set min_turn_chars to 0 to enforce always.
        return
    required = config_labels(settings, "required_subsections")
    optional = config_labels(settings, "optional_subsections")
    # The last marker occurrence is the closing section; earlier hits are prose.
    idx = text.rfind(marker)
    if idx >= 0 and all(label in text[idx + len(marker):] for label in required):
        return
    if already_blocked(data.get("session_id"), data.get("prompt_id")):
        return
    reason = (
        "End your turn with a '%s' section: 2-5 bullets with the outcome, "
        "concrete values, and the next step." % marker
    )
    if required:
        reason += " Group the bullets under the sub-section label%s %s." % (
            "s" if len(required) > 1 else "",
            ", ".join("'%s'" % label for label in required),
        )
    if optional:
        reason += (
            " Add %s only when there are bullets for it — an empty sub-section "
            "is omitted, not written." % ", ".join("'%s'" % label for label in optional)
        )
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
