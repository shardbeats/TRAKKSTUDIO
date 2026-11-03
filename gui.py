"""TRAKKSTUDIO GUI — multitool 3 tabs independientes + top bar comun (PySide6)."""
from __future__ import annotations

import ctypes
import os
import shutil
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMessageBox, QPushButton, QProgressBar, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
    QAbstractSpinBox,
)

import converter as C
import normalizer as N
from organizer import (
    PRESETS, apply_rename, create_structure, guess_category,
    preview_rename, scan_to_rows,
)
from db import upsert_files
from player import SamplePlayer, ffplay_bin


def resource_path(name: str) -> Path:
    """File next to source OR bundled in PyInstaller one-file (_MEIPASS)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = Path(base) / name
        if p.exists():
            return p
    return Path(__file__).with_name(name)


def short_folder(path: Path) -> str:
    """Last 2 folder parts for narrow panels (full path stays in tooltip)."""
    parts = path.parent.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return str(path.parent)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


APP_VERSION = "1.0"

SHORTCUTS: list[tuple[str, str]] = [
    ("Ctrl+O", "Add folder"),
    ("Ctrl+R", "Preview rename (tab 1)"),
    ("Space", "START / Cancel current tab (never while typing)"),
    ("Del", "Clear file list"),
    ("F1", "Quick tour"),
    ("Dbl-click", "Play sample under cursor"),
]


def tour_text() -> str:
    return (
        "TRAKKSTUDIO in 3 steps:\n\n"
        "1 · ORGANIZER rename — pick files (or all), set Prefix/Suffix/Old/New, "
        "Preview rename (Ctrl+R), check After, then APPLY. In-place by default.\n\n"
        "2 · CONVERTER SP-404 — pick rate (48k native), Preview actions "
        "(copy/convert/skip), START CONVERT (Space). Output: *_sp.wav.\n\n"
        "3 · NORMALIZER peak — set Target (-1.0dB) and tolerance, "
        "START NORMALIZE (Space). Output: *_N.wav.\n\n"
        "Each tab is independent with its own START/Cancel. "
        "Drag & drop folders anytime (Ctrl+O). Space never fires while typing.\n\n"
        "Double-click any row (or Play) to listen — audio preview, Stop to cut it."
    )


def about_text() -> str:
    return (
        f"TRAKKSTUDIO v{APP_VERSION}\n"
        "Offline multitool for beatmakers · ShardBeats TRAKK SUITE\n"
        "\n"
        "MIT licensed (see LICENSE + NOTICE.md + THIRD-PARTY-NOTICES.md).\n"
        "Portable and offline: inventory lives in %APPDATA%/TRAKKSTUDIO/library.db."
    )


def welcomed_path() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "TRAKKSTUDIO" / ".welcomed"


def is_first_run() -> bool:
    return not welcomed_path().is_file()


def mark_welcomed() -> None:
    try:
        p = welcomed_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("v1\n", encoding="utf-8")
    except OSError:
        pass


def fmt_bytes(n: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


class BatchThread(QThread):
    prog = Signal(int, int, str)
    done = Signal(dict)

    def __init__(self, jobs: list, fn, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.fn = fn
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        ok = fail = skip = 0
        rows: list[tuple[str, str, str]] = []
        total = len(self.jobs)
        for i, job in enumerate(self.jobs, 1):
            if self._cancel:
                rows.append((str(job), "", "cancelled"))
                self.prog.emit(i, total, "cancelled")
                continue
            try:
                out, status, err = self.fn(job, lambda: self._cancel)
            except Exception as e:  # never kill batch
                out, status, err = "", "failed", str(e)
            if status in ("skipped", "skip"):
                skip += 1
            elif status == "done":
                ok += 1
            else:
                fail += 1
            rows.append((str(job), out, status if not err else f"{status}: {err}"))
            self.prog.emit(i, total, str(job))
        self.done.emit({"ok": ok, "fail": fail, "skip": skip, "rows": rows})


class MainWindow(QMainWindow):
    def __init__(self, welcome: bool = True):
        super().__init__()
        self.setWindowTitle("TRAKKSTUDIO — Organizer / Converter / Normalizer")
        self.resize(1080, 720)
        self.setAcceptDrops(True)
        self.files: list[Path] = []
        self.thread: BatchThread | None = None

        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)

        # Brand header (TRAKK SUITE identity: title + amber subtitle, styled in QSS)
        brand = QHBoxLayout()
        self.lblTitle = QLabel("TRAKKSTUDIO")
        self.lblTitle.setObjectName("titleLabel")
        self.lblSub = QLabel("SHARDBEATS TRAKK SUITE — ORGANIZE / CONVERT / NORMALIZE")
        self.lblSub.setObjectName("subtitleLabel")
        brand.addWidget(self.lblTitle)
        brand.addWidget(self.lblSub, 1)
        lay.addLayout(brand)

        # Top bar comun
        top = QHBoxLayout()
        self.btnAddFolder = QPushButton("Add folder  (Ctrl+O)")
        self.btnAddFiles = QPushButton("Add files")
        self.btnClear = QPushButton("Clear  (Del)")
        self.btnPlay = QPushButton("Play")
        self.btnPlay.setToolTip("Play selected (or first) sample — audio preview via ffplay")
        self.btnStop = QPushButton("Stop")
        self.btnStop.setToolTip("Stop playback")
        self.lblPlay = QLabel("")
        self.lblPlay.setObjectName("statusLabel")
        self.lblCount = QLabel("0 files — drag & drop folders here")
        self.lblCount.setObjectName("statusLabel")
        top.addWidget(self.btnAddFolder)
        top.addWidget(self.btnAddFiles)
        top.addWidget(self.btnClear)
        top.addWidget(self.btnPlay)
        top.addWidget(self.btnStop)
        top.addWidget(self.lblPlay)
        top.addWidget(self.lblCount, 1)
        lay.addLayout(top)

        if is_admin():
            w = QLabel("WARNING: running as Administrator — Windows blocks drag&drop. Restart normally.")
            w.setObjectName("warnLabel")
            lay.addWidget(w)

        self.queue = QTableWidget(0, 3)
        self.queue.setHorizontalHeaderLabels(["File", "Folder", "Category?"])
        # Two columns: queue left (tall), tools right. File stretches inside left panel.
        from PySide6.QtWidgets import QHeaderView as _HV, QSplitter as _SPLIT, QGroupBox as _GB
        _hh = self.queue.horizontalHeader()
        _hh.setStretchLastSection(False)
        _hh.setSectionResizeMode(0, _HV.Stretch)
        _hh.setSectionResizeMode(1, _HV.Interactive)
        _hh.setSectionResizeMode(2, _HV.Fixed)
        self.queue.setColumnWidth(1, 160)
        self.queue.setColumnWidth(2, 100)
        self.queue.verticalHeader().setVisible(False)
        self.queue.setSelectionBehavior(self.queue.SelectionBehavior.SelectRows)
        self.queue.setTextElideMode(Qt.ElideRight)
        self.queue.setMinimumWidth(400)

        left = QWidget()
        leftLay = QVBoxLayout(left)
        leftLay.setContentsMargins(0, 0, 0, 0)
        gbFiles = _GB("FILES — drag & drop here")
        gbLay = QVBoxLayout(gbFiles)
        gbLay.addWidget(self.queue)
        leftLay.addWidget(gbFiles)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._org_tab(), "1 · ORGANIZER rename")
        self.tabs.addTab(self._conv_tab(), "2 · CONVERTER SP-404")
        self.tabs.addTab(self._norm_tab(), "3 · NORMALIZER peak")

        split = _SPLIT(Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(self.tabs)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        split.setSizes([470, 610])
        split.setChildrenCollapsible(False)
        lay.addWidget(split, 1)

        self.lblFooter = QLabel(f"SHARDBEATS TRAKK SUITE · portable · offline · v{APP_VERSION}")
        self.lblFooter.setObjectName("footerLabel")
        lay.addWidget(self.lblFooter)

        try:
            from PySide6.QtGui import QIcon
            ico = resource_path("icon.ico")
            if ico.exists():
                self.setWindowIcon(QIcon(str(ico)))
        except Exception:
            pass

        self.btnAddFolder.clicked.connect(self.add_folder)
        self.btnAddFiles.clicked.connect(self.add_files)
        self.btnClear.clicked.connect(self.clear_all)
        self.btnClear.setShortcut("Del")
        self.btnAddFolder.setShortcut("Ctrl+O")
        self.player = SamplePlayer(self)
        self.player.started.connect(self._on_play_started)
        self.player.stopped.connect(self._on_play_stopped)
        QApplication.instance().aboutToQuit.connect(self.player.stop)
        self.btnPlay.clicked.connect(self.play_selected)
        self.btnStop.clicked.connect(self.player.stop)
        self.queue.cellDoubleClicked.connect(self._play_row)
        self._setup_shortcuts()
        self._setup_help_menu()
        if welcome:
            self._maybe_welcome()

    # ---- guide: shortcuts + help menu + first-run tour ----
    def _setup_shortcuts(self):
        # Window-level Space routes to the visible tab. Button-level Space
        # is banned: it also fires while typing spaces in the rename fields.
        sc = QShortcut(QKeySequence("Space"), self)
        sc.setContext(Qt.WindowShortcut)
        sc.activated.connect(self._on_space)

    def _on_space(self):
        fw = QApplication.focusWidget()
        if isinstance(fw, (QLineEdit, QTextEdit, QAbstractSpinBox, QComboBox)):
            return  # never steal keystrokes while typing
        if self.thread and self.thread.isRunning():
            self.do_cancel()
            return
        idx = self.tabs.currentIndex()
        if idx == 0:
            self.do_preview_rn()
        elif idx == 1:
            self.do_start_conv()
        else:
            self.do_start_norm()

    def _setup_help_menu(self):
        m = self.menuBar().addMenu("Help")
        a_tour = m.addAction("Quick tour…")
        a_tour.setShortcut("F1")
        a_tour.triggered.connect(lambda: self.show_tour())
        a_keys = m.addAction("Keyboard shortcuts…")
        a_keys.triggered.connect(self.show_shortcuts)
        m.addSeparator()
        a_about = m.addAction("About TRAKKSTUDIO…")
        a_about.triggered.connect(self.show_about)

    def _maybe_welcome(self):
        if is_first_run():
            mark_welcomed()
            self.show_tour()

    def show_tour(self):
        box = QDialog(self)
        box.setWindowTitle("TRAKKSTUDIO — Quick tour")
        lay = QVBoxLayout(box)
        lab = QLabel(tour_text())
        lab.setWordWrap(True)
        lab.setMinimumWidth(460)
        lay.addWidget(lab)
        btn = QPushButton("Start organizing")
        btn.clicked.connect(box.accept)
        lay.addWidget(btn)
        box.exec()

    def show_shortcuts(self):
        lines = "\n".join(f"{k:10s}  {desc}" for k, desc in SHORTCUTS)
        QMessageBox.information(self, "Keyboard shortcuts", lines)

    def show_about(self):
        QMessageBox.about(self, "About TRAKKSTUDIO", about_text())

    # ---- shared queue ----
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [Path(u.toLocalFile()) for u in e.mimeData().urls()]
        self.add_paths(paths)

    def add_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Add folder")
        if d:
            self.add_paths([Path(d)])

    def add_files(self):
        fs, _ = QFileDialog.getOpenFileNames(self, "Add files", "", "Audio (*.wav *.mp3 *.flac *.ogg *.m4a *.aac *.aiff *.aif *.wma *.opus *.webm)")
        if fs:
            self.add_paths([Path(f) for f in fs])

    def add_paths(self, paths: list[Path]):
        new: list[Path] = []
        for p in paths:
            if not p.exists():
                continue
            if p.is_file() and p.suffix.lower() in C.SUPPORTED_EXTENSIONS:
                new.append(p)
            elif p.is_dir():
                new.extend(C.find_audio_files(p))
        # dedup + skip already processed unless re-procesar
        seen = {str(f).lower() for f in self.files}
        for f in new:
            if str(f).lower() not in seen:
                self.files.append(f)
                seen.add(str(f).lower())
        try:
            upsert_files(scan_to_rows(self.files))
        except Exception:
            pass
        self.refresh_queue()

    def clear_all(self):
        self.player.stop()
        self.files = []
        self.refresh_queue()

    # ---- playback preview (ffplay audio-only, never modal) ----
    def play_selected(self):
        files = self.selected_or_all()
        if not files:
            self.lblPlay.setText("nothing to play — add files first")
            return
        self._play(files[0])

    def _play_row(self, row: int, _col: int):
        ordered = sorted(self.files)
        if 0 <= row < len(ordered):
            self._play(ordered[row])

    def _play(self, path: Path):
        if self.player.play(path):
            return
        if ffplay_bin() is None:
            self.lblPlay.setText("ffplay missing — install FFmpeg on PATH (portable exe brings it)")
        else:
            self.lblPlay.setText(f"cannot play {Path(path).name}")

    def _on_play_started(self, path: str):
        self.lblPlay.setText(f"▶ {Path(path).name}")

    def _on_play_stopped(self):
        if not self.player.is_playing():
            self.lblPlay.setText("")

    def refresh_queue(self):
        self.queue.setRowCount(len(self.files))
        groups: dict[str, int] = {}
        for i, f in enumerate(sorted(self.files)):
            groups[str(f.parent)] = groups.get(str(f.parent), 0) + 1
            it0 = QTableWidgetItem(f.name)
            it0.setToolTip(str(f))
            it1 = QTableWidgetItem(short_folder(f))
            it1.setToolTip(str(f.parent))
            self.queue.setItem(i, 0, it0)
            self.queue.setItem(i, 1, it1)
            self.queue.setItem(i, 2, QTableWidgetItem(guess_category(f)))
        total_b = sum(f.stat().st_size for f in self.files if f.exists())
        self.lblCount.setText(f"{len(self.files)} files / {len(groups)} packs / {fmt_bytes(total_b)}")

    def selected_or_all(self) -> list[Path]:
        rows = sorted({ix.row() for ix in self.queue.selectedIndexes()})
        if rows:
            ordered = sorted(self.files)
            return [ordered[r] for r in rows if r < len(ordered)]
        return list(self.files)

    def browse_out(self, line: QLineEdit):
        d = QFileDialog.getExistingDirectory(self, "Output folder (empty = next to source)")
        if d:
            line.setText(d)

    @staticmethod
    def check_space(files: list[Path], parent: QWidget) -> bool:
        try:
            need = sum(f.stat().st_size for f in files if f.exists()) * 1.8 + 100 * 1024 * 1024
            free = shutil.disk_usage(str(Path(files[0]).anchor)).free if files else 10**12
            if need > free:
                QMessageBox.critical(parent, "No space", f"Need ~{fmt_bytes(int(need))}, free {fmt_bytes(free)}")
                return False
        except Exception:
            pass
        return True

    # ---- TAB 1 organizer ----
    def _org_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        g1 = QGroupBox("Structure presets (FR-3)")
        h = QHBoxLayout(g1)
        self.cmbPreset = QComboBox()
        self.cmbPreset.addItems(sorted(PRESETS))
        self.btnMkStruct = QPushButton("Create structure")
        h.addWidget(self.cmbPreset, 1)
        h.addWidget(self.btnMkStruct)
        lay.addWidget(g1)

        g2 = QGroupBox("Bulk rename (FR-4) — preview first, then APPLY")
        v = QVBoxLayout(g2)
        # Vertical: un campo por fila a ancho completo para nombres largos
        self.edPrefix = QLineEdit()
        self.edPrefix.setPlaceholderText("prefix (ej PACK)")
        self.edSuffix = QLineEdit()
        self.edSuffix.setPlaceholderText("suffix tag (ej @producer) — se concatena sin tocar base")
        self.edOld = QLineEdit(); self.edOld.setPlaceholderText("replace old")
        self.edNew = QLineEdit(); self.edNew.setPlaceholderText("replace new")
        for label, field in (("Prefix:", self.edPrefix), ("Suffix:", self.edSuffix),
                             ("Old:", self.edOld), ("New:", self.edNew)):
            row = QHBoxLayout()
            lb = QLabel(label); lb.setMinimumWidth(48)
            row.addWidget(lb)
            row.addWidget(field, 1)
            v.addLayout(row)
        r2 = QHBoxLayout()
        self.chkWhole = QCheckBox("Whole name (=New)")
        self.chkWhole.setToolTip("ON = borra todo el nombre y usa New completo. Auto-activa Numerate si hay >1 archivo para evitar colisiones.")
        self.chkNumerate = QCheckBox("Numerate _{001}")
        self.spinNum = QSpinBox(); self.spinNum.setRange(0, 99999); self.spinNum.setValue(1)
        r2.addWidget(self.chkWhole)
        r2.addWidget(self.chkNumerate); r2.addWidget(self.spinNum)
        r2.addStretch(1)
        v.addLayout(r2)
        r3 = QHBoxLayout()
        self.btnPreviewRn = QPushButton("Preview rename  (Ctrl+R)")
        self.btnPreviewRn.setShortcut("Ctrl+R")
        self.rbOrgCopy = QCheckBox("Copy to output (keep originals)")
        self.rbOrgCopy.setChecked(False)
        self.rbOrgCopy.setToolTip("OFF = rename in-place (renombra originales). ON = copia con nuevo nombre a output folder.")
        self.edOrgOut = QLineEdit(); self.edOrgOut.setPlaceholderText("output folder (only if Copy checked, else in-place)")
        self.btnOrgBrowse = QPushButton("Browse")
        self.btnOrgBrowse.setObjectName("browseBtn")
        self.btnApplyRn = QPushButton("APPLY RENAME")
        self.btnApplyRn.setObjectName("convertBtn")
        r3.addWidget(self.btnPreviewRn)
        r3.addWidget(self.rbOrgCopy)
        r3.addWidget(self.edOrgOut, 1)
        r3.addWidget(self.btnOrgBrowse)
        r3.addWidget(self.btnApplyRn)
        v.addLayout(r3)
        self.tblRn = QTableWidget(0, 3)
        self.tblRn.setHorizontalHeaderLabels(["Before", "After", "Error"])
        from PySide6.QtWidgets import QHeaderView as _HV2
        _hr = self.tblRn.horizontalHeader()
        _hr.setStretchLastSection(False)
        _hr.setSectionResizeMode(0, _HV2.Stretch)
        _hr.setSectionResizeMode(1, _HV2.Stretch)
        _hr.setSectionResizeMode(2, _HV2.Fixed)
        self.tblRn.setColumnWidth(2, 220)
        self.tblRn.verticalHeader().setDefaultSectionSize(26)
        self.tblRn.setSelectionBehavior(self.tblRn.SelectionBehavior.SelectRows)
        v.addWidget(self.tblRn, 1)
        self.lblOrg = QLabel("")
        self.lblOrg.setObjectName("statusLabel")
        v.addWidget(self.lblOrg)
        lay.addWidget(g2)
        self._pairs = []
        self.btnMkStruct.clicked.connect(self.do_structure)
        self.btnOrgBrowse.clicked.connect(lambda: self.browse_out(self.edOrgOut))
        self.btnPreviewRn.clicked.connect(self.do_preview_rn)
        self.btnApplyRn.clicked.connect(self.do_apply_rn)
        return w

    def do_structure(self):
        dest_text = self.edOrgOut.text().strip()
        if not dest_text:
            d = QFileDialog.getExistingDirectory(self, "Where to create structure?")
            if not d:
                return
            dest_text = d
        try:
            paths = create_structure(Path(dest_text), self.cmbPreset.currentText())
            QMessageBox.information(self, "OK", f"Created {len(paths)} folders in {dest_text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def do_preview_rn(self):
        files = self.selected_or_all()
        if not files:
            QMessageBox.warning(self, "Empty", "Add files first (drag & drop).")
            return
        # NOTE: Old/New se pasan RAW (sin strip): un espacio es un reemplazo valido.
        old, new = self.edOld.text(), self.edNew.text()
        whole = self.chkWhole.isChecked()
        if whole and not new.strip():
            QMessageBox.warning(self, "Whole name", "Escribe el nombre completo en New.")
            return
        if whole and len(files) > 1 and not self.chkNumerate.isChecked():
            self.chkNumerate.setChecked(True)
        self._pairs = preview_rename(
            files, prefix=self.edPrefix.text().strip(), suffix_tag=self.edSuffix.text().strip(),
            replace_old=old, replace_new=new, replace_whole=whole,
            numerate_from=self.spinNum.value() if self.chkNumerate.isChecked() else None)
        self.tblRn.setRowCount(len(self._pairs))
        blocked = 0
        changed = 0
        for i, p in enumerate(self._pairs):
            self.tblRn.setItem(i, 0, QTableWidgetItem(p.src.name))
            self.tblRn.setItem(i, 1, QTableWidgetItem(p.dst_name))
            # Error state via text (chrome colors live in styles.qss, not here)
            it = QTableWidgetItem(("" if not p.error else "BLOCKED: ") + p.error)
            if p.error:
                blocked += 1
            if p.dst_name != p.src.name:
                changed += 1
            self.tblRn.setItem(i, 2, it)
        msg = f"{len(self._pairs)} preview, {changed} cambian, {blocked} blocked"
        if old and changed == 0 and not blocked:
            msg += f" — Replace '{old}' no encontrado en ningun nombre (revisa espacios/guiones/mayusculas)"
        elif not blocked:
            msg += " — ready to APPLY"
        else:
            msg += " — fix collisions (enable numerate)"
        self.lblOrg.setText(msg)

    def do_apply_rn(self):
        if not self._pairs:
            self.do_preview_rn()
            if not self._pairs:
                return
        if any(p.error for p in self._pairs):
            QMessageBox.critical(self, "Blocked", "Fix collisions first (enable Numerate).")
            return
        mode = "copy" if self.rbOrgCopy.isChecked() else "inplace"
        out = Path(self.edOrgOut.text().strip()) if (mode == "copy" and self.edOrgOut.text().strip()) else None
        if mode == "copy" and out is None:
            QMessageBox.warning(self, "Need output", "Copy mode needs an output folder.")
            return
        done, errs = apply_rename(self._pairs, mode=mode, output_dir=out)
        self.lblOrg.setText(f"done {done}, errors {len(errs)}")
        if errs:
            QMessageBox.critical(self, "Errors", "\n".join(errs[:10]))
        else:
            QMessageBox.information(self, "OK", f"Renamed {done} files.")
            if mode == "inplace":
                self.files = [f.parent / p.dst_name for f, p in zip([p.src for p in self._pairs], self._pairs)]
                self.refresh_queue()

    # ---- TAB 2 converter ----
    def _conv_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        g = QGroupBox("Converter SP-404MK2 (standalone — FR-6)")
        v = QVBoxLayout(g)
        r = QHBoxLayout()
        self.cmbRate = QComboBox(); self.cmbRate.addItems(["48000", "44100"]); self.cmbRate.setCurrentText("48000")
        self.chkForce = QCheckBox("Force to rate (uniform pack)"); self.chkForce.setChecked(True)
        r.addWidget(QLabel("Target rate:")); r.addWidget(self.cmbRate)
        r.addWidget(self.chkForce)
        v.addLayout(r)
        r2 = QHBoxLayout()
        self.edConvOut = QLineEdit(); self.edConvOut.setPlaceholderText("output folder (empty = <source>_sp next to source)")
        self.btnConvBrowse = QPushButton("Browse")
        self.btnConvBrowse.setObjectName("browseBtn")
        self.chkConvPreserve = QCheckBox("Preserve structure"); self.chkConvPreserve.setChecked(True)
        self.chkConvDel = QCheckBox("Delete original after OK (in-place)")
        r2.addWidget(self.edConvOut, 1); r2.addWidget(self.btnConvBrowse)
        r2.addWidget(self.chkConvPreserve); r2.addWidget(self.chkConvDel)
        v.addLayout(r2)
        r3 = QHBoxLayout()
        self.btnPrevConv = QPushButton("Preview actions")
        self.btnStartConv = QPushButton("START CONVERT (Space)")
        self.btnStartConv.setObjectName("convertBtn")
        self.btnCancelConv = QPushButton("Cancel")
        self.barConv = QProgressBar()
        r3.addWidget(self.btnPrevConv); r3.addWidget(self.btnStartConv); r3.addWidget(self.btnCancelConv); r3.addWidget(self.barConv, 1)
        v.addLayout(r3)
        self.tblConv = QTableWidget(0, 3)
        self.tblConv.setHorizontalHeaderLabels(["File", "Action", "Info"])
        self.tblConv.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.tblConv)
        self.logConv = QTextEdit(); self.logConv.setMaximumHeight(110); self.logConv.setReadOnly(True)
        v.addWidget(self.logConv)
        lay.addWidget(g)
        self.btnConvBrowse.clicked.connect(lambda: self.browse_out(self.edConvOut))
        self.btnPrevConv.clicked.connect(self.do_preview_conv)
        self.btnStartConv.clicked.connect(self.do_start_conv)
        self.btnCancelConv.clicked.connect(self.do_cancel)
        return w

    def _conv_dest(self, src: Path, out_text: str, preserve: bool) -> tuple[Path, Path | None]:
        if out_text:
            return Path(out_text), (src.parent if preserve else None)
        base = src.parent
        # next-to-source mirror <source>_sp
        root = src.parent
        dest = root.parent / f"{root.name}_sp"
        return dest, (root if preserve else None)

    def do_preview_conv(self):
        files = self.selected_or_all()
        if not files:
            QMessageBox.warning(self, "Empty", "Add files first.")
            return
        rate = int(self.cmbRate.currentText())
        self.tblConv.setRowCount(len(files))
        for i, f in enumerate(files):
            if f.stem.endswith("_sp"):
                act, info = "skip", "already _sp"
            else:
                info_d = C.get_audio_info(f)
                if not info_d:
                    act, info = "convert?", "unreadable->try"
                elif not self.chkForce.isChecked() and not C.needs_conversion(f, None, info_d):
                    act, info = "copy", f"{info_d.get('sample_rate')}Hz ok"
                elif not C.needs_conversion(f, rate if self.chkForce.isChecked() else None, info_d):
                    act, info = "copy", f"{info_d.get('sample_rate')}Hz ok"
                else:
                    act, info = "convert", f"{info_d.get('sample_rate')}->{rate}Hz"
            self.tblConv.setItem(i, 0, QTableWidgetItem(f.name))
            self.tblConv.setItem(i, 1, QTableWidgetItem(act))
            self.tblConv.setItem(i, 2, QTableWidgetItem(str(info)))

    def do_start_conv(self):
        files = self.selected_or_all()
        if not files or not self.check_space(files, self):
            return
        rate = int(self.cmbRate.currentText())
        out_text = self.edConvOut.text().strip()
        preserve = self.chkConvPreserve.isChecked()
        del_orig = self.chkConvDel.isChecked()

        def job(src: Path, cancelled):
            dest, root = self._conv_dest(src, out_text, preserve)
            tgt = rate if self.chkForce.isChecked() else None
            r = C.convert_file(src, dest, root, preserve, tgt or rate)
            if not r.success:
                return "", "failed", r.error or ""
            if del_orig and r.output_path and r.output_path.exists():
                try:
                    if r.output_path.resolve() != src.resolve():
                        src.unlink()
                except OSError as e:
                    return str(r.output_path), "done", f"converted but keep orig: {e}"
            return str(r.output_path), "done", ""

        self.run_batch(files, job, self.barConv, self.logConv)

    # ---- TAB 3 normalizer ----
    def _norm_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        g = QGroupBox("Normalizer peak propio (standalone — FR-7)")
        v = QVBoxLayout(g)
        r = QHBoxLayout()
        self.spinTarget = QDoubleSpinBox(); self.spinTarget.setRange(-60, 0); self.spinTarget.setValue(-1.0); self.spinTarget.setSingleStep(0.5)
        self.spinTol = QDoubleSpinBox(); self.spinTol.setRange(0, 12); self.spinTol.setValue(0.5); self.spinTol.setSingleStep(0.1)
        self.chkReplace = QCheckBox("Replace original (only next-to-source)")
        r.addWidget(QLabel("Target peak dB:")); r.addWidget(self.spinTarget)
        r.addWidget(QLabel("Skip if within:")); r.addWidget(self.spinTol)
        r.addWidget(self.chkReplace)
        v.addLayout(r)
        r2 = QHBoxLayout()
        self.edNormOut = QLineEdit(); self.edNormOut.setPlaceholderText("output folder (empty = next to source)")
        self.btnNormBrowse = QPushButton("Browse")
        self.btnNormBrowse.setObjectName("browseBtn")
        self.chkNormPreserve = QCheckBox("Preserve structure"); self.chkNormPreserve.setChecked(True)
        r2.addWidget(self.edNormOut, 1); r2.addWidget(self.btnNormBrowse); r2.addWidget(self.chkNormPreserve)
        v.addLayout(r2)
        r3 = QHBoxLayout()
        self.btnStartNorm = QPushButton("START NORMALIZE (Space)")
        self.btnStartNorm.setObjectName("convertBtn")
        self.btnCancelNorm = QPushButton("Cancel")
        self.barNorm = QProgressBar()
        r3.addWidget(self.btnStartNorm); r3.addWidget(self.btnCancelNorm); r3.addWidget(self.barNorm, 1)
        v.addLayout(r3)
        self.logNorm = QTextEdit(); self.logNorm.setMaximumHeight(140); self.logNorm.setReadOnly(True)
        v.addWidget(self.logNorm)
        lay.addWidget(g)
        hint = QLabel("Cada clip a su propio peak (linear gain). `_N.wav` se skipea. Silencio → skip + log.")
        hint.setObjectName("statusLabel")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)
        self.btnNormBrowse.clicked.connect(lambda: self.browse_out(self.edNormOut))
        self.btnStartNorm.clicked.connect(self.do_start_norm)
        self.btnCancelNorm.clicked.connect(self.do_cancel)
        return w

    def do_start_norm(self):
        files = self.selected_or_all()
        if not files or not self.check_space(files, self):
            return
        tgt, tol = self.spinTarget.value(), self.spinTol.value()
        out_text = self.edNormOut.text().strip()
        preserve = self.chkNormPreserve.isChecked()
        mode = "replace" if (self.chkReplace.isChecked() and not out_text) else "copy"
        if self.chkReplace.isChecked() and out_text:
            QMessageBox.warning(self, "Replace", "Replace only applies next-to-source (output empty). Using Copy.")
            mode = "copy"

        def job(src: Path, cancelled):
            from threading import Event
            ev = Event()
            if cancelled():
                ev.set()
            out = Path(out_text) if out_text else None
            # derive source_root for mirror when preserve
            root = src.parent if preserve else None
            r = N.normalize_file(src, mode=mode, target_db=tgt, tolerance_db=tol,
                                 output_dir=out, source_root=root,
                                 preserve_structure=preserve, cancel_event=ev)
            if r.action in ("skipped_suffix", "skipped_range"):
                return "", "skipped", r.action
            if not r.success:
                return "", "failed", r.error or ""
            return str(r.output_path), "done", f"gain {r.gain_db:+.1f}dB"

        self.run_batch(files, job, self.barNorm, self.logNorm)

    # ---- runner (summary stays in the UI log panel — no sidecar files) ----
    def run_batch(self, files, job, bar, log):
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, "Busy", "Wait or Cancel current batch.")
            return
        bar.setRange(0, len(files)); bar.setValue(0)
        log.append(f"START {len(files)} files …")
        t0 = time.time()
        self.thread = BatchThread(files, job, self)
        self.thread.prog.connect(lambda i, n, s: (bar.setValue(i), log.append(f"[{i}/{n}] {Path(s).name}")))
        def fin(summary):
            log.append(f"DONE ok={summary['ok']} skip={summary['skip']} fail={summary['fail']} in {time.time()-t0:.1f}s")
            QMessageBox.information(self, "Batch done", f"ok={summary['ok']} skip={summary['skip']} fail={summary['fail']}")
        self.thread.done.connect(fin)
        self.thread.start()

    def do_cancel(self):
        if self.thread and self.thread.isRunning():
            self.thread.cancel()


def run():
    app = QApplication(sys.argv)
    qss = resource_path("styles.qss")
    if qss.exists():
        try:
            app.setStyleSheet(qss.read_text(encoding="utf-8"))
        except Exception:
            pass
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
