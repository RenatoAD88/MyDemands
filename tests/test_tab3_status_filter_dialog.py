import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import STATUS_EDIT_OPTIONS, StatusFilterDialog

QApplication = qtwidgets.QApplication
Qt = qtcore.Qt


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_status_filter_dialog_treats_all_checked_as_no_filter():
    _get_app()
    dialog = StatusFilterDialog(STATUS_EDIT_OPTIONS, [], None)

    assert dialog.selected_statuses() == []

    first_status_item = dialog.list_widget.item(1)
    first_status_item.setCheckState(Qt.Unchecked)

    selected = dialog.selected_statuses()
    assert len(selected) == len(STATUS_EDIT_OPTIONS) - 1
    assert first_status_item.text() not in selected

    dialog.close()


def test_status_filter_dialog_select_all_controls_statuses():
    _get_app()
    dialog = StatusFilterDialog(STATUS_EDIT_OPTIONS, [STATUS_EDIT_OPTIONS[0]], None)

    assert dialog._all_item.checkState() == Qt.Unchecked

    dialog._all_item.setCheckState(Qt.Checked)

    assert dialog.selected_statuses() == []

    dialog.close()
