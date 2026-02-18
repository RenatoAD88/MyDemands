from __future__ import annotations

from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout

from mydemands.services.email_service import EmailService
from mydemands.ui.dialogs.smtp_settings_dialog import SmtpSettingsDialog


class MasterSettingsDialog(QDialog):
    def __init__(self, email_service: EmailService, master_email: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações Master")
        self.email_service = email_service
        self.master_email = master_email
        layout = QVBoxLayout(self)
        btn = QPushButton("Config. recuperação de senha")
        btn.clicked.connect(self._open_smtp)
        layout.addWidget(btn)

    def _open_smtp(self):
        dialog = SmtpSettingsDialog(self.email_service, self.master_email, self)
        dialog.exec()
