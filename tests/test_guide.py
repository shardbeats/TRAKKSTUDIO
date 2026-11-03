"""Guide tests: shortcuts, Space routing, tour/about texts, first-run flag (offscreen)."""
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

import gui  # noqa: E402
from gui import (  # noqa: E402
    APP_VERSION,
    SHORTCUTS,
    about_text,
    is_first_run,
    mark_welcomed,
    tour_text,
    welcomed_path,
)


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def win(app, tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    w = gui.MainWindow(welcome=False)
    yield w
    w.close()


def test_shortcuts_registered(win):
    from PySide6.QtGui import QShortcut

    keys = {s.key().toString() for s in win.findChildren(QShortcut)}
    assert "Space" in keys
    assert win.btnAddFolder.shortcut().toString() == "Ctrl+O"
    assert win.btnPreviewRn.shortcut().toString() == "Ctrl+R"
    assert win.btnClear.shortcut().toString() == "Del"
    advertised = {k for k, _ in SHORTCUTS}
    assert {"Ctrl+O", "Ctrl+R", "Space", "Del", "F1"} <= advertised


def test_space_routes_to_visible_tab(win, monkeypatch):
    calls = []
    monkeypatch.setattr(win, "do_preview_rn", lambda: calls.append("preview"))
    monkeypatch.setattr(win, "do_start_conv", lambda: calls.append("conv"))
    monkeypatch.setattr(win, "do_start_norm", lambda: calls.append("norm"))
    for idx, want in ((0, "preview"), (1, "conv"), (2, "norm")):
        calls.clear()
        win.tabs.setCurrentIndex(idx)
        win._on_space()
        assert calls == [want]


def test_space_ignored_while_typing(win, monkeypatch):
    calls = []
    monkeypatch.setattr(win, "do_start_conv", lambda: calls.append("conv"))
    # offscreen never grants real focus: simulate a typing widget instead
    monkeypatch.setattr(QApplication, "focusWidget",
                        classmethod(lambda cls: win.edConvOut))
    win.tabs.setCurrentIndex(1)
    win._on_space()
    assert calls == []


def test_space_cancels_running_batch(win, monkeypatch):
    from types import SimpleNamespace

    cancelled = []
    win.thread = SimpleNamespace(isRunning=lambda: True,
                                 cancel=lambda: cancelled.append(True))
    win._on_space()
    assert cancelled == [True]
    win.thread = None


def test_tour_and_about_texts():
    t = tour_text()
    assert "ORGANIZER" in t and "CONVERTER" in t and "NORMALIZER" in t
    assert "Space" in t
    a = about_text()
    assert APP_VERSION in a and "MIT" in a


def test_first_run_flag_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert is_first_run() is True
    mark_welcomed()
    assert is_first_run() is False
    assert welcomed_path().is_file()


def test_maybe_welcome_shows_once(win, monkeypatch):
    shown = []
    monkeypatch.setattr(win, "show_tour", lambda: shown.append(True))
    win._maybe_welcome()
    win._maybe_welcome()
    assert shown == [True]
