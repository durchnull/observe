#!/usr/bin/env python3
"""Test runner for the observe hook scripts. Stdlib only.

Pipes the sample hook inputs from tests/samples/ into each script — the
placeholders __CWD__ and __TRANSCRIPT__ resolve to a per-case temp project —
and asserts on exit code, stdout, and filesystem effects. Every case also
asserts exit code 0: a hook script must never fail hard.

    python3 tests/run_tests.py
"""

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(HERE, os.pardir, "scripts")
SAMPLES_DIR = os.path.join(HERE, "samples")

FULL_CONFIG = {
    "tldr": {
        "enabled": True,
        "marker": "## TL;DR",
        "min_turn_chars": 200,
        "required_subsections": ["**Informational**"],
        "optional_subsections": ["**Actionable**"],
    },
    "faq": {"enabled": True, "dir": "docs/faq/", "language": "en", "min_prompt_chars": 60},
}

CONFIG_DIR = os.path.join(".claude", "observe")


def load_sample(name, cwd=None, transcript=None):
    with open(os.path.join(SAMPLES_DIR, name), encoding="utf-8") as fh:
        data = json.load(fh)
    placeholders = {"__CWD__": cwd, "__TRANSCRIPT__": transcript}
    resolved = {k: placeholders.get(v, v) if isinstance(v, str) else v for k, v in data.items()}
    return json.dumps(resolved)


def run_script(script, stdin_text, tmpdir, cwd=None, args=()):
    """Run a bundled script. `cwd` matters for resolve_config.py, help.py and
    tldr_contract.py, which read the project from their working directory rather
    than from the hook input."""
    env = dict(os.environ, TMPDIR=tmpdir)
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, script)] + list(args),
        input=stdin_text, capture_output=True, text=True, env=env, timeout=30, cwd=cwd,
    )
    return proc.returncode, proc.stdout.strip()


def write_config(project, config):
    os.makedirs(os.path.join(project, CONFIG_DIR), exist_ok=True)
    with open(os.path.join(project, CONFIG_DIR, "config.json"), "w", encoding="utf-8") as fh:
        json.dump(config, fh)


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_silent(rc, out):
    expect(rc == 0, "exit code %d, expected 0" % rc)
    expect(out == "", "expected no output, got: %r" % out)


class Env:
    """Fresh temp project dir + fresh TMPDIR (isolates the one-shot block markers)."""

    def __init__(self, config=None):
        self.root = tempfile.mkdtemp(prefix="observe-test-")
        self.project = os.path.join(self.root, "project")
        self.tmpdir = os.path.join(self.root, "tmp")
        os.makedirs(self.project)
        os.makedirs(self.tmpdir)
        if config is not None:
            write_config(self.project, config)

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


# --- check_tldr.py -----------------------------------------------------------

