"""Player tests: ffplay resolution + play/stop + GUI wiring (offscreen)."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

import gui  # noqa: E402
from player import SamplePlayer, ffplay_bin  # noqa: E402

FF = shutil.which("ffmpeg")
FFPLAY = ffplay_bin()


def _tone(path: Path):
    cmd = ["ffmpeg", "-nostdin", "-y", "-f", "lavfi", "-i",
           "sine=frequency=440:sample_rate=44100:duration=0.5",
           "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(path)]
    subprocess.run(cmd, capture_output=True, check=True, timeout=60)


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_ffplay_bin_str_or_none():
    assert ffplay_bin() is None or Path(ffplay_bin()).name.lower() == "ffplay.exe"


def test_play_missing_binary_returns_false(monkeypatch):
    monkeypatch.setattr("player.shutil.which", lambda *a, **k: None)
    import player as P

    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    assert P.ffplay_bin() is None


def test_play_missing_file_returns_false(app):
    pl = SamplePlayer()
    assert pl.play(Path("nope_missing.wav")) is False
    assert pl.is_playing() is False


@pytest.mark.skipif(not (FF and FFPLAY), reason="needs ffmpeg + ffplay")
def test_play_stop_tone(app, tmp_path):
    tone = tmp_path / "tone.wav"
    _tone(tone)
    pl = SamplePlayer()
    assert pl.play(tone) is True
    assert pl.is_playing() is True
    assert pl.current() == str(tone)
    pl.stop()
    assert pl.is_playing() is False
    assert pl.current() == ""


@pytest.mark.skipif(not (FF and FFPLAY), reason="needs ffmpeg + ffplay")
def test_restart_while_playing(app, tmp_path):
    tone = tmp_path / "tone.wav"
    _tone(tone)
    pl = SamplePlayer()
    assert pl.play(tone) is True
    assert pl.play(tone) is True  # restart must not stack processes
    assert pl.is_playing() is True
    pl.stop()


@pytest.fixture()
def win(app, tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    w = gui.MainWindow(welcome=False)
    yield w
    w.close()


def test_double_click_plays_row_file(win, tmp_path, monkeypatch):
    f = tmp_path / "kick.wav"
    f.write_bytes(b"RIFF....")
    played = []
    monkeypatch.setattr(win.player, "play", lambda p: played.append(Path(p)) or True)
    win.files = [f]
    win.refresh_queue()
    win._play_row(0, 0)
    assert played == [f]


def test_play_button_empty_list_no_modal(win):
    win.files = []
    win.play_selected()  # must not pop any dialog
    assert "nothing to play" in win.lblPlay.text()


def test_stop_button_and_clear_stop_player(win, monkeypatch):
    stops = []
    monkeypatch.setattr(win.player, "stop", lambda: stops.append(True))
    win.btnStop.click()
    win.clear_all()
    assert len(stops) == 2


def test_selecting_another_row_cuts_preview(win, tmp_path, monkeypatch):
    f1, f2 = tmp_path / "a.wav", tmp_path / "b.wav"
    f1.write_bytes(b"RIFF....")
    f2.write_bytes(b"RIFF....")
    win.files = [f1, f2]
    win.refresh_queue()
    stops = []
    playing = {"on": False}
    monkeypatch.setattr(win.player, "is_playing", lambda: playing["on"])
    monkeypatch.setattr(win.player, "stop",
                        lambda: (stops.append(True), playing.__setitem__("on", False)))
    win.queue.selectRow(0)
    assert stops == []
    playing["on"] = True  # preview running…
    win.queue.selectRow(1)  # …pick another row: cut, no Stop needed
    assert stops == [True]


def test_stale_finished_never_wipes_new_process(app):
    from types import SimpleNamespace

    pl = SamplePlayer()
    fired = []
    pl.stopped.connect(lambda: fired.append(True))
    old = SimpleNamespace(deleteLater=lambda: None)
    new = SimpleNamespace(deleteLater=lambda: None)
    pl._proc = new
    pl._current = "new.wav"
    pl._on_proc_finished(old)  # late signal from the killed preview
    assert pl._proc is new and pl._current == "new.wav"
    assert fired == []
    pl._on_proc_finished(new)
    assert pl._proc is None and pl.current() == ""
    assert fired == [True]
