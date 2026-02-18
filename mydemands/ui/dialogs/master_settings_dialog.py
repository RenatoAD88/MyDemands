from __future__ import annotations

from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout

from mydemands.services.email_service import EmailService
from mydemands.services.master_password_admin_service import MasterPasswordAdminService
from mydemands.services.password_reset_service import PasswordResetService
from mydemands.ui.dialogs.passwords_registered_dialog import PasswordsRegisteredDialog
from mydemands.ui.dialogs.smtp_settings_dialog import SmtpSettingsDialog


class MasterSettingsDialog(QDialog):
    def __init__(
        self,
        email_service: EmailService,
        master_email: str,
        password_reset_service: PasswordResetService,
        admin_service: MasterPasswordAdminService,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Configurações Master")
        self.email_service = email_service
        self.master_email = master_email
        self.password_reset_service = password_reset_service
        self.admin_service = admin_service

        layout = QVBoxLayout(self)
        smtp_btn = QPushButton("Config. recuperação de senha")
        smtp_btn.clicked.connect(self._open_smtp)
        layout.addWidget(smtp_btn)

        passwords_btn = QPushButton("Senhas cadastradas")
        passwords_btn.clicked.connect(self._open_passwords_registered)
        layout.addWidget(passwords_btn)

    def _open_smtp(self):
        dialog = SmtpSettingsDialog(self.email_service, self.master_email, self)
        dialog.exec()

    def _open_passwords_registered(self):
        dialog = PasswordsRegisteredDialog(self.admin_service, self)
        dialog.exec()
