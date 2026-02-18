from __future__ import annotations

import re

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox

from mydemands.domain.password_policy import PasswordPolicy
from mydemands.services.password_reset_service import PasswordResetService


class ResetPasswordDialog(QDialog):
    def __init__(self, reset_service: PasswordResetService, parent=None):
        super().__init__(parent)
        self.reset_service = reset_service
        self.setWindowTitle("Redefinir senha")
        self.email = QLineEdit()
        self.token = QLineEdit()
        self.password = QLineEdit()
        self.confirm = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.confirm.setEchoMode(QLineEdit.Password)
        self.feedback = QLabel()
        form = QFormLayout()
        form.addRow("E-mail", self.email)
        form.addRow("Código", self.token)
        form.addRow("Nova senha", self.password)
        form.addRow("Confirmar", self.confirm)
        save = QPushButton("Salvar")
        save.clicked.connect(self._save)
        self.token.textChanged.connect(self._validate)
        self.password.textChanged.connect(self._validate)
        self.confirm.textChanged.connect(self._validate)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.feedback)
        layout.addWidget(save)

    def _validate(self):
        errors = []
        if self.token.text() and not re.match(r"^Prov_\d{10}$", self.token.text()):
            errors.append("Código inválido. Use formato Prov_##########")
        ok, pwd_errors = PasswordPolicy.validate(self.password.text())
        if not ok:
            errors.extend(pwd_errors)
        if self.password.text() != self.confirm.text():
            errors.append("Confirmação de senha não confere")
        self.feedback.setText("\n".join(errors) if errors else "OK")

    def _save(self):
        try:
            self.reset_service.confirm_reset(self.email.text(), self.token.text(), self.password.text())
            QMessageBox.information(self, "Sucesso", "Senha redefinida com sucesso")
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))
