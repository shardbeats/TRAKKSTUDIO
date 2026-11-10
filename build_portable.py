"""Build the portable TRAKKSTUDIO (one-dir inside a ZIP).

One-dir starts instantly: nothing is extracted on launch. The portable is
shipped as a ZIP the user unzips once:

    dist\\TRAKKSTUDIO-portable-<version>.zip
        TRAKKSTUDIO\\
            TRAKKSTUDIO.exe
            _internal\\   (Qt, FFmpeg/ffprobe/ffplay, ...)
            README.md / LICENSE / NOTICE.md / THIRD-PARTY-NOTICES.md

Usage (from the project root):
    python build_portable.py

The old `build_exe.py` produced a one-file exe that re-extracted ~750 MB to
%TMP% on EVERY launch; it was removed on purpose.
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXE_DIR = ROOT / "dist" / "portable" / "TRAKKSTUDIO"
DOCS = ("README.md", "LICENSE", "NOTICE.md", "THIRD-PARTY-NOTICES.md")


def project_version() -> str:
    """Read APP_VERSION from gui.py (single source for footer + About)."""
    text = (ROOT / "gui.py").read_text(encoding="utf-8")
    m = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else "dev"


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT))


def main() -> int:
    version = project_version()
    print(f"TRAKKSTUDIO portable version: {version}")

    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onedir", "--windowed",
        "--name", "TRAKKSTUDIO",
        "--distpath", "dist/portable",
        "--workpath", "build/portable",
        "--specpath", "build/portable",
        str(ROOT / "main.py"),
    ]

    for exe in ("ffmpeg.exe", "ffprobe.exe", "ffplay.exe"):
        p = shutil.which(exe) or shutil.which(Path(exe).stem)
        if p:
            args += ["--add-binary", f"{p};."]
            print(f"bundling {p}")
        else:
            print(f"WARN missing {exe}: build will NOT be portable ({exe} features disabled)")

    qss = ROOT / "styles.qss"
    if qss.exists():
        args += ["--add-data", f"{qss};."]
    icon = ROOT / "icon.ico"
    if icon.exists():
        args += ["--icon", str(icon), "--add-data", f"{icon};."]
    for doc in DOCS:
        p = ROOT / doc
        if p.is_file():
            args += ["--add-data", f"{p};."]

    if EXE_DIR.exists():
        shutil.rmtree(EXE_DIR, ignore_errors=True)

    rc = run(args)
    if rc != 0:
        return rc

    exe = EXE_DIR / "TRAKKSTUDIO.exe"
    if not exe.is_file():
        print(f"ERROR: {exe} was not created.")
        return 1

    # Docs visible next to the exe inside the ZIP.
    for name in DOCS:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, EXE_DIR / name)

    out = ROOT / "dist" / f"TRAKKSTUDIO-portable-{version}.zip"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in sorted(EXE_DIR.rglob("*")):
            if p.is_file():
                zf.write(p, Path("TRAKKSTUDIO") / p.relative_to(EXE_DIR))

    print(f"OK: {out} ({out.stat().st_size / 1e6:.1f} MB)")
    print("Unzip once, then run TRAKKSTUDIO\\TRAKKSTUDIO.exe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
