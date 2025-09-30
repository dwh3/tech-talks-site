# Operations

## Commands
- `pip install -r requirements.txt` to install MkDocs dependencies.
- `python validate_schedule.py` to lint the schedule data.
- `mkdocs serve` for local preview at http://127.0.0.1:8000.
- `mkdocs build` to generate the static `site/` output.

## Deployment
- Workflow `.github/workflows/deploy.yml` runs on pushes to `main` and manual `workflow_dispatch`, building from `main` and publishing the GitHub Pages branch.
- Deployments use the `github-pages` environment; no approvals are required in the workflow.
- Manual fallback: `mkdocs gh-deploy` after installing dependencies pushes the latest build to Pages.
- No preview or staging flow is configured for pull requests.

## Constraints
- Public URLs must remain stable; avoid breaking existing slugs in `/data/schedule.yml` and navigation.
- No authentication layer; content is fully static.
