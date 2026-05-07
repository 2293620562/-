from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from livestt.core.session import StreamSession
from livestt.core.types import TranscriptEntry
from livestt.ui.add_dialog import AddDialog


@dataclass
class SessionViewState:
    session: StreamSession
    buffer: list[str]


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LiveSTT")

        self._states: Dict[int, SessionViewState] = {}
        self._current_id: Optional[int] = None

        self.list = QtWidgets.QListWidget()
        self.list.currentRowChanged.connect(self._on_select)

        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self.text.setFont(font)

        self.status = QtWidgets.QLabel("就绪")

        left = QtWidgets.QVBoxLayout()
        left.addWidget(self.list)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(self.text, 1)
        right.addWidget(self.status)

        root = QtWidgets.QHBoxLayout()
        root.addLayout(left, 1)
        root.addLayout(right, 3)

        c = QtWidgets.QWidget()
        c.setLayout(root)
        self.setCentralWidget(c)

        tb = self.addToolBar("main")
        act_add = QtGui.QAction("添加", self)
        act_remove = QtGui.QAction("删除", self)
        act_start = QtGui.QAction("开始", self)
        act_stop = QtGui.QAction("停止", self)
        act_export = QtGui.QAction("导出TXT/SRT", self)
        act_summary = QtGui.QAction("导出整理/摘要", self)

        act_add.triggered.connect(self._add)
        act_remove.triggered.connect(self._remove)
        act_start.triggered.connect(self._start)
        act_stop.triggered.connect(self._stop)
        act_export.triggered.connect(self._export)
        act_summary.triggered.connect(self._export_summary)

        tb.addAction(act_add)
        tb.addAction(act_remove)
        tb.addSeparator()
        tb.addAction(act_start)
        tb.addAction(act_stop)
        tb.addSeparator()
        tb.addAction(act_export)
        tb.addAction(act_summary)

        self.resize(1100, 700)

    def _add(self) -> None:
        ok, name, url = AddDialog.get(parent=self)
        if not ok:
            return
        if not url:
            QtWidgets.QMessageBox.warning(self, "提示", "链接不能为空")
            return
        display = name or url
        item = QtWidgets.QListWidgetItem(display)
        self.list.addItem(item)

        sess = StreamSession(name=display, url=url, parent=self)
        sess.segment_ready.connect(self._on_segment)
        sess.status_changed.connect(self._on_status)
        sess.error.connect(self._on_error)
        sess.stopped.connect(self._on_stopped)

        sid = id(sess)
        item.setData(QtCore.Qt.ItemDataRole.UserRole, sid)
        self._states[sid] = SessionViewState(session=sess, buffer=[])
        if self.list.count() == 1:
            self.list.setCurrentRow(0)

    def _remove(self) -> None:
        row = self.list.currentRow()
        if row < 0:
            return
        item = self.list.takeItem(row)
        if item is None:
            return
        sid = item.data(QtCore.Qt.ItemDataRole.UserRole)
        st = self._states.pop(sid, None)
        if st:
            st.session.stop()
        if self.list.count() == 0:
            self.text.setPlainText("")
            self.status.setText("就绪")

    def _current(self) -> Optional[SessionViewState]:
        if self._current_id is None:
            return None
        return self._states.get(self._current_id)

    def _on_select(self, row: int) -> None:
        if row < 0:
            self._current_id = None
            self.text.setPlainText("")
            return
        item = self.list.item(row)
        if not item:
            return
        sid = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self._current_id = sid
        st = self._states.get(sid)
        if not st:
            return
        self.text.setPlainText("\n".join(st.buffer))

    def _start(self) -> None:
        st = self._current()
        if not st:
            return
        st.session.start()

    def _stop(self) -> None:
        st = self._current()
        if not st:
            return
        st.session.stop()

    def _export(self) -> None:
        st = self._current()
        if not st:
            return
        base, _ = QtWidgets.QFileDialog.getSaveFileName(self, "导出SRT", "", "SRT (*.srt)")
        if not base:
            return
        p = Path(base)
        st.session.export_srt(p)
        st.session.export_txt(p.with_suffix(".txt"))
        QtWidgets.QMessageBox.information(self, "完成", f"已导出:\n{p}\n{p.with_suffix('.txt')}")

    def _export_summary(self) -> None:
        st = self._current()
        if not st:
            return
        base, _ = QtWidgets.QFileDialog.getSaveFileName(self, "导出整理/摘要", "", "TXT (*.txt)")
        if not base:
            return
        p = Path(base)
        st.session.export_summary(p)
        QtWidgets.QMessageBox.information(self, "完成", f"已导出:\n{p}")

    @QtCore.Slot(object)
    def _on_segment(self, seg: TranscriptEntry) -> None:
        sid = id(self.sender())
        st = self._states.get(sid)
        if not st:
            return
        line = f"[{seg.start_sec:8.2f}-{seg.end_sec:8.2f}] {seg.speaker}: {seg.text}"
        st.buffer.append(line)
        if self._current_id == sid:
            self.text.appendPlainText(line)

    @QtCore.Slot(str)
    def _on_status(self, s: str) -> None:
        sid = id(self.sender())
        if self._current_id == sid:
            self.status.setText(s)

    @QtCore.Slot(str)
    def _on_error(self, msg: str) -> None:
        sid = id(self.sender())
        if self._current_id == sid:
            self.status.setText("错误")
        QtWidgets.QMessageBox.critical(self, "错误", msg)

    @QtCore.Slot()
    def _on_stopped(self) -> None:
        sid = id(self.sender())
        if self._current_id == sid:
            self.status.setText("已停止")

