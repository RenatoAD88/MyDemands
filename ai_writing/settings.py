from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Dict

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ai_writing.config_store import AIConfig, AIConfigStore, OPENAI_PROVIDER
from ai_writing.errors import AIRequestTimeoutError, AIWritingError, MissingAPIKeyError, ModelNotFoundError, RateLimitError
from ai_writing.openai_client import OpenAIClient
from ui_prefs import load_prefs, save_prefs


@dataclass
class AISettings:
    enabled: bool = False
    show_chips: bool = True
    provider: str = OPENAI_PROVIDER
    model: str = "gpt-4o-mini"
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
        merged["provider"] = OPENAI_PROVIDER
        return AISettings(**merged)

    def save(self, settings: AISettings) -> None:
        payload = asdict(settings)
        payload["provider"] = OPENAI_PROVIDER
        prefs = load_prefs(self.base_dir)
        prefs[self.KEY] = payload
        save_prefs(self.base_dir, prefs)


class AIConsumptionDialog(QDialog):
    def __init__(self, cfg: AIConfig, model_name: str, parent=None):
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
        form.addRow("Provedor", QLabel("OPENIA"))
        form.addRow("Uso atual", QLabel(f"{cfg.ia_usage_count} / {cfg.ia_usage_limit}"))
        form.addRow("Percentual utilizado", QLabel(f"{usage_pct}%"))
        form.addRow("Data do último reset", QLabel(cfg.ia_last_reset))
        form.addRow("Próxima data de reset", QLabel(cfg.next_reset_date.strftime("%Y-%m-%d")))
        form.addRow("Modelo em uso", QLabel(model_name))
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
        self.setWindowTitle("Configurações da OPENIA ✨")
        self._settings = self.store.load()

        self.enabled = QCheckBox("Habilitar Redigir com IA")
        self.enabled.setChecked(self._settings.enabled)

        self.provider = QLabel("OPENIA")

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Normal)
        self.api_key_input.setPlaceholderText("Cole aqui sua chave da OpenAI")

        self.model = QLineEdit()
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)

        self.max_new_tokens = QSpinBox()
        self.max_new_tokens.setRange(1, 4096)

        self.monthly_limit = QSpinBox()
        self.monthly_limit.setRange(1, 100000)

        self.cache_enabled = QCheckBox("Ativar cache")
        self.usage_label = QLabel()

        test_btn = QPushButton("Testar conexão")
        test_btn.clicked.connect(self._test_connection)
        consumo_btn = QPushButton("Consumo de IA")
        consumo_btn.clicked.connect(self._open_consumption_dialog)

        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

        self.form = QFormLayout()
        self.form.addRow("Provedor", self.provider)
        self.form.addRow("Chave OpenAI", self.api_key_input)
        self.form.addRow("Modelo", self.model)
        self.form.addRow("Temperatura", self.temperature)
        self.form.addRow("Máx Tokens", self.max_new_tokens)
        self.form.addRow("Limite mensal", self.monthly_limit)
        self.form.addRow("", self.cache_enabled)
        self.form.addRow("", self.usage_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(consumo_btn)
        buttons.addWidget(test_btn)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.enabled)
        layout.addLayout(self.form)
        layout.addLayout(buttons)

        self._sync_fields()

    def _sync_fields(self):
        cfg = self.config_store.load_config(provider=OPENAI_PROVIDER)
        self.api_key_input.setText(cfg.openai_api_key)
        self.model.setText(cfg.openai_model)
        self.temperature.setValue(float(cfg.temperature))
        self.max_new_tokens.setValue(int(cfg.max_new_tokens))
        self.monthly_limit.setValue(int(cfg.ia_usage_limit))
        self.cache_enabled.setChecked(cfg.ia_cache_enabled)
        self.usage_label.setText(f"Uso atual: {cfg.ia_usage_count} / {cfg.ia_usage_limit}")

    def _open_consumption_dialog(self):
        cfg = self.config_store.reset_usage_if_needed(self.config_store.load_config(provider=OPENAI_PROVIDER), provider=OPENAI_PROVIDER)
        AIConsumptionDialog(cfg, cfg.openai_model, self).exec()

    def _test_connection(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "IA", "Chave da OpenAI não configurada")
            return
        try:
            client = OpenAIClient(
                api_key=api_key,
                model=self.model.text().strip(),
                temperature=float(self.temperature.value()),
                max_new_tokens=int(self.max_new_tokens.value()),
            )
            client.check_connectivity()
            QMessageBox.information(self, "IA", "Conexão OK")
        except MissingAPIKeyError:
            QMessageBox.warning(self, "IA", "Chave da OpenAI inválida ou ausente")
        except ModelNotFoundError:
            QMessageBox.warning(self, "IA", "Modelo da OpenAI inválido ou indisponível")
        except RateLimitError:
            QMessageBox.warning(self, "IA", "Limite de requisições da OpenAI atingido")
        except AIRequestTimeoutError:
            QMessageBox.warning(self, "IA", "Tempo de resposta da OpenAI excedido")
        except AIWritingError as exc:
            QMessageBox.warning(self, "IA", f"Falha ao testar conexão: {exc}")
        except Exception as exc:
            QMessageBox.warning(self, "IA", f"Falha inesperada ao testar conexão: {exc}")

    def _save(self):
        settings = AISettings(
            enabled=self.enabled.isChecked(),
            show_chips=self._settings.show_chips,
            provider=OPENAI_PROVIDER,
            model=self.model.text().strip() or AISettings.model,
            temperature=float(self.temperature.value()),
            privacy_mode=self._settings.privacy_mode,
            debug_log_text=self._settings.debug_log_text,
        )
        self.store.save(settings)

        cfg = self.config_store.load_config(provider=OPENAI_PROVIDER)
        cfg.openai_api_key = self.api_key_input.text().strip()
        cfg.openai_model = self.model.text().strip() or cfg.openai_model
        cfg.temperature = float(self.temperature.value())
        cfg.max_new_tokens = int(self.max_new_tokens.value())
        cfg.ia_usage_limit = int(self.monthly_limit.value())
        cfg.ia_cache_enabled = self.cache_enabled.isChecked()
        if cfg.ia_last_reset == "":
            cfg.ia_last_reset = date.today().strftime("%Y-%m-%d")
        self.config_store.save_config(cfg, provider=OPENAI_PROVIDER)
        self.accept()
