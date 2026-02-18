from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from mydemands.domain.models import EmailSettings
from mydemands.services.email_service import EmailService, SMTP_PASSWORD_KEY


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
        self.from_email = QLineEdit()
        self.reply_to = QLineEdit()
        self.subject = QLineEdit()
        self.body = QPlainTextEdit()

        form = QFormLayout()
        form.addRow("SMTP Host", self.smtp_host)
        form.addRow("SMTP Port", self.smtp_port)
        form.addRow("TLS", self.use_tls)
        form.addRow("SMTP Username", self.smtp_username)
        form.addRow("SMTP App Password", self.smtp_password)
        form.addRow("From Email", self.from_email)
        form.addRow("Reply-To", self.reply_to)
        form.addRow("Subject", self.subject)
        form.addRow("Body", self.body)

        save = QPushButton("Salvar")
        save.clicked.connect(self._save)
        test_send = QPushButton("Testar envio")
        test_send.clicked.connect(self._test)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(save)
        layout.addWidget(test_send)

        self._load()

    def _load(self) -> None:
        settings = self.email_service.load_settings()
        if not settings:
            return
        self.smtp_host.setText(settings.smtp_host)
        self.smtp_port.setValue(settings.smtp_port)
        self.use_tls.setChecked(settings.use_tls)
        self.smtp_username.setText(settings.smtp_username)
        self.from_email.setText(settings.from_email)
        self.reply_to.setText(settings.reply_to or "")
        self.subject.setText(settings.subject_template)
        self.body.setPlainText(settings.body_template)
        self.smtp_password.clear()

    def _validate_template(self) -> None:
        body = self.body.toPlainText()
        if "{TOKEN}" not in body:
            raise ValueError("Body deve conter {TOKEN}")
        if "spam" not in body.lower():
            raise ValueError("Body deve orientar verificação de spam")
        if not self.subject.text().strip():
            raise ValueError("Subject obrigatório")

    def _save(self):
        try:
            self._validate_template()
            settings = EmailSettings(
                smtp_host=self.smtp_host.text().strip(),
                smtp_port=self.smtp_port.value(),
                use_tls=self.use_tls.isChecked(),
                smtp_username=self.smtp_username.text().strip(),
                from_email=self.from_email.text().strip(),
                reply_to=self.reply_to.text().strip() or None,
                subject_template=self.subject.text().strip(),
                body_template=self.body.toPlainText(),
            )
            self.email_service.settings_repository.save_email_settings(settings)
            if self.smtp_password.text().strip():
                self.email_service.secret_store.set(SMTP_PASSWORD_KEY, self.smtp_password.text().encode("utf-8"))
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))

    def _test(self):
        try:
            self.email_service.send_test_email(self.master_email)
            QMessageBox.information(self, "OK", "Teste enviado")
        except Exception as exc:
            QMessageBox.warning(self, "Erro", str(exc))
