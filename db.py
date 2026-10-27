"""TRAKKSTUDIO shared SQLite inventory (stdlib only, offline)."""
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Iterable


def get_db_path() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    p = Path(base) / "TRAKKSTUDIO" / "library.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
  path TEXT PRIMARY KEY,
  size INTEGER DEFAULT 0,
  mtime REAL DEFAULT 0,
  sha_partial TEXT DEFAULT '',
  sample_rate INTEGER DEFAULT 0,
  channels INTEGER DEFAULT 0,
  codec TEXT DEFAULT '',
  duration REAL DEFAULT 0,
  category TEXT DEFAULT '',
  action TEXT DEFAULT '',
  status TEXT DEFAULT 'pending',
  updated_at REAL DEFAULT 0
);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = db_path or get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def upsert_files(rows: Iterable[dict], db_path: Path | None = None) -> int:
    conn = connect(db_path)
    n = 0
    now = time.time()
    with conn:
        for r in rows:
            conn.execute(
                """INSERT INTO files
                   (path,size,mtime,sha_partial,sample_rate,channels,codec,duration,category,action,status,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(path) DO UPDATE SET
                     size=excluded.size, mtime=excluded.mtime, sha_partial=excluded.sha_partial,
                     sample_rate=excluded.sample_rate, channels=excluded.channels, codec=excluded.codec,
                     duration=excluded.duration, category=excluded.category, action=excluded.action,
                     status=excluded.status, updated_at=excluded.updated_at""",
                (
                    str(r.get("path")), int(r.get("size", 0)), float(r.get("mtime", 0)),
                    str(r.get("sha_partial", "")), int(r.get("sample_rate", 0)),
                    int(r.get("channels", 0)), str(r.get("codec", "")),
                    float(r.get("duration", 0.0)), str(r.get("category", "")),
                    str(r.get("action", "")), str(r.get("status", "pending")), now,
                ),
            )
            n += 1
    conn.close()
    return n


def list_files(status: str | None = None, db_path: Path | None = None) -> list[dict]:
    conn = connect(db_path)
    conn.row_factory = sqlite3.Row
    if status:
        cur = conn.execute("SELECT * FROM files WHERE status=? ORDER BY path", (status,))
    else:
        cur = conn.execute("SELECT * FROM files ORDER BY path")
    out = [dict(r) for r in cur.fetchall()]
    conn.close()
    return out


def clear(db_path: Path | None = None) -> None:
    conn = connect(db_path)
    with conn:
        conn.execute("DELETE FROM files")
    conn.close()
