# TRAKKSTUDIO — SRS v1.0 (Software Requirements Specification)

**Status:** FROZEN v1.0 — approved by owner 2026-10-27 (chat)
**Freeze date:** 2026-10-27
**Author:** Senior Eng. + ShardBeats (owner)
**Repo:** `D:\Proyectos programacion\TRAKKSTUDIO` → https://github.com/shardbeats/TRAKKSTUDIO
**Frozen stack:** Python 3.10+ + PySide6 + SQLite (stdlib) + local FFmpeg + portable PyInstaller .exe

---

## 1. Goal + Multitool Architecture

**Goal:** Offline-first portable desktop tool for beatmakers that bundles **3 independent tools in one program**, sharing only inventory + folder management:
- **TOOL-ORGANIZER:** bulk organize (create structure + classify + bulk rename with `@producer` tag).
- **TOOL-CONVERTER:** batch convert to SP-404MK2-compatible WAV (100% TRAKKCONVERTER heritage).
- **TOOL-NORMALIZER:** peak-normalize per file (100% TRAKKNORMALIZER heritage).

**v1 architecture principle (owner note 27-oct-2026):**
Each tool is **optional and independent**. The producer can open the app and use ONLY the Normalizer, ONLY the Converter, or ONLY Rename, without touching the others. NO mandatory pipeline.

```
                 +---------------------+
                 |  Shared Services    |
                 | Scan/Inventory DB   |
                 | Folder resolver     |
                 | (Copy/Overwrite)    |
                 +-----+------+------+--+
                       |      |      |
         +-------------+      |      +-------------+
         |                    |                    |
TOOL ORGANIZER      TOOL CONVERTER      TOOL NORMALIZER
structure +         48k/16b/stereo      own-peak -1dB
bulk rename         _sp.wav             _N.wav
@tag append         copy/convert/skip   skip if ±0.5dB
```

Chaining tools (e.g. Rename -> Convert -> Normalize) is possible manually by reusing the output as input, but NEVER automatic or forced.

---

## 2. Users + Non-Goals

### 2.1 Users
- **U1 Beatmaker / Producer:** owns 5-50GB of messy drumkits, wants to clean up, uniform them to 48kHz/16-bit/stereo for the SP-404MK2 or a DAW, normalize to -1dB, and tag with their `@username` without breaking names.
- **U2 Pack seller (Splice-ready):** wants a standard structure, names like `PACK_Type_BPM_Key_UniqueName.wav`, -1dB headroom, a uniform pack export.

