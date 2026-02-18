from __future__ import annotations

import base64
import csv
import io
import os
from dataclasses import dataclass
from typing import List, Dict, Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from csv_store import DISPLAY_COLUMNS
from mydemands.infra.secrets.secret_store import ISecretStore

ENC_HEADER = "MYDEMANDS_ENCRYPTED_V1"
MASTER_KEY_SECRET = "csv_exchange_master_key"


class CsvExchangeError(Exception):
    pass


@dataclass
class ImportResult:
    csv_text: str
    encrypted: bool


class SecureCsvExchangeService:
    def __init__(self, secret_store: ISecretStore):
        self.secret_store = secret_store

    def _get_or_create_master_key(self) -> bytes:
        key = self.secret_store.get(MASTER_KEY_SECRET)
        if key and len(key) >= 32:
            return key[:32]
        key = os.urandom(32)
        self.secret_store.set(MASTER_KEY_SECRET, key)
        return key

    def _derive_key(self, passphrase: str, salt: bytes) -> bytes:
        if not passphrase:
            raise CsvExchangeError("Palavra-passe obrigatória.")
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
        return kdf.derive(passphrase.encode("utf-8"))

    def render_csv_text(self, rows: List[Dict[str, Any]], delimiter: str = ",") -> str:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=DISPLAY_COLUMNS, delimiter=delimiter)
        writer.writeheader()
        for row in rows:
            payload = {k: row.get(k, "") for k in DISPLAY_COLUMNS}
            writer.writerow(payload)
        return buf.getvalue()

    def export_payload(self, csv_text: str, passphrase: str, is_master: bool) -> str:
        data_key = os.urandom(32)
        salt = os.urandom(16)
        data_nonce = os.urandom(12)

        data_cipher = AESGCM(data_key).encrypt(data_nonce, csv_text.encode("utf-8-sig"), None)

        master_key = self._get_or_create_master_key()
        wrap_nonce_master = os.urandom(12)
        wrapped_key_master = AESGCM(master_key).encrypt(wrap_nonce_master, data_key, None)

        wrapped_key_user = b""
        wrap_nonce_user = b""
        if passphrase:
            user_key = self._derive_key(passphrase, salt)
            wrap_nonce_user = os.urandom(12)
            wrapped_key_user = AESGCM(user_key).encrypt(wrap_nonce_user, data_key, None)
        elif not is_master:
            raise CsvExchangeError("Usuário padrão precisa informar palavra-passe para exportação.")

        lines = [
            ENC_HEADER,
            f"salt:{base64.b64encode(salt).decode('ascii')}",
            f"nonce:{base64.b64encode(data_nonce).decode('ascii')}",
            f"wrap_nonce_user:{base64.b64encode(wrap_nonce_user).decode('ascii')}",
            f"wrapped_key_user:{base64.b64encode(wrapped_key_user).decode('ascii')}",
            f"wrap_nonce_master:{base64.b64encode(wrap_nonce_master).decode('ascii')}",
            f"wrapped_key_master:{base64.b64encode(wrapped_key_master).decode('ascii')}",
            f"data:{base64.b64encode(data_cipher).decode('ascii')}",
        ]
        return "\n".join(lines)

    def import_payload(self, raw_text: str, passphrase: str, is_master: bool) -> ImportResult:
        if not raw_text.startswith(ENC_HEADER):
            return ImportResult(csv_text=raw_text, encrypted=False)

        values: dict[str, bytes] = {}
        for line in raw_text.splitlines()[1:]:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            values[key.strip()] = base64.b64decode(value.strip() or "")

        salt = values.get("salt", b"")
        data_nonce = values.get("nonce", b"")
        data_cipher = values.get("data", b"")
        wrapped_key_user = values.get("wrapped_key_user", b"")
        wrap_nonce_user = values.get("wrap_nonce_user", b"")
        wrapped_key_master = values.get("wrapped_key_master", b"")
        wrap_nonce_master = values.get("wrap_nonce_master", b"")

        data_key: bytes | None = None
        if is_master:
            try:
                data_key = AESGCM(self._get_or_create_master_key()).decrypt(wrap_nonce_master, wrapped_key_master, None)
            except Exception:
                data_key = None

        if data_key is None:
            if not passphrase:
                raise CsvExchangeError("Palavra-passe inválida ou ausente para descriptografar o arquivo.")
            try:
                user_key = self._derive_key(passphrase, salt)
                data_key = AESGCM(user_key).decrypt(wrap_nonce_user, wrapped_key_user, None)
            except Exception as exc:
                raise CsvExchangeError("Não foi possível descriptografar o arquivo. Verifique a palavra-passe.") from exc

        try:
            plain = AESGCM(data_key).decrypt(data_nonce, data_cipher, None)
        except Exception as exc:
            raise CsvExchangeError("Arquivo criptografado inválido ou corrompido.") from exc

        return ImportResult(csv_text=plain.decode("utf-8-sig"), encrypted=True)
