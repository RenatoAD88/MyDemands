from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox

from mydemands.domain.password_policy import PasswordPolicy
from mydemands.services.password_reset_service import PasswordResetService


class ResetPasswordDialog(QDialog):
    def __init__(self, reset_service: PasswordResetService, email: str, parent=None):
        super().__init__(parent)
        self.reset_service = reset_service
        self.email = email.strip().lower()
        self.final_password = ""
        self.setWindowTitle("Confirmar nova senha / Definir senha final")

        self.password = QLineEdit()
        self.confirm = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.confirm.setEchoMode(QLineEdit.Password)
        self.feedback = QLabel()

        form = QFormLayout()
        form.addRow("Nova senha", self.password)
        form.addRow("Confirmar nova senha", self.confirm)

        self.save_btn = QPushButton("Salvar")
        self.save_btn.clicked.connect(self._save)

        self.password.textChanged.connect(self._validate)
        self.confirm.textChanged.connect(self._validate)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.feedback)
        layout.addWidget(self.save_btn)
        self._validate()

    def _validate(self):
        ok, pwd_errors = PasswordPolicy.validate(self.password.text())
        errors = list(pwd_errors if not ok else [])
        if self.password.text() != self.confirm.text():
            errors.append("Confirmação de senha não confere")
        self.feedback.setText("\n".join(errors) if errors else "OK")
        self.save_btn.setEnabled(not errors)

    def _save(self):
        try:
            if self.password.text() != self.confirm.text():
                raise ValueError("Confirmação de senha não confere")
            self.reset_service.save_final_password(self.email, self.password.text())
            self.final_password = self.password.text()
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))
