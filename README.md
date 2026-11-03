# TRAKKSTUDIO — Multitool (ShardBeats TRAKK SUITE)

`Folders/files -> Organize (rename) | Convert (SP-404 WAV) | Normalize (peak) -> Mirror output, resumen en panel`

3 tools independientes en 1 ventana (files izquierda, tools derecha). Cada tab tiene su START/Cancel y su resumen propios. Sin pipeline forzado.

## Features

| Tool | Qué hace | Salida |
|---|---|---|
| 1 · ORGANIZER rename | Crea estructura `sp404_splice` (16 carpetas), bulk rename preview Antes→Después: Clean, Replace Old→New, Whole name (=New), Prefix, Suffix `@tag` append, Numerate anti-colisión, in-place default. No deja archivos extra junto a tus samples | Resumen en el panel |
| 2 · CONVERTER SP-404 | Batch a WAV SP-404MK2: 48kHz (o 44.1k legacy) / 16-bit / stereo PCM; copia si ya está a target, resamplea si Force-to-rate, skipea `*_sp.wav` | `*_sp.wav` |
| 3 · NORMALIZER peak | Cada clip a su propio peak (linear gain, sin compresión), default -1.0dB ±0.5dB skip, preserva rate/depth, skipea `*_N.wav` y silencios | `*_N.wav` |
| Shared | Scan drag&drop agrupado por pack, SQLite local, folder resolver Mirror/Flat/Next-to-source, check disco, Cancel que mata ffmpeg, tema ámbar `#F5A623` | `library.db` |

## Requirements

- Windows 10/11 64-bit, ~300MB libres + espacio para copias (`input×1.8 + 100MB`, la app lo chequea antes del START).
- Para instalar: ejecuta `TRAKKSTUDIO-Setup-1.0.exe` (per-user, sin admin, con desinstalador).
- Para correr desde fuente: Python 3.10+ y FFmpeg en PATH (`ffmpeg -version`).
- Para usar el portable: nada (el `.exe` trae Qt + FFmpeg bundlados, v1.0 real: 210MB con FFmpeg full build; con essentials baja a ~120MB). Algunos antivirus marcan los one-file de PyInstaller como falso positivo.

## Quick start (3 pasos)

1. Doble clic `start.bat` (crea `.venv`, instala, abre el GUI).
2. Primer arranque: tour de 3 pasos (revívelo en Help → Quick tour, F1).
3. Arrastra tu drumkit a FILES (izquierda).
4. Ve al tab que necesites → Preview → START. Ej: Tab 1, Old `Closed Hat` New `hhat` → Preview → APPLY.
5. Doble-click en cualquier fila (o Play) para escucharla; Stop corta. Al seleccionar otra fila el preview se corta solo.

## Shortcuts

| Atajo | Acción |
|---|---|
| `Ctrl+O` | Add folder |
| `Ctrl+R` | Preview rename (tab 1) |
| `Space` | START / Cancel del tab visible (nunca mientras escribes) |
| `Del` | Clear file list |
| `F1` | Quick tour |

## Manual setup (devs)

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

## Usage

1. Add folder/files o drag&drop (si corre como Admin, Windows bloquea el arrastre: reabre normal).
2. (Solo rename) Tab 1: elige preset `sp404_splice` → Create structure si necesitas carpetas.
3. (Solo rename) Tab 1: Prefix/Suffix/Old/New + Whole/Numerate → Preview rename → revisa After → APPLY (in-place default; marca Copy solo si quieres conservar originales en otro folder; confirma con conteo y avisa si tocas TODOS sin selección).
4. (Solo convertir) Tab 2: rate 48000, Force-to-rate ON → Preview actions (`copy/convert/skip`) → START CONVERT.
5. (Solo normalizar) Tab 3: Target -1.0, Tol 0.5 → START NORMALIZE.
6. Resultado esperado: `Closed Hat (8).wav` → rename `hhat_(8).wav` → convert `hhat_(8)_sp.wav` (48k/stereo) → normalize `hhat_(8)_sp_N.wav` (-1dB). Cada paso es opcional y muestra su resumen en el panel. Tus carpetas quedan limpias: cero CSVs ni sidecars.
7. La DB local (`%APPDATA%/TRAKKSTUDIO/library.db`) guarda el inventario; se regenera con cada scan.

## Project structure

```
TRAKKSTUDIO/
├── main.py            # entry: GUI default, CLI con flags
├── gui.py             # 2 columnas: FILES izq + 3 tabs der
├── organizer.py       # scan/structure/bulk-rename (sin FFmpeg)
├── player.py          # preview audio vía ffplay (doble-click/Play/Stop)
├── converter.py       # herencia TRAKKCONVERTER (SP-404)
├── normalizer.py      # herencia TRAKKNORMALIZER (peak)
├── db.py              # SQLite library.db (stdlib)
├── styles.qss         # tema ámbar heritage #F5A623
├── build_exe.py       # PyInstaller one-file + ffmpeg bundlado
├── start.bat          # setup + launch
├── docs/SRS.md        # spec congelada v1.0
├── tests/             # pytest (tonos generados, skip sin ffmpeg)
├── README.md / MAINTENANCE.md / CHANGELOG.md
```

## Tests

```
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest tests -q
```

45 tests: organizer/rename/whole-name/tools/db-scan + e2e ffmpeg (genera tonos al vuelo, skip si no hay ffmpeg).

## Troubleshooting

| Síntoma | Causa probable / fix |
|---|---|
| `Copy mode needs an output folder` | Desmarca Copy (in-place) o elige output con Browse |
| Preview no cambia nada | `Old` no encontrado: revisa espacios/guiones/mayúsculas; el label dice cuántos cambian |
| `BLOCKED: collision` | Activa Numerate o cambia New |
| Drag&drop no entra (cursor prohibido) | Corres como Admin: reabre normal |
| `ffmpeg not found` (desde fuente) | Instala FFmpeg y agrégalo al PATH; el `.exe` no lo necesita |
| Falso positivo antivirus en el `.exe` | Normal en PyInstaller one-file; compila tú mismo con `python build_exe.py` |
| SmartScreen "editor desconocido" | Build sin firmar: Más info → Ejecutar de todas formas |
| Sin espacio | Libera `input×1.8 + 100MB`; el START lo bloquea antes de escribir |
| Exe se ve blanco/nativo | Build vieja sin QSS: usa build2+ (QSS via `--add-data`, ver CHANGELOG) |

## Roadmap (dónde vamos — 2026-10-28)

- [x] **M0 Spec:** SRS v1.0 CONGELADO (`docs/SRS.md`).
- [x] **Sprint 1 Engine:** `organizer/converter/normalizer/db` + 45 pytest verdes.
- [x] **Sprint 2 GUI:** 2 columnas, tema ámbar heritage, rename in-place + Whole name.
- [x] **Build 1:** `dist/TRAKKSTUDIO.exe` 210MB portable (ffmpeg+ffprobe).
- [x] **Build 2:** QSS dentro del exe (`--add-data` + `resource_path()`), columnas legibles (`pack/sub`), cero CSVs, placeholder `@producer`. Pusheado + tag `v1.0`.
- [ ] **MVP done:** USB test 500 files sin pérdida ni sidecars en otro PC → release.
- [ ] **Backlog v1.1+:** reporte opcional a `%APPDATA%`, undo rename, toggles 24-bit/keep-mono, LUFS, ZIP Splice, icono `icon.ico`, FR-5 v2.

## License

Ver `LICENSE` (herencia TRAKK SUITE).
