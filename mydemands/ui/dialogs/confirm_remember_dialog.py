from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout


class ConfirmRememberDialog(QDialog):
    def __init__(self, email: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirmar entrada")
        self._choice: str | None = None

        label = QLabel(f"Continuar como {email}?")
        continue_btn = QPushButton("Continuar")
        switch_btn = QPushButton("Trocar conta")
        continue_btn.setDefault(True)

        continue_btn.clicked.connect(self._continue)
        switch_btn.clicked.connect(self._switch)

        row = QHBoxLayout()
        row.addWidget(continue_btn)
        row.addWidget(switch_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addLayout(row)

        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

    @property
    def choice(self) -> str | None:
        return self._choice

    def _continue(self) -> None:
        self._choice = "continue"
        self.accept()

    def _switch(self) -> None:
        self._choice = "switch"
        self.reject()

    def reject(self) -> None:
        if self._choice is None:
            self._choice = "switch"
        super().reject()
