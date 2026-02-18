from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox

from mydemands.domain.password_policy import PasswordPolicy
from mydemands.services.auth_service import AuthService, hash_password


class ResetPasswordDialog(QDialog):
    def __init__(self, auth_service: AuthService, email: str, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
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
            user = self.auth_service.users.get_by_email(self.email)
            if user is None:
                raise ValueError("Usuário não encontrado")
            ok, errors = PasswordPolicy.validate(self.password.text())
            if not ok:
                raise ValueError("; ".join(errors))
            if self.password.text() != self.confirm.text():
                raise ValueError("Confirmação de senha não confere")
            user.password_hash = hash_password(self.password.text())
            user.must_change_password = False
            self.auth_service.users.update(user)
            self.final_password = self.password.text()
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))