### 2.2 v1 Non-Goals (Backlog, NOT sprint 1)
- NG-1: No AI auto-tag / key/BPM detection from audio. Only filename/folder inference + ffprobe metadata.
- NG-2: No effect playback preview, no waveform editing, no chop/slice. (Audio-only preview allowed: double-click/Play via ffplay, no window.)
- NG-3: No pack-wide LUFS loudness, no compression, no loop-click repair fades (a clicking loop is only documented).
- NG-4: No cloud, login, telemetry, auto-update server, or networked database.
- NG-5: No video support (that's another TRAKK module).
- NG-6: No 20-format support. Only the 11 CONVERTER formats in v1.
- NG-7: No complex settings dialog. Just 1 screen + 3 collapsible panels.

---

## 3. Functional Requirements

Convention: each FR states `Input / Behavior / Output / Error path`. Every `must` is verified in §6.

### MODULE A — Shared Inventory (common service, not a process)

**FR-0 Tool independence (global rule)**
- Behavior: MUST hold for every FR-4/FR-6/FR-7: each tool has its own START/Cancel button, its own output folder + Copy/Overwrite mode, its own CSV report. MUST be able to run FR-4 alone, FR-6 alone, or FR-7 alone without touching the others. They share FR-1 (scan) and FR-8 (folder resolver) as a library, never as a mandatory prior step.
- Verification: AC-0: open the app, load 10 files, run ONLY Normalize -> 10x `_N.wav` with zero `_sp.wav` and zero renames. And vice versa.

**FR-1 Mass drag&drop scan**
- Input: 1..N dropped paths (files or folders, including nested packs), Add Folder button.
- Behavior: MUST walk recursively, filter by supported extensions `wav, mp3, flac, ogg, m4a, aac, aiff, aif, wma, opus, webm` (case-insensitive). MUST group by source folder with a header (like CONVERTER). MUST store in local SQLite `library.db`: path, size, mtime, partial sha1 (first 64KB for fast dedup), format/ffprobe (sample_rate, channels, codec, bits), duration, status.
- Output: inventory table + `X files / Y packs / Z GB` counter. Visible timing.
- Error: missing path or no permission -> log row + skip, never aborts the batch. When running as Administrator on Windows MUST show a "drag&drop blocked by Windows, run normally" warning (CONVERTER heritage).
- Verification: §6 AC-1.

**FR-2 No-reprocess detection + copy-vs-convert**
- Input: inventoried file.
- Behavior: MUST auto-skip when the filename ends in `_sp.wav` (already converted) or `_N.wav` (already normalized) unless an explicit `Re-process` flag is set. MUST classify with the CONVERTER rules:
  - `already_at_target` -> copy without re-encode
  - `different_rate_compatible` -> resample when `Force to rate = ON` (default ON for uniformity)
  - `compressed_or_mismatch` -> convert
- Output: `Action: copy/convert/skip` column in preview.
- Error: ffprobe fails -> mark `unreadable`, list at the end.
- Verification: AC-2.

**FR-3 In-app folder structure (single merged preset, per owner)**
- Input: destination folder (fixed `sp404_splice` preset, no selector).
- Behavior: MUST create the single SP-404 + Splice merged preset:
  `Kicks/ Snares_Claps/ HiHats/ Percs/ 808s_Bass/ FX_Textures/ Oneshots/{Drums,Bass,Synth,Vox}/ Loops/{BPM_120,BPM_140,BPM_150}/ MIDI/ Favorites/ Artwork/`
- MUST create on disk without deleting anything existing, with a `dry-run` listing first.
- Output: created folders + log.
- Error: unwritable destination -> blocking error with the path.
- Verification: AC-3.

### MODULE B — TOOL ORGANIZER standalone (owner-requested core)

**FR-4 Bulk rename with preview + producer tag append (standalone)**
- Input: N selected files (1..10000), chosen operation.
- Behavior: MUST support these 5 combinable ops in v1, in fixed order:
  1. `Clean`: trim, collapse spaces, replace spaces with `_`, strip Windows-illegal `<>:"/\|?*` chars.
  2. `Replace text`: find `old` -> `new` (case-insensitive toggle).
  3. `Add prefix`: `PACK_` or custom.
  4. `Add suffix (append tag)`: concatenated to the stem WITHOUT touching the base. E.g. `Kick_Trap_01` + suffix `@shardbeats` -> `Kick_Trap_01_@shardbeats`. MUST sanitize with `@` allowed but spaces in the suffix converted to `_`. Default OFF.
  5. `Numerate`: `_{001}` with eligible start/padding, only on collision or on user request.
- MUST show an `Before -> After` preview table before applying, with collisions in red.
- MUST never allow two identical outputs in the same folder; on collision it auto-suggests numbering and blocks Apply until resolved.
- Writes no sidecars (owner decision 28-oct-2026: `rename_log.csv` removed, user folders stay clean). The summary lives in the app panel.
- APPLY asks for confirmation with a count (`N files (mode)?` + scope + destination, default No); with no selection it warns that ALL listed files are touched.
- Output: renamed files per the §FR-8 output mode (copy or in-place).
- Error: resulting name >180 chars or empty -> row blocked + explained.
- Verification: AC-4. Critical owner example: `snare_03.wav` + suffix `@producer` MUST yield `snare_03_@producer.wav`, NOT `snare@producer03.wav`.

**FR-5 [DEGRADED v1 — passive hint only, no auto-move] Keyword classification (no AI)**
- Input: inventoried file.
- Behavior v1: `guess_category()` on filename + parent folder keywords ONLY feeds the informational `Category?` queue column. NO bulk `Apply suggestions`, NO file moves, NO blocking. No match -> `Unsorted` (manual review queue).
- Forbidden v1: audio-content detection, confidence scores, auto-sort into folders (see Backlog).
- Verification: AC-5 (display only, see §6).

### MODULE C — TOOL CONVERTER standalone (100% TRAKKCONVERTER heritage)

**FR-6 Batch conversion to SP-404MK2 WAV (standalone)**
- Input: FR-1 files selected in the Converter tab, selected target sample_rate (`48000 SP-404 native default`, optional `44100 legacy`), fixed `16-bit` bit depth v1, `stereo` channels v1 (mono upmixes to stereo unless the `Keep mono` toggle is set).
- Behavior: MUST run standalone with its own START, requiring neither FR-4 nor FR-7. MUST use `ffmpeg_bin()/ffprobe_bin()` resolving `sys._MEIPASS` when bundled else PATH (heritage). Probe JSON `ffprobe -v error -show_streams -show_format -of json`. When `already_at_target` MUST copy. Otherwise MUST `ffmpeg -y -i in -ar RATE -ac 2 -sample_fmt s16 -c:a pcm_s16le out_sp.wav`. MUST preserve structure per its own FR-8 tab. MUST append `_sp.wav`. MUST use 2 parallel workers (like NORMALIZER).
- Reference-only supported spec table (not re-validated in v1): rates `16000,22050,32000,44100,48000,88200,96000,176400,192000`, depth `16/24`, ch `1/2`, codec `pcm_s16le/s24le + be`, container `WAV`.
- Output: uniform WAVs + report.
- Error: missing ffmpeg -> fatal error with PATH instructions; corrupt file -> skip + log.
- Verification: AC-6 (ffprobe rate/ch/codec check).

### MODULE D — TOOL NORMALIZER standalone (100% TRAKKNORMALIZER heritage)

**FR-7 Per-file peak normalization (standalone)**
- Input: files selected in the Normalizer tab (straight from disk, NOT required to pass through the Converter), `Target peak dB default -1.0`, `Skip if within default 0.5dB`.
- Behavior: MUST run standalone with its own START. MUST measure `max_volume` with `ffmpeg -i in -af volumedetect -f null -` and parse it. When `|target - measured| <= tolerance` MUST skip. Otherwise MUST apply linear `volume=+XdB` preserving rate/depth: `ffmpeg -y -i in -af volume=+XdB -c:a pcm_s16le out_N.wav` (or s24 for 24-bit input with the toggle). MUST append `_N.wav`. MUST use 2 workers.
- Manual Convert-then-Normalize chaining: `kick.wav -> kick_sp.wav -> kick_sp_N.wav` (traceable double suffix). Normalize-only: `kick.wav -> kick_N.wav`.
- Output: normalized files.
- Error: `max_volume: n/a/-inf` (silence) -> skip + `silent` log.
- Verification: AC-7.

### MODULE E — Shared Output / Folder management (library used by all 3 tools)

**FR-8 Per-tab output modes: Mirror / Next-to-source / Controlled in-place**
- Input (per Organizer/Converter/Normalizer tab separately): own output folder (empty = next-to-source), `Preserve structure default ON` checkbox, `Mode: Copy (safe default) | Overwrite/In-place` radio.
- Behavior (identical in all 3 tabs, values not shared: each tab remembers its own output/mode):
  - With output folder + Preserve ON: MUST recreate `output/<pack>/<subfolders>/...` (CONVERTER heritage).
  - Without output folder + Preserve ON: MUST create `<source>_sp` and `<source>_N`, or `<source>_trakk` for pure organizer, next-to-source.
  - Preserve OFF: MUST save flat into the output folder (flattened, with anti-collision numbering).
  - Copy mode (default): MUST never delete originals.
  - Overwrite/In-place mode (explicit + count confirm dialog): MUST allow replacement only after verified success (output exists + size>0 + ffprobe ok), then delete/rename the original per operation. Pure in-place rename MUST operate directly.
- Output: files at destination. No sidecars (owner decision 28-oct-2026: user folders always clean).
- Error: no disk space (estimate `input_bytes*1.8 + 100MB`) -> blocks START.
- Verification: AC-8.

**FR-9 In-UI summary + persistent SQLite**
- Input: finished batch.
- Behavior: MUST keep `library.db` with `pending/done/skipped/failed` states. MUST show a `copied/converted/normalized/renamed/skipped/failed` summary in the log panel + popup. Does NOT write `process_report.csv` (removed with the sidecars).
- Output: queryable DB + visible summary.
- Verification: AC-9.

---

## 4. Non-Functionals

- **NFR-1 Platform:** Windows 10/11 64-bit first. Source runs on Python 3.10+. Portable exe via PyInstaller one-file.
- **NFR-2 Offline:** Zero network calls on the critical path. Local FFmpeg/ffprobe. Local DB at `%APPDATA%/TRAKKSTUDIO/` or next to the exe when portable.
- **NFR-3 v1 Performance (measured on i5/8GB SSD):** 1000-file scan <60s; 1000 short one-shot converts (<10s each) <25min on 2 threads; 5000-row rename preview <3s. Max file 500MB, max batch 10000 files.
- **NFR-4 Storage:** Never duplicates without permission; Copy mode warns about size. Mandatory pre-run estimate. Final exe ~100-130MB (Qt+FFmpeg) documented + antivirus false-positive note.
- **NFR-5 Privacy:** No telemetry. Paths never leave the PC. Local logs.
- **NFR-6 Robustness:** Cancel button kills the child ffmpeg. Pure engine without Qt (`engine.py`) for testability. GUI only calls the engine.
- **NFR-7 Code conventions:** English-only identifiers/comments/commits. Standard layout: `main.py gui.py engine.py converter.py normalizer.py organizer.py db.py build_exe.py start.bat run.bat requirements.txt styles.qss tests/ docs/SRS.md README.md MAINTENANCE.md`.

---

## 5. UX Scope — Multitool 2 columns (files left + tools right) + amber brand

**Frozen v1 layout (horizontal QSplitter, owner 27-oct-2026):**
- **Brand header:** `TRAKKSTUDIO` 19px bold + amber subtitle `SHARDBEATS TRAKK SUITE — ORGANIZE / CONVERT / NORMALIZE` + gray footer.
- **Common top bar:** Add folder (Ctrl+O) / Add files / Clear (Del) + Play/Stop preview + `X files / Y packs / Z GB` counter + admin warning (no drag&drop).
- **Left (tall):** `FILES` group with `File (stretch) | Folder (pack/sub) | Category? passive FR-5 hint` table, full-path tooltips, row selection. Double-click plays the sample (audio-only ffplay); selecting another row cuts the running preview.
- **Right (2x wide):** independent tabs:
- **Tab 1 ORGANIZER:** single `sp404_splice` preset + Create, full-width vertical Prefix/Suffix/Old/New inputs, `Whole name (=New)` + `Numerate` checks, `Copy to output` default OFF (= in-place rename), `Before/After (stretch) | Error` preview table + amber `APPLY RENAME` (asks with file count) + panel summary.
- **Tab 2 CONVERTER:** sample_rate dropdown (48k/44.1k), Force-to-rate toggle, keep-mono toggle, `copy/convert/skip` column (FR-2), own output+mode + `START CONVERT (Space)`/`Cancel` + progress + panel summary.
- **Tab 3 NORMALIZER:** target peak (-1.0), tolerance (0.5), replace-original toggle (next-to-source only, heritage), own output+mode + `START NORMALIZE (Space)`/`Cancel` + progress + panel summary.

NO global START button. NO wizard forcing all 3 steps.

**Empty states:** no files -> "Drag your drumkit here" text illustration. No output -> "<source>_trakk next to source" hint.

**Error states:** red ffmpeg-missing banner, yellow admin-mode warning, blocking red rename-collision table.

**Shortcuts v1:** `Ctrl+O` add folder, `Ctrl+R` rename preview, `Space` START/Cancel of the visible tab (never while typing), `Del` remove selected, `F1` quick tour, double-click plays the sample.

**First run:** one-time 3-step tour dialog (flag at `%APPDATA%/TRAKKSTUDIO/.welcomed`, reopen in Help).

**Theme:** dark heritage `styles.qss` (reuse).

---

## 6. Acceptance Criteria (each FR mapped to an executable check)

- **AC-0 (FR-0 independence):** load 10 files, run ONLY the Normalizer tab -> 10x `_N.wav` exist, zero `_sp.wav`, zero renames. Repeat for Converter-only and Organizer-only. `pytest tests/test_independence.py -q` green.
- **AC-1 (FR-1):** drag test folder `demo_pack/Drums/Kick/k1.wav,k2.mp3` -> inventory shows 2 rows grouped under the `demo_pack` header, DB holds 2 rows. `pytest tests/test_scan.py::test_group_by_source -q` green.
- **AC-2 (FR-2):** file `x_sp.wav` at 48k stereo MUST mark `skip`. File `y_44k.wav` with 48k target + Force ON MUST mark `convert`. Test `test_classifier_rules`.
- **AC-3 (FR-3):** single `sp404_splice` preset into an empty folder MUST create the exact 16 paths (Kicks, 808s_Bass, FX_Textures, Favorites, Oneshots/Drums, Loops/BPM_120, Artwork, MIDI...). `pytest tests/test_organizer.py -q` green + manual `dir /s`.
- **AC-4 (FR-4):** select 3 files + suffix `@producer` -> preview shows `*_@producer.wav`, no collision, Apply produces files and zero `*.csv` next to samples. Test `test_bulk_suffix_append`.
- **AC-5 (FR-5 degraded):** `808_glide_C.wav` shows `808s_Bass` and `mystery_xyz.wav` shows `Unsorted` in the informational column. Moves nothing. Test `test_guess_category`.
- **AC-6 (FR-6):** convert `mp3 44.1k` tone -> `_sp.wav` output and `ffprobe -show_streams` MUST report `sample_rate=48000, channels=2, codec_name=pcm_s16le`. E2e test `test_convert_tone`.
- **AC-7 (FR-7):** -6dB-peak tone + -1dB target -> `_N.wav` output with `max_volume ≈ -1.0 ±0.3dB` measured via volumedetect. Tone already at -1.0 ±0.5 MUST skip. Test `test_normalize_gain`.
- **AC-8 (FR-8):** no output folder + Preserve ON MUST create a `<source>_trakk/` mirror. With output + Preserve OFF MUST flatten without duplicates. Overwrite mode MUST confirm + only delete after ffprobe ok. Test `test_output_resolver`.
- **AC-9 (FR-9):** after a batch the panel shows counts matching ok/skip/fail and `library.db` persists them. No CSVs in user folders.

**v1 release gate:** `pytest -q` green (65 tests, on-the-fly generated tones, skip without ffmpeg), `start.bat` works on a clean machine, `python build_exe.py` produces a portable `dist/TRAKKSTUDIO.exe` with bundled ffmpeg+ffprobe+ffplay.

---

## 7. Milestones (status 2026-11-02)

- **[DONE] M0 Spec:** SRS v1.0 FROZEN. Owner approved the TRAKKSTUDIO name + single preset + `@producer` suffix.
- **[DONE] Sprint 1 — Pure engine (no GUI):** `db.py + organizer.py + converter.py + normalizer.py` + green tests. Done = `pytest -q` green + `main.py --scan/--preset` CLI.
- **[DONE] Sprint 2 — GUI:** 2 columns (FILES left + 3 tabs right, splitter), heritage amber `styles.qss`, in-place rename + Whole name + Numerate. Done = 100+ legible drag&dropped files.
- **[DONE] Build 2:** 210MB exe with bundled QSS (`--add-data` + `resource_path()`), zero sidecars. Pushed + tag `v1.0`.
- **[DONE] Icon:** option C (3 amber layers), `make_icon.py` + bundled in exe.
- **[DONE] Installer:** per-user Inno Setup 6 + silent smoke (install/scan/GUI/uninstall).
- **[DONE] Guide:** window Space router, Help menu, first-run tour, About, `APP_VERSION` single-source.
- **[DONE] Preview:** ffplay audio preview (double-click/Play/Stop, auto-cut on select) + stale-finished guard.
- **[DONE] Safety:** APPLY confirm with count.
- **[DONE] English-only:** code + docs in English for international users.
- **[TODO] MVP v1.0:** real 500-file USB pack test with no loss or sidecars → tag + release.
- **Backlog v1.1+:** `%APPDATA%` optional report, undo rename, keep-mono toggle, 24-bit toggle, LUFS mode, Splice ZIP export with artwork, BPM/key detection, FR-5 v2.

---

## 8. Frozen v1 decisions (freeze 2026-10-27)

1. Name: **TRAKKSTUDIO multitool (3 independent tabs)**.
2. Heritage suffixes stay per tool: `_sp` Converter-only, `_N` Normalizer-only, `_@tag` Organizer-append-only. Only manual chaining combines them, e.g. `Kick_01_@producer_sp_N.wav`.
3. Per-tab defaults: Organizer `in-place` (Copy OFF); Converter/Normalizer `Mode=Copy`, `Preserve=ON`, Converter `Force to rate=ON`, `48kHz/16-bit/stereo`, Normalizer `Target -1.0dB / Tol 0.5dB`.
4. Direct in-place rename (no extra confirm); overwrite convert/normalize only after ffprobe OK. APPLY asks with a file count.
5. Single `sp404_splice` preset (16 paths, SP-404 + Splice merge). All other presets removed.
6. FR-5 degraded to passive hint. No content detection in v1.
7. 2-column layout (files left + tools right) with splitter + heritage amber `#F5A623` brand. No icons in v1 (icon added post-freeze: option C).
8. Zero sidecars: neither `rename_log.csv` nor `process_report_*.csv` next to samples (owner 28-oct-2026). Summary in UI + DB only.
9. No global START. Each tab has its own START/Cancel.

## 9. Backlog (not in v1)

- FR-5 v2: wider dict + duration + confidence + auto-move (only if owner re-requests).
- Opt-in spectral content detection via FFmpeg (lowpass/highpass ratio).
- Audio-hash deduplication (partial sha only in v1).
- ZIP packs in/out.
- Hybrid auto-copy favorites.
- MPC 8-char naming support.
- Code signing against antivirus flags.
- BPM/key detector.
- LUFS mode.

---
**v1 Freeze:** Approved by owner in chat 2026-10-27. Later changes target v1.1 with a CHANGELOG entry.
