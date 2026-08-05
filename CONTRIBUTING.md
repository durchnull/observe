# Contributing

Thanks for considering it. This is a small, personally maintained project, so before a large
change please **open an issue first** and check the direction. A focused pull request against
an agreed shape gets merged; a large one that takes the project somewhere it was not going is
a lot of wasted effort on both sides. Small fixes — a typo, a dead link, an obvious bug — need
no preamble at all. Just send them.

## Running it locally

Point Claude Code at your clone. Nothing gets installed, and whatever version you already
have stays untouched:

```bash
claude --plugin-dir /path/to/observe
/reload-plugins
```

Loading this way is also how you catch what a linter cannot see — malformed frontmatter or a
broken hook surfaces at load time, not in review.

## Tests

[`docs/development.md`](docs/development.md) is the working reference: what the tests cover and how to try a change. It is kept
current with CI; this file deliberately does not repeat the commands, because a second copy
is the one that goes stale.

Manifests are validated with three separate commands, not one: `claude plugin validate`
against a directory checks only **one** manifest — `marketplace.json` wins when both are
present, and `plugin.json` is silently skipped. All three must exit 0:

```bash
claude plugin validate . --strict
claude plugin validate ./.claude-plugin/plugin.json --strict
claude plugin validate ./.claude-plugin/marketplace.json --strict
```

## What gets merged

- **`main` is the published artifact.** An unpinned install resolves this repository's default
  branch, so every commit on it has to be installable and complete on its own. That is why pull
  requests get read closely rather than quickly.
- **Leave `version` alone.** Bumping `plugin.json`'s version is part of cutting a release, and
  a bump inside a pull request collides with the next one. Describe the change in the pull
  request; the version and its changelog entry are set when it ships.
- **This plugin must work as the only thing a user installs.** It may not reference, import
  from, or assume any other plugin — including by name, in documentation or examples. If a
  change only makes sense when something else is installed, it does not belong here.
- **Nothing project-specific gets baked in.** Branch names, directory layouts and gate commands
  are resolved at runtime from the consuming project, never hardcoded. An installed plugin is
  one machine-global copy shared by every project on the machine, so a value that is right for
  one project is wrong for all the others.
- **Nothing in the plugin's own tree stores user state.** It is replaced wholesale on update, so
  anything written there is lost. State belongs in the consuming project.
- **Commit messages are public writing.** Write them as though the repository were already being
  read by strangers, because it is. No machine paths, no personal addresses, no credentials, and
  no `wip`-grade subjects.

## Licensing

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE),
the same license this project ships under. You keep the copyright on what you write — this is
the ordinary inbound-equals-outbound arrangement, and there is no contributor licence agreement
to sign.

## Security

Please do not use a pull request or a public issue to report a security problem.
[SECURITY.md](SECURITY.md) has the private channel.
