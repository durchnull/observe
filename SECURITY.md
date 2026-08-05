# Security policy

## Supported versions

This project is pre-1.0. Only the latest released version is supported — there are no
backported fixes to earlier tags. If you are pinned to an older ref, the fix for anything
reported here will arrive as a new release, not as a patch to the version you pinned.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.** A public issue tells everyone
at the same moment, including anyone who would use it, and this plugin runs inside other people's projects.

Use GitHub's private vulnerability reporting instead: the **Security** tab of
[durchnull/observe](https://github.com/durchnull/observe/security/advisories/new) → *Report a vulnerability*.
That channel is private between you and the maintainer, and it exists so you can share
details without publishing them.

Please include what you did, what happened, and what you expected instead. A minimal
reproduction is worth more than a long description. You will get an acknowledgement within
a few days; if a report is valid, you will be told when a fix ships and credited in the
release notes unless you ask not to be.

## What counts as a vulnerability here

`observe` installs hooks that run on every session turn and writes documents into the host project. In scope: any path where observed content is executed rather than recorded; any write outside the project's configured documentation directory; and any case where it captures and persists content into a file that a reasonable reader would not expect it to keep — a log that quietly records more than it says it does is a privacy failure, and it is in scope here.

## What does not

Not every defect is a security problem, and treating them alike wastes the private channel:

- A crash, a wrong result, or a confusing report with no security consequence — open a normal issue.
- Behaviour that requires the user to have already granted a permission the tool asks for plainly.
- Anything that needs an attacker to already control the machine or the repository, since at that point they do not need this plugin.

There is no bug bounty. This is a personal open-source project, and the thanks are sincere
but non-monetary.
