from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox

from mydemands.services.password_reset_service import PasswordResetService


class ForgotPasswordDialog(QDialog):
    def __init__(self, reset_service: PasswordResetService, parent=None):
        super().__init__(parent)
        self.reset_service = reset_service
        self.setWindowTitle("Esqueci a senha")
        self.email = QLineEdit()
        self.info = QLabel()
        self.send_button = QPushButton("Enviar código")
        self.send_button.clicked.connect(self._send)
        form = QFormLayout()
        form.addRow("E-mail", self.email)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.info)
        layout.addWidget(self.send_button)

    def _send(self):
        try:
            self.reset_service.request_reset(self.email.text())
            self.info.setText("Se houver uma conta com este e-mail, enviaremos instruções. Verifique a caixa de spam.")
            self.send_button.setEnabled(False)
            QTimer.singleShot(30000, lambda: self.send_button.setEnabled(True))
        except RuntimeError as exc:
            if str(exc) == "SMTP_NOT_CONFIGURED":
                QMessageBox.warning(self, "Configuração pendente", "SMTP não configurado.")
            else:
                raise
