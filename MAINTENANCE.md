# MAINTENANCE — TRAKKSTUDIO

## Versioning (1 min)

1. Bump `APP_VERSION` in `gui.py` (footer + About read it from there) and `STABLE_VERSION` in `build_installer.py` if there is an installer.
2. Add a `CHANGELOG.md` entry (Added/Fixed/Changed + date).
3. `pytest tests -q` green before committing.

## Rebuild portable exe

```
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe build_exe.py
```

Lands in `dist/TRAKKSTUDIO.exe` (v1.0 actual: 210MB with FFmpeg 9 full build + Qt6; ~120MB with essentials build) with ffmpeg/ffprobe/ffplay bundled via `--add-binary`. Without `icon.ico` it uses the PyInstaller default. Document real size + antivirus false-positive note in the release.

## Installer (Inno Setup 6)

```
python build_installer.py
```

Needs `dist/TRAKKSTUDIO.exe` already built. Lands in `dist/TRAKKSTUDIO-Setup-<version>.exe` (per-user, no admin, EN/ES, with uninstaller). Version in `build_installer.py: STABLE_VERSION` (must match the `gui.py` footer). Unsigned build: SmartScreen will warn on first run.

## Local data / backup

- DB: `%APPDATA%/TRAKKSTUDIO/library.db` (deletable, regenerates on scan).
- First-run flag: `%APPDATA%/TRAKKSTUDIO/.welcomed` (delete to see the tour again).
- Logs: summary in the UI panel + `library.db`. No sidecars next to samples since Build 2 (no CSV-based undo).
- No keys, accounts or cloud: nothing to rotate.

## Release rules

- Main always green (`pytest -q`), `start.bat` tested on a clean machine.
- Tags `v1.0`, `v1.1`… on GitHub for each portable.
