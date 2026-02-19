import pytest

from mydemands.infra.secrets.fake_secret_store import FakeSecretStore
from mydemands.services import secure_csv_exchange_service as secure_csv_module
from mydemands.services.secure_csv_exchange_service import (
    CRYPTO_AVAILABLE,
    CsvExchangeError,
    DPAPI_HEADER,
    ENC_HEADER,
    SecureCsvExchangeService,
)


pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography não disponível no ambiente")
def test_secure_export_roundtrip():
    svc = SecureCsvExchangeService(FakeSecretStore())
    csv_text = "ID,Projeto\n1,Projeto X\n"

    payload = svc.export_payload(csv_text, passphrase="senha123", is_master=False)
    result = svc.import_payload(payload, passphrase="senha123", is_master=False)

    assert result.encrypted is True
    assert result.csv_text == csv_text


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography não disponível no ambiente")
def test_envelope_encryption_master_can_decrypt_without_passphrase():
    svc = SecureCsvExchangeService(FakeSecretStore())
    csv_text = "ID,Projeto\n1,Projeto Master\n"

    payload = svc.export_payload(csv_text, passphrase="abc12345", is_master=False)
    result = svc.import_payload(payload, passphrase="", is_master=True)

    assert result.csv_text == csv_text


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography não disponível no ambiente")
def test_user_cannot_decrypt_with_wrong_passphrase():
    svc = SecureCsvExchangeService(FakeSecretStore())
    payload = svc.export_payload("ID,Projeto\n1,Privado\n", passphrase="certa123", is_master=False)

    with pytest.raises(CsvExchangeError):
        svc.import_payload(payload, passphrase="errada", is_master=False)


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography não disponível no ambiente")
def test_master_can_export_without_passphrase():
    svc = SecureCsvExchangeService(FakeSecretStore())
    csv_text = "ID,Projeto\n1,A\n2,B\n"

    payload = svc.export_payload(csv_text, passphrase="", is_master=True)
    result = svc.import_payload(payload, passphrase="", is_master=True)

    assert result.csv_text == csv_text


def test_export_requires_passphrase_for_standard_user():
    svc = SecureCsvExchangeService(FakeSecretStore())

    with pytest.raises(CsvExchangeError, match="palavra-passe válida"):
        svc.export_payload("ID,Projeto\n1,Teste\n", passphrase="", is_master=False)


def test_export_error_message_not_crypto_unavailable_when_passphrase_provided():
    svc = SecureCsvExchangeService(FakeSecretStore())

    if CRYPTO_AVAILABLE:
        payload = svc.export_payload("ID,Projeto\n1,Teste\n", passphrase="senha123", is_master=False)
        assert payload.startswith(ENC_HEADER)
    else:
        with pytest.raises(CsvExchangeError) as exc:
            svc.export_payload("ID,Projeto\n1,Teste\n", passphrase="senha123", is_master=False)
        assert "dependência ausente" in str(exc.value)


def test_import_encrypted_payload_without_cryptography_returns_controlled_error(monkeypatch):
    svc = SecureCsvExchangeService(FakeSecretStore())

    monkeypatch.setattr(secure_csv_module, "CRYPTO_AVAILABLE", False)

    with pytest.raises(CsvExchangeError, match="dependência ausente"):
        svc.import_payload(f"{ENC_HEADER}\ndata:AA==", passphrase="", is_master=True)


def test_dpapi_fallback_roundtrip_when_cryptography_unavailable(monkeypatch):
    class _FakeWin32Crypt:
        @staticmethod
        def CryptProtectData(value, *_args):
            return b"dpapi:" + value

        @staticmethod
        def CryptUnprotectData(value, *_args):
            assert value.startswith(b"dpapi:")
            return None, value[len(b"dpapi:") :]

    svc = SecureCsvExchangeService(FakeSecretStore())
    monkeypatch.setattr(secure_csv_module, "CRYPTO_AVAILABLE", False)
    monkeypatch.setattr(secure_csv_module, "win32crypt", _FakeWin32Crypt)

    payload = svc.export_payload("ID,Projeto\n1,DPAPI\n", passphrase="", is_master=True)
    assert payload.startswith(DPAPI_HEADER)

    result = svc.import_payload(payload, passphrase="", is_master=True)
    assert result.csv_text == "ID,Projeto\n1,DPAPI\n"


def test_dpapi_fallback_blocks_user_passphrase_mode(monkeypatch):
    svc = SecureCsvExchangeService(FakeSecretStore())

    monkeypatch.setattr(secure_csv_module, "CRYPTO_AVAILABLE", False)

    with pytest.raises(CsvExchangeError, match="dependência ausente"):
        svc.export_payload("ID,Projeto\n1,Teste\n", passphrase="senha123", is_master=False)


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography não disponível no ambiente")
def test_crypto_available_roundtrip():
    svc = SecureCsvExchangeService(FakeSecretStore())
    payload = svc.export_payload("ID,Projeto\n1,Seguro\n", passphrase="senha123", is_master=False)

    result = svc.import_payload(payload, passphrase="senha123", is_master=False)

    assert result.encrypted is True
    assert "Seguro" in result.csv_text


def test_export_blocks_when_crypto_missing(monkeypatch):
    svc = SecureCsvExchangeService(FakeSecretStore())

    monkeypatch.setattr(secure_csv_module, "CRYPTO_AVAILABLE", False)
    monkeypatch.setattr(secure_csv_module, "CRYPTO_IMPORT_ERROR", "ImportError('missing cryptography')")

    with pytest.raises(CsvExchangeError, match="dependência ausente"):
        svc.export_payload("ID,Projeto\n1,Teste\n", passphrase="", is_master=False)


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography não disponível no ambiente")
def test_master_import_can_require_passphrase_when_master_key_disabled():
    svc = SecureCsvExchangeService(FakeSecretStore())
    csv_text = "ID,Projeto\n1,Protegido\n"

    payload = svc.export_payload(csv_text, passphrase="abc12345", is_master=False)

    with pytest.raises(CsvExchangeError, match="Palavra-passe inválida ou ausente"):
        svc.import_payload(payload, passphrase="", is_master=True, allow_master_key=False)

    result = svc.import_payload(payload, passphrase="abc12345", is_master=True, allow_master_key=False)
    assert result.csv_text == csv_text
