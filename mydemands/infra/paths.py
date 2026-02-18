from __future__ import annotations

from pathlib import Path


DEFAULT_BASE_DIR = Path(r"C:\MyDemands\masterData")


class Paths:
    def __init__(self, base_dir: Path | str | None = None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_BASE_DIR

    def ensure_base_dir(self) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        return self.base_dir

    @property
    def users_db(self) -> Path:
        return self.base_dir / "users.db"

    @property
    def session_file(self) -> Path:
        return self.base_dir / "session.json"

    @property
    def email_settings_file(self) -> Path:
        return self.base_dir / "email_settings.json"

    @property
    def secrets_file(self) -> Path:
        return self.base_dir / "secrets.dat"
