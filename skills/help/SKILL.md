---
description: Print what the observe plugin does, the commands it ships, and which of its capabilities this project has switched on.
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/help.py":*)
---

# Observe help

The block below is the entire reply. `scripts/help.py` rendered it before you read this: the
version and documentation link come from the manifest, the command list is checked against what
`skills/` actually ships, and the "In this project" lines were measured in the directory this was
run from.

!`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/help.py"`

Print it **verbatim** — no summary, no reordering, no extra commands, no explaining a command in
your own words. A help text that reads differently each session is exactly what this command
replaces. If the block carries an "out of date" warning, print that too: it tells the reader the
plugin ships something the text does not list.

This command only reads. It never writes `.claude/observe/config.json`, never switches a capability
on, and never starts an improvement axis — if the user wants one of the listed commands, they type
it.
