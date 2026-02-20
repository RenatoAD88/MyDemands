from __future__ import annotations

import math
from typing import Dict, List

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from mydemands.dashboard.metrics_service import DashboardMetrics


class DonutChartWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.data: Dict[str, int] = {}
        self.colors = ["#6366F1", "#10B981", "#F59E0B", "#F97316", "#94A3B8"]
        self.empty_placeholder = "Sem dados suficientes"
        self.empty_color = "#64748B"
        self.setMinimumHeight(280)

    def set_data(self, data: Dict[str, int]) -> None:
        self.data = data
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        total = sum(self.data.values())
        rect = self.rect().adjusted(24, 16, -24, -16)
        size = min(rect.width(), rect.height())
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
            placeholder_font = QFont(self.font())
            placeholder_font.setPointSize(12)
            placeholder_font.setWeight(QFont.Medium)
            painter.setFont(placeholder_font)
            painter.drawText(self.rect(), Qt.AlignCenter, self.empty_placeholder)
        else:
            for idx, (_label, value) in enumerate(self.data.items()):
                if value <= 0:
                    continue
                span = int(5760 * (value / total))
                painter.setPen(QPen(QColor("#F8FAFC"), 2))
                painter.setBrush(QColor(self.colors[idx % len(self.colors)]))
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
                painter.setPen(QColor("#0F172A"))
                painter.drawText(QRect(x - 18, y - 10, 36, 20), Qt.AlignCenter, str(value))
                start_angle += span
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().window().color())
        hole = pie_rect.adjusted(30, 30, -30, -30)
        painter.drawEllipse(hole)


class BarChartWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.data = {"Alta": 0, "Média": 0, "Baixa": 0}
        self.empty_placeholder = "Sem dados suficientes"
        self.empty_color = "#64748B"
        self.setMinimumHeight(280)

    def set_data(self, data: Dict[str, int]) -> None:
        self.data = {"Alta": data.get("Alta", 0), "Média": data.get("Média", 0), "Baixa": data.get("Baixa", 0)}
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(20, 20, -20, -30)
        max_value = max(self.data.values()) if self.data else 1
        max_value = max(max_value, 1)
        labels = ["Alta", "Média", "Baixa"]
        bar_colors = {"Alta": "#EF4444", "Média": "#F59E0B", "Baixa": "#10B981"}
        col_w = rect.width() // max(1, len(labels))
        total = sum(self.data.values())

        if total <= 0:
            painter.setPen(QColor(self.empty_color))
            placeholder_font = QFont(self.font())
            placeholder_font.setPointSize(12)
            placeholder_font.setWeight(QFont.Medium)
            painter.setFont(placeholder_font)
            painter.drawText(self.rect(), Qt.AlignCenter, self.empty_placeholder)
            return

        for idx, label in enumerate(labels):
            value = self.data.get(label, 0)
            ratio = value / max_value
            bar_h = int((rect.height() - 20) * ratio)
            x = rect.left() + idx * col_w + int(col_w * 0.2)
            y = rect.bottom() - bar_h
            bar_w = int(col_w * 0.6)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(bar_colors[label]))
            painter.drawRoundedRect(x, y, bar_w, bar_h, 6, 6)
            painter.setPen(self.palette().text().color())
            label_font = QFont(self.font())
            label_font.setPointSize(11)
            label_font.setWeight(QFont.DemiBold)
            painter.setFont(label_font)
            col_rect = QRect(rect.left() + idx * col_w, rect.bottom() + 4, col_w, 26)
            painter.drawText(col_rect, Qt.AlignHCenter | Qt.AlignTop, label)
            value_font = QFont(self.font())
            value_font.setPointSize(12)
            value_font.setWeight(QFont.Bold)
            painter.setFont(value_font)
            value_rect = QRect(rect.left() + idx * col_w, y - 24, col_w, 20)
            painter.drawText(value_rect, Qt.AlignHCenter | Qt.AlignVCenter, str(value))


