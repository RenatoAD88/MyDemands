import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import TAB3_STATUS_FILTER_OPTIONS, StatusFilterDialog

QApplication = qtwidgets.QApplication
Qt = qtcore.Qt


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_status_filter_dialog_treats_all_checked_as_no_filter():
    _get_app()
    dialog = StatusFilterDialog(TAB3_STATUS_FILTER_OPTIONS, [], None)

    assert dialog.selected_statuses() == []

    first_status_item = dialog.list_widget.item(0)
    first_status_item.setCheckState(Qt.Unchecked)

    selected = dialog.selected_statuses()
    assert len(selected) == len(TAB3_STATUS_FILTER_OPTIONS) - 1
    assert first_status_item.text() not in selected

    dialog.close()


def test_status_filter_dialog_cancel_keeps_selection_unchanged():
    _get_app()
    selected = [TAB3_STATUS_FILTER_OPTIONS[0], TAB3_STATUS_FILTER_OPTIONS[2]]
    dialog = StatusFilterDialog(TAB3_STATUS_FILTER_OPTIONS, selected, None)

    assert dialog.selected_statuses() == selected

    dialog.reject()

    assert dialog.result() == dialog.Rejected

    dialog.close()
