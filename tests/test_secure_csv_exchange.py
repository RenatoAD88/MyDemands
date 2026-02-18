import pytest

from mydemands.infra.secrets.fake_secret_store import FakeSecretStore
from mydemands.services.secure_csv_exchange_service import SecureCsvExchangeService, CsvExchangeError


def test_encrypt_decrypt_with_passphrase_roundtrip():
    svc = SecureCsvExchangeService(FakeSecretStore())
    csv_text = "ID,Projeto\n1,Projeto X\n"

    payload = svc.export_payload(csv_text, passphrase="senha123", is_master=False)
    result = svc.import_payload(payload, passphrase="senha123", is_master=False)

    assert result.encrypted is True
    assert result.csv_text == csv_text


def test_envelope_encryption_master_can_decrypt_without_passphrase():
    svc = SecureCsvExchangeService(FakeSecretStore())
    csv_text = "ID,Projeto\n1,Projeto Master\n"

    payload = svc.export_payload(csv_text, passphrase="abc12345", is_master=False)
    result = svc.import_payload(payload, passphrase="", is_master=True)

    assert result.csv_text == csv_text


def test_user_cannot_decrypt_with_wrong_passphrase():
    svc = SecureCsvExchangeService(FakeSecretStore())
    payload = svc.export_payload("ID,Projeto\n1,Privado\n", passphrase="certa123", is_master=False)

    with pytest.raises(CsvExchangeError):
        svc.import_payload(payload, passphrase="errada", is_master=False)


def test_master_import_export_all_without_passphrase():
    svc = SecureCsvExchangeService(FakeSecretStore())
    csv_text = "ID,Projeto\n1,A\n2,B\n"

    payload = svc.export_payload(csv_text, passphrase="", is_master=True)
    result = svc.import_payload(payload, passphrase="", is_master=True)

    assert result.csv_text == csv_text
