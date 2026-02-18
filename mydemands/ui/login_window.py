from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QDialog, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from mydemands.infra.repositories.last_login_repository import LastLoginRepository
from mydemands.infra.repositories.user_prefs_repository import UserPrefsRepository
from mydemands.services.auth_service import AuthService
from mydemands.services.password_reset_service import PasswordResetService
from mydemands.ui.dialogs.forgot_password_dialog import ForgotPasswordDialog
from mydemands.ui.dialogs.register_dialog import RegisterDialog
from mydemands.ui.dialogs.reset_password_dialog import ResetPasswordDialog


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QLabel { color: #1a73e8; }"
            "QLabel:hover { text-decoration: underline; }"
        )

    def mouseReleaseEvent(self, event):  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class LoginWindow(QDialog):
    def __init__(
        self,
        auth_service: AuthService,
        reset_service: PasswordResetService,
        on_login: Callable[[str], None],
        user_prefs: UserPrefsRepository,
        last_login: LastLoginRepository,
        parent=None,
    ):
        super().__init__(parent)
        self.auth_service = auth_service
        self.reset_service = reset_service
        self.on_login = on_login
        self.user_prefs = user_prefs
        self.last_login = last_login
        self.remembered_user_email: str | None = None
        self._known_email: str | None = None
        self.setWindowTitle("Login")

        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.remember_me = QCheckBox("Lembrar de mim")
        self.remember_me.toggled.connect(self._toggle_remember_me)
        self.always_require_password_on_start = QCheckBox("Sempre iniciar pedindo senha")
        self.always_require_password_on_start.setToolTip(
            "Mesmo com ‘Lembrar de mim’ ativo, eu quero digitar a senha ao abrir o aplicativo."
        )
        self.always_require_password_on_start.toggled.connect(self._toggle_always_require_password)
        self.msg = QLabel()

        enter_btn = QPushButton("Entrar")
        enter_btn.clicked.connect(self._login)
        register_btn = QPushButton("Criar sua conta")
        register_btn.clicked.connect(self._register)
        self.forgot_label = ClickableLabel("Esqueci a senha")
        self.forgot_label.clicked.connect(self._open_forgot_password)

        form = QFormLayout()
        form.addRow("E-mail", self.email)
        form.addRow("Senha", self.password)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.remember_me)
        layout.addWidget(self.always_require_password_on_start)
        layout.addWidget(enter_btn)
        layout.addWidget(register_btn)
        layout.addWidget(self.forgot_label)
        layout.addWidget(self.msg)

        self._initialize_start_mode()

    def _initialize_start_mode(self) -> None:
        last_email = self.last_login.load_last_email()
        if last_email:
            self._known_email = last_email
            self.email.setText(last_email)
            prefs = self.user_prefs.load(last_email)
            always_require = bool(prefs.get("always_require_password_on_start", False))
            self.always_require_password_on_start.setChecked(always_require)
            if always_require:
                self._set_normal_mode()
                return
        remembered = self.auth_service.try_auto_login()
        if remembered:
            self.remembered_user_email = remembered.email
            self._known_email = remembered.email
            self.email.setText(remembered.email)
            self.remember_me.setChecked(True)
            self.password.setEnabled(False)
            self.password.setPlaceholderText("••••••••")
            self.msg.setText("Sessão lembrada ativa. Clique em Entrar para continuar.")
        else:
            self._set_normal_mode()

    def _set_normal_mode(self) -> None:
        self.remembered_user_email = None
        self.password.setEnabled(True)
        self.password.setPlaceholderText("")
        self.msg.setText("")

    def _toggle_remember_me(self, checked: bool) -> None:
        if not checked:
            self.auth_service.clear_remember_session()
            self._set_normal_mode()

    def _toggle_always_require_password(self, checked: bool) -> None:
        email = self.email.text().strip().lower() or self._known_email
        if not email:
            return
        self._known_email = email
        self.user_prefs.save(email, {"always_require_password_on_start": checked})
        if checked:
            self.auth_service.clear_remember_session()
            self.remember_me.setChecked(False)
            self._set_normal_mode()

    def _login(self):
        try:
            if not self.password.isEnabled() and self.remembered_user_email:
                user = self.auth_service.try_auto_login()
                if not user:
                    raise Exception("Sessão lembrada inválida. Digite sua senha.")
            else:
                try:
                    user = self.auth_service.authenticate(self.email.text(), self.password.text())
                except Exception as exc:
                    if str(exc) == self.auth_service.EXPIRED_PROVISIONAL_MESSAGE:
                        self.reset_service.auto_resend_expired_provisional(self.email.text())
                    raise
                if user.auth_state == "requires_password_change":
                    dialog = ResetPasswordDialog(self.reset_service, user.email, self)
                    if dialog.exec() != QDialog.Accepted:
                        return
                    user = self.auth_service.authenticate(self.email.text(), dialog.final_password)
                if self.remember_me.isChecked():
                    self.auth_service.create_remember_session(user.email)
                else:
                    self.auth_service.clear_remember_session()
                self._known_email = user.email
            self.last_login.save_last_email(user.email)
            self.on_login(user.email)
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))

    def _register(self):
        dialog = RegisterDialog(self.auth_service, self)
        dialog.exec()

    def _open_forgot_password(self):
        dialog = ForgotPasswordDialog(self.reset_service, self)
        dialog.exec()
