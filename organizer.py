"""TRAKKSTUDIO TOOL-ORGANIZER (standalone, no FFmpeg required).

- Scan helpers re-export hardened find_audio_files from converter.
- Preset folder creation, keyword category guess, bulk rename preview/apply.
- Every function is pure (no Qt) so pytest can cover it.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from converter import SUPPORTED_EXTENSIONS, find_audio_files  # noqa: F401 (shared discovery)

# --- Presets (SRS FR-3: single fusion SP-404 + Splice, per owner) ---------------

PRESETS: dict[str, list[str]] = {
    "sp404_splice": [
        # SP-404 one-shots raiz (pad-friendly, shallow)
        "Kicks", "Snares_Claps", "HiHats", "Percs", "808s_Bass",
        "FX_Textures",
        # Splice distribution
        "Oneshots/Drums", "Oneshots/Bass", "Oneshots/Synth", "Oneshots/Vox",
        "Loops/BPM_120", "Loops/BPM_140", "Loops/BPM_150",
        # Comun
        "MIDI", "Favorites", "Artwork",
    ],
}

# --- Category guess (SRS FR-5, keyword only, no AI) ---------------------------

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Kicks": ["kick", "bd_", "bassdrum"],
    "808s_Bass": ["808", "sub", "bass"],
    "Snares_Claps": ["snare", "clap", "rim"],
    "HiHats": ["hat", "hihat", "hi-hat", "openhat", "closedhat"],
    "Percs": ["perc", "shaker", "tamb", "conga", "bongo", "tom", "crash", "cymbal"],
    "Loops": ["loop"],
    "Melodic": ["melod", "keys", "piano", "synth", "guitar", "strings", "pad", "lead"],
    "Vox": ["vox", "vocal", "chant", "adlib"],
    "FX_Textures": ["fx", "riser", "impact", "sweep", "texture", "atmos"],
    "MIDI": [".mid"],
}


def guess_category(file_path: Path) -> str:
    name = file_path.name.lower() + " " + str(file_path.parent.name).lower()
    for cat, keys in CATEGORY_KEYWORDS.items():
        if any(k in name for k in keys):
            return cat
    return "Unsorted"


def create_structure(dest: Path, preset: str, dry_run: bool = False) -> list[Path]:
    """Create preset folders under dest. Never deletes. Returns created/listed paths."""
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset {preset!r}. Valid: {sorted(PRESETS)}")
    out: list[Path] = []
    for rel in PRESETS[preset]:
        p = Path(dest) / rel
        out.append(p)
        if not dry_run:
            p.mkdir(parents=True, exist_ok=True)
    return out


# --- Bulk rename (SRS FR-4) ---------------------------------------------------

WINDOWS_ILLEGAL = r'<>:"/\\|?*'


def sanitize_stem(stem: str) -> str:
    s = stem.strip()
    s = re.sub(r"\s+", "_", s)
    for ch in WINDOWS_ILLEGAL:
        s = s.replace(ch, "")
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "sample"


def sanitize_suffix(suffix: str) -> str:
    # Producer tag case: "@producer" must survive; spaces become _.
    s = suffix.strip()
    s = re.sub(r"\s+", "_", s)
    for ch in WINDOWS_ILLEGAL:
        if ch == "@":
            continue
        s = s.replace(ch, "")
    return s.strip("_")


@dataclass
class RenamePair:
    src: Path
    dst_name: str  # filename only, with extension
    error: str = ""


def preview_rename(
    files: list[Path],
    prefix: str = "",
    suffix_tag: str = "",
    replace_old: str = "",
    replace_new: str = "",
    case_insensitive_replace: bool = True,
    numerate_from: int | None = None,
    numerate_padding: int = 3,
    clean: bool = True,
    replace_whole: bool = False,
) -> list[RenamePair]:
    """Pure preview Antes->Despues. Never touches disk.

    Order (fixed): Replace on RAW stem first, then Clean once.
    So Old='Kick 01' (as seen in Explorer) matches before spaces become _.
    replace_whole=True: ignora Old, borra todo el stem y usa New completo
    (luego aplican prefix/suffix/numerate). Util para renombrar pack entero
    a un nombre base ej New='hhat' -> hhat_001, hhat_002...
    """
    pairs: list[RenamePair] = []
    n = numerate_from
    for f in files:
        stem, ext = f.stem, f.suffix.lower()
        if replace_whole:
            stem = replace_new
        elif replace_old:
            if case_insensitive_replace:
                stem = re.sub(re.escape(replace_old), replace_new, stem, flags=re.IGNORECASE)
            else:
                stem = stem.replace(replace_old, replace_new)
        if clean:
            stem = sanitize_stem(stem) or stem
        if prefix:
            stem = f"{sanitize_stem(prefix)}_{stem}" if stem else sanitize_stem(prefix)
        if suffix_tag:
            stem = f"{stem}_{sanitize_suffix(suffix_tag)}"
        if n is not None:
            stem = f"{stem}_{n:0{numerate_padding}d}"
            n += 1
        new_name = f"{stem}{ext}"
        err = ""
        if not stem:
            err = "empty name"
        elif len(new_name) > 180:
            err = "name >180 chars"
        pairs.append(RenamePair(src=f, dst_name=new_name, error=err))
    # collision check within same folder
    seen: dict[tuple[str, str], int] = {}
    for p in pairs:
        key = (str(p.src.parent).lower(), p.dst_name.lower())
        seen[key] = seen.get(key, 0) + 1
    for p in pairs:
        if not p.error and seen[(str(p.src.parent).lower(), p.dst_name.lower())] > 1:
            p.error = "collision: enable numerate"
    return pairs


def apply_rename(
    pairs: list[RenamePair],
    mode: str = "inplace",
    output_dir: Path | None = None,
) -> tuple[int, list[str]]:
    """Apply a preview. mode=inplace renames; mode=copy copies with new name.

    No sidecar files are written (owner decision: keep user folders clean).
    Returns (done_count, errors). Blocked when any pair has error.
    """
    errors = [f"{p.src.name}: {p.error}" for p in pairs if p.error]
    if errors:
        return 0, errors
    import shutil

    done = 0
    errs: list[str] = []
    for p in pairs:
        try:
            if mode == "copy":
                if output_dir is None:
                    errs.append(f"{p.src.name}: copy needs output_dir")
                    continue
                dst = Path(output_dir) / p.dst_name
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    errs.append(f"{p.src.name}: exists {dst.name}")
                    continue
                shutil.copy2(p.src, dst)
            else:
                dst = p.src.parent / p.dst_name
                if dst.exists() and dst.resolve() != p.src.resolve():
                    errs.append(f"{p.src.name}: exists {dst.name}")
                    continue
                p.src.rename(dst)
            done += 1
        except OSError as e:
            errs.append(f"{p.src.name}: {e}")
    return done, errs


def sha_partial(file_path: Path, n_bytes: int = 65536) -> str:
    try:
        h = hashlib.sha1()
        with open(file_path, "rb") as fh:
            h.update(fh.read(n_bytes))
        return h.hexdigest()[:16]
    except OSError:
        return ""


def scan_to_rows(folders: list[Path]) -> list[dict]:
    """Scan folders -> DB-ready rows (no ffprobe here; enrichment is lazy)."""
    rows: list[dict] = []
    for folder in folders:
        folder = Path(folder)
        if folder.is_file() and folder.suffix.lower() in SUPPORTED_EXTENSIONS:
            files = [folder]
        else:
            files = find_audio_files(folder)
        for f in files:
            try:
                st = f.stat()
            except OSError:
                continue
            rows.append({
                "path": str(f),
                "size": st.st_size,
                "mtime": st.st_mtime,
                "sha_partial": sha_partial(f),
                "category": guess_category(f),
                "status": "pending",
            })
    return rows
