# Security policy

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub's private
[vulnerability reporting](https://github.com/satriazoid/antitextai/security/advisories/new)
instead, or the contact address on the repository owner's GitHub profile.

Include the commit or version, the operating system and Python version, the exact command, and
what happened. A minimal reproduction is worth more than a description.

## Scope

antitextai reads and rewrites UTF-8 text files. The realistic risks are narrow:

- Path handling. It walks the files and directories you name, skips binaries and non-UTF-8
  files, and has no mechanism to write outside the paths it was given. Report any escape.
- Destructive rewriting. `clean --write` modifies files in place, so a rule that deletes
  content is treated as a serious bug. `verify --strict` exists to catch that before a commit.
- No network access, no subprocesses, no third-party dependencies, no credentials, no telemetry.

## Supported versions

The latest release on `main`. This is a small project: there are no backport branches, and a fix
lands on `main` and in the next release.
