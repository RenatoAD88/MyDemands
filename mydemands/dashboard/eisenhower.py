from __future__ import annotations

from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from mydemands.dashboard.eisenhower_classifier import QUADRANTS, EisenhowerClassifierService


class DemandCardButton(QPushButton):
    def __init__(self, row: Dict[str, Any], on_click):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(False)
        self.setObjectName("eisenhowerDemandCard")
        self.setStyleSheet(
            "QPushButton#eisenhowerDemandCard {text-align: left; border: 1px solid #d0d7de; border-radius: 8px; padding: 8px;}"
            "QPushButton#eisenhowerDemandCard:hover {border-color: #8c959f;}"
        )

        demand_number = (row.get("ID") or row.get("_id") or "-")
        description = (row.get("Descrição") or "").strip()
        short_description = (description[:120] + "...") if len(description) > 120 else description

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        id_label = QLabel(f"#{demand_number}")
        id_label.setStyleSheet("font-weight: 600;")
        desc_label = QLabel(short_description or "Sem descrição")
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(36)

        badges = QLabel(
            f"Prioridade: {(row.get('Prioridade') or 'Média')}  |  "
            f"Timing: {(row.get('Timing') or 'Sem prazo')}  |  "
            f"Urgente: {(row.get('É Urgente?') or 'Não')}"
        )
        badges.setStyleSheet("font-size: 11px; color: #57606a;")

        layout.addWidget(id_label)
        layout.addWidget(desc_label)
        layout.addWidget(badges)

        self.clicked.connect(lambda: on_click(row))


class EisenhowerView(QWidget):
    def __init__(self, on_card_click, classifier: EisenhowerClassifierService | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self._on_card_click = on_card_click
        self._classifier = classifier or EisenhowerClassifierService()
        self.last_groups: Dict[str, List[Dict[str, Any]]] = {q.key: [] for q in QUADRANTS}
        self._columns_layouts: Dict[str, QVBoxLayout] = {}
        root = QHBoxLayout(self)
        root.setSpacing(8)

        for quadrant in QUADRANTS:
            column = QFrame()
            column.setFrameShape(QFrame.StyledPanel)
            column_layout = QVBoxLayout(column)
            column_layout.setContentsMargins(8, 8, 8, 8)
            column_layout.setSpacing(6)

            title = QLabel(quadrant.title)
            title.setStyleSheet("font-weight: 700;")
            count = QLabel("0")
            count.setObjectName(f"{quadrant.key}_count")

            header = QHBoxLayout()
            header.addWidget(title)
            header.addStretch()
            header.addWidget(count)

            content_host = QWidget()
            content_layout = QVBoxLayout(content_host)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(6)
            content_layout.addWidget(QLabel("Sem demandas"))
            content_layout.addStretch()
            self._columns_layouts[quadrant.key] = content_layout

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(content_host)

            column_layout.addLayout(header)
            column_layout.addWidget(scroll)
            root.addWidget(column, 1)

    def set_rows(self, rows: List[Dict[str, Any]]) -> None:
        self.last_groups = self._classifier.group_rows(rows)
        for quadrant in QUADRANTS:
            key = quadrant.key
            rows_in_group = self.last_groups.get(key, [])
            layout = self._columns_layouts[key]

            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            if not rows_in_group:
                layout.addWidget(QLabel("Sem demandas"))
                layout.addStretch()
            else:
                for row in rows_in_group:
                    layout.addWidget(DemandCardButton(row, self._on_card_click))
                layout.addStretch()

            count_label = self.findChild(QLabel, f"{key}_count")
            if count_label is not None:
                count_label.setText(str(len(rows_in_group)))
