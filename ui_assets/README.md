# UI Assets

Files the UI's `ui-config.json` points at — a footer, a logo, anything a
deployment wants to drop in without rebuilding the image.

This directory is mounted read-only at `/usr/src/app/ui_assets` in the UI
container, so a config refers to what lands here as `ui_assets/<file>`:

Point `UI_ASSETS` in `.env` at a different directory to swap the set, the way
`UI_CONFIG` swaps the page set. The scenarios deployment uses
`UI_ASSETS=./scenarios/assets`.

Not to be confused with `../assets/`, which holds map data the application code
reads directly and which ships inside the image.
