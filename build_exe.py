"""PyInstaller one-file portable build (bundles ffmpeg/ffprobe/ffplay)."""
import shutil
import sys
from pathlib import Path

import PyInstaller.__main__ as P

root = Path(__file__).parent
adds = []
for exe in ("ffmpeg.exe", "ffprobe.exe", "ffplay.exe"):
    p = shutil.which(exe) or shutil.which(Path(exe).stem)
    if p:
        adds += ["--add-binary", f"{p};."]
        print(f"bundling {p}")
    else:
        print(f"WARN missing {exe}: build will NOT be portable ({exe} features disabled)")

icon = root / "icon.ico"
args = ["--onefile", "--windowed", "--name", "TRAKKSTUDIO", str(root / "main.py")]
qss = root / "styles.qss"
if qss.exists():
    args += ["--add-data", f"{qss};."]
    print(f"bundling {qss}")
else:
    print("WARN missing styles.qss: exe will use native theme")
icon = root / "icon.ico"
if icon.exists():
    args += ["--icon", str(icon), "--add-data", f"{icon};."]
    print(f"bundling {icon}")
else:
    print("WARN missing icon.ico: exe will use default PyInstaller icon")
for doc in ("LICENSE", "NOTICE.md", "THIRD-PARTY-NOTICES.md"):
    p = root / doc
    if p.is_file():
        args += ["--add-data", f"{p};."]
        print(f"bundling {p}")
for a in adds:
    args.append(a)
print(" ".join(args))
P.run(args)
