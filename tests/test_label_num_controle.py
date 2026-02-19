from pathlib import Path


def test_label_renamed_num_controle():
    source = Path("app.py").read_text(encoding="utf-8")
    assert 'opc_form.addRow("Núm. Controle", self.id_azure)' in source
    assert 'opc_form.addRow("ID Azure", self.id_azure)' not in source
