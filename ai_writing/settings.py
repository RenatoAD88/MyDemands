from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Dict

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
    QWidget,
)

from ai_writing.config_store import AIConfig, AIConfigStore, DEFAULT_HF_MODEL, HUGGINGFACE_PROVIDER, OPENAI_PROVIDER
from ai_writing.errors import AIRequestTimeoutError, AIWritingError, MissingAPIKeyError, ModelNotFoundError, RateLimitError
from ai_writing.provider_factory import AIProviderFactory
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
        merged: Dict[str, Any] = asdict(AISettings())
        if isinstance(data, dict):
            merged.update({k: v for k, v in data.items() if k in merged})
        cfg = AIConfigStore().load_config()
        merged["enabled"] = cfg.ai_enabled
        merged["provider"] = cfg.ai_provider
        merged["model"] = cfg.openai_model if cfg.ai_provider == OPENAI_PROVIDER else cfg.hf_model
        merged["temperature"] = cfg.openai_temperature if cfg.ai_provider == OPENAI_PROVIDER else cfg.hf_temperature
        return AISettings(**merged)

    def save(self, settings: AISettings) -> None:
        payload = asdict(settings)
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
        form.addRow("Provedor", QLabel(cfg.ai_provider.upper()))
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
        self.setWindowTitle("Configuração de IA ✨")
        self._settings = self.store.load()

        self.enabled = QCheckBox("Habilitar IA")

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("OpenAI", OPENAI_PROVIDER)
        self.provider_combo.addItem("Hugging Face", HUGGINGFACE_PROVIDER)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)

        self.openai_key = QLineEdit()
        self.openai_model = QLineEdit()
        self.openai_temperature = QDoubleSpinBox(); self.openai_temperature.setRange(0.0, 2.0); self.openai_temperature.setSingleStep(0.1)
        self.openai_max_tokens = QSpinBox(); self.openai_max_tokens.setRange(1, 8192)

        self.hf_token = QLineEdit()
        self.hf_model = QLineEdit()
        self.hf_temperature = QDoubleSpinBox(); self.hf_temperature.setRange(0.0, 2.0); self.hf_temperature.setSingleStep(0.1)
        self.hf_max_tokens = QSpinBox(); self.hf_max_tokens.setRange(1, 8192)
        self.hf_top_p = QDoubleSpinBox(); self.hf_top_p.setRange(0.0, 1.0); self.hf_top_p.setSingleStep(0.1)

        self.monthly_limit = QSpinBox(); self.monthly_limit.setRange(1, 100000)
        self.cache_enabled = QCheckBox("IA_CACHE_ENABLED")
        self.usage_label = QLabel()

        self.openai_widget = self._build_openai_form()
        self.hf_widget = self._build_hf_form()

        test_btn = QPushButton("Testar conexão")
        test_btn.clicked.connect(self._test_connection)
        consumo_btn = QPushButton("Consumo de IA")
        consumo_btn.clicked.connect(self._open_consumption_dialog)
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

        form = QFormLayout()
        form.addRow("Provedor de IA", self.provider_combo)
        form.addRow("", self.openai_widget)
        form.addRow("", self.hf_widget)
        form.addRow("Limite mensal", self.monthly_limit)
        form.addRow("", self.cache_enabled)
        form.addRow("", self.usage_label)

        buttons = QHBoxLayout()
        buttons.addStretch(); buttons.addWidget(consumo_btn); buttons.addWidget(test_btn); buttons.addWidget(save_btn); buttons.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.enabled)
        layout.addLayout(form)
        layout.addLayout(buttons)

        self._sync_fields()

    def _build_openai_form(self) -> QWidget:
        widget = QWidget()
        f = QFormLayout(widget)
        f.addRow("OPENAI_API_KEY", self.openai_key)
        f.addRow("OPENAI_MODEL", self.openai_model)
        f.addRow("temperature", self.openai_temperature)
        f.addRow("max_output_tokens", self.openai_max_tokens)
        return widget

    def _build_hf_form(self) -> QWidget:
        widget = QWidget()
        f = QFormLayout(widget)
        f.addRow("HF_API_TOKEN", self.hf_token)
        f.addRow("HF_MODEL", self.hf_model)
        f.addRow("temperature", self.hf_temperature)
        f.addRow("max_new_tokens", self.hf_max_tokens)
        f.addRow("top_p (opcional)", self.hf_top_p)
        return widget

    def _provider(self) -> str:
        return str(self.provider_combo.currentData() or OPENAI_PROVIDER)

    def _toggle_provider_fields(self):
        is_openai = self._provider() == OPENAI_PROVIDER
        self.openai_widget.setVisible(is_openai)
        self.hf_widget.setVisible(not is_openai)

    def _ensure_hf_default_model(self) -> None:
        if self._provider() == HUGGINGFACE_PROVIDER and not self.hf_model.text().strip():
            self.hf_model.setText(DEFAULT_HF_MODEL)

    def _on_provider_changed(self):
        self._toggle_provider_fields()
        self._ensure_hf_default_model()

    def _sync_fields(self):
        cfg = self.config_store.load_config()
        self.enabled.setChecked(cfg.ai_enabled)
        self.provider_combo.setCurrentIndex(0 if cfg.ai_provider == OPENAI_PROVIDER else 1)

        self.openai_key.setText(cfg.openai_api_key)
        self.openai_model.setText(cfg.openai_model)
        self.openai_temperature.setValue(float(cfg.openai_temperature))
        self.openai_max_tokens.setValue(int(cfg.openai_max_output_tokens))

        self.hf_token.setText(cfg.hf_api_token)
        self.hf_model.setText(cfg.hf_model or DEFAULT_HF_MODEL)
        self.hf_temperature.setValue(float(cfg.hf_temperature))
        self.hf_max_tokens.setValue(int(cfg.hf_max_new_tokens))
        self.hf_top_p.setValue(float(cfg.hf_top_p))

        self.monthly_limit.setValue(int(cfg.ia_usage_limit))
        self.cache_enabled.setChecked(cfg.ia_cache_enabled)
        self.usage_label.setText(f"Uso atual: {cfg.ia_usage_count} / {cfg.ia_usage_limit}")
        self._toggle_provider_fields()
        self._ensure_hf_default_model()

    def _open_consumption_dialog(self):
        cfg = self.config_store.reset_usage_if_needed(self.config_store.load_config())
        model = cfg.openai_model if cfg.ai_provider == OPENAI_PROVIDER else cfg.hf_model
        AIConsumptionDialog(cfg, model, self).exec()

    def _test_connection(self):
        provider = self._provider()
        cfg = self._build_config_from_form()
        try:
            AIProviderFactory.create(provider, cfg).check_connectivity()
            QMessageBox.information(self, "IA", "Conexão OK")
        except MissingAPIKeyError:
            msg = "Chave/token ausente ou inválido"
            QMessageBox.warning(self, "IA", msg)
        except ModelNotFoundError:
            QMessageBox.warning(self, "IA", "Modelo inválido")
        except RateLimitError:
            QMessageBox.warning(self, "IA", "Cota/limite atingido")
        except AIRequestTimeoutError:
            QMessageBox.warning(self, "IA", "Timeout/rede")
        except AIWritingError as exc:
            QMessageBox.warning(self, "IA", f"Falha ao testar conexão: {exc}")
        except Exception as exc:
            QMessageBox.warning(self, "IA", f"Falha inesperada ao testar conexão: {exc}")

    def _build_config_from_form(self) -> AIConfig:
        cfg = self.config_store.load_config()
        cfg.ai_enabled = self.enabled.isChecked()
        cfg.ai_provider = self._provider()
        cfg.openai_api_key = self.openai_key.text().strip()
        cfg.openai_model = self.openai_model.text().strip() or cfg.openai_model
        cfg.openai_temperature = float(self.openai_temperature.value())
        cfg.openai_max_output_tokens = int(self.openai_max_tokens.value())
        cfg.hf_api_token = self.hf_token.text().strip()
        cfg.hf_model = self.hf_model.text().strip() or DEFAULT_HF_MODEL
        cfg.hf_temperature = float(self.hf_temperature.value())
        cfg.hf_max_new_tokens = int(self.hf_max_tokens.value())
        cfg.hf_top_p = float(self.hf_top_p.value())
        cfg.ia_usage_limit = int(self.monthly_limit.value())
        cfg.ia_cache_enabled = self.cache_enabled.isChecked()
        if cfg.ia_last_reset == "":
            cfg.ia_last_reset = date.today().strftime("%Y-%m-%d")
        return cfg

    def _save(self):
        cfg = self._build_config_from_form()
        self.config_store.save_config(cfg)

        settings = AISettings(
            enabled=cfg.ai_enabled,
            show_chips=self._settings.show_chips,
            provider=cfg.ai_provider,
            model=cfg.openai_model if cfg.ai_provider == OPENAI_PROVIDER else cfg.hf_model,
            temperature=cfg.openai_temperature if cfg.ai_provider == OPENAI_PROVIDER else cfg.hf_temperature,
            privacy_mode=self._settings.privacy_mode,
            debug_log_text=self._settings.debug_log_text,
        )
        self.store.save(settings)
        self.accept()
