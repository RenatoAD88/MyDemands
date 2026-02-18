from __future__ import annotations

import sqlite3
from pathlib import Path

from mydemands.infra.paths import Paths


class Database:
    def __init__(self, paths: Paths):
        self.paths = paths

    def connect(self) -> sqlite3.Connection:
        self.paths.ensure_base_dir()
        conn = sqlite3.connect(self.paths.users_db)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role in ('master','default')),
                    must_change_password INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reset_tokens (
                    email TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (email, token_hash)
                )
                """
            )
            conn.commit()
