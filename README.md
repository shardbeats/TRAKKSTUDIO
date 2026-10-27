# TRAKKSTUDIO — Multitool

Part of ShardBeats TRAKK SUITE.

3 tools independientes en 1 app (misma ventana, distinto tab):
- TOOL-ORGANIZER: estructura + bulk rename `@tag`
- TOOL-CONVERTER: SP-404MK2 WAV `_sp.wav`
- TOOL-NORMALIZER: peak propio `_N.wav`

Shared: scan/inventario SQLite + folder resolver Copy/Overwrite.

Stack: Python + PySide6 + SQLite + FFmpeg, offline-first portable .exe.

## Estado

SRS v1 en `docs/SRS.md` — corregido a multitool, pendiente firma owner.

## Arquitectura v1 (no pipeline forzado)

```
Shared scan/DB ─┬─ Organizer (standalone)
                ├─ Converter (standalone)
                └─ Normalizer (standalone)
```

Cada tab tiene su START/Cancel, output y CSV propios.

## Siguiente

Sprint 1: engine puro (`organizer.py`, `converter.py`, `normalizer.py`, `db.py`) + 60 tests.
