"""PyInstaller one-file portable build (bundles ffmpeg/ffprobe)."""
import shutil
import sys
from pathlib import Path

import PyInstaller.__main__ as P

root = Path(__file__).parent
adds = []
for exe in ("ffmpeg.exe", "ffprobe.exe"):
    p = shutil.which(exe) or shutil.which(Path(exe).stem)
    if p:
        adds += ["--add-binary", f"{p};."]
        print(f"bundling {p}")
    else:
        print(f"WARN missing {exe}: build will NOT be portable")

icon = root / "icon.ico"
args = ["--onefile", "--windowed", "--name", "TRAKKSTUDIO", str(root / "main.py")]
for a in adds:
    args.append(a)
if icon.exists():
    args += ["--icon", str(icon)]
print(" ".join(args))
P.run(args)