class MonitoramentoView(QWidget):
    order_changed = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        self.header_title = QLabel("Dashboard")
        self.header_title.setStyleSheet("font-size: 30px; font-weight: 800;")
        self.header_subtitle = QLabel("Visão geral das suas demandas")
        self.header_subtitle.setStyleSheet("font-size: 16px;")
        self.header_subtitle.setObjectName("mutedText")
        root.addWidget(self.header_title)
        root.addWidget(self.header_subtitle)

        self.block_list = QListWidget()
        self.block_list.setDragDropMode(QListWidget.InternalMove)
        self.block_list.setDefaultDropAction(Qt.MoveAction)
        self.block_list.setSpacing(10)
        self.block_list.setFrameShape(QFrame.NoFrame)
        self.block_list.model().rowsMoved.connect(self._emit_order_changed)
        root.addWidget(self.block_list)

        self._cards: Dict[str, QFrame] = {}
        self._build_blocks()
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
        out: List[str] = []
        for idx in range(self.block_list.count()):
            item = self.block_list.item(idx)
            out.append(str(item.data(Qt.UserRole)))
        return out

    def update_metrics(self, metrics: DashboardMetrics) -> None:
        self.total_value.setText(str(metrics.total_demandas))
        self.done_value.setText(str(metrics.concluidas))
        self.delay_value.setText(str(metrics.em_atraso))
        self.progress_value.setText(str(metrics.em_andamento))
        self.cancelled_value.setText(str(metrics.canceladas))
        self.progress_bar.setValue(metrics.concluidas_percentual)
        self.progress_percent_label.setText(f"{metrics.concluidas_percentual}%")
        self.progress_subtitle.setText(f"{metrics.concluidas} de {metrics.total_demandas} demandas concluídas")
        self.donut.set_data(metrics.por_status)
        self.bars.set_data(metrics.por_prioridade)
        self._render_legendas(metrics.por_status)
        self._render_alertas(metrics.alertas)

    def apply_theme(self, theme_name: str) -> None:
        dark = (theme_name or "light").lower() == "dark"
        bg = "#0F172A" if dark else "#F7F9FC"
        card_bg = "#1E293B" if dark else "#FFFFFF"
        text = "#E2E8F0" if dark else "#0F172A"
        muted = "#94A3B8" if dark else "#475569"
        placeholder = "#64748B" if dark else "#64748B"
        label_bg = "#334155" if dark else "#EEF2FF"
        label_color = "#C7D2FE" if dark else "#3730A3"
        self.donut.empty_color = placeholder
        self.bars.empty_color = placeholder
        self.setStyleSheet(
            f"""
            MonitoramentoView, QListWidget {{ background: {bg}; color: {text}; }}
            QFrame[dashboardCard='true'] {{ background: {card_bg}; border: 1px solid {'#334155' if dark else '#E2E8F0'}; border-radius: 14px; }}
            QLabel#sectionTitle {{ color: {label_color}; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; background: {label_bg}; border-radius: 8px; padding: 6px 10px; min-width: 220px; max-width: 300px; }}
            QLabel#sectionIcon {{ color: {'#CBD5E1' if dark else '#334155'}; font-size: 16px; font-weight: 700; background: {'#1E293B' if dark else '#F1F5F9'}; border-radius: 12px; padding: 4px 8px; min-width: 24px; }}
            QLabel#metricTitle {{ color: {muted}; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.2px; }}
            QLabel#metricValue {{ color: {text}; font-size: 32px; font-weight: 800; background: {'#1E293B' if dark else '#F8FAFC'}; border-radius: 10px; padding: 4px 10px; min-height: 40px; }}
            QLabel#metricSubtitle, QLabel#mutedText {{ color: {muted}; font-size: 13px; }}
            QLabel#metricPlaceholder {{ color: {muted}; font-size: 13px; font-weight: 500; }}
            QLabel#progressPercent {{ color: {text}; font-size: 20px; font-weight: 800; background: {'#312E81' if dark else '#EEF2FF'}; border-radius: 12px; padding: 4px 10px; min-width: 58px; }}
            QProgressBar {{ border: none; background: {'#334155' if dark else '#E2E8F0'}; border-radius: 8px; height: 18px; margin-top: 8px; }}
            QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6366F1, stop:1 #8B5CF6); border-radius: 6px; }}
            QLabel[badge='late'] {{ background: {'#7F1D1D' if dark else '#FEE2E2'}; color: {'#FECACA' if dark else '#B91C1C'}; border-radius: 10px; padding: 3px 8px; font-weight: 700; }}
            QLabel[badge='today'] {{ background: {'#854D0E' if dark else '#FEF3C7'}; color: {'#FDE68A' if dark else '#92400E'}; border-radius: 10px; padding: 3px 8px; font-weight: 700; }}
            QLabel[badge='next'] {{ background: {'#0C4A6E' if dark else '#DBEAFE'}; color: {'#BAE6FD' if dark else '#1D4ED8'}; border-radius: 10px; padding: 3px 8px; font-weight: 700; }}
            """
        )

    def _emit_order_changed(self, *_args) -> None:
        self.order_changed.emit(self.current_order())

    def _section_header(self, title: str, icon: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("sectionTitle")
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("sectionIcon")
        row.addWidget(title_lbl)
        row.addStretch()
        row.addWidget(icon_lbl)
        return row

    def _metric_card(self, title: str, icon: str, show_subtitle: bool = True):
        frame = QFrame()
        frame.setProperty("dashboardCard", True)
        frame.setMinimumHeight(120)
        l = QVBoxLayout(frame)
        l.setContentsMargins(18, 16, 18, 16)
        l.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("metricTitle")
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("sectionIcon")
        top.addWidget(title_lbl)
        top.addStretch()
        top.addWidget(icon_lbl)
        value_lbl = QLabel("0")
        value_lbl.setObjectName("metricValue")
        l.addLayout(top)
        l.addWidget(value_lbl)
        subtitle_lbl = QLabel("")
        subtitle_lbl.setObjectName("metricSubtitle")
        subtitle_lbl.setMinimumHeight(18)
        subtitle_lbl.setVisible(show_subtitle)
        l.addWidget(subtitle_lbl)
        return frame, value_lbl, subtitle_lbl

    def _build_big_numbers_block(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("dashboardCard", True)
        frame.setMinimumHeight(260)
        wrapper = QVBoxLayout(frame)
        wrapper.setContentsMargins(18, 16, 18, 16)
        wrapper.setSpacing(10)
        wrapper.addLayout(self._section_header("Dados gerais", "◫"))

        l = QGridLayout()
        l.setContentsMargins(0, 6, 0, 0)
        l.setHorizontalSpacing(12)
        l.setVerticalSpacing(12)
        c1, self.total_value, _ = self._metric_card("Total de demandas", "◉", False)
        c2, self.progress_value, _ = self._metric_card("Em andamento", "◔", False)
        c3, self.delay_value, _ = self._metric_card("Atrasadas", "◷", False)
        c4, self.cancelled_value, _ = self._metric_card("Canceladas", "◍", False)
        c5, self.done_value, self.done_subtitle = self._metric_card("Concluídas", "◕", False)
        cards = (c1, c2, c3, c4, c5)
        for col, card in enumerate(cards):
            row = col // 3
            column = col % 3
            l.addWidget(card, row, column)
            l.setColumnStretch(column, 1)
        wrapper.addLayout(l)
        return frame

    def _build_progress_block(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("dashboardCard", True)
        frame.setMinimumHeight(132)
        l = QVBoxLayout(frame)
        l.setContentsMargins(20, 18, 20, 18)
        l.setSpacing(10)
        l.addLayout(self._section_header("Progresso geral", "◔"))

        percent_row = QHBoxLayout()
        percent_row.addStretch()
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setObjectName("progressPercent")
        percent_row.addWidget(self.progress_percent_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_subtitle = QLabel("0 de 0 demandas concluídas")
        self.progress_subtitle.setObjectName("metricSubtitle")
        l.addLayout(percent_row)
        l.addWidget(self.progress_bar)
        l.addWidget(self.progress_subtitle)
        return frame

    def _build_charts_block(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("dashboardCard", True)
        frame.setMinimumHeight(320)
        l = QGridLayout(frame)
        l.setContentsMargins(18, 18, 18, 18)
        l.setHorizontalSpacing(14)
        l.setVerticalSpacing(14)
        status_card = QFrame()
        status_card.setProperty("dashboardCard", True)
        status_card.setMinimumHeight(280)
        ls = QVBoxLayout(status_card)
        ls.setContentsMargins(16, 16, 16, 16)
        ls.setSpacing(10)
        ls.addLayout(self._section_header("Por status", "◎"))
        self.donut = DonutChartWidget()
        self.legend_status = QLabel("")
        self.legend_status.setWordWrap(True)
        self.legend_status.setObjectName("metricSubtitle")
        ls.addWidget(self.donut)
        ls.addWidget(self.legend_status)

        priority_card = QFrame()
        priority_card.setProperty("dashboardCard", True)
        priority_card.setMinimumHeight(280)
        lp = QVBoxLayout(priority_card)
        lp.setContentsMargins(16, 16, 16, 16)
        lp.setSpacing(10)
        lp.addLayout(self._section_header("Por prioridade", "▤"))
        self.bars = BarChartWidget()
        lp.addWidget(self.bars)

        l.addWidget(status_card, 0, 0)
        l.addWidget(priority_card, 0, 1)
        l.setColumnStretch(0, 1)
        l.setColumnStretch(1, 1)
        return frame

    def _build_alerts_block(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("dashboardCard", True)
        frame.setMinimumHeight(260)
        l = QVBoxLayout(frame)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(10)
        l.addLayout(self._section_header("Alertas de prazo", "◷"))
        self.alerts_container = QVBoxLayout()
        self.alerts_container.setSpacing(8)
        l.addLayout(self.alerts_container)
        return frame

    def _render_legendas(self, by_status: Dict[str, int]) -> None:
        legend_items = []
        for idx, (status, value) in enumerate(by_status.items()):
            if value <= 0:
                continue
            color = self.donut.colors[idx % len(self.donut.colors)]
            legend_items.append(f"<span style='color:{color}; font-weight:700'>●</span> {status}: <b>{value}</b>")
        self.legend_status.setText(" &nbsp;&nbsp; ".join(legend_items) or "Sem dados")

    def _render_alertas(self, alertas: List[Dict[str, str]]) -> None:
        while self.alerts_container.count():
            item = self.alerts_container.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        if not alertas:
            empty = QLabel("Sem demandas atrasadas, para hoje ou com vencimento próximo.")
            empty.setObjectName("metricPlaceholder")
            self.alerts_container.addWidget(empty)
            return

        groups = {
            "Atrasada": "Atrasadas",
            "Prazo hoje": "Entregar hoje",
            "Vencimento próximo": "Vencimento próximo",
        }
        for badge_key, group_title in groups.items():
            group_items = [a for a in alertas if a["badge"] == badge_key]
            if not group_items:
                continue

            section = QFrame()
            section.setProperty("dashboardCard", True)
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(12, 10, 12, 10)
            section_layout.setSpacing(6)
            title = QLabel(group_title)
            title.setObjectName("metricTitle")
            section_layout.addWidget(title)

            for alerta in group_items:
                row = QFrame()
                hl = QHBoxLayout(row)
                hl.setContentsMargins(8, 6, 8, 6)
                text = QLabel(f"{alerta['id']} — {alerta['titulo']}\nPrazo: {alerta['prazo']}")
                text.setWordWrap(True)
                badge = QLabel(alerta["badge"])
                badge_map = {"Atrasada": "late", "Prazo hoje": "today", "Vencimento próximo": "next"}
                badge.setProperty("badge", badge_map.get(alerta["badge"], "today"))
                hl.addWidget(text)
                hl.addStretch()
                hl.addWidget(badge)
                section_layout.addWidget(row)

            self.alerts_container.addWidget(section)
