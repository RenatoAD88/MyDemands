from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import Qt, Signal
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
        rect = self.rect().adjusted(30, 20, -30, -20)
        size = min(rect.width(), rect.height())
        pie_rect = rect
        pie_rect.setWidth(size)
        pie_rect.setHeight(size)
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
            for idx, (label, value) in enumerate(self.data.items()):
                if value <= 0:
                    continue
                span = int(5760 * (value / total))
                painter.setPen(QPen(QColor("#F8FAFC"), 2))
                painter.setBrush(QColor(self.colors[idx % len(self.colors)]))
                painter.drawPie(pie_rect, start_angle, span)
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
            x = rect.left() + idx * col_w + int(col_w * 0.3)
            y = rect.bottom() - bar_h
            bar_w = int(col_w * 0.4)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(bar_colors[label]))
            painter.drawRoundedRect(x, y, bar_w, bar_h, 6, 6)
            painter.setPen(self.palette().text().color())
            label_font = QFont(self.font())
            label_font.setPointSize(11)
            label_font.setWeight(QFont.DemiBold)
            painter.setFont(label_font)
            painter.drawText(x, rect.bottom() + 18, label)
            value_font = QFont(self.font())
            value_font.setPointSize(12)
            value_font.setWeight(QFont.Bold)
            painter.setFont(value_font)
            painter.drawText(x, y - 8, str(value))


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
        self.done_subtitle.setText(
            "Nenhuma demanda concluída ainda" if metrics.concluidas == 0 else f"Concluídas - {metrics.concluidas}"
        )
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
        self.donut.empty_color = placeholder
        self.bars.empty_color = placeholder
        self.setStyleSheet(
            f"""
            MonitoramentoView, QListWidget {{ background: {bg}; color: {text}; }}
            QFrame[dashboardCard='true'] {{ background: {card_bg}; border: 1px solid {'#334155' if dark else '#E2E8F0'}; border-radius: 14px; }}
            QLabel#metricTitle {{ color: {muted}; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.4px; }}
            QLabel#metricValue {{ color: {text}; font-size: 42px; font-weight: 700; }}
            QLabel#metricSubtitle, QLabel#mutedText {{ color: {muted}; font-size: 13px; }}
            QLabel#metricPlaceholder {{ color: {muted}; font-size: 13px; font-weight: 500; }}
            QProgressBar {{ border: none; background: {'#334155' if dark else '#E2E8F0'}; border-radius: 8px; height: 18px; }}
            QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6366F1, stop:1 #8B5CF6); border-radius: 6px; }}
            QLabel[badge='late'] {{ background: {'#7F1D1D' if dark else '#FEE2E2'}; color: {'#FECACA' if dark else '#B91C1C'}; border-radius: 10px; padding: 3px 8px; font-weight: 700; }}
            QLabel[badge='today'] {{ background: {'#854D0E' if dark else '#FEF3C7'}; color: {'#FDE68A' if dark else '#92400E'}; border-radius: 10px; padding: 3px 8px; font-weight: 700; }}
            """
        )

    def _emit_order_changed(self, *_args) -> None:
        self.order_changed.emit(self.current_order())

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
        icon_lbl.setStyleSheet("font-size: 20px;")
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
        frame.setMinimumHeight(150)
        l = QGridLayout(frame)
        l.setContentsMargins(18, 16, 18, 16)
        l.setHorizontalSpacing(12)
        l.setVerticalSpacing(12)
        c1, self.total_value, _ = self._metric_card("Total de Demandas", "📋", False)
        c2, self.progress_value, _ = self._metric_card("Em Andamento", "📊", False)
        c3, self.delay_value, _ = self._metric_card("Em Atraso", "⚠️", False)
        c4, self.cancelled_value, _ = self._metric_card("Canceladas", "🚫", False)
        c5, self.done_value, self.done_subtitle = self._metric_card("Concluídas", "✅", True)
        cards = (c1, c2, c3, c4, c5)
        for col, card in enumerate(cards):
            l.addWidget(card, 0, col)
            l.setColumnStretch(col, 1)
        return frame

    def _build_progress_block(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("dashboardCard", True)
        frame.setMinimumHeight(132)
        l = QVBoxLayout(frame)
        l.setContentsMargins(20, 18, 20, 18)
        l.setSpacing(10)
        top = QHBoxLayout()
        title = QLabel("PROGRESSO GERAL")
        title.setObjectName("metricTitle")
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setObjectName("metricValue")
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.progress_percent_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_subtitle = QLabel("0 de 0 demandas concluídas")
        self.progress_subtitle.setObjectName("metricSubtitle")
        l.addLayout(top)
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
        t1 = QLabel("POR STATUS")
        t1.setObjectName("metricTitle")
        self.donut = DonutChartWidget()
        self.legend_status = QLabel("")
        self.legend_status.setWordWrap(True)
        self.legend_status.setObjectName("metricSubtitle")
        ls.addWidget(t1)
        ls.addWidget(self.donut)
        ls.addWidget(self.legend_status)

        priority_card = QFrame()
        priority_card.setProperty("dashboardCard", True)
        priority_card.setMinimumHeight(280)
        lp = QVBoxLayout(priority_card)
        lp.setContentsMargins(16, 16, 16, 16)
        lp.setSpacing(10)
        t2 = QLabel("POR PRIORIDADE")
        t2.setObjectName("metricTitle")
        self.bars = BarChartWidget()
        lp.addWidget(t2)
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
        title = QLabel("⚠️ ALERTAS DE PRAZO")
        title.setObjectName("metricTitle")
        self.alerts_container = QVBoxLayout()
        self.alerts_container.setSpacing(8)
        l.addWidget(title)
        l.addLayout(self.alerts_container)
        return frame

    def _render_legendas(self, by_status: Dict[str, int]) -> None:
        self.legend_status.setText(" • ".join([f"{k}: {v}" for k, v in by_status.items() if v > 0]) or "Sem dados")

    def _render_alertas(self, alertas: List[Dict[str, str]]) -> None:
        while self.alerts_container.count():
            item = self.alerts_container.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        if not alertas:
            empty = QLabel("Sem demandas atrasadas ou vencendo hoje.")
            empty.setObjectName("metricPlaceholder")
            self.alerts_container.addWidget(empty)
            return

        for alerta in alertas:
            row = QFrame()
            row.setProperty("dashboardCard", True)
            hl = QHBoxLayout(row)
            hl.setContentsMargins(14, 10, 14, 10)
            text = QLabel(f"{alerta['id']} — {alerta['titulo']}\nPrazo: {alerta['prazo']}")
            text.setWordWrap(True)
            badge = QLabel(alerta["badge"])
            badge.setProperty("badge", "late" if alerta["badge"] == "Atrasada" else "today")
            hl.addWidget(text)
            hl.addStretch()
            hl.addWidget(badge)
            self.alerts_container.addWidget(row)
