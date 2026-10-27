# TRAKKSTUDIO — SRS v1.0 (Software Requirements Specification)

**Estado:** Borrador para congelar v1
**Fecha:** 2026-10-27
**Autor:** Ing. Senior + ShardBeats (owner)
**Repo:** `D:\Proyectos programacion\TRAKKSTUDIO`
**Stack congelado:** Python 3.10+ + PySide6 + SQLite (stdlib) + FFmpeg local + PyInstaller portable .exe

---

## 1. Goal + Arquitectura Multitool

**Goal:** Herramienta desktop portable offline-first para beatmakers que reúne **3 tools independientes en el mismo programa**, compartiendo solo inventario + gestión de folders:
- **TOOL-ORGANIZER:** organizar masivo (crear estructura + clasificar + bulk rename con tag `@producer`).
- **TOOL-CONVERTER:** convertir batch a WAV compatible SP-404MK2 (hereda 100% TRAKKCONVERTER).
- **TOOL-NORMALIZER:** normalizar peak por archivo propio (hereda 100% TRAKKNORMALIZER).

**Principio arquitectónico v1 (aclaración owner 27-oct-2026):**
Cada tool es **opcional e independiente**. El producer puede abrir la app y usar SOLO Normalizer, SOLO Converter, o SOLO Rename, sin pasar por las otras. NO hay pipeline obligatorio.

```
                +---------------------+
                |  Shared Services    |
                | Scan/Inventario DB  |
                | Folder resolver     |
                | (Copy/Overwrite)    |
                +-----+------+------+--+
                      |      |      |
        +-------------+      |      +-------------+
        |                    |                    |
TOOL ORGANIZER      TOOL CONVERTER      TOOL NORMALIZER
estructura +        48k/16b/stereo      peak -1dB propio
bulk rename         _sp.wav             _N.wav
@tag append         copy/convert/skip   skip si ±0.5dB
```

Encadenar tools (ej: Rename -> Convert -> Normalize) es posible manualmente reutilizando la salida como entrada, pero NUNCA automático ni forzado.

---

## 2. Usuarios + No-Goals

### 2.1 Usuarios
- **U1 Beatmaker / Producer:** tiene 5-50GB de drumkits desordenados, quiere limpiar, uniformar a 48kHz/16-bit/stereo para SP-404MK2 o DAW, normalizar a -1dB, y taggear con su `@username` sin romper nombres.
- **U2 Creador de packs para venta (Splice-ready):** quiere crear estructura estándar, nombrar `PACK_Tipo_BPM_Key_NombreUnico.wav`, dejar headroom -1dB, exportar pack uniforme.

### 2.2 Non-Goals v1 (van a Backlog, NO se hacen en sprint 1)
- NG-1: No hay auto-tag por IA / detección de key/BPM por audio. Solo inferencia por nombre de archivo/carpeta + metadatos ffprobe.
- NG-2: No hay preview con playback con efectos, ni edizione de waveform, ni chop/slice.
- NG-3: No hay loudness LUFS global del pack, ni compresión, ni fades correctivos de loops (solo se documenta si el loop clickea).
- NG-4: No hay cloud, login, telemetría, auto-update server, ni base de datos en red.
- NG-5: No hay soporte video (ese es otro módulo TRAKK).
- NG-6: No hay soporte para 20 formatos. Solo 11 de CONVERTER en v1.
- NG-7: No hay settings dialog complejo. Solo 1 pantalla + 3 paneles colapsables.

---

## 3. Requisitos Funcionales

Convención: cada FR tiene `Input / Behavior / Output / Error path`. Todo `must` tiene verificación en §6.

### MÓDULO A — Shared Inventario (servicio común, no es un proceso)

