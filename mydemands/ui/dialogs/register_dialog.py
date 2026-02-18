from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox

from mydemands.domain.password_policy import PasswordPolicy
from mydemands.services.auth_service import AuthService


class RegisterDialog(QDialog):
    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.setWindowTitle("Criar conta")
        self.email = QLineEdit()
        self.password = QLineEdit()
        self.confirm = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.confirm.setEchoMode(QLineEdit.Password)
        self.feedback = QLabel()
        form = QFormLayout()
        form.addRow("E-mail", self.email)
        form.addRow("Senha", self.password)
        form.addRow("Confirmar", self.confirm)
        save = QPushButton("Salvar")
        save.clicked.connect(self._on_save)
        self.password.textChanged.connect(self._validate)
        self.confirm.textChanged.connect(self._validate)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.feedback)
        layout.addWidget(save)

    def _validate(self):
        ok, errors = PasswordPolicy.validate(self.password.text())
        if self.password.text() != self.confirm.text():
            errors.append("Confirmação de senha não confere.")
            ok = False
        self.feedback.setText("\n".join(errors) if not ok else "Senha válida.")

    def _on_save(self):
        self._validate()
        if self.password.text() != self.confirm.text():
            QMessageBox.warning(self, "Erro", "Confirmação de senha inválida")
            return
        ok, errors = PasswordPolicy.validate(self.password.text())
        if not ok:
            QMessageBox.warning(self, "Erro", "\n".join(errors))
            return
        self.auth_service.register(self.email.text(), self.password.text())
        self.accept()
