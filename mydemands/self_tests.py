from __future__ import annotations

import os
import tempfile

def run_ui_self_test() -> int:
    from PySide6.QtWidgets import QApplication, QLineEdit, QTabBar, QTableWidget, QToolButton
    from app import MainWindow
    from csv_store import CsvStore
    from mydemands.services.theme_service import ThemeService
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    theme = ThemeService(app)

    with tempfile.TemporaryDirectory(prefix="mydemands_ui_selftest_") as temp_dir:
        window = MainWindow(CsvStore(temp_dir), theme_service=theme)
        window.show()

        def metrics() -> dict[str, int]:
            app.processEvents()
            tab_bar = window.findChild(QTabBar)
            line_edit = window.findChild(QLineEdit)
            toolbar_btn = next((btn for btn in window.findChildren(QToolButton) if bool(btn.property("toolbarAction"))), None)
            table = window.findChild(QTableWidget)
            header = table.horizontalHeader() if table is not None else None

            if tab_bar is None or line_edit is None or toolbar_btn is None or header is None:
                raise RuntimeError("Widgets críticos não encontrados no MainWindow")

            tab_height = tab_bar.tabRect(0).height() if tab_bar.count() else tab_bar.sizeHint().height()
            return {
                "toolbar_height": toolbar_btn.sizeHint().height(),
                "toolbar_icon_size": toolbar_btn.iconSize().height(),
                "lineedit_min_height": line_edit.minimumHeight(),
                "tab_height": tab_height,
                "header_height": header.height(),
            }

        theme.apply_theme("light")
        light = metrics()
        theme.apply_theme("dark")
        dark = metrics()
        window.close()

    if dark != light:
        print(f"[SELF-TEST-UI] Falha: métricas diferentes. light={light} dark={dark}")
        return 1
    print(f"[SELF-TEST-UI] OK: métricas consistentes {light}")
    return 0


def run_crypto_self_test() -> int:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception as exc:
        print(f"[SELF-TEST-CRYPTO] Falha ao importar AESGCM: {exc}")
        return 1

    key = AESGCM.generate_key(bit_length=128)
    aesgcm = AESGCM(key)
    nonce = b"0123456789ab"
    plaintext = b"mydemands-self-test"
    aad = b"v1"

    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    restored = aesgcm.decrypt(nonce, ciphertext, aad)
    if restored != plaintext:
        print("[SELF-TEST-CRYPTO] Falha: roundtrip AESGCM invalido")
        return 1

    print("[SELF-TEST-CRYPTO] OK")
    return 0
