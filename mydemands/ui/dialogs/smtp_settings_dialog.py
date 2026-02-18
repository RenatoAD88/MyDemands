from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from mydemands.domain.models import EmailSettings
from mydemands.services.email_service import (
    DEFAULT_RECOVERY_BODY,
    DEFAULT_RECOVERY_SUBJECT,
    EmailService,
)

DEFAULT_SUBJECT = DEFAULT_RECOVERY_SUBJECT
DEFAULT_BODY = DEFAULT_RECOVERY_BODY


class SmtpSettingsDialog(QDialog):
    def __init__(self, email_service: EmailService, master_email: str, parent=None):
        super().__init__(parent)
        self.email_service = email_service
        self.master_email = master_email
        self.setWindowTitle("Configuração SMTP")

        self.smtp_host = QLineEdit()
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        self.use_tls = QCheckBox("TLS/STARTTLS")
        self.use_tls.setChecked(True)
        self.smtp_username = QLineEdit()
        self.smtp_password = QLineEdit()
        self.smtp_password.setEchoMode(QLineEdit.Password)
        self.smtp_password_status = QLabel("")
        self.from_email = QLineEdit()
        self.reply_to = QLineEdit()
        self.subject = QLineEdit()
        self.body = QPlainTextEdit()

        password_row = QHBoxLayout()
        password_row.addWidget(self.smtp_password)
        password_row.addWidget(self.smtp_password_status)

        placeholders_row = QHBoxLayout()
        insert_password = QPushButton("Inserir {PASSWORD}")
        insert_password.clicked.connect(lambda: self._insert_placeholder("{PASSWORD}"))
        insert_minutes = QPushButton("Inserir {MINUTOS}")
        insert_minutes.clicked.connect(lambda: self._insert_placeholder("{MINUTOS}"))
        placeholders_row.addWidget(insert_password)
        placeholders_row.addWidget(insert_minutes)
        placeholders_row.addStretch(1)

        body_layout = QVBoxLayout()
        body_layout.addWidget(self.body)
        body_layout.addLayout(placeholders_row)

        form = QFormLayout()
        form.addRow("SMTP Host", self.smtp_host)
        form.addRow("SMTP Port", self.smtp_port)
        form.addRow("TLS", self.use_tls)
        form.addRow("SMTP Username", self.smtp_username)
        form.addRow("SMTP App Password", password_row)
        form.addRow("From Email", self.from_email)
        form.addRow("Reply-To", self.reply_to)
        form.addRow("Subject", self.subject)
        form.addRow("Body", body_layout)

        save = QPushButton("Salvar")
        save.clicked.connect(self._save)
        test_send = QPushButton("Testar envio")
        test_send.clicked.connect(self._test)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(save)
        layout.addWidget(test_send)

        self._load()

    def _insert_placeholder(self, placeholder: str) -> None:
        cursor = self.body.textCursor()
        cursor.insertText(placeholder)

    def _load(self) -> None:
        settings = self.email_service.load_settings()
        if settings:
            self.smtp_host.setText(settings.smtp_host)
            self.smtp_port.setValue(settings.smtp_port)
            self.use_tls.setChecked(settings.use_tls)
            self.smtp_username.setText(settings.smtp_username)
            self.from_email.setText(settings.from_email)
            self.reply_to.setText(settings.reply_to or "")
            self.subject.setText(settings.subject_template or DEFAULT_SUBJECT)
            migrated_body = self.email_service.migrate_legacy_recovery_template(settings.body_template)
            self.body.setPlainText(migrated_body)
        else:
            self.subject.setText(DEFAULT_SUBJECT)
            self.body.setPlainText(DEFAULT_BODY)
        self.smtp_password.clear()
        self.smtp_password_status.setText("Senha configurada" if self.email_service.get_smtp_password() else "")

    def _prompt_legacy_template_migration(self) -> bool:
        message = (
            "Seu template está usando {TOKEN} (modelo antigo). "
            "Vamos atualizar para {PASSWORD}. Deseja corrigir automaticamente?"
        )
        response = QMessageBox.question(
            self,
            "Template legado detectado",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if response == QMessageBox.Yes:
            self.body.setPlainText(self.email_service.migrate_legacy_recovery_template(self.body.toPlainText()))
            return True
        return False

    def _validate_template(self) -> None:
        body = self.body.toPlainText()
        if "{TOKEN}" in body and "{PASSWORD}" not in body:
            if not self._prompt_legacy_template_migration():
                raise ValueError("Salvamento cancelado para manter o template atual.")
            body = self.body.toPlainText()
        try:
            self.email_service.validate_recovery_template(body)
        except ValueError as exc:
            if str(exc) == "TOKEN_LEGACY_PLACEHOLDER":
                if not self._prompt_legacy_template_migration():
                    raise ValueError("Salvamento cancelado para manter o template atual.") from exc
                self.email_service.validate_recovery_template(self.body.toPlainText())
            elif str(exc) == "Body deve conter {PASSWORD}":
                raise ValueError("Body precisa conter {PASSWORD}. Clique em ‘Inserir placeholder’ para adicionar automaticamente.") from exc
            else:
                raise
        if not self.subject.text().strip():
            raise ValueError("Subject obrigatório")

    def _settings_from_ui(self) -> EmailSettings:
        return EmailSettings(
            smtp_host=self.smtp_host.text().strip(),
            smtp_port=self.smtp_port.value(),
            use_tls=self.use_tls.isChecked(),
            smtp_username=self.smtp_username.text().strip(),
            from_email=self.from_email.text().strip(),
            reply_to=self.reply_to.text().strip() or None,
            subject_template=self.subject.text().strip(),
            body_template=self.body.toPlainText(),
        )

    def _save(self):
        try:
            self._validate_template()
            settings = self._settings_from_ui()
            new_password = self.smtp_password.text().strip()
            self.email_service.save_smtp_settings(settings, smtp_password=new_password or None)
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))

    def _test(self):
        try:
            self._validate_template()
            settings = self._settings_from_ui()
            password_field_value = self.smtp_password.text().strip()
            smtp_password = password_field_value or self.email_service.get_smtp_password_for_send()
            self.email_service.send_test_email(
                self.master_email,
                settings_override=settings,
                smtp_password_override=smtp_password,
            )
            QMessageBox.information(self, "OK", "Teste enviado")
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))