**FR-0 Independencia de tools (regla global)**
- Behavior: MUST cumplirse para todo FR-4/FR-6/FR-7: cada tool tiene su propio botón START/Cancel, su propio output folder + modo Copy/Overwrite, su propio reporte CSV. MUST ser posible ejecutar FR-4 solo, FR-6 solo, o FR-7 solo sin tocar los otros. Comparten FR-1 (scan) y FR-8 (folder resolver) como librería, no como paso previo obligatorio.
- Verificación: AC-0: abrir app, cargar 10 files, correr SOLO Normalize -> 10x `_N.wav` sin crear ningún `_sp.wav` ni rename. Y viceversa.

**FR-1 Escaneo masivo drag&drop**
- Input: 1..N rutas arrastradas (archivos o carpetas, incluyendo packs anidados), botón Add Folder.
- Behavior: MUST recorrer recursivo, filtrar por extensiones soportadas `wav, mp3, flac, ogg, m4a, aac, aiff, aif, wma, opus, webm` (case-insensitive). MUST agrupar por carpeta fuente con header (como CONVERTER). MUST guardar en SQLite local `library.db`: path, size, mtime, sha1-parcial (primeros 64KB para dedup rápido), formato/ffprobe (sample_rate, channels, codec, bits), duración, estado.
- Output: tabla inventario + contador `X archivos / Y packs / Z GB`. Tiempo visible.
- Error: ruta inexistente o sin permiso -> fila en log + skip, no aborta batch. Si se corre como Administrador en Windows MUST mostrar warning "drag&drop bloqueado por Windows, corre normal" (heredado de CONVERTER).
- Verificación: §6 AC-1.

**FR-2 Detección no-reprocesar + copy-vs-convert**
- Input: archivo inventariado.
- Behavior: MUST skip automático si filename termina en `_sp.wav` (ya convertido) o `_N.wav` (ya normalizado) salvo flag explícito `Re-procesar`. MUST clasificar por reglas CONVERTER:
  - `already_at_target` -> copiar sin re-encode
  - `different_rate_compatible` -> resamplear si `Force to rate = ON` (default ON para uniformidad)
  - `compressed_or_mismatch` -> convertir
- Output: columna `Acción: copy/convert/skip` en preview.
- Error: ffprobe falla -> marcar `unreadable`, listar al final.
- Verificación: AC-2.

**FR-3 Crear estructura de carpetas desde el programa (preset único fusión, per owner)**
- Input: carpeta destino (preset fijo `sp404_splice`, sin selector).
- Behavior: MUST crear preset único fusión SP-404 + Splice:
  `Kicks/ Snares_Claps/ HiHats/ Percs/ 808s_Bass/ FX_Textures/ Oneshots/{Drums,Bass,Synth,Vox}/ Loops/{BPM_120,BPM_140,BPM_150}/ MIDI/ Favorites/ Artwork/`
- MUST crear en disco sin borrar nada existente, con `dry-run` listado antes.
- Output: carpetas creadas + log.
- Error: destino sin escritura -> error bloqueante con mensaje path.
- Verificación: AC-3.

### MÓDULO B — TOOL ORGANIZER independiente (core pedido por owner)

**FR-4 Bulk rename con preview + append producer tag (standalone)**
- Input: N archivos seleccionados (1..10000), operación elegida.
- Behavior: MUST soportar en v1 estas 5 ops combinables en orden fijo:
  1. `Clean`: trim, colapsa espacios, reemplaza espacios por `_`, quita caracteres `<>:"/\|?*` Windows-ilegales.
  2. `Replace text`: buscar `old` -> `new` (case-insensitive toggle).
  3. `Add prefix`: `PACK_` o custom.
  4. `Add suffix (append tag)`: concatena al stem SIN modificar base. Ej: `Kick_Trap_01` + suffix `@shardbeats` -> `Kick_Trap_01_@shardbeats`. MUST sanitizar `@` permitido, pero convertir espacios en suffix a `_`. Default OFF.
  5. `Numerate`: `_{001}` con inicio/padding elegible, solo si hay colisión o usuario lo pide.
