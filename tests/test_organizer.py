import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from organizer import PRESETS, create_structure, guess_category


@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_preset_creates_folders(tmp_path, preset):
    out = create_structure(tmp_path / "kit", preset)
    assert len(out) == len(PRESETS[preset])
    for p in out:
        assert p.is_dir()


def test_preset_dry_run_creates_nothing(tmp_path):
    out = create_structure(tmp_path / "kit", "sp404_splice", dry_run=True)
    assert len(out) == len(PRESETS["sp404_splice"])
    assert not (tmp_path / "kit").exists()


def test_unknown_preset_raises(tmp_path):
    with pytest.raises(ValueError):
        create_structure(tmp_path, "nope")


def test_fusion_has_sp404_and_splice_folders(tmp_path):
    out = create_structure(tmp_path, "sp404_splice")
    names = {str(p.relative_to(tmp_path)).replace("\\", "/") for p in out}
    # SP-404 raiz
    assert "Kicks" in names
    assert "808s_Bass" in names
    assert "FX_Textures" in names
    assert "Favorites" in names
    # Splice
    assert "Oneshots/Drums" in names
    assert "Loops/BPM_120" in names
    assert "Artwork" in names
    assert "MIDI" in names


@pytest.mark.parametrize(("fname", "expected"), [
    ("kick_punch_01.wav", "Kicks"),
    ("808_glide_C.wav", "808s_Bass"),
    ("snare_trap_02.wav", "Snares_Claps"),
    ("clap_big.wav", "Snares_Claps"),
    ("hihat_closed_01.wav", "HiHats"),
    ("openhat_air.wav", "HiHats"),
    ("shaker_loop_120.wav", "Percs"),
    ("drum_loop_140bpm.wav", "Loops"),
    ("riser_big.wav", "FX_Textures"),
    ("vocal_chop.wav", "Vox"),
    ("mystery_xyz.wav", "Unsorted"),
])
def test_guess_category(fname, expected, tmp_path):
    assert guess_category(tmp_path / fname) == expected
