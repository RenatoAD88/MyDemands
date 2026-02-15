from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import os
import sqlite3
import time
from datetime import datetime
from typing import List, Optional

from .models import Channel, Notification, NotificationType, Preferences

ENC_MAGIC = b"MYDEMANDS_NOTIF_ENC_V1"


class NotificationStore:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.db_path = os.path.join(base_dir, "notifications.db")
        self.enc_csv_path = os.path.join(base_dir, "notifications_history.enc.csv")
        self.key_path = os.path.join(base_dir, ".notifications.key")
        self._key = self._load_or_create_key()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _ensure_schema(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    read INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload_json TEXT NOT NULL
                )
                """
            )

    def _load_or_create_key(self) -> bytes:
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                key = f.read()
            if len(key) >= 32:
                return key[:32]
        key = os.urandom(32)
        with open(self.key_path, "wb") as f:
            f.write(key)
        return key

    def _encrypt_bytes(self, plain: bytes) -> bytes:
        nonce = os.urandom(16)
        cipher = bytearray()
        counter = 0
        i = 0
        while i < len(plain):
            block = hashlib.sha256(self._key + nonce + counter.to_bytes(8, "big")).digest()
            chunk = plain[i : i + len(block)]
            cipher.extend(bytes(a ^ b for a, b in zip(chunk, block)))
            i += len(block)
            counter += 1
        mac = hmac.new(self._key, ENC_MAGIC + nonce + bytes(cipher), hashlib.sha256).digest()
        return ENC_MAGIC + b"\n" + base64.urlsafe_b64encode(nonce + bytes(cipher) + mac)

    def insert(self, notification: Notification) -> int:
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO notifications (timestamp, type, title, body, payload_json, read) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    notification.timestamp.isoformat(),
                    notification.type.value,
                    notification.title,
                    notification.body,
                    json.dumps(notification.payload, ensure_ascii=False),
                    1 if notification.read else 0,
                ),
            )
            new_id = int(cur.lastrowid)
        self._rewrite_encrypted_csv_snapshot()
        return new_id

    def list_notifications(
        self,
        *,
        type_filter: Optional[NotificationType] = None,
        read_filter: Optional[bool] = None,
        limit: int = 300,
    ) -> List[Notification]:
        clauses = []
        params: list = []
        if type_filter is not None:
            clauses.append("type = ?")
            params.append(type_filter.value)
        if read_filter is not None:
            clauses.append("read = ?")
            params.append(1 if read_filter else 0)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._connect() as con:
            rows = con.execute(
                f"SELECT id, timestamp, type, title, body, payload_json, read FROM notifications {where} ORDER BY id DESC LIMIT ?",
                [*params, limit],
            ).fetchall()
        out = []
        for r in rows:
            out.append(
                Notification(
                    id=int(r["id"]),
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    type=NotificationType(r["type"]),
                    title=r["title"],
                    body=r["body"],
                    payload=json.loads(r["payload_json"] or "{}"),
                    read=bool(r["read"]),
                )
            )
        return out

    def mark_as_read(self, notification_id: int) -> None:
        with self._connect() as con:
            con.execute("UPDATE notifications SET read = 1 WHERE id = ?", (notification_id,))
        self._rewrite_encrypted_csv_snapshot()

    def save_preferences(self, preferences: Preferences) -> None:
        payload = {
            "enabled_types": {k.value: v for k, v in preferences.enabled_types.items()},
            "enabled_channels": {k.value: v for k, v in preferences.enabled_channels.items()},
            "scheduler_interval_minutes": preferences.scheduler_interval_minutes,
            "muted_until_epoch": preferences.muted_until_epoch,
        }
        with self._connect() as con:
            con.execute(
                "INSERT INTO preferences (id, payload_json) VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET payload_json = excluded.payload_json",
                (json.dumps(payload, ensure_ascii=False),),
            )

    def load_preferences(self) -> Preferences:
        with self._connect() as con:
            row = con.execute("SELECT payload_json FROM preferences WHERE id = 1").fetchone()
        if not row:
            return Preferences()
        payload = json.loads(row["payload_json"])
        pref = Preferences()
        pref.enabled_types = {
            nt: bool(payload.get("enabled_types", {}).get(nt.value, True)) for nt in NotificationType
        }
        pref.enabled_channels = {
            ch: bool(payload.get("enabled_channels", {}).get(ch.value, pref.enabled_channels[ch])) for ch in Channel
        }
        pref.scheduler_interval_minutes = int(payload.get("scheduler_interval_minutes", pref.scheduler_interval_minutes))
        pref.muted_until_epoch = float(payload.get("muted_until_epoch", 0.0) or 0.0)
        return pref

    def mute_for_seconds(self, seconds: int) -> None:
        pref = self.load_preferences()
        pref.muted_until_epoch = time.time() + max(0, seconds)
        self.save_preferences(pref)

    def _rewrite_encrypted_csv_snapshot(self) -> None:
        notifications = self.list_notifications(limit=5000)
        out = io.StringIO()
        writer = csv.writer(out, delimiter=";")
        writer.writerow(["id", "timestamp", "type", "title", "body", "payload_json", "read"])
        for n in reversed(notifications):
            writer.writerow([
                n.id,
                n.timestamp.isoformat(),
                n.type.value,
                n.title,
                n.body,
                json.dumps(n.payload, ensure_ascii=False),
                "1" if n.read else "0",
            ])
        encrypted = self._encrypt_bytes(out.getvalue().encode("utf-8"))
        with open(self.enc_csv_path, "wb") as f:
            f.write(encrypted)