- MUST mostrar tabla preview `Antes -> Después` antes de aplicar, con detección de colisiones en rojo.
- MUST nunca permitir dos outputs iguales en el mismo folder; si colisiona, auto-sugiere numeración y bloquea Apply hasta resolver.
- MUST escribir `rename_log.csv` (timestamp, old_path, new_path) para undo manual v1.
- Output: archivos renombrados según modo salida §FR-7 (copia o in-place).
- Error: nombre resultante >180 chars o vacío -> bloquea fila + explica.
- Verificación: AC-4. Ejemplo crítico owner: `snare_03.wav` + suffix `@dario` MUST dar `snare_03_@dario.wav`, NO `snare@dario03.wav`.

**FR-5 Clasificación asistida por nombre (sin IA)**
- Input: archivo inventariado.
- Behavior: MUST inferir categoría por diccionario keyword (ej: `kick,808,snare,clap,hat,openhat,perc,rim,shaker,crash,loop,melody,bass,vox,fx,riser` en filename o parent folder) a carpeta destino sugerida del preset activo. MUST permitir override manual por fila y `Aplicar sugerencias` bulk. NO mueve nada sin confirmación.
- Output: columna `Categoría sugerida + confianza (keyword match)`.
- Error: sin match -> `Unsorted/`, no falla.
- Verificación: AC-5.

### MÓDULO C — TOOL CONVERTER independiente (hereda 100% TRAKKCONVERTER)

**FR-6 Conversión batch a SP-404MK2 WAV (standalone)**
- Input: archivos FR-1 seleccionados en Tab Converter, target sample_rate seleccionado (`48000 default nativo SP-404`, opcional `44100 legacy`), bit_depth fijo `16-bit` v1, canales `stereo` v1 (mono se upmixa a stereo salvo toggle `Keep mono`).
- Behavior: MUST correr standalone con su propio START, sin requerir FR-4 ni FR-7. MUST usar `ffmpeg_bin()/ffprobe_bin()` con resolución `sys._MEIPASS` si bundle else PATH (heredado). Probe JSON `ffprobe -v error -show_streams -show_format -of json`. Si `already_at_target` MUST copiar. Si no MUST `ffmpeg -y -i in -ar RATE -ac 2 -sample_fmt s16 -c:a pcm_s16le out_sp.wav`. MUST preservar estructura según FR-8 propio del tab. MUST sufijo `_sp.wav`. MUST 2 workers paralelos (como NORMALIZER).
- Input: archivos FR-1, target sample_rate seleccionado (`48000 default nativo SP-404`, opcional `44100 legacy`), bit_depth fijo `16-bit` v1, canales `stereo` v1 (mono se upmixa a stereo salvo toggle `Keep mono`).
- Behavior: MUST usar `ffmpeg_bin()/ffprobe_bin()` con resolución `sys._MEIPASS` si bundle else PATH (heredado). Probe JSON `ffprobe -v error -show_streams -show_format -of json`. Si `already_at_target` MUST copiar. Si no MUST `ffmpeg -y -i in -ar RATE -ac 2 -sample_fmt s16 -c:a pcm_s16le out_sp.wav`. MUST preservar estructura según FR-7. MUST sufijo `_sp.wav`. MUST 2 workers paralelos (como NORMALIZER).
- Spec table soportada (solo informativa, no re-validar en v1): rates `16000,22050,32000,44100,48000,88200,96000,176400,192000`, depth `16/24`, ch `1/2`, codec `pcm_s16le/s24le + be`, container `WAV`.
- Output: WAVs uniformes + reporte.
- Error: ffmpeg missing -> error fatal con instrucciones PATH; archivo corrupto -> skip + log.
- Verificación: AC-6 (ffprobe check rate/ch/codec).

### MÓDULO D — TOOL NORMALIZER independiente (hereda 100% TRAKKNORMALIZER)

