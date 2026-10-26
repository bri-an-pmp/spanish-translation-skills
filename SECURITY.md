# Security

Skill instructions (Markdown) and one helper script (`check_strings.py`, Python standard library only). No package dependencies. CI runs the checker's unit tests with read-only permissions, and its GitHub Action is pinned to an exact commit.

## Reporting a vulnerability

Please report security issues privately through GitHub: **Security → Report a vulnerability** on this repository. Don't open a public issue for security problems.

## How the skills handle untrusted input

- The files you check or translate are treated as data. `l10n-qa` tells Claude explicitly not to follow instructions found inside string files.
- `check_strings.py` only reads the files you name and prints a report. It never writes files, runs other programs, or connects to the network. It parses XML with Python's built-in parser, which does not fetch external entities.

## Checks run on 2026-10-26

| Check | Result |
|---|---|
| Secret patterns (Anthropic, OpenAI, AWS, GitHub, ElevenLabs keys; private keys) and personal email in every file | ✅ None found |
| `claude plugin validate --strict` on the marketplace and plugin | ✅ Passed |
| Checker unit tests | ✅ 11 passed |

## Not covered

These checks are automated and point-in-time. They are not a penetration test or a formal audit.
