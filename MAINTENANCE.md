# MAINTENANCE — TRAKKSTUDIO

## Versionar (1 min)

1. Sube versión en `gui.py` footer (`v1.X`) y en este archivo.
2. Agrega entrada en `CHANGELOG.md` (Added/Fixed/Changed + fecha).
3. `pytest tests -q` en verde antes de commitear.

## Rebuild exe portable

```
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe build_exe.py
```

Sale en `dist/TRAKKSTUDIO.exe` (v1.0 real: 210MB con FFmpeg 9 full build + Qt6; con build essentials ~120MB) con ffmpeg/ffprobe bundlados vía `--add-binary`. Sin `icon.ico` usa el default de PyInstaller. Documenta tamaño real + nota falso-positivo antivirus en el release.

## Datos locales / backup

- DB: `%APPDATA%/TRAKKSTUDIO/library.db` (borrable, se regenera con scan).
- Logs: resumen en el panel UI + `library.db`. Sin sidecars junto a los samples desde Build 2 (no hay undo vía CSV).
- No hay keys, cuentas ni cloud: nada que rotar.

## Reglas de release

- Main siempre verde (`pytest -q`), `start.bat` probado en máquina limpia.
- Tags `v1.0`, `v1.1`… en GitHub para cada portable.
