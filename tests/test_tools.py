import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import converter as C
import normalizer as N
from organizer import apply_rename, preview_rename


def test_spec_table_has_required_rates():
    for r in (16000, 22050, 32000, 44100, 48000, 88200, 96000, 176400, 192000):
        assert r in C.TRAKK_SPEC["sample_rates"]
    assert C.TRAKK_SPEC["recommended_sample_rate"] == 48000


def test_supported_extensions_shared():
    assert ".wav" in C.SUPPORTED_EXTENSIONS
    assert ".mp3" in C.SUPPORTED_EXTENSIONS
    assert N.SUPPORTED_EXTENSIONS == C.SUPPORTED_EXTENSIONS


def test_ffmpeg_cmd_pins_rate_and_codec(tmp_path):
    cmd = C.build_ffmpeg_cmd(tmp_path / "a.mp3", tmp_path / "a_sp.wav", 48000)
    assert "-ar" in cmd and "48000" in cmd
    assert "pcm_s16le" in cmd
    assert "-nostdin" in cmd


def test_compute_converter_path_mirror(tmp_path):
    src = tmp_path / "pack" / "Drums" / "k.wav"
    out = C.compute_output_path(src, tmp_path / "out", tmp_path / "pack", True)
    assert out.name == "k_sp.wav"
    # heritage mirrors relative to source_root: out/Drums/k_sp.wav
    assert "Drums" in out.parts


def test_compute_converter_path_flat(tmp_path):
    src = tmp_path / "pack" / "k.mp3"
    out = C.compute_output_path(src, tmp_path / "out", tmp_path / "pack", False)
    assert out.parent == tmp_path / "out"
    assert out.suffix == ".wav"


def test_find_audio_files_ignores_txt_and_caps(tmp_path):
    (tmp_path / "a.WAV").write_bytes(b"x")
    (tmp_path / "b.Mp3").write_bytes(b"x")
    (tmp_path / "c.txt").write_bytes(b"x")
    found = C.find_audio_files(tmp_path)
    assert len(found) == 2


def test_normalizer_skip_suffix_constant():
    assert N.SKIP_SUFFIX == "_N"


def test_normalizer_output_path_suffix(tmp_path):
    src = tmp_path / "k.wav"
    out = N.compute_output_path(src, None, None, False)
    assert out.name == "k_N.wav"


def test_encode_args_lossy_goes_wav():
    ext, args = N.encode_args({"codec_name": "mp3"}, ".mp3")
    assert ext == ".wav" and "pcm_s16le" in args


def test_encode_args_pcm16_kept():
    ext, args = N.encode_args({"codec_name": "pcm_s16le"}, ".wav")
    assert ext == ".wav"


# AC-0 independencia: cada tool no deja rastro de las otras
def test_rename_only_never_creates_sp_or_N(tmp_path):
    f = tmp_path / "kick.wav"
    f.write_bytes(b"x" * 128)
    pairs = preview_rename([f], suffix_tag="@producer")
    done, _ = apply_rename(pairs, mode="inplace")
    assert done == 1
    names = {p.name for p in tmp_path.iterdir()}
    assert not any(n.endswith("_sp.wav") for n in names)
    assert not any(n.endswith("_N.wav") for n in names)


def test_converter_suffix_distinct_from_normalizer(tmp_path):
    c = C.compute_output_path(tmp_path / "k.wav", tmp_path / "o", tmp_path, False)
    n = N.compute_output_path(tmp_path / "k.wav", None, None, False)
    assert c.name != n.name
    assert c.stem.endswith("_sp") and n.stem.endswith("_N")
