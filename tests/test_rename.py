import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from organizer import apply_rename, preview_rename


def _f(tmp_path, name="snare_03.wav"):
    p = tmp_path / name
    p.write_bytes(b"x" * 64)
    return p


def test_replace_matches_raw_name_with_spaces(tmp_path):
    # regression: Old='Kick 01' (como se ve en Explorer) debe matchear antes del Clean
    f = _f(tmp_path, "Kick 01.wav")
    (p,) = preview_rename([f], replace_old="Kick 01", replace_new="808")
    assert p.dst_name == "808.wav"
    assert p.error == ""


def test_replace_partial_before_clean(tmp_path):
    f = _f(tmp_path, "Kick 01.wav")
    (p,) = preview_rename([f], replace_old="kick", replace_new="808")
    assert p.dst_name == "808_01.wav"


def test_replace_whole_uses_new_fully(tmp_path):
    from pathlib import Path as _P
    files = [_P(f"a{i}.wav") for i in range(3)]
    pairs = preview_rename(files, replace_new="hhat", replace_whole=True, numerate_from=1)
    assert [p.dst_name for p in pairs] == ["hhat_001.wav", "hhat_002.wav", "hhat_003.wav"]
    blocked = preview_rename(files, replace_new="hhat", replace_whole=True)
    assert all(p.error for p in blocked)


def test_owner_suffix_append_keeps_stem(tmp_path):
    f = _f(tmp_path)
    (p,) = preview_rename([f], suffix_tag="@dario")
    assert p.dst_name == "snare_03_@dario.wav"
    assert p.error == ""


def test_suffix_spaces_become_underscore(tmp_path):
    f = _f(tmp_path, "kick 01.wav")
    (p,) = preview_rename([f], suffix_tag="my tag")
    assert p.dst_name == "kick_01_my_tag.wav"


def test_prefix_plus_suffix(tmp_path):
    f = _f(tmp_path, "hat.wav")
    (p,) = preview_rename([f], prefix="PACK", suffix_tag="@dario")
    assert p.dst_name == "PACK_hat_@dario.wav"


def test_replace_case_insensitive(tmp_path):
    f = _f(tmp_path, "Kick_Trap.wav")
    (p,) = preview_rename([f], replace_old="kick", replace_new="808")
    assert p.dst_name == "808_Trap.wav"


def test_collision_blocked_until_numerate(tmp_path):
    a = _f(tmp_path, "a.wav")
    b = _f(tmp_path, "A.WAV")
    pairs = preview_rename([a, b], replace_old="a", replace_new="same")
    assert all(p.error != "" for p in pairs)
    pairs2 = preview_rename([a, b], replace_old="a", replace_new="same",
                            numerate_from=1, numerate_padding=3)
    assert all(p.error == "" for p in pairs2)
    assert pairs2[0].dst_name != pairs2[1].dst_name


def test_long_name_blocked(tmp_path):
    f = _f(tmp_path, "x" * 100 + ".wav")
    (p,) = preview_rename([f], suffix_tag="y" * 100)
    assert "180" in p.error


def test_illegal_chars_cleaned(tmp_path):
    f = _f(tmp_path, "a.wav")
    (p,) = preview_rename([f], prefix='a<b:c')
    assert "<" not in p.dst_name and ":" not in p.dst_name


def test_apply_inplace_renames_and_logs(tmp_path):
    f = _f(tmp_path)
    pairs = preview_rename([f], suffix_tag="@dario")
    done, errs = apply_rename(pairs, mode="inplace", log_csv=tmp_path / "rename_log.csv")
    assert done == 1 and errs == []
    assert (tmp_path / "snare_03_@dario.wav").exists()
    assert (tmp_path / "rename_log.csv").exists()


def test_apply_copy_keeps_original(tmp_path):
    f = _f(tmp_path)
    out = tmp_path / "out"
    pairs = preview_rename([f], suffix_tag="@dario")
    done, errs = apply_rename(pairs, mode="copy", output_dir=out)
    assert done == 1 and errs == []
    assert f.exists()
    assert (out / "snare_03_@dario.wav").exists()


def test_apply_blocked_on_error_writes_nothing(tmp_path):
    a = _f(tmp_path, "a.wav")
    b = _f(tmp_path, "A.WAV")
    pairs = preview_rename([a, b], replace_old="a", replace_new="same")
    done, errs = apply_rename(pairs, mode="inplace")
    assert done == 0 and errs
