# CHANGELOG — TRAKKSTUDIO

## [v1.0.1] - 2026-11-10

### Fixed
- Normalizer default target changed from -1.0 dB to **0.0 dB** (maximum clean peak, no compression). GUI target range now allows 0.0 dB.
- `normalize_file()` default `target_db` and clamp fallback are now 0.0 dB.
- Docs/SRS updated to the new default.

## [Unreleased]

### Added
- APPLY confirm with count: before renaming it asks `N files (mode)?` + scope (`N selected of M` or `ALL` warning) + destination; default No. Kills the whole-pack accident.
- Audio preview: double-click any row (or Play) listens to the sample via audio-only ffplay (`-nodisp -autoexit`); Stop cuts it; `build_exe.py` bundles `ffplay.exe` so the portable plays sound. No modals: missing binary warns in the label.
- Preview auto-cut: selecting another row cuts the running playback without touching Stop; a late `finished` from a killed preview never wipes the new process (identity guard).
- Guide & shortcuts: window Space routes to the visible tab (START Convert/Normalize, Preview rename, Cancel on running batch; never while typing), Help menu (Quick tour F1, Keyboard shortcuts, About), first-run-only welcome tour (`%APPDATA%/TRAKKSTUDIO/.welcomed`, reopen in Help).
- `APP_VERSION` single-source in `gui.py` (footer + About read it from there).
- Tests: `tests/test_guide.py` (10 tests offscreen), `tests/test_player.py` (10 tests, real playback on tones). Suite 45 → 65.

## [v1.0] — 2026-11-02 (build 2 + installer, tag v1.0)

### Added
- Installer `installer/trakkstudio.iss` (Inno Setup 6, per-user no admin, EN/ES) + `build_installer.py` (`STABLE_VERSION` must match the `gui.py` footer) → `dist/TRAKKSTUDIO-Setup-1.0.exe` (210MB). Smoke green: silent install, installed-exe CLI scan, offscreen GUI, silent uninstall.
- App icon (option C, 3 amber layers): `make_icon.py` + `icon.png`/`icon.ico` bundled in the exe (`--icon` + `--add-data`).
- `resource_path()` helper (`_MEIPASS` first): QSS and icon resolve inside the exe.
- Compact Folder column (`pack/sub`, full path in tooltip), hidden row header, FILES panel min 400px, 470/610 splitter.

### Changed
- Placeholder suffix: `@dario` → `@producer` (GUI, tests, SRS).

### Fixed
- Exe showed native light theme: `styles.qss` now travels with `--add-data` (was only ffmpeg `--add-binary`). Rule added to the skills.
- Truncated File column (`N...`): Folder took 220px fixed with absolute paths.

### Removed
- Sidecars next to samples: `rename_log.csv` and `process_report_*.csv` are no longer written (user folders always clean). Summary only in UI panel + `library.db`. No CSV-based undo after this.

## [v1.0-freeze] — 2026-10-27 (SRS freeze, 2-column GUI)

### Added
- Multitool with 3 independent tabs (Organizer / Converter SP-404 / Normalizer peak) + shared SQLite scan.
- Organizer: single `sp404_splice` preset (16 folders), bulk rename preview with RAW-first Replace, Whole name (=New), Prefix/Suffix `@tag`, Numerate, in-place default, `rename_log.csv`.
- Converter with TRAKKCONVERTER heritage (`_sp.wav`, 48k/16-bit/stereo, Force-to-rate, `_sp` skip).
- Normalizer with TRAKKNORMALIZER heritage (`_N.wav`, -1.0dB ±0.5dB, silence skip).
- 2-column GUI (FILES left + tools right, splitter), heritage amber `#F5A623` theme, per-tab CSV reports.
- Tests: 45 pytest (generated tones, skip without ffmpeg).

### Changed
- FR-5 degraded to passive hint (no auto-move, no audio content).
- Rename Copy mode default OFF (in-place).

### Fixed
- Replace with spaces (`Kick 01`) didn't match without Clean-first.
- Category? column ate the width (File truncated).

## [v1.0-build1] — 2026-10-27 (portable)

### Added
- `dist/TRAKKSTUDIO.exe` one-file windowed, 210MB, ffmpeg 9.0.1 + ffprobe bundled (`--add-binary`, verified in build log).
- 10-section README + MAINTENANCE + skill-format CHANGELOG. SRS FROZEN v1.0.