**FR-7 Normalización peak por archivo propio (standalone)**
- Input: archivos seleccionados en Tab Normalizer (directos del disco, NO requiere pasar por Converter), `Target peak dB default -1.0`, `Skip if within default 0.5dB`.
- Behavior: MUST correr standalone con su propio START. MUST medir `max_volume` con `ffmpeg -i in -af volumedetect -f null -`, parsear. Si `|target - measured| <= tolerance` MUST skip. Si no MUST aplicar `volume=+XdB` lineal preservando rate/depth: `ffmpeg -y -i in -af volume=+XdB -c:a pcm_s16le out_N.wav` (o s24 si input 24 y toggle). MUST sufijo `_N.wav`. MUST 2 workers.
- Si el usuario encadena manualmente Convert y luego Normalize: `kick.wav -> kick_sp.wav -> kick_sp_N.wav` (doble sufijo trazable). Si solo normaliza: `kick.wav -> kick_N.wav`.
- Input: archivos (post-conversión o directos), `Target peak dB default -1.0`, `Skip if within default 0.5dB`.
- Behavior: MUST medir `max_volume` con `ffmpeg -i in -af volumedetect -f null -`, parsear. Si `|target - measured| <= tolerance` MUST skip. Si no MUST aplicar `volume=+XdB` lineal preservando rate/depth: `ffmpeg -y -i in -af volume=+XdB -c:a pcm_s16le out_N.wav` (o s24 si input 24 y toggle). MUST sufijo `_N.wav`. MUST 2 workers.
- Si cadena Convert+Normalize activa: `kick.wav -> kick_sp.wav -> kick_sp_N.wav` (doble sufijo trazable). Si solo normaliza: `kick.wav -> kick_N.wav`.
- Output: archivos normalizados.
- Error: `max_volume: n/a/-inf` (silencio) -> skip + log `silent`.
- Verificación: AC-7.

### MÓDULO E — Shared Salida / Folder management (librería usada por las 3 tools)

**FR-8 Modos de salida por-tab: Mirror / Next-to-source / In-place controlado**
- Input (por cada tab Organizer/Converter/Normalizer por separado): output folder propio (vacío = next-to-source), checkbox `Preserve structure default ON`, radio `Mode: Copy (default seguro) | Overwrite/In-place`.
- Behavior (idéntico en las 3 tabs, no compartido el valor: cada tab recuerda su propio output/mode):
  - Con output folder + Preserve ON: MUST recrear `output/<pack>/<subfolders>/...` (herencia CONVERTER).
  - Sin output folder + Preserve ON: MUST crear `<source>_sp` y `<source>_N` o `<source>_trakk` para organizer puro next-to-source.
  - Preserve OFF: MUST guardar flat en output folder (aplana, con numeración anti-colisión).
  - Mode Copy (default): MUST nunca borrar originales.
  - Mode Overwrite/In-place (explícito + confirm dialog con conteo): MUST permitir reemplazo solo tras éxito verificado (output existe + size>0 + ffprobe ok), luego borra/renombra original según operación. Para rename puro in-place MUST operar directo.
- Output: archivos en destino + `process_report.csv`.
- Error: sin espacio disco (estimado `input_bytes*1.8 + 100MB`) -> bloquea START.
- Verificación: AC-8.

**FR-9 Reporte + SQLite persistente**
- Input: batch terminado.
- Behavior: MUST escribir `process_report.csv` + mantener `library.db` con estados `pending/done/skipped/failed`. MUST mostrar resumen `copiados/convertidos/normalizados/renombrados/skipeados/fallidos`.
- Output: CSV + DB consultable.
- Verificación: AC-9.

---

## 4. No-Funcionales

