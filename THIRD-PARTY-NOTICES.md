# THIRD-PARTY-NOTICES — TRAKKSTUDIO

TRAKKSTUDIO code is GPL-3.0-only (`LICENSE`, see `LICENSING.md`; versions published before 2026-11-23 remain MIT). The components below keep
their own licenses, in source runs AND inside the frozen exe.

| Component | License | Notes |
|---|---|---|
| PySide6 + Qt | LGPLv3 | GUI toolkit. https://www.qt.io + https://pypi.org/project/PySide6/ |
| FFmpeg + FFprobe + ffplay (system PATH in dev, `--add-binary` bundled in exe) | LGPLv2.1+ | Converter + normalizer backends + audio-only preview. https://ffmpeg.org/download.html |
| Python stdlib (sqlite3) | PSF | `library.db` scan/history. |

Build tool only: PyInstaller (GPLv2 with bootloader exception),
pytest (MIT, dev only).

Compliance: ship `LICENSE` + `LICENSING.md` + `LICENSING.md` + `NOTICE.md` + this file with the app
(`build_exe.py` bundles `styles.qss` today — add these three the
same way). LGPL texts via the links above.
