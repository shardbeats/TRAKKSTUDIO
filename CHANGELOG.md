# CHANGELOG — TRAKKSTUDIO

## [v1.0] — 2026-10-27 (freeze SRS, GUI 2 columnas)

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