- **NFR-1 Plataforma:** Windows 10/11 64-bit primero. Source run Python 3.10+. Exe portable vía PyInstaller one-file.
- **NFR-2 Offline:** Cero llamadas red en critical path. FFmpeg/ffprobe locales. DB local `%APPDATA%/TRAKKSTUDIO/` o junto a exe en portable.
- **NFR-3 Performance v1 (medido en SSD i5/8GB):** scan 1000 archivos <60s; convert 1000 one-shots cortos (<10s c/u) <25min en 2 threads; rename preview 5000 filas <3s. Máx archivo 500MB, máx batch 10000 archivos.
- **NFR-4 Storage:** Nunca duplica sin permiso en Copy mode se avisa tamaño. Estimación pre-run obligatoria. Exe final ~100-130MB (Qt+FFmpeg) documentado + nota falso-positivo antivirus.
- **NFR-5 Privacidad:** Sin telemetría. Paths nunca salen del PC. Logs locales.
- **NFR-6 Robustez:** Cancel button mata child ffmpeg. Engine puro sin Qt (`engine.py`) testeable. GUI solo llama engine.
- **NFR-7 Convenciones código:** Inglés-only identifiers/comments/commits. Estructura estándar: `main.py gui.py engine.py converter.py normalizer.py organizer.py db.py build_exe.py start.bat run.bat requirements.txt styles.qss tests/ docs/SRS.md README.md MAINTENANCE.md`.

---

## 5. UX Scope — Multitool con 3 Tabs independientes + 1 barra común

**Layout v1 (QTabWidget):**
- **Top bar común (siempre visible):** drag&drop zone + Add Folder / Clear + indicador Admin-warning + contador `X files`.
- **Tab 1 ORGANIZER:** preset estructura (FR-3) + Create, tabla preview `Antes -> Después` rename (FR-4), inputs prefix/suffix/replace/numerate, categoría sugerida (FR-5), su propio output+mode (FR-8) + botón `APPLY RENAME` + `process_report_organizer.csv`.
- **Tab 2 CONVERTER:** sample_rate dropdown (48k/44.1k), Force-to-rate toggle, keep-mono toggle, columna `copy/convert/skip` (FR-2), su propio output+mode + `START CONVERT`/`Cancel` + progress + `process_report_converter.csv`.
- **Tab 3 NORMALIZER:** target peak (-1.0), tolerance (0.5), replace-original toggle (solo next-to-source, herencia), su propio output+mode + `START NORMALIZE`/`Cancel` + progress + `process_report_normalizer.csv`.

NO hay botón START global. NO hay wizard que obligue a pasar por los 3.

**Empty states:** sin archivos -> ilustración texto "Arrastra tu drumkit aquí". Sin output -> hint "<source>_trakk al lado del origen".

**Error states:** banner rojo ffmpeg missing, warning amarillo admin-mode, tabla colisiones rename en rojo bloqueante.

**Shortcuts v1:** `Ctrl+O` add folder, `Ctrl+R` preview rename, `Space` START/Cancel, `Del` remove selected.

**Tema:** dark `styles.qss` heredado TRAKK (reusar).

---

## 6. Acceptance Criteria (cada FR mapeado a check ejecutable)

