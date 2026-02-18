from __future__ import annotations

from typing import Optional

from mydemands.domain.models import User
from mydemands.infra.db import Database


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def _normalize_email(email: str) -> str:
        return (email or "").strip().lower()

    def get_by_email(self, email: str) -> Optional[User]:
        normalized = self._normalize_email(email)
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT email,password_hash,role,must_change_password FROM users WHERE email = ?",
                (normalized,),
            ).fetchone()
        if not row:
            return None
        return User(
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            must_change_password=bool(row["must_change_password"]),
        )

    def add(self, user: User) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO users(email,password_hash,role,must_change_password) VALUES (?,?,?,?)",
                (
                    self._normalize_email(user.email),
                    user.password_hash,
                    user.role,
                    int(user.must_change_password),
                ),
            )
            conn.commit()

    def update(self, user: User) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash=?, role=?, must_change_password=? WHERE email=?",
                (user.password_hash, user.role, int(user.must_change_password), self._normalize_email(user.email)),
            )
            conn.commit()

    def exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None
