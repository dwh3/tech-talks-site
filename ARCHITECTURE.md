# Architecture

## Stack
- MkDocs with the Material theme on Python 3.10+, built via `mkdocs build`.

## Routing
- Static site generation; navigation and URLs defined in `mkdocs.yml` and emitted as pre-rendered HTML.

## Content Source
- Markdown pages under `/docs`, data-driven context from `/data/schedule.yml`, assets alongside content in `/docs/assets`.

## Hosting & Deployment
- Published to GitHub Pages using `.github/workflows/deploy.yml`, which uploads the `site/` build artifact.

## Key Directories
- `/docs` - page content and images.
- `/data` - YAML schedule and supporting datasets.
- `/hooks.py` & `macros.py` - extensions that load schedule data, generate missing talk pages, and expose macros for templates.
- `/docs/assets/dashboard.css` - custom styling referenced via `extra_css` in `mkdocs.yml`.