- **AC-0 (FR-0 independencia):** cargar 10 files, correr SOLO Tab Normalizer -> existen 10x `_N.wav`, cero `_sp.wav`, cero renames. Repetir SOLO Converter y SOLO Organizer. `pytest tests/test_independence.py -q` green.
- **AC-1 (FR-1):** Arrastrar carpeta test `demo_pack/Drums/Kick/k1.wav,k2.mp3` -> inventario muestra 2 filas agrupadas bajo header `demo_pack`, DB tiene 2 rows. `pytest tests/test_scan.py::test_group_by_source -q` green.
- **AC-2 (FR-2):** Archivo `x_sp.wav` a 48k stereo MUST marcar `skip`. `y_44k.wav` con target 48k + Force ON MUST marcar `convert`. Test `test_classifier_rules`.
- **AC-3 (FR-3):** Preset único `sp404_splice` en carpeta vacía MUST crear 16 paths exactos (Kicks, 808s_Bass, FX_Textures, Favorites, Oneshots/Drums, Loops/BPM_120, Artwork, MIDI...). `pytest tests/test_organizer.py -q` green + `dir /s` manual.
- **AC-4 (FR-4):** Seleccionar 3 files + suffix `@dario` -> preview muestra `*_@dario.wav`, sin colisión, Apply genera files + `rename_log.csv` con 3 líneas. Test `test_bulk_suffix_append`.
- **AC-5 (FR-5):** `808_glide_C.wav` sugiere `808s_Bass`, `snare_trap_02.wav` sugiere `Snares_Claps`. Test `test_guess_category`.
- **AC-6 (FR-6):** Convertir tono `mp3 44.1k` -> output `_sp.wav` y `ffprobe -show_streams` MUST dar `sample_rate=48000, channels=2, codec_name=pcm_s16le`. Test e2e `test_convert_tone`.
- **AC-7 (FR-7):** Tono -6dB peak + target -1dB -> output `_N.wav` con `max_volume ≈ -1.0 ±0.3dB` medido con volumedetect. Tono ya en -1.0 ±0.5 MUST skip. Test `test_normalize_gain`.
- **AC-8 (FR-8):** Sin output folder + Preserve ON MUST crear `<source>_trakk/` espejo. Con output + Preserve OFF MUST aplanar sin duplicados. Overwrite mode MUST pedir confirm + solo borrar tras ffprobe ok. Test `test_output_resolver`.
- **AC-9 (FR-9):** Tras batch MUST existir `process_report.csv` y `library.db` con counts que cuadran con UI summary.

**Gate release v1:** `pytest -q` green (mín 60 tests, tonos generados on-the-fly, skip si no ffmpeg), `start.bat` funciona en máquina limpia, `python build_exe.py` produce `dist/TRAKKSTUDIO.exe` portable con ffmpeg+ffprobe bundlados.

---

## 7. Milestones

- **M0 Spec (esta semana):** Congelar este SRS. Owner aprueba nombre TRAKKSTUDIO + presets + suffix `@username`.
- **Sprint 1 — Engine puro (sin GUI):** `db.py + organizer.py (scan/rename/structure) + converter.py + normalizer.py` portados desde repos + tests 60. Done = `pytest -q` green + CLI `python -m engine --scan demo`.
- **Sprint 2 — GUI mínima:** `gui.py` queue + preview rename + process panel + `styles.qss` + `start.bat`. Done = drag&drop 1000 files <60s manual.
- **MVP v1.0:** Exe portable + README + MAINTENANCE + `process_report.csv`. Done = instala en USB, corre sin Python/FFmpeg, convierte+normaliza+renombra pack real 500 files sin pérdida.
- **Backlog v1.1+:** undo rename desde CSV, keep-mono toggle, 24-bit toggle, LUFS mode, export Splice ZIP con artwork, detector BPM/key.

---

## 8. Decisiones congeladas para v1

1. Nombre: **TRAKKSTUDIO multitool (3 tabs independientes)**.
2. Sufijos heritage se mantienen por tool: `_sp` solo Converter, `_N` solo Normalizer, `_@tag` solo Organizer append. Solo si el usuario encadena manualmente se combinan ej: `Kick_01_@dario_sp_N.wav`.
3. Default seguro por tab: `Mode=Copy`, `Preserve=ON`, Converter `Force to rate=ON`, `48kHz/16-bit/stereo`, Normalizer `Target -1.0dB / Tol 0.5dB`.
4. In-place solo con confirm explícita + verificación ffprobe, por tab.
5. Estructura base creada desde app, no se asume estructura entrante.
6. No hay START global. Cada tab tiene su START/Cancel y su CSV.

## 9. Backlog (no hacer ahora)

- Deduplicación por hash audio (solo sha parcial en v1).
- Packs ZIP in/out.
- Favoritos hybrid auto-copy.
- Soporte MPC 8-char naming.
- Firma código para evitar flag antivirus.

---
**Firma owner para congelar:** _________________ Fecha: _______
