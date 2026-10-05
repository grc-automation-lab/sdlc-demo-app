# sdlc-demo-app

A deliberately tiny Flask "Task Tracker" API. The app itself is not the
point — it exists to generate a realistic history of commits, pull requests,
issues, and CI runs that can be evaluated by a separate project:
[`sdlc-controls-automation`](#) (link once that repo is public).

## Why this exists

This repo is the **evidence source** for four SDLC controls:

| Control | How this repo demonstrates it |
|---|---|
| Segregation of Duties | `CODEOWNERS` + branch protection requiring 1 independent approval, no self-approval |
| Change control (no direct commits to main) | Branch protection rule blocking direct pushes |
| Automated Security Testing Gate | Automated static analysis (SAST) and dependency/software composition analysis (SCA) checks before PR can be merged |
| Change traceability | Every PR is linked to a GitHub Issue via `Closes #<id>` |
| Access review | Repo collaborator list, reviewed and documented periodically |

A fifth control (automated security testing gate) is demonstrated using a
**separate** fork of OWASP Juice Shop, since this app is too small/clean to
trigger real findings.

## Running locally

```bash
pip install -r requirements.txt
python app.py
```

## Running tests

```bash
python -m pytest tests/ -v
```

## Setup

See [SETUP.md](SETUP.md) for the full step-by-step: creating the repo,
configuring branch protection, and seeding the commit/PR/issue history that
the controls automation evaluates.