@case
def tldr_no_config_is_silent(env_factory):
    env = env_factory(config=None)
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_disabled_is_silent(env_factory):
    env = env_factory(config={"tldr": {"enabled": False}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_section_without_enabled_true_is_silent(env_factory):
    # Opt-in is explicit: tuning keys alone never activate a capability.
    env = env_factory(config={"tldr": {"marker": "## TL;DR"}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_enabled_non_boolean_is_silent(env_factory):
    env = env_factory(config={"tldr": {"enabled": 1}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_other_capability_active_is_still_silent(env_factory):
    # Capabilities activate individually: an active faq does not activate tldr.
    env = env_factory(config={"faq": {"enabled": True}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_stop_hook_active_is_silent(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("check_tldr.py", load_sample("stop_hook_active.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_marker_present_passes(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_present.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_marker_missing_blocks(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    result = json.loads(out)
    expect(result.get("decision") == "block", "expected decision=block, got: %r" % out)
    expect("## TL;DR" in result.get("reason", ""), "reason does not name the marker: %r" % out)


@case
def tldr_blocks_only_once_per_prompt(env_factory):
    env = env_factory(config=FULL_CONFIG)
    stdin_text = load_sample("stop_marker_missing.json", cwd=env.project)
    rc, out = run_script("check_tldr.py", stdin_text, env.tmpdir)
    expect(json.loads(out).get("decision") == "block", "first run should block, got: %r" % out)
    rc, out = run_script("check_tldr.py", stdin_text, env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_custom_marker_blocks(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "marker": "## Zusammenfassung"}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_present.json", cwd=env.project), env.tmpdir)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    result = json.loads(out)
    expect(result.get("decision") == "block", "'## TL;DR' must not satisfy a custom marker: %r" % out)
    expect("## Zusammenfassung" in result.get("reason", ""), "reason does not name the custom marker: %r" % out)


@case
def tldr_short_turn_is_exempt(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("check_tldr.py", load_sample("stop_short_turn.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_min_turn_chars_zero_enforces_short_turns(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "min_turn_chars": 0}})
    rc, out = run_script("check_tldr.py", load_sample("stop_short_turn.json", cwd=env.project), env.tmpdir)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    expect(json.loads(out).get("decision") == "block", "min_turn_chars=0 must enforce short turns: %r" % out)


@case
def tldr_flat_tldr_missing_required_subsection_blocks(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("check_tldr.py", load_sample("stop_flat_tldr.json", cwd=env.project), env.tmpdir)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    result = json.loads(out)
    expect(result.get("decision") == "block", "marker without required sub-section must block: %r" % out)
    reason = result.get("reason", "")
    expect("**Informational**" in reason, "reason does not name the required label: %r" % out)
    expect("**Actionable**" in reason, "reason does not name the optional label: %r" % out)


@case
def tldr_optional_subsection_omitted_passes(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("check_tldr.py", load_sample("stop_required_subsection_only.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_empty_required_subsections_accepts_flat_tldr(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "required_subsections": [], "optional_subsections": []}})
    rc, out = run_script("check_tldr.py", load_sample("stop_flat_tldr.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_malformed_subsections_config_accepts_flat_tldr(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "required_subsections": "**Informational**"}})
    rc, out = run_script("check_tldr.py", load_sample("stop_flat_tldr.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_transcript_fallback_blocks(env_factory):
    env = env_factory(config=FULL_CONFIG)
    transcript = os.path.join(SAMPLES_DIR, "transcript_no_marker.jsonl")
    rc, out = run_script("check_tldr.py", load_sample("stop_transcript_fallback.json", cwd=env.project, transcript=transcript), env.tmpdir)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    expect(json.loads(out).get("decision") == "block", "expected decision=block, got: %r" % out)


@case
def tldr_transcript_fallback_passes_and_skips_sidechain(env_factory):
    env = env_factory(config=FULL_CONFIG)
    transcript = os.path.join(SAMPLES_DIR, "transcript_with_marker.jsonl")
    rc, out = run_script("check_tldr.py", load_sample("stop_transcript_fallback.json", cwd=env.project, transcript=transcript), env.tmpdir)
    expect_silent(rc, out)


@case
def tldr_default_style_adds_nothing_to_the_reason(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    reason = json.loads(out).get("reason", "")
    expect("plain language" not in reason.lower(),
           "the default style must not push a wording style: %r" % reason)


@case
def tldr_plain_language_style_is_named_in_the_reason(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style": "iso-24495-1"}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    reason = json.loads(out).get("reason", "")
    expect("ISO 24495-1:2023" in reason, "reason does not name the standard: %r" % reason)
    expect("exact" in reason, "reason drops the identifiers-stay-exact half: %r" % reason)


@case
def tldr_style_spelling_variants_resolve_to_the_same_style(env_factory):
    # A hand-edited config is allowed to say it the way a person would.
    for written in ("plain", "plain language", "ISO 24495-1:2023", "Iso-24495-1"):
        env = env_factory(config={"tldr": {"enabled": True, "style": written}})
        rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
        reason = json.loads(out).get("reason", "")
        expect("ISO 24495-1:2023" in reason, "%r did not resolve to the plain-language style: %r"
               % (written, reason))


@case
def tldr_unknown_style_still_blocks_with_the_default_wording(env_factory):
    # A typo in a wording knob must never cost the summary itself.
    env = env_factory(config={"tldr": {"enabled": True, "style": "iso-99999"}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    result = json.loads(out)
    expect(result.get("decision") == "block", "an unknown style must not disable the hook: %r" % out)
    expect("plain language" not in result.get("reason", "").lower(),
           "an unknown style must fall back to the default wording: %r" % out)


@case
def tldr_non_string_style_is_survived(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style": ["plain"]}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    expect(json.loads(out).get("decision") == "block", "a malformed style must not break the hook: %r" % out)


@case
def tldr_style_notes_reach_the_reason(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style_notes": 'Say "deploy", never "ship".'}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    reason = json.loads(out).get("reason", "")
    expect('Say "deploy", never "ship".' in reason, "the project's own note is missing: %r" % reason)


@case
def tldr_long_style_notes_are_capped(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style_notes": "x" * 900}})
    rc, out = run_script("check_tldr.py", load_sample("stop_marker_missing.json", cwd=env.project), env.tmpdir)
    reason = json.loads(out).get("reason", "")
    expect("x" * 300 in reason, "the note was not passed through at all: %r" % reason)
    expect("x" * 400 not in reason, "a note this long must be capped, not echoed whole: %r" % reason)


@case
def tldr_garbage_stdin_is_silent(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("check_tldr.py", "this is not json {{{", env.tmpdir)
    expect_silent(rc, out)


# --- faq_reminder.py ---------------------------------------------------------

@case
def faq_no_config_is_silent(env_factory):
    env = env_factory(config=None)
    rc, out = run_script("faq_reminder.py", load_sample("prompt_question.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_disabled_is_silent(env_factory):
    env = env_factory(config={"faq": {"enabled": False}})
    rc, out = run_script("faq_reminder.py", load_sample("prompt_question.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_section_without_enabled_true_is_silent(env_factory):
    env = env_factory(config={"faq": {"min_prompt_chars": 10}})
    rc, out = run_script("faq_reminder.py", load_sample("prompt_question.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_other_capability_active_is_still_silent(env_factory):
    env = env_factory(config={"tldr": {"enabled": True}})
    rc, out = run_script("faq_reminder.py", load_sample("prompt_question.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_short_question_is_silent(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("faq_reminder.py", load_sample("prompt_short_question.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_statement_without_question_is_silent(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("faq_reminder.py", load_sample("prompt_long_statement.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_question_marks_only_in_code_are_silent(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("faq_reminder.py", load_sample("prompt_code_question_marks.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_midline_question_mark_is_silent(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("faq_reminder.py", load_sample("prompt_midline_question_mark.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_substantive_question_reminds(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("faq_reminder.py", load_sample("prompt_question.json", cwd=env.project), env.tmpdir)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    output = json.loads(out)["hookSpecificOutput"]
    expect(output.get("hookEventName") == "UserPromptSubmit", "wrong hookEventName: %r" % out)
    context = output.get("additionalContext", "")
    expect("/observe:faq" in context and "docs/faq/" in context,
           "context misses skill or dir: %r" % context)
    expect("\n" not in context, "additionalContext should be one line: %r" % context)


@case
def faq_min_chars_from_config_respected(env_factory):
    env = env_factory(config={"faq": {"enabled": True, "min_prompt_chars": 200}})
    rc, out = run_script("faq_reminder.py", load_sample("prompt_question.json", cwd=env.project), env.tmpdir)
    expect_silent(rc, out)


@case
def faq_garbage_stdin_is_silent(env_factory):
    env = env_factory(config=FULL_CONFIG)
    rc, out = run_script("faq_reminder.py", "]]] not json", env.tmpdir)
    expect_silent(rc, out)


# --- improve_reminder.py -----------------------------------------------------
#
# The reminder is the only automatic part of `improve`, and its whole job is to
# stay quiet: it speaks once a full window of evidence has accumulated that no
# review has read yet. Everything it needs is derived — the last review from the
# log, the evidence from transcript timestamps — so these cases build both.

IMPROVE_LOG_DIR = os.path.join("docs", "improvements")


def improve_config(**overrides):
    """One enabled axis, plus whatever the case overrides."""
    section = {
        "dir": "docs/improvements/",
        "axes": {"session-behaviour": {"enabled": True, "title": "Claude session behaviour"}},
    }
    section.update(overrides)
    return {"improve": section}


def write_sessions(env, count, days_ago=0):
    """`count` past transcripts, plus the one for the session being started.

    Returns the path of the session being started — what `transcript_path`
    carries, and the file the reminder must never count as evidence of itself.
    """
    directory = os.path.join(env.root, "sessions")
    os.makedirs(directory, exist_ok=True)
    stamp = time.time() - days_ago * 86400
    for index in range(count):
        path = os.path.join(directory, "past-%d.jsonl" % index)
        open(path, "w").close()
        os.utime(path, (stamp, stamp))
    current = os.path.join(directory, "current.jsonl")
    open(current, "w").close()
    return current


def write_log(env, slug="session-behaviour", reviewed=None):
    """The axis log, carrying one review section when `reviewed` is a date."""
    directory = os.path.join(env.project, IMPROVE_LOG_DIR)
    os.makedirs(directory, exist_ok=True)
    lines = ["---", "axis: %s" % slug, "---", "", "# %s" % slug, "", "What this log observes.", ""]
    if reviewed is not None:
        lines += ["## %s — 5 sessions" % reviewed, "", "### Context arrives late — new", ""]
    path = os.path.join(directory, "%s.md" % slug)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


def days_ago(count):
    return (datetime.date.today() - datetime.timedelta(days=count)).isoformat()


def run_reminder(env, transcript, sample="session_start.json"):
    return run_script("improve_reminder.py", load_sample(sample, cwd=env.project, transcript=transcript), env.tmpdir)


@case
def improve_no_config_is_silent(env_factory):
    env = env_factory(config=None)
    rc, out = run_reminder(env, write_sessions(env, 9))
    expect_silent(rc, out)


@case
def improve_without_an_axis_is_silent(env_factory):
    # An improve section alone observes nothing: an axis has to be named first.
    env = env_factory(config=improve_config(axes={}))
    rc, out = run_reminder(env, write_sessions(env, 9))
    expect_silent(rc, out)


@case
def improve_switched_off_axis_is_silent(env_factory):
    env = env_factory(config=improve_config(
        axes={"session-behaviour": {"enabled": False, "title": "Claude session behaviour"}}))
    rc, out = run_reminder(env, write_sessions(env, 9))
    expect_silent(rc, out)


@case
def improve_below_the_threshold_is_silent(env_factory):
    env = env_factory(config=improve_config())
    rc, out = run_reminder(env, write_sessions(env, 4))
    expect_silent(rc, out)


@case
def improve_never_reviewed_axis_reminds(env_factory):
    env = env_factory(config=improve_config())
    rc, out = run_reminder(env, write_sessions(env, 5))
    expect(rc == 0, "exit code %d, expected 0" % rc)
    output = json.loads(out)["hookSpecificOutput"]
    expect(output.get("hookEventName") == "SessionStart", "wrong hookEventName: %r" % out)
    context = output.get("additionalContext", "")
    expect("no review yet" in context, "a never-reviewed axis should say so: %r" % context)
    expect("/observe:improve session-behaviour" in context, "context misses the command: %r" % context)
    expect("never run one unasked" in context, "the line must stay an offer: %r" % context)
    expect("\n" not in context, "additionalContext should be one line: %r" % context)


@case
def improve_excludes_the_session_being_started(env_factory):
    # 4 past transcripts + the one for this session = 5 files, one short of the
    # threshold: a session must never be evidence for the review it offers.
    env = env_factory(config=improve_config())
    transcript = write_sessions(env, 4)
    present = [n for n in os.listdir(os.path.dirname(transcript)) if n.endswith(".jsonl")]
    expect(len(present) == 5, "fixture should hold 5 transcripts, has %d" % len(present))
    rc, out = run_reminder(env, transcript)
    expect_silent(rc, out)


@case
def improve_sessions_the_last_review_read_do_not_count(env_factory):
    # Reviewed today, transcripts touched today: already read, so nothing is due.
    env = env_factory(config=improve_config())
    write_log(env, reviewed=datetime.date.today().isoformat())
    rc, out = run_reminder(env, write_sessions(env, 9))
    expect_silent(rc, out)


@case
def improve_counts_only_sessions_after_the_last_review(env_factory):
    env = env_factory(config=improve_config())
    write_log(env, reviewed=days_ago(30))
    rc, out = run_reminder(env, write_sessions(env, 5))
    expect(rc == 0, "exit code %d, expected 0" % rc)
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    expect("5 sessions since" in context, "count wrong: %r" % context)
    expect(days_ago(30) in context, "the line should name the last review date: %r" % context)


@case
def improve_newest_review_heading_wins(env_factory):
    # Logs are newest-first, but a hand-edited one need not be: the reminder
    # takes the latest date it finds, never the first.
    env = env_factory(config=improve_config())
    directory = os.path.join(env.project, IMPROVE_LOG_DIR)
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, "session-behaviour.md"), "w", encoding="utf-8") as fh:
        fh.write("# log\n\n## %s — 5 sessions\n\n## %s — 5 sessions\n"
                 % (days_ago(40), days_ago(1)))
    # Transcripts sit between the two headings: read against the newest review
    # they are old news, read against the first one in the file they would look
    # like a full unreviewed window.
    rc, out = run_reminder(env, write_sessions(env, 9, days_ago=10))
    expect_silent(rc, out)


@case
def improve_reminders_can_be_switched_off(env_factory):
    env = env_factory(config=improve_config(remind=False))
    rc, out = run_reminder(env, write_sessions(env, 9))
    expect_silent(rc, out)


@case
def improve_one_axis_is_silenced_without_silencing_the_rest(env_factory):
    env = env_factory(config=improve_config(axes={
        "session-behaviour": {"enabled": True, "title": "Claude session behaviour", "remind": False},
        "error-handling": {"enabled": True, "title": "Error handling"},
    }))
    rc, out = run_reminder(env, write_sessions(env, 9))
    expect(rc == 0, "exit code %d, expected 0" % rc)
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    expect("Error handling" in context, "the axis still wanting reminders is missing: %r" % context)
    expect("session-behaviour" not in context,
           "an axis with its own remind:false must not appear: %r" % context)


@case
def improve_an_axis_can_opt_in_while_the_section_is_off(env_factory):
    # The per-axis value wins in both directions, or "quiet except this one"
    # would be unreachable.
    env = env_factory(config=improve_config(remind=False, axes={
        "session-behaviour": {"enabled": True, "title": "Claude session behaviour", "remind": True},
        "error-handling": {"enabled": True, "title": "Error handling"},
    }))
    rc, out = run_reminder(env, write_sessions(env, 9))
    expect(rc == 0, "exit code %d, expected 0" % rc)
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    expect("Claude session behaviour" in context, "the opted-in axis is missing: %r" % context)
    expect("error-handling" not in context,
           "an axis following a switched-off section must stay quiet: %r" % context)


@case
def improve_resumed_session_is_silent(env_factory):
    # Resuming continues work in progress; an offer there is an interruption.
    env = env_factory(config=improve_config())
    rc, out = run_reminder(env, write_sessions(env, 9), sample="session_start_resume.json")
    expect_silent(rc, out)


@case
def improve_threshold_follows_the_sessions_knob(env_factory):
    env = env_factory(config=improve_config(sessions=2))
    rc, out = run_reminder(env, write_sessions(env, 2))
    expect(rc == 0, "exit code %d, expected 0" % rc)
    expect("2 sessions" in json.loads(out)["hookSpecificOutput"]["additionalContext"],
           "configured threshold not honored: %r" % out)


@case
def improve_missing_session_directory_is_silent(env_factory):
    env = env_factory(config=improve_config())
    rc, out = run_reminder(env, os.path.join(env.root, "nowhere", "current.jsonl"))
    expect_silent(rc, out)


@case
def improve_garbage_stdin_is_silent(env_factory):
    env = env_factory(config=improve_config())
    rc, out = run_script("improve_reminder.py", "{{{ not json", env.tmpdir)
    expect_silent(rc, out)


@case
def improve_never_writes_to_the_project(env_factory):
    env = env_factory(config=improve_config())
    run_reminder(env, write_sessions(env, 9))
    expect(os.listdir(os.path.join(env.project, ".claude", "observe")) == ["config.json"],
           "the reminder wrote state into the project: %r"
           % os.listdir(os.path.join(env.project, ".claude", "observe")))


# --- resolve_config.py -------------------------------------------------------
#
# The init skill reads this script's output instead of the config file, so what
# it reports is a contract: a wrong "activated" line would have init re-propose
# a setup the project already has, or overwrite one it does not know about.

def resolve(env, cwd=None):
    rc, out = run_script("resolve_config.py", "", env.tmpdir, cwd=cwd or env.project)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    return out


@case
def resolve_no_config_reports_nothing_activated(env_factory):
    env = env_factory(config=None)
    out = resolve(env)
    expect("absent, so nothing is activated" in out, "missing the absent-config line: %r" % out)
    expect("tldr      OFF (never activated)" in out, "tldr not reported off: %r" % out)
    expect("faq       OFF (never activated)" in out, "faq not reported off: %r" % out)
    expect("no axes — nothing is observed" in out, "improve not reported empty: %r" % out)


@case
def resolve_infers_config_dir_without_a_docs_directory(env_factory):
    env = env_factory(config=None)
    out = resolve(env)
    expect("the project has no docs/ directory" in out, "docs/ absence not reported: %r" % out)
    expect(".claude/observe/faq/ (inferred" in out, "faq dir not inferred beside the config: %r" % out)
    expect(".claude/observe/improvements/ (inferred" in out,
           "improvements dir not inferred beside the config: %r" % out)


@case
def resolve_infers_docs_dir_when_the_project_has_one(env_factory):
    env = env_factory(config=None)
    os.makedirs(os.path.join(env.project, "docs"))
    out = resolve(env)
    expect("docs/ (the project has one)" in out, "docs/ presence not reported: %r" % out)
    expect("docs/faq/ (inferred" in out, "faq dir not inferred under docs/: %r" % out)
    expect("docs/improvements/ (inferred" in out, "improvements dir not inferred under docs/: %r" % out)


@case
def resolve_separates_configured_values_from_defaults(env_factory):
    env = env_factory(config={"configVersion": 1, "tldr": {"enabled": True},
                              "faq": {"enabled": False, "language": "de"}})
    out = resolve(env)
    expect("configVersion 1" in out, "configVersion not reported: %r" % out)
    expect("tldr      ON" in out, "activated tldr not reported on: %r" % out)
    expect("faq       OFF (switched off)" in out,
           "an explicitly disabled faq must read differently from one never activated: %r" % out)
    expect('language "de" (configured)' in out, "configured language not marked configured: %r" % out)
    expect("min_prompt_chars 60 (default)" in out, "untouched knob not marked default: %r" % out)


@case
def resolve_lists_every_axis_with_its_state(env_factory):
    env = env_factory(config={
        "improve": {
            "dir": "docs/improvements/",
            "axes": {
                "session-behaviour": {"enabled": True, "title": "Claude session behaviour",
                                      "focus": "How I phrase requests.", "preset": "session-behaviour"},
                "english-phrasing": {"enabled": False, "title": "English phrasing"},
            },
        },
    })
    os.makedirs(os.path.join(env.project, "docs", "improvements"))
    open(os.path.join(env.project, "docs", "improvements", "session-behaviour.md"), "w").close()
    out = resolve(env)
    expect("2 axes, 1 enabled" in out, "axis counts wrong: %r" % out)
    expect("ON   session-behaviour" in out, "enabled axis not reported on: %r" % out)
    expect("OFF  english-phrasing" in out, "disabled axis not reported off: %r" % out)
    expect("session-behaviour.md (exists)" in out, "existing log not detected: %r" % out)
    expect("english-phrasing.md (not created yet)" in out, "missing log not detected: %r" % out)
    expect("focus: How I phrase requests." in out, "focus sentence not echoed: %r" % out)


@case
def resolve_reports_the_reminder_switch(env_factory):
    env = env_factory(config=improve_config())
    expect("reminders on (default)" in resolve(env),
           "naming an axis is the opt-in, so reminders default to on: %r" % resolve(env))
    off = env_factory(config=improve_config(remind=False))
    expect("reminders off (configured)" in resolve(off),
           "an opted-out project must read as off: %r" % resolve(off))
    per_axis = env_factory(config=improve_config(axes={
        "session-behaviour": {"enabled": True, "title": "Claude session behaviour", "remind": False}}))
    expect("reminders off (its own, over the section's)" in resolve(per_axis),
           "an axis overriding the section must say so: %r" % resolve(per_axis))


@case
def resolve_reports_the_tldr_style(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style": "plain",
                                       "style_notes": "Write for a new teammate."}})
    out = resolve(env)
    expect("style plain language (ISO 24495-1:2023) (configured)" in out,
           "the resolved style is not reported: %r" % out)
    expect("Write for a new teammate." in out, "the style notes are not reported: %r" % out)


@case
def resolve_flags_an_unknown_tldr_style(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style": "iso-99999"}})
    out = resolve(env)
    expect("configured, but unrecognized" in out, "an unknown style reads as a real choice: %r" % out)


@case
def resolve_unreadable_config_is_reported_not_ignored(env_factory):
    # Silently treating a broken file as absent would let init overwrite it.
    env = env_factory(config=None)
    os.makedirs(os.path.join(env.project, CONFIG_DIR))
    with open(os.path.join(env.project, CONFIG_DIR, "config.json"), "w", encoding="utf-8") as fh:
        fh.write("{ not json")
    out = resolve(env)
    expect("present but unreadable" in out, "a broken config must be reported, not silently absent: %r" % out)


@case
def resolve_never_writes_to_the_project(env_factory):
    env = env_factory(config=None)
    resolve(env)
    expect(os.listdir(env.project) == [], "resolve_config.py wrote into the project: %r"
           % os.listdir(env.project))


# --- tldr_contract.py --------------------------------------------------------
#
# The tldr skill injects this script, and an injected command that fails aborts
# the whole invocation — so "always exits 0, always prints a usable contract" is
# the contract here, not a nicety.

def contract(env, cwd=None):
    rc, out = run_script("tldr_contract.py", "", env.tmpdir, cwd=cwd or env.project)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    return out


@case
def contract_without_a_config_states_the_defaults_and_says_off(env_factory):
    env = env_factory(config=None)
    out = contract(env)
    expect("never activated" in out, "an unconfigured project must be reported off: %r" % out)
    expect("## TL;DR" in out, "the default marker is missing from the skeleton: %r" % out)
    expect("**Informational**" in out, "the default required label is missing: %r" % out)
    expect("**Actionable**" in out, "the default optional label is missing: %r" % out)


@case
def contract_uses_the_projects_own_marker_and_labels(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "marker": "## Zusammenfassung",
                                       "required_subsections": ["**Ergebnis**"],
                                       "optional_subsections": []}})
    out = contract(env)
    expect("state       ON" in out, "an activated project must be reported on: %r" % out)
    expect("## Zusammenfassung" in out, "the configured marker is missing: %r" % out)
    expect("**Ergebnis**" in out, "the configured label is missing: %r" % out)
    expect("**Informational**" not in out,
           "a default label leaked into a project that replaced it: %r" % out)


@case
def contract_states_the_plain_language_rules_and_its_reference(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style": "plain"}})
    out = contract(env)
    expect("ISO 24495-1:2023" in out, "the style is not named: %r" % out)
    reference = os.path.normpath(os.path.join(SCRIPTS_DIR, os.pardir, "reference", "plain-language.md"))
    expect(os.path.exists(reference), "the style names a reference the plugin does not ship")
    expect(reference in out, "the contract does not point at the bundled guidance: %r" % out)


@case
def contract_default_style_names_no_reference(env_factory):
    env = env_factory(config={"tldr": {"enabled": True}})
    out = contract(env)
    expect("style       default" in out, "the default style is not reported: %r" % out)
    expect("plain-language.md" not in out,
           "the default style must not point at another style's guidance: %r" % out)


@case
def contract_flags_a_style_it_does_not_know(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style": "iso-99999"}})
    out = contract(env)
    expect("not a style this plugin knows" in out, "an unknown style is not flagged: %r" % out)
    expect("iso-24495-1" in out, "the valid values are not listed: %r" % out)


@case
def contract_passes_the_projects_notes_through(env_factory):
    env = env_factory(config={"tldr": {"enabled": True, "style_notes": "Write for a new teammate."}})
    out = contract(env)
    expect("Write for a new teammate." in out, "the project's own note is missing: %r" % out)


@case
def contract_survives_a_broken_config(env_factory):
    env = env_factory(config=None)
    os.makedirs(os.path.join(env.project, CONFIG_DIR), exist_ok=True)
    with open(os.path.join(env.project, CONFIG_DIR, "config.json"), "w", encoding="utf-8") as fh:
        fh.write("{ not json")
    out = contract(env)
    expect("## TL;DR" in out, "a broken config must still yield a usable contract: %r" % out)


@case
def contract_never_writes_to_the_project(env_factory):
    env = env_factory(config=None)
    contract(env)
    expect(os.listdir(env.project) == [], "tldr_contract.py wrote into the project: %r"
           % os.listdir(env.project))


# --- help.py -----------------------------------------------------------------
#
# /observe:help prints this script's output verbatim, so a wrong line here is a
# wrong answer nobody re-words into shape. It also runs where nothing is set up,
# which is exactly where someone types it first.

def help_out(env, cwd=None, args=()):
    rc, out = run_script("help.py", "", env.tmpdir, cwd=cwd or env.project, args=args)
    expect(rc == 0, "exit code %d, expected 0" % rc)
    return out


@case
def help_self_test_agrees_with_what_ships(env_factory):
    env = env_factory(config=None)
    rc, out = run_script("help.py", "", env.tmpdir, args=("--self-test",))
    expect(rc == 0, "the authored command table disagrees with skills/: %r" % out)


@case
def help_lists_every_shipped_command(env_factory):
    env = env_factory(config=None)
    out = help_out(env)
    shipped = sorted(name for name in os.listdir(os.path.join(SCRIPTS_DIR, os.pardir, "skills"))
                     if os.path.isfile(os.path.join(SCRIPTS_DIR, os.pardir, "skills", name, "SKILL.md")))
    for name in shipped:
        expect("/observe:%s" % name in out, "help does not list /observe:%s: %r" % (name, out))
    expect("out of date" not in out, "help reported drift against skills/: %r" % out)


@case
def help_in_a_bare_project_says_nothing_is_activated(env_factory):
    env = env_factory(config=None)
    out = help_out(env)
    expect("Nothing is activated here" in out, "a bare project is not reported as inactive: %r" % out)
    expect("/observe:init" in out, "help does not say how to set the project up: %r" % out)


@case
def help_reports_the_activated_capabilities(env_factory):
    env = env_factory(config={
        "tldr": {"enabled": True, "style": "plain"},
        "faq": {"enabled": True, "dir": "docs/faq/"},
        "improve": {"dir": "docs/improvements/", "axes": {
            "prompts": {"enabled": True, "title": "Prompts", "focus": "x"},
            "english": {"enabled": False, "title": "English", "focus": "y"}}},
    })
    out = help_out(env)
    expect("TL;DR: on" in out, "an active tldr is not reported: %r" % out)
    expect("ISO 24495-1:2023" in out, "the configured style is not reported: %r" % out)
    expect("FAQ capture: on" in out, "an active faq is not reported: %r" % out)
    expect("1 of 2 axes on (prompts)" in out, "the axis count is wrong: %r" % out)


@case
def help_survives_a_broken_config(env_factory):
    env = env_factory(config=None)
    os.makedirs(os.path.join(env.project, CONFIG_DIR), exist_ok=True)
    with open(os.path.join(env.project, CONFIG_DIR, "config.json"), "w", encoding="utf-8") as fh:
        fh.write("{ not json")
    out = help_out(env)
    expect("could not be read" in out, "a broken config must be reported, not hidden: %r" % out)
    expect("/observe:tldr" in out, "the command list must survive a broken config: %r" % out)


@case
def help_never_writes_to_the_project(env_factory):
    env = env_factory(config=None)
    help_out(env)
    expect(os.listdir(env.project) == [], "help.py wrote into the project: %r"
           % os.listdir(env.project))


# --- harness -----------------------------------------------------------------

def main():
    failures = 0
    for fn in CASES:
        envs = []

        def env_factory(config=None):
            env = Env(config)
            envs.append(env)
            return env

        try:
            fn(env_factory)
            print("ok   %s" % fn.__name__)
        except Exception as exc:
            failures += 1
            print("FAIL %s: %s" % (fn.__name__, exc))
        finally:
            for env in envs:
                env.cleanup()
    print("\n%d/%d cases passed" % (len(CASES) - failures, len(CASES)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
