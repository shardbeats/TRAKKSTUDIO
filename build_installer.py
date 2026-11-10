"""Build the TRAKKSTUDIO installer (Inno Setup), separately from the portable ZIP.

Portable:  python build_portable.py
Installer: python build_installer.py

Version: STABLE_VERSION below (must match the footer in gui.py).
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STABLE_VERSION = "1.0.2"


def _which_in(candidate: str) -> str | None:
    return candidate if Path(candidate).is_file() else None


def main() -> int:
    exe = ROOT / "dist" / "portable" / "TRAKKSTUDIO" / "TRAKKSTUDIO.exe"
    if not exe.is_file():
        print("[installer] one-dir build missing; running build_portable.py...")
        rc = subprocess.call([sys.executable, "build_portable.py"], cwd=str(ROOT))
        if rc != 0 or not exe.is_file():
            print("[installer] ERROR: could not build the one-dir app.")
            return 2
    iss = ROOT / "installer" / "trakkstudio.iss"
    iscc = (
        shutil.which("ISCC")
        or shutil.which("iscc")
        or _which_in(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
        or _which_in(r"C:\Program Files\Inno Setup 6\ISCC.exe")
    )
    defines = [f"/DMyVersion={STABLE_VERSION}"]
    if iscc is None:
        print("[installer] ISCC not found (install Inno Setup 6).")
        print(f"[installer] then run: ISCC {' '.join(defines)} {iss}")
        return 3
    print("+", iscc, *defines, str(iss))
    subprocess.check_call([iscc, *defines, str(iss)])
    setup = ROOT / "dist-installer" / f"TRAKKSTUDIO-Setup-{STABLE_VERSION}.exe"
    if setup.is_file():
        print(f"[installer] {setup.name} ready ({setup.stat().st_size // 1024 // 1024} MB).")
        return 0
    print("[installer] done (setup not found?).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
