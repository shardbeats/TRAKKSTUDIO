# CHANGELOG — TRAKKSTUDIO

## [Unreleased]

### Added
- Guía y atajos: Space de ventana rutea al tab visible (START Convert/Normalize, Preview rename, Cancel si hay batch; nunca mientras escribes), menú Help (Quick tour F1, Keyboard shortcuts, About), tour de bienvenida solo en primer arranque (`%APPDATA%/TRAKKSTUDIO/.welcomed`, revívelo en Help).
- `APP_VERSION` single-source en `gui.py` (footer + About la leen de ahí).
- Tests: `tests/test_guide.py` (7 tests offscreen). Suite 45 → 52.

## [v1.0] — 2026-11-02 (build 2 + installer, tag v1.0)

### Added
- Installer `installer/trakkstudio.iss` (Inno Setup 6, per-user sin admin, EN/ES) + `build_installer.py` (`STABLE_VERSION` debe igualar el footer de `gui.py`) → `dist/TRAKKSTUDIO-Setup-1.0.exe` (210MB). Smoke verde: install silencioso, scan CLI del exe instalado, GUI offscreen, uninstall silencioso.
- `resource_path()` helper (`_MEIPASS` primero): QSS e icono resuelven dentro del exe.
- Columna Folder compacta (`pack/sub`, tooltip con ruta completa), header de filas oculto, panel FILES mínimo 400px, splitter 470/610.

### Changed
- Placeholder suffix: `@dario` → `@producer` (GUI, tests, SRS).

### Fixed
- Exe mostraba tema nativo claro: `styles.qss` ahora viaja con `--add-data` (antes solo `--add-binary` de ffmpeg). Regla añadida a los skills.
- Columna File truncada (`N...`): Folder ocupaba 220px fijos con rutas absolutas.

### Removed
- Sidecars junto a los samples: `rename_log.csv` y `process_report_*.csv` ya no se escriben (carpetas del user siempre limpias). Resumen solo en panel UI + `library.db`. Sin esto no hay undo vía CSV.

## [v1.0-freeze] — 2026-10-27 (freeze SRS, GUI 2 columnas)

### Added
- Multitool 3 tabs independientes (Organizer / Converter SP-404 / Normalizer peak) + shared scan SQLite.
- Organizer: preset único `sp404_splice` (16 carpetas), bulk rename preview con Replace RAW-first, Whole name (=New), Prefix/Suffix `@tag`, Numerate, in-place default, `rename_log.csv`.
- Converter herencia TRAKKCONVERTER (`_sp.wav`, 48k/16-bit/stereo, Force-to-rate, skip `_sp`).
- Normalizer herencia TRAKKNORMALIZER (`_N.wav`, -1.0dB ±0.5dB, skip silencio).
- GUI 2 columnas (FILES izq + tools der, splitter), tema ámbar `#F5A623` heritage, reportes CSV por tab.
- Tests: 45 pytest (tonos generados, skip sin ffmpeg).

### Changed
- FR-5 degradado a hint pasivo (sin auto-move ni contenido audio).
- Copy mode rename default OFF (in-place).

### Fixed
- Replace con espacios (`Kick 01`) no matcheaba por Clean-first.
- Columna Category? se comía el ancho (File truncado).

## [v1.0-build1] — 2026-10-27 (portable)

### Added
- `dist/TRAKKSTUDIO.exe` one-file windowed, 210MB, ffmpeg 9.0.1 + ffprobe bundlados (`--add-binary`, verificado en log de build).
- README 10 secciones + MAINTENANCE + CHANGELOG a formato skill. SRS CONGELADO v1.0.
