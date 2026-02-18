from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox

from mydemands.services.password_reset_service import PasswordResetService


class ForgotPasswordDialog(QDialog):
    def __init__(self, reset_service: PasswordResetService, parent=None):
        super().__init__(parent)
        self.reset_service = reset_service
        self.setWindowTitle("Esqueci a senha")
        self.email = QLineEdit()
        self.info = QLabel()
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self._send)
        form = QFormLayout()
        form.addRow("E-mail", self.email)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.info)
        layout.addWidget(self.send_button)

    def _send(self):
        try:
            message = self.reset_service.request_password_reset(self.email.text())
            self.info.setText(message)
        except RuntimeError as exc:
            if str(exc) == "SMTP_NOT_CONFIGURED":
                QMessageBox.warning(
                    self,
                    "Configuração pendente",
                    "Recuperação por e-mail ainda não configurada. Contate o administrador.",
                )
            else:
                raise
