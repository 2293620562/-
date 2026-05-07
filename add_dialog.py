from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class AddDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加连接")

        self.name_edit = QtWidgets.QLineEdit()
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("支持：RTMP/M3U8/网页分享链接（抖音/快手/B站等）")

        form = QtWidgets.QFormLayout()
        form.addRow("名称", self.name_edit)
        form.addRow("链接", self.url_edit)

        self.btn_ok = QtWidgets.QPushButton("确定")
        self.btn_cancel = QtWidgets.QPushButton("取消")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)

        root = QtWidgets.QVBoxLayout()
        root.addLayout(form)
        root.addLayout(btns)
        self.setLayout(root)
        self.resize(560, 140)

    def values(self) -> tuple[str, str]:
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        return name, url

    @staticmethod
    def get(parent=None) -> tuple[bool, str, str]:
        d = AddDialog(parent=parent)
        ok = d.exec() == QtWidgets.QDialog.Accepted
        name, url = d.values()
        return ok, name, url
