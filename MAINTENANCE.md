# MAINTENANCE — TRAKKSTUDIO

## Versionar (1 min)

1. Sube `APP_VERSION` en `gui.py` (footer + About la leen de ahí) y `STABLE_VERSION` en `build_installer.py` si hay installer.
2. Agrega entrada en `CHANGELOG.md` (Added/Fixed/Changed + fecha).
3. `pytest tests -q` en verde antes de commitear.

## Rebuild exe portable

```
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe build_exe.py
```

Sale en `dist/TRAKKSTUDIO.exe` (v1.0 real: 210MB con FFmpeg 9 full build + Qt6; con build essentials ~120MB) con ffmpeg/ffprobe bundlados vía `--add-binary`. Sin `icon.ico` usa el default de PyInstaller. Documenta tamaño real + nota falso-positivo antivirus en el release.

## Installer (Inno Setup 6)

```
python build_installer.py
```

Necesita `dist/TRAKKSTUDIO.exe` ya construido. Sale en `dist/TRAKKSTUDIO-Setup-<version>.exe` (per-user, sin admin, EN/ES, con desinstalador). Versión en `build_installer.py: STABLE_VERSION` (debe igualar el footer de `gui.py`). Build sin firmar: SmartScreen avisará en el primer run.

## Datos locales / backup

- DB: `%APPDATA%/TRAKKSTUDIO/library.db` (borrable, se regenera con scan).
- Logs: resumen en el panel UI + `library.db`. Sin sidecars junto a los samples desde Build 2 (no hay undo vía CSV).
- No hay keys, cuentas ni cloud: nada que rotar.

## Reglas de release

- Main siempre verde (`pytest -q`), `start.bat` probado en máquina limpia.
- Tags `v1.0`, `v1.1`… en GitHub para cada portable.
