import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import clear, list_files, upsert_files
from organizer import scan_to_rows


def test_db_roundtrip(tmp_path):
    db = tmp_path / "t.db"
    clear(db)
    upsert_files([{"path": "a.wav", "size": 10, "category": "Kicks"}], db_path=db)
    rows = list_files(db_path=db)
    assert len(rows) == 1 and rows[0]["category"] == "Kicks"


def test_scan_groups_files(tmp_path):
    pack = tmp_path / "demo_pack" / "Drums" / "Kick"
    pack.mkdir(parents=True)
    (pack / "k1.wav").write_bytes(b"x" * 32)
    (pack / "k2.mp3").write_bytes(b"x" * 32)
    (pack / "note.txt").write_bytes(b"x")
    rows = scan_to_rows([tmp_path / "demo_pack"])
    assert len(rows) == 2
    upsert_files(rows, db_path=tmp_path / "t.db")
    assert len(list_files(db_path=tmp_path / "t.db")) == 2
