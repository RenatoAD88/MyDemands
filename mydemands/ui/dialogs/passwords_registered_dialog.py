from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from mydemands.services.master_password_admin_service import MasterPasswordAdminService


class PasswordsRegisteredDialog(QDialog):
    def __init__(self, admin_service: MasterPasswordAdminService, parent=None):
        super().__init__(parent)
        self.admin_service = admin_service
        self.setWindowTitle("Senhas cadastradas")

        self.feedback = QLabel("")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["E-mail", "Perfil", "Ação"])

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addWidget(self.feedback)

        self._load_users()

    def _load_users(self) -> None:
        users = self.admin_service.list_users()
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(user.email))
            self.table.setItem(row, 1, QTableWidgetItem(user.role))
            action = QPushButton("Enviar nova senha")
            action.clicked.connect(lambda _=False, email=user.email: self._send_new_password(email))
            self.table.setCellWidget(row, 2, action)

    def _send_new_password(self, email: str) -> None:
        try:
            message = self.admin_service.send_new_password(email)
            self.feedback.setText(f"{email}: {message}")
        except RuntimeError as exc:
            code = str(exc)
            if code == "SMTP_NOT_CONFIGURED":
                self.feedback.setText("SMTP não configurado")
            elif code == "RATE_LIMIT":
                self.feedback.setText(f"{email}: limite de 5 solicitações por hora")
            else:
                self.feedback.setText(f"{email}: erro ao enviar nova senha")
