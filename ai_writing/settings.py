from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QDoubleSpinBox,
)

from ui_prefs import load_prefs, save_prefs
from ai_writing.openai_client import OpenAIWritingClient


@dataclass
class AISettings:
    enabled: bool = True
    show_chips: bool = True
    model: str = "gpt-5.2"
    temperature: float = 0.3
    log_channel: str = "sqlite"
    privacy_mode: bool = True
    debug_log_text: bool = False


class AISettingsStore:
    KEY = "ai_writing"

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def load(self) -> AISettings:
        prefs = load_prefs(self.base_dir)
        data = prefs.get(self.KEY, {}) if isinstance(prefs, dict) else {}
        if not isinstance(data, dict):
            return AISettings()
        merged: Dict[str, Any] = asdict(AISettings())
        merged.update({k: v for k, v in data.items() if k in merged})
        return AISettings(**merged)

    def save(self, settings: AISettings) -> None:
        prefs = load_prefs(self.base_dir)
        prefs[self.KEY] = asdict(settings)
        save_prefs(self.base_dir, prefs)


class AISettingsDialog(QDialog):
    def __init__(self, store: AISettingsStore, parent=None):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Configurações da IA ✨")
        self._settings = self.store.load()

        self.enabled = QCheckBox("Habilitar Redigir com IA")
        self.enabled.setChecked(self._settings.enabled)

        self.show_chips = QCheckBox("Mostrar chips de ação")
        self.show_chips.setChecked(self._settings.show_chips)

        self.privacy_mode = QCheckBox("Modo privacidade (não registrar texto completo)")
        self.privacy_mode.setChecked(self._settings.privacy_mode)

        self.debug_log_text = QCheckBox("Modo debug de auditoria (registrar texto)")
        self.debug_log_text.setChecked(self._settings.debug_log_text)

        self.model = QComboBox()
        self.model.addItems(["gpt-5.2", "gpt-4.1-mini"])
        self.model.setCurrentText(self._settings.model)

        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(float(self._settings.temperature))

        self.key_status = QLabel(self._key_status_text())

        test_btn = QPushButton("Testar conexão")
        test_btn.clicked.connect(self._test_connection)

        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

        form = QFormLayout()
        form.addRow("Status da chave", self.key_status)
        form.addRow("Modelo", self.model)
        form.addRow("Temperatura", self.temperature)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(test_btn)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.enabled)
        layout.addWidget(self.show_chips)
        layout.addWidget(self.privacy_mode)
        layout.addWidget(self.debug_log_text)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def _key_status_text(self) -> str:
        return "Detectada" if os.getenv("OPENAI_API_KEY") else "Não detectada"

    def _test_connection(self):
        if not os.getenv("OPENAI_API_KEY"):
            QMessageBox.warning(self, "IA", "Chave não configurada")
            return
        try:
            client = OpenAIWritingClient(model=self.model.currentText(), temperature=float(self.temperature.value()), max_retries=2)
            client.suggest("teste", "Responda com a palavra OK em pt-BR.", {"field": "connection_test"})
            QMessageBox.information(self, "IA", "Conexão OK")
        except Exception as exc:
            QMessageBox.warning(self, "IA", f"Falha ao testar conexão: {exc}")

    def _save(self):
        settings = AISettings(
            enabled=self.enabled.isChecked(),
            show_chips=self.show_chips.isChecked(),
            model=self.model.currentText(),
            temperature=float(self.temperature.value()),
            privacy_mode=self.privacy_mode.isChecked(),
            debug_log_text=self.debug_log_text.isChecked(),
        )
        self.store.save(settings)
        self.accept()
