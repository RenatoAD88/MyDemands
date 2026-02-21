from __future__ import annotations

import math
from typing import Dict, List

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from mydemands.dashboard.demandas_schema_registry import DemandasSchemaRegistry
from mydemands.dashboard.grid_preferences import GridPreferencesService
from mydemands.dashboard.grid_widgets import BaseGridView, ColumnConfigDialog
from mydemands.dashboard.metrics_service import DashboardMetrics


class DonutChartWidget(QWidget):
    def __init__(self, labels_order: List[str] | None = None, colors: Dict[str, str] | None = None) -> None:
        super().__init__()
        self.labels_order = labels_order or []
        self.data: Dict[str, int] = {}
        self.colors = colors or {}
        self.empty_placeholder = "Sem dados suficientes"
        self.empty_color = "#64748B"
        self.value_color = QColor("black")
        self.chart_scale = 0.9
        self.setMinimumHeight(260)

    def set_data(self, data: Dict[str, int]) -> None:
        if self.labels_order:
            self.data = {label: int(data.get(label, 0)) for label in self.labels_order}
        else:
            self.data = {str(k): int(v) for k, v in data.items()}
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        total = sum(self.data.values())
        rect = self.rect().adjusted(24, 16, -24, -16)
        size = int(min(rect.width(), rect.height()) * self.chart_scale)
        pie_rect = rect
        pie_rect.setWidth(size)
        pie_rect.setHeight(size)
        pie_rect.moveLeft(rect.left() + (rect.width() - size) // 2)
        pie_rect.moveTop(rect.top() + (rect.height() - size) // 2)
        start_angle = 0
        if total <= 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#CBD5E1"))
            painter.drawEllipse(pie_rect)
            painter.setPen(QColor(self.empty_color))
            painter.drawText(self.rect(), Qt.AlignCenter, self.empty_placeholder)
        else:
            for idx, (label, value) in enumerate(self.data.items()):
                if value <= 0:
                    continue
                span = int(5760 * (value / total))
                fill = self.colors.get(label, ["#6366F1", "#10B981", "#F59E0B"][idx % 3])
                painter.setPen(QPen(QColor("#F8FAFC"), 2))
                painter.setBrush(QColor(fill))
                painter.drawPie(pie_rect, start_angle, span)
                mid_angle = start_angle + span / 2
                radius = pie_rect.width() / 2
                center_x = pie_rect.center().x()
                center_y = pie_rect.center().y()
                label_radius = radius * 1.1
                x = int(center_x + label_radius * math.cos(-mid_angle / 16 * math.pi / 180))
                y = int(center_y + label_radius * math.sin(-mid_angle / 16 * math.pi / 180))
                value_font = QFont(self.font())
                value_font.setPointSize(10)
                value_font.setWeight(QFont.Bold)
                painter.setFont(value_font)
                painter.setPen(self.value_color)
                painter.drawText(QRect(x - 18, y - 10, 36, 20), Qt.AlignCenter, str(value))
                start_angle += span
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().window().color())
        painter.drawEllipse(pie_rect.adjusted(30, 30, -30, -30))


class TimingBarsWidget(QWidget):
    COLOR_MAP = {
        "Dentro do prazo": "#1E3A8A",
        "Concluído antes do prazo": "#1D4ED8",
        "Concluído no prazo": "#3B82F6",
        "Concluída com atraso": "#93C5FD",
        "Em atraso": "#EF4444",
    }

    def __init__(self) -> None:
        super().__init__()
        self.order = ["Dentro do prazo", "Concluído antes do prazo", "Concluído no prazo", "Concluída com atraso", "Em atraso"]
        self.data = {k: 0 for k in self.order}
        self.min_bar_height = 3
        self.min_column_width = 116
        self.label_height = 52
        self._last_column_width = 0
        self.setMinimumHeight(260)

    def _column_width(self, available_width: int) -> int:
        return max(available_width // len(self.order), self.min_column_width)

    def set_data(self, data: Dict[str, int]) -> None:
        self.data = {k: int(data.get(k, 0)) for k in self.order}
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(14, 16, -14, -30)
        max_value = max(max(self.data.values()), 1)
        col_w = self._column_width(rect.width())
        self._last_column_width = col_w
        chart_w = col_w * len(self.order)
        start_x = rect.left() + max((rect.width() - chart_w) // 2, 0)
        for idx, label in enumerate(self.order):
            value = self.data.get(label, 0)
            proportional = int((rect.height() - (self.label_height + 12)) * (value / max_value))
            bar_h = max(proportional, self.min_bar_height)
            x = start_x + idx * col_w + int(col_w * 0.25)
            y = rect.bottom() - bar_h - 20
            bar_w = int(col_w * 0.5)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(self.COLOR_MAP[label]))
            painter.drawRoundedRect(x, y, bar_w, bar_h, 6, 6)
            painter.setPen(self.palette().text().color())
            painter.drawText(QRect(start_x + idx * col_w, y - 20, col_w, 18), Qt.AlignHCenter, str(value))
            painter.drawText(QRect(start_x + idx * col_w, rect.bottom() + 4, col_w, self.label_height), Qt.AlignHCenter | Qt.TextWordWrap, label)


class MonitoramentoView(QWidget):
    order_changed = Signal(list)

    ALERTAS_TABLE_KEY = "monitoring_alertas_atrasos_grid"
    ALERTAS_DEFAULT_VISIBLE = ["id", "urgente", "status", "timing", "prioridade", "prazo", "projeto", "percentual", "responsavel"]

    def __init__(self, *, user_id: str = "anonimo", preferences_service: GridPreferencesService | None = None) -> None:
        super().__init__()
        self._user_id = user_id or "anonimo"
        self._schema_registry = DemandasSchemaRegistry()
        self._grid_preferences_service = preferences_service
        self._alertas_preferences: Dict = self._schema_registry.default_table_preferences(self.ALERTAS_DEFAULT_VISIBLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)
        self.header_title = QLabel("Monitoramento")
        self.header_subtitle = QLabel("Indicadores operacionais")
        self.header_subtitle.setObjectName("mutedText")
        root.addWidget(self.header_title)
        root.addWidget(self.header_subtitle)

        self.block_list = QListWidget()
        self.block_list.setDragDropMode(QListWidget.InternalMove)
        self.block_list.setDefaultDropAction(Qt.MoveAction)
        self.block_list.setSpacing(8)
        self.block_list.setFrameShape(QFrame.NoFrame)
        self.block_list.model().rowsMoved.connect(self._emit_order_changed)
        root.addWidget(self.block_list)

        self._cards: Dict[str, QFrame] = {}
        self._build_blocks()
        if self._grid_preferences_service is not None:
            self._alertas_preferences = self._grid_preferences_service.load_table_preferences(
                self._user_id,
                self.ALERTAS_TABLE_KEY,
                self.ALERTAS_DEFAULT_VISIBLE,
            )
        self.alerts_table.apply_preferences(self._alertas_preferences)
        self.apply_theme("light")

    def _build_blocks(self) -> None:
        self._cards = {
            "big_numbers": self._build_big_numbers_block(),
            "progresso": self._build_progress_block(),
            "graficos": self._build_charts_block(),
            "alertas": self._build_alerts_block(),
        }

    def set_order(self, order: List[str]) -> None:
        self.block_list.clear()
        for block_id in order:
            card = self._cards.get(block_id)
            if card is None:
                continue
            item = QListWidgetItem()
            item.setData(Qt.UserRole, block_id)
            item.setSizeHint(card.sizeHint())
            self.block_list.addItem(item)
            self.block_list.setItemWidget(item, card)

    def current_order(self) -> List[str]:
        return [str(self.block_list.item(idx).data(Qt.UserRole)) for idx in range(self.block_list.count())]

    def update_metrics(self, metrics: DashboardMetrics) -> None:
        for title, label in self.big_number_labels.items():
            label.setText(str(metrics.big_numbers.get(title, 0)))
        self.done_value.setText(str(metrics.concluidas))
        self.progress_bar.setValue(metrics.concluidas_percentual)
        self.progress_percent_label.setText(f"{metrics.concluidas_percentual}%")
        self.progress_subtitle.setText(f"{metrics.concluidas} de {metrics.total_demandas} demandas concluídas")
        self.priority_donut.set_data(metrics.por_prioridade)
        self.status_gerais_bars.set_data(metrics.status_gerais)
        self._render_priority_legenda(metrics.por_prioridade)
        self._render_alertas(metrics.alertas)

    def apply_theme(self, theme_name: str) -> None:
        dark = (theme_name or "light").lower() == "dark"
        text = "#E2E8F0" if dark else "#0F172A"
        self.priority_donut.value_color = QColor("white") if dark else QColor("black")
        self.setStyleSheet(
            f"""
            MonitoramentoView, QListWidget {{ background: {'#0F172A' if dark else '#F7F9FC'}; color: {text}; }}
            QFrame[dashboardCard='true'] {{ background: {'#1E293B' if dark else '#FFFFFF'}; border: 1px solid {'#334155' if dark else '#E2E8F0'}; border-radius: 14px; }}
            QLabel#sectionTitle {{ color: {'#C7D2FE' if dark else '#3730A3'}; font-size: 12px; font-weight: 700; text-transform: uppercase; }}
            QLabel#metricTitle {{ color: {'#94A3B8' if dark else '#475569'}; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
            QLabel#metricValue {{ color: {text}; font-size: 28px; font-weight: 800; }}
            QLabel#metricSubtitle, QLabel#mutedText {{ color: {'#94A3B8' if dark else '#475569'}; font-size: 13px; }}
            QLabel#metricPlaceholder {{ color: {'#94A3B8' if dark else '#475569'}; font-size: 13px; font-weight: 500; }}
            QLabel#progressPercent {{ color: {text}; font-size: 20px; font-weight: 800; }}
            QHeaderView::section {{ background: {'#334155' if dark else '#F1F5F9'}; color: {text}; border: none; padding: 6px; font-weight: 700; }}
            QTableWidget {{ gridline-color: {'#334155' if dark else '#E2E8F0'}; }}
            """
        )

    def _emit_order_changed(self, *_args) -> None:
        self.order_changed.emit(self.current_order())

    def _section_header(self, title: str) -> QHBoxLayout:
        row = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setObjectName("sectionTitle")
        row.addWidget(title_lbl)
        row.addStretch()
        return row

    def _simple_metric(self, title: str):
        frame = QFrame(); frame.setProperty("dashboardCard", True); frame.setMinimumHeight(120)
        l = QVBoxLayout(frame); l.setContentsMargins(16, 16, 16, 16); l.setSpacing(4)
        t = QLabel(title); t.setObjectName("metricTitle")
        v = QLabel("0"); v.setObjectName("metricValue")
        l.addWidget(t); l.addWidget(v); l.addStretch()
        return frame, v

    def _build_big_numbers_block(self) -> QFrame:
        frame = QFrame(); frame.setProperty("dashboardCard", True); frame.setMinimumHeight(180)
        wrapper = QVBoxLayout(frame); wrapper.setContentsMargins(16, 16, 16, 16); wrapper.setSpacing(8)
        wrapper.addLayout(self._section_header("Dados Gerais"))
        row = QHBoxLayout(); row.setSpacing(8)
        self.big_number_labels = {}
        order = ["Total de Demandas", "Não iniciado", "Em andamento", "Bloqueado", "Requer revisão", "Cancelado", "Concluído"]
        for title in order:
            c, v = self._simple_metric(title)
            row.addWidget(c, 1)
            self.big_number_labels[title] = v
            if title == "Concluído":
                self.done_value = v
        wrapper.addLayout(row)
        return frame

    def _build_progress_block(self) -> QFrame:
        frame = QFrame(); frame.setProperty("dashboardCard", True); frame.setMinimumHeight(132)
        l = QVBoxLayout(frame); l.setContentsMargins(20, 18, 20, 18); l.setSpacing(10)
        l.addLayout(self._section_header("Progresso geral"))
        percent_row = QHBoxLayout(); percent_row.addStretch()
        self.progress_percent_label = QLabel("0%"); self.progress_percent_label.setObjectName("progressPercent")
        percent_row.addWidget(self.progress_percent_label)
        self.progress_bar = QProgressBar(); self.progress_bar.setTextVisible(False)
        self.progress_subtitle = QLabel("0 de 0 demandas concluídas"); self.progress_subtitle.setObjectName("metricSubtitle")
        l.addLayout(percent_row); l.addWidget(self.progress_bar); l.addWidget(self.progress_subtitle)
        return frame

    def _build_charts_block(self) -> QFrame:
        frame = QFrame(); frame.setProperty("dashboardCard", True); frame.setMinimumHeight(340)
        l = QGridLayout(frame); l.setContentsMargins(18, 18, 18, 18); l.setHorizontalSpacing(14); l.setVerticalSpacing(14)

        self.status_gerais_card = QFrame(); self.status_gerais_card.setProperty("dashboardCard", True); self.status_gerais_card.setMinimumHeight(300)
        ls = QVBoxLayout(self.status_gerais_card); ls.setContentsMargins(16, 16, 16, 16); ls.setSpacing(10)
        ls.addLayout(self._section_header("Status Gerais"))
        self.status_gerais_bars = TimingBarsWidget()
        ls.addWidget(self.status_gerais_bars)

        self.priority_card = QFrame(); self.priority_card.setProperty("dashboardCard", True); self.priority_card.setMinimumHeight(300)
        lp = QVBoxLayout(self.priority_card); lp.setContentsMargins(16, 16, 16, 16); lp.setSpacing(10)
        lp.addLayout(self._section_header("Por prioridade"))
        self.priority_donut = DonutChartWidget(
            labels_order=["Alta", "Média", "Baixa"],
            colors={"Alta": "#EF4444", "Média": "#FACC15", "Baixa": "#22C55E"},
        )
        self.priority_legend = QLabel("")
        self.priority_legend.setObjectName("metricSubtitle")
        self.priority_legend.setAlignment(Qt.AlignCenter)
        lp.addStretch(1)
        lp.addWidget(self.priority_donut, 0, Qt.AlignCenter)
        lp.addWidget(self.priority_legend, 0, Qt.AlignHCenter)
        lp.addStretch(1)

        l.addWidget(self.status_gerais_card, 0, 0)
        l.addWidget(self.priority_card, 0, 1)
        l.setColumnStretch(0, 1)
        l.setColumnStretch(1, 1)
        return frame

    def _build_alerts_block(self) -> QFrame:
        frame = QFrame(); frame.setProperty("dashboardCard", True); frame.setMinimumHeight(170)
        l = QVBoxLayout(frame); l.setContentsMargins(16, 16, 16, 16); l.setSpacing(8)
        header_row = self._section_header("Alertas de atrasos")
        self.alerts_config_button = QPushButton("Configurar colunas")
        self.alerts_restore_button = QPushButton("Restaurar padrão")
        self.alerts_config_button.clicked.connect(self._open_column_config_dialog)
        self.alerts_restore_button.clicked.connect(self._restore_alertas_defaults)
        header_row.addWidget(self.alerts_config_button)
        header_row.addWidget(self.alerts_restore_button)
        l.addLayout(header_row)
        self.alerts_table = BaseGridView(self._schema_registry.demand_columns())
        self.alerts_table.preferences_changed.connect(self._persist_alertas_preferences)
        l.addWidget(self.alerts_table)
        self.alerts_empty = QLabel("Nenhuma demanda em atraso.")
        self.alerts_empty.setObjectName("metricPlaceholder")
        self.alerts_empty.setAlignment(Qt.AlignCenter)
        l.addWidget(self.alerts_empty)
        return frame

    def _render_priority_legenda(self, by_priority: Dict[str, int]) -> None:
        order = ["Alta", "Média", "Baixa"]
        legend_parts = [f"{label}: <b>{int(by_priority.get(label, 0))}</b>" for label in order]
        self.priority_legend.setText("   ".join(legend_parts))

    def _render_alertas(self, alertas: List[Dict[str, str]]) -> None:
        atraso_only = [a for a in alertas if str(a.get("timing") or "").strip().lower() == "em atraso"]
        if not alertas:
            self.alerts_table.setVisible(False)
            self.alerts_empty.setVisible(True)
            return

        if not atraso_only:
            self.alerts_table.setVisible(False)
            self.alerts_empty.setVisible(True)
            return

        self.alerts_table.setVisible(True)
        self.alerts_empty.setVisible(False)
        self.alerts_table.set_rows(atraso_only)

    def _persist_alertas_preferences(self, table_prefs: Dict) -> None:
        self._alertas_preferences = table_prefs
        if self._grid_preferences_service is not None:
            self._alertas_preferences = self._grid_preferences_service.save_table_preferences(
                self._user_id,
                self.ALERTAS_TABLE_KEY,
                table_prefs,
            )

    def _restore_alertas_defaults(self) -> None:
        if self._grid_preferences_service is not None:
            self._alertas_preferences = self._grid_preferences_service.reset_table_preferences(
                self._user_id,
                self.ALERTAS_TABLE_KEY,
                self.ALERTAS_DEFAULT_VISIBLE,
            )
        else:
            self._alertas_preferences = self._schema_registry.default_table_preferences(self.ALERTAS_DEFAULT_VISIBLE)
        self.alerts_table.apply_preferences(self._alertas_preferences)

    def _open_column_config_dialog(self) -> None:
        selected = [c.get("id") for c in self._alertas_preferences.get("columns", []) if c.get("visible")]
        dialog = ColumnConfigDialog(self._schema_registry.demand_columns(), [str(x) for x in selected if x], self)
        result = dialog.exec()
        if result == QDialog.Rejected:
            self._restore_alertas_defaults()
            return
        selected_ids = set(dialog.selected_column_ids())
        updated = self.alerts_table.extract_preferences()
        for col in updated.get("columns", []):
            col["visible"] = col.get("id") in selected_ids
        self._persist_alertas_preferences(updated)
        self.alerts_table.apply_preferences(self._alertas_preferences)
