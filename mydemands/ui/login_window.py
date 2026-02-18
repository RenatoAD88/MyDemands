from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QCheckBox, QDialog, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from mydemands.services.auth_service import AuthService
from mydemands.services.password_reset_service import PasswordResetService
from mydemands.ui.dialogs.forgot_password_dialog import ForgotPasswordDialog
from mydemands.ui.dialogs.register_dialog import RegisterDialog


class LoginWindow(QDialog):
    def __init__(self, auth_service: AuthService, reset_service: PasswordResetService, on_login: Callable[[str], None], parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.reset_service = reset_service
        self.on_login = on_login
        self.setWindowTitle("Login")

        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.remember_me = QCheckBox("Lembrar de mim")
        self.msg = QLabel()

        enter_btn = QPushButton("Entrar")
        enter_btn.clicked.connect(self._login)
        register_btn = QPushButton("Criar sua conta")
        register_btn.clicked.connect(self._register)
        forgot_btn = QPushButton("Esqueci a senha")
        forgot_btn.clicked.connect(self._forgot)

        form = QFormLayout()
        form.addRow("E-mail", self.email)
        form.addRow("Senha", self.password)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.remember_me)
        layout.addWidget(enter_btn)
        layout.addWidget(register_btn)
        layout.addWidget(forgot_btn)
        layout.addWidget(self.msg)

    def _login(self):
        try:
            user = self.auth_service.authenticate(self.email.text(), self.password.text())
            if self.remember_me.isChecked():
                self.auth_service.create_remember_session(user.email)
            self.on_login(user.email)
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))

    def _register(self):
        dialog = RegisterDialog(self.auth_service, self)
        dialog.exec()

    def _forgot(self):
        dialog = ForgotPasswordDialog(self.reset_service, self)
        dialog.exec()
