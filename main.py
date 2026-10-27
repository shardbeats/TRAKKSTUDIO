"""TRAKKSTUDIO entry: GUI by default, CLI when flags given."""
from __future__ import annotations

import argparse
from pathlib import Path

from organizer import PRESETS, create_structure, scan_to_rows
from db import clear, get_db_path, list_files, upsert_files


def run_cli(args) -> int:
    if args.clear:
        clear()
        print("db cleared")
    if args.preset and args.mkdir:
        paths = create_structure(Path(args.mkdir), args.preset)
        print(f"created {len(paths)} folders")
        for p in paths:
            print(f"  {p}")
    if args.scan:
        rows = scan_to_rows([Path(s) for s in args.scan])
        upsert_files(rows)
        print(f"scanned {len(rows)} files -> {get_db_path()}")
    if args.list:
        for r in list_files()[:50]:
            print(r["path"], "|", r["category"], "|", r["status"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="trakkstudio")
    ap.add_argument("--scan", nargs="*", default=[], help="folders/files to inventory (CLI mode)")
    ap.add_argument("--preset", default="", help=f"create structure preset {sorted(PRESETS)}")
    ap.add_argument("--mkdir", default="", help="dest for --preset")
    ap.add_argument("--list", action="store_true", help="print DB rows")
    ap.add_argument("--clear", action="store_true", help="clear DB")
    ap.add_argument("--cli", action="store_true", help="force CLI even without args")
    args = ap.parse_args()

    if args.scan or args.preset or args.list or args.clear or args.cli:
        return run_cli(args)
    from gui import run as run_gui
    run_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
