"""Sample playback preview via ffplay (audio-only, offline, no modals)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal


def ffplay_bin() -> str | None:
    """Path to the ffplay binary, or None when unavailable.

    Frozen exe: bundled via --add-binary next to the app (sys._MEIPASS).
    Source runs: ffplay on PATH (ships next to ffmpeg in Gyan builds).
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidate = Path(base) / "ffplay.exe"
        if candidate.exists():
            return str(candidate)
    return shutil.which("ffplay") or shutil.which("ffplay.exe")


class SamplePlayer(QObject):
    """One-shot audio preview. Never blocks, never pops dialogs."""

    started = Signal(str)  # path
    stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None
        self._current = ""

    def is_playing(self) -> bool:
        return self._proc is not None and self._proc.state() != QProcess.NotRunning

    def current(self) -> str:
        return self._current if self.is_playing() else ""

    def play(self, path: str | Path) -> bool:
        """Play a file (audio-only window). Restarts any current preview."""
        self.stop()
        exe = ffplay_bin()
        if exe is None or not Path(path).is_file():
            return False
        proc = QProcess(self)
        proc.finished.connect(self._on_finished)
        proc.start(exe, ["-nodisp", "-autoexit", "-loglevel", "quiet", str(path)])
        if not proc.waitForStarted(3000):
            proc.deleteLater()
            return False
        self._proc = proc
        self._current = str(path)
        self.started.emit(self._current)
        return True

    def stop(self) -> None:
        proc, self._proc = self._proc, None
        self._current = ""
        if proc is not None:
            if proc.state() != QProcess.NotRunning:
                proc.kill()
                proc.waitForFinished(1000)
            proc.deleteLater()
        self.stopped.emit()

    def _on_finished(self) -> None:
        self._proc = None
        self._current = ""
        self.stopped.emit()
