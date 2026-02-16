from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Any, Dict

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QDoubleSpinBox,
    QSpinBox,
    QProgressBar,
)

from ui_prefs import load_prefs, save_prefs
from ai_writing.config_store import AIConfig, AIConfigStore
from ai_writing.huggingface_client import (
    HuggingFaceClient,
    MissingAPIKeyError,
    ModelNotFoundError,
    RateLimitError,
)


@dataclass
class AISettings:
    enabled: bool = True
    show_chips: bool = True
    model: str = "google/flan-t5-base"
    temperature: float = 0.5
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


class AIConsumptionDialog(QDialog):
    def __init__(self, cfg: AIConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Consumo de IA")

        usage_pct = min(100, int((cfg.ia_usage_count / max(1, cfg.ia_usage_limit)) * 100))
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(usage_pct)

        color = "#2e7d32"
        if cfg.ia_usage_count >= cfg.ia_usage_limit:
            color = "#c62828"
        elif usage_pct > 80:
            color = "#f9a825"
        progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

        form = QFormLayout()
        form.addRow("Uso atual", QLabel(f"{cfg.ia_usage_count} / {cfg.ia_usage_limit}"))
        form.addRow("Percentual utilizado", QLabel(f"{usage_pct}%"))
        form.addRow("Data do último reset", QLabel(cfg.ia_last_reset))
        form.addRow("Próxima data de reset", QLabel(cfg.next_reset_date.strftime("%Y-%m-%d")))
        form.addRow("Modelo em uso", QLabel(cfg.hf_model))
        form.addRow("Cache ativo", QLabel("Sim" if cfg.ia_cache_enabled else "Não"))
        form.addRow("Progresso", progress)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(close_btn)


class AISettingsDialog(QDialog):
    def __init__(self, store: AISettingsStore, parent=None):
        super().__init__(parent)
        self.store = store
        self.config_store = AIConfigStore()
        self.setWindowTitle("Configurações da IA ✨")
        self._settings = self.store.load()
        self._config = self.config_store.load_config()

        self.enabled = QCheckBox("Habilitar Redigir com IA")
        self.enabled.setChecked(self._settings.enabled)

        self.model = QLineEdit(self._config.hf_model)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(float(self._config.temperature))

        self.max_new_tokens = QSpinBox()
        self.max_new_tokens.setRange(1, 4096)
        self.max_new_tokens.setValue(int(self._config.max_new_tokens))

        self.monthly_limit = QSpinBox()
        self.monthly_limit.setRange(1, 100000)
        self.monthly_limit.setValue(int(self._config.ia_usage_limit))

        self.cache_enabled = QCheckBox("Ativar cache")
        self.cache_enabled.setChecked(self._config.ia_cache_enabled)

        self.api_key_input = QLineEdit(self._config.hf_api_token)
        self.api_key_input.setPlaceholderText("Cole aqui seu token do Hugging Face")
        self.api_key_input.setEchoMode(QLineEdit.Normal)

        self.usage_label = QLabel(f"Uso atual: {self._config.ia_usage_count} / {self._config.ia_usage_limit}")

        test_btn = QPushButton("Testar conexão")
        test_btn.clicked.connect(self._test_connection)
        consumo_btn = QPushButton("Consumo de IA")
        consumo_btn.clicked.connect(self._open_consumption_dialog)

        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

        form = QFormLayout()
        form.addRow("Token Hugging Face", self.api_key_input)
        form.addRow("Modelo", self.model)
        form.addRow("Temperatura", self.temperature)
        form.addRow("Máx Tokens", self.max_new_tokens)
        form.addRow("Limite mensal", self.monthly_limit)
        form.addRow("", self.cache_enabled)
        form.addRow("", self.usage_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(consumo_btn)
        buttons.addWidget(test_btn)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.enabled)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def _open_consumption_dialog(self):
        cfg = self.config_store.reset_usage_if_needed(self.config_store.load_config())
        AIConsumptionDialog(cfg, self).exec()

    def _test_connection(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "IA", "Token do Hugging Face não configurado")
            return
        try:
            client = HuggingFaceClient(
                api_token=api_key,
                model=self.model.text().strip(),
                temperature=float(self.temperature.value()),
                max_new_tokens=int(self.max_new_tokens.value()),
            )
            client.check_connectivity()
            try:
                client.suggest("Teste", "Responda apenas OK.", {"field": "connection_test"})
            except ModelNotFoundError:
                QMessageBox.warning(
                    self,
                    "IA",
                    "Conectividade com Hugging Face OK, mas o modelo informado é inválido ou indisponível. Atualize o campo Modelo.",
                )
                return
            QMessageBox.information(self, "IA", "Conexão OK")
        except MissingAPIKeyError:
            QMessageBox.warning(self, "IA", "Token do Hugging Face inválido ou ausente")
        except RateLimitError:
            QMessageBox.warning(self, "IA", "Limite de requisições atingido. Tente novamente em instantes.")
        except Exception as exc:
            QMessageBox.warning(self, "IA", f"Falha ao testar conexão: {exc}")

    def _save(self):
        settings = AISettings(
            enabled=self.enabled.isChecked(),
            show_chips=self._settings.show_chips,
            model=self.model.text().strip() or AISettings.model,
            temperature=float(self.temperature.value()),
            privacy_mode=self._settings.privacy_mode,
            debug_log_text=self._settings.debug_log_text,
        )
        self.store.save(settings)

        cfg = self.config_store.load_config()
        cfg.hf_api_token = self.api_key_input.text().strip()
        cfg.hf_model = self.model.text().strip() or cfg.hf_model
        cfg.temperature = float(self.temperature.value())
        cfg.max_new_tokens = int(self.max_new_tokens.value())
        cfg.ia_usage_limit = int(self.monthly_limit.value())
        cfg.ia_cache_enabled = self.cache_enabled.isChecked()
        if cfg.ia_last_reset == "":
            cfg.ia_last_reset = date.today().strftime("%Y-%m-%d")
        self.config_store.save_config(cfg)
        self.accept()
