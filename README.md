# Tech Talks Site

Static MkDocs Material site for a biweekly lecture series covering engineering topics.

## Prerequisites
- Python 3.10+ installed.
- Activate a virtualenv before running `pip install -r requirements.txt` to keep dependencies isolated.

## Quick Start
1. `python -m venv .venv` (optional but recommended)
2. Activate the virtualenv and run `pip install -r requirements.txt`
3. `mkdocs serve` to preview at http://127.0.0.1:8000

## Validation
Run `python validate_schedule.py` to validate `data/schedule.yml` before building or pushing.

## Dependency Policy
Dependencies in `requirements.txt` are pinned to ensure reproducible builds. Review and refresh the versions at least quarterly to pick up fixes and security updates.

## Documentation
- [AGENT.md](AGENT.md) - Codex operating playbook.
- [ARCHITECTURE.md](ARCHITECTURE.md) - Site structure and deployment notes.
- [OPERATIONS.md](OPERATIONS.md) - Runbooks and constraints.
- [CONTENT_MODEL.md](CONTENT_MODEL.md) - Talks data schema reference.
