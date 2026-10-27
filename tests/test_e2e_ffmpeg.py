import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import converter as C
import normalizer as N

FF = shutil.which("ffmpeg")


def _tone(path: Path, db_drop: float = 0.0, rate: int = 44100):
    # 0.5s sine; volume drop to control peak for normalize tests
    cmd = ["ffmpeg", "-nostdin", "-y", "-f", "lavfi", "-i",
           f"sine=frequency=440:sample_rate={rate}:duration=0.5",
           "-af", f"volume={db_drop}dB", "-ar", str(rate), "-ac", "2",
           "-c:a", "pcm_s16le", str(path)]
    subprocess.run(cmd, capture_output=True, check=True, timeout=60)


@pytest.mark.skipif(not FF, reason="ffmpeg not on PATH")
def test_e2e_convert_mp3_to_48k_sp(tmp_path):
    src = tmp_path / "tone.mp3"
    _tone(tmp_path / "tone.wav", rate=44100)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-i", str(tmp_path / "tone.wav"),
                    "-c:a", "libmp3lame", str(src)],
                   capture_output=True, check=True, timeout=60)
    r = C.convert_file(src, tmp_path / "out", tmp_path, False, 48000)
    assert r.success and r.output_path and r.output_path.name.endswith("_sp.wav")
    info = C.get_audio_info(r.output_path)
    assert info["sample_rate"] == 48000 and info["channels"] == 2


@pytest.mark.skipif(not FF, reason="ffmpeg not on PATH")
def test_e2e_normalize_quiet_tone_to_minus1(tmp_path):
    src = tmp_path / "quiet.wav"
    _tone(src, db_drop=-12.0)
    r = N.normalize_file(src, target_db=-1.0, tolerance_db=0.5)
    assert r.success and r.output_path is not None
    peak = N.measure_peak_db(r.output_path)
    assert peak is not None and abs(peak - (-1.0)) < 0.6


@pytest.mark.skipif(not FF, reason="ffmpeg not on PATH")
def test_e2e_normalize_skips_when_in_range(tmp_path):
    src = tmp_path / "hot.wav"
    _tone(src, db_drop=-3.0)
    peak = N.measure_peak_db(src)
    assert peak is not None
    # target = measured peak -> gain 0 -> must skip (tests tolerance logic, not absolute level)
    r = N.normalize_file(src, target_db=peak, tolerance_db=0.5)
    assert r.success and r.action == "skipped_range"
