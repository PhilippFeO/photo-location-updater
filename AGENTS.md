# AGENTS

This file gives coding agents the minimum project context needed to work safely and quickly.

## Scope

- Python desktop app for editing photo EXIF GPS metadata.
- Main workflow and usage details are documented in [README.md](README.md).

## Quick Start

- Create env: `python -m venv venv`
- Activate (Windows): `venv\\Scripts\\activate`
- Activate (Linux/macOS): `source venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run app: `python main.py`

## Key Files

- [main.py](main.py): PyQt6 entrypoint, UI event handlers, map/webchannel integration.
- [metadataHandler.py](metadataHandler.py): EXIF read/write and coordinate conversion.
- [locationHistoryLoader.py](locationHistoryLoader.py): Google Takeout parsing + closest timestamp match.
- [googleTakeOutSplitter.py](googleTakeOutSplitter.py): split large Takeout file by month.
- [map.html](map.html): Leaflet map embedded in Qt WebEngine.
- [design.py](design.py): generated UI class.

## Project Conventions

- Treat [design.py](design.py) as generated code. Regenerate with `pyuic6` instead of manual edits.
- Preserve current PyQt6 + WebEngine dependency compatibility in [requirements.txt](requirements.txt).
- Prefer focused edits in source modules over broad refactors.
- Keep user-facing behavior unchanged unless task explicitly requests behavior changes.

## Safety Notes

- Metadata writes are in-place; no automatic rollback. Avoid introducing silent bulk-write behavior.
- The app currently uses module-level state in [main.py](main.py). Be careful when changing signal/slot flows.
- Google Takeout parsing handles multiple formats; keep backward compatibility when adjusting parsers.

## Validation

- No automated test suite is configured in this repository.
- For changes, run `python main.py` and verify:
  - folder selection and image listing
  - map loads and click-to-coordinate flow
  - metadata save path
  - optional Google Takeout loading flow
