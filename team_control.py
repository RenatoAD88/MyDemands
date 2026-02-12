from __future__ import annotations

import json
import os
import uuid
from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

TEAM_CONTROL_FILE = "team_control.json"
MAX_SECTIONS = 10
WEEKDAY_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
STATUS_COLORS: Dict[str, tuple[int, int, int, int, int, int]] = {
    "F": (128, 90, 213, 255, 255, 255),
    "A": (239, 68, 68, 255, 255, 255),
    "P": (37, 99, 235, 255, 255, 255),
    "D": (147, 197, 253, 15, 23, 42),
    "R": (253, 224, 71, 15, 23, 42),
    "H": (250, 204, 21, 15, 23, 42),
    "K": (74, 222, 128, 15, 23, 42),
}


@dataclass
class TeamMember:
    id: str
    name: str
    entries: Dict[str, str]


@dataclass
class TeamSection:
    id: str
    name: str
    members: List[TeamMember]


class TeamControlStore:
    def __init__(self, base_dir: str):
        self.path = os.path.join(base_dir, TEAM_CONTROL_FILE)
        self.sections: List[TeamSection] = []
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.path):
            self.sections = []
            return
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        out: List[TeamSection] = []
        for s in raw.get("sections", []):
            members: List[TeamMember] = []
            for m in s.get("members", []):
                members.append(
                    TeamMember(
                        id=str(m.get("id") or uuid.uuid4().hex),
                        name=str(m.get("name") or "").strip(),
                        entries={str(k): str(v) for k, v in (m.get("entries") or {}).items()},
                    )
                )
            out.append(
                TeamSection(
                    id=str(s.get("id") or uuid.uuid4().hex),
                    name=str(s.get("name") or "").strip(),
                    members=members,
                )
            )
        self.sections = out

    def save(self) -> None:
        payload = {
            "sections": [
                {
                    "id": s.id,
                    "name": s.name,
                    "members": [
                        {
                            "id": m.id,
                            "name": m.name,
                            "entries": m.entries,
                        }
                        for m in s.members
                    ],
                }
                for s in self.sections
            ]
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def create_section(self, name: str) -> TeamSection:
        cleaned = (name or "").strip()
        if not cleaned:
            raise ValueError("Nome da seção é obrigatório.")
        if len(self.sections) >= MAX_SECTIONS:
            raise ValueError("Limite de 10 seções atingido.")
        section = TeamSection(id=uuid.uuid4().hex, name=cleaned, members=[])
        self.sections.append(section)
        self.save()
        return section

    def delete_section(self, section_id: str) -> None:
        self.sections = [s for s in self.sections if s.id != section_id]
        self.save()

    def add_member(self, section_id: str, name: str) -> TeamMember:
        cleaned = (name or "").strip()
        if not cleaned:
            raise ValueError("Nome do funcionário é obrigatório.")
        section = self._get_section(section_id)
        member = TeamMember(id=uuid.uuid4().hex, name=cleaned, entries={})
        section.members.append(member)
        self.save()
        return member

    def remove_member(self, section_id: str, member_id: str) -> None:
        section = self._get_section(section_id)
        section.members = [m for m in section.members if m.id != member_id]
        self.save()

    def rename_member(self, section_id: str, member_id: str, name: str) -> None:
        cleaned = (name or "").strip()
        if not cleaned:
            raise ValueError("Nome do funcionário é obrigatório.")
        member = self._get_member(section_id, member_id)
        member.name = cleaned
        self.save()

    def set_entry(self, section_id: str, member_id: str, when: date, code: str) -> None:
        member = self._get_member(section_id, member_id)
        key = when.isoformat()
        value = (code or "").strip().upper()
        if not value:
            member.entries.pop(key, None)
        else:
            member.entries[key] = value
        self.save()

    def _get_section(self, section_id: str) -> TeamSection:
        for s in self.sections:
            if s.id == section_id:
                return s
        raise ValueError("Seção não encontrada.")

    def _get_member(self, section_id: str, member_id: str) -> TeamMember:
        section = self._get_section(section_id)
        for m in section.members:
            if m.id == member_id:
                return m
        raise ValueError("Funcionário não encontrado.")


def month_days(year: int, month: int) -> int:
    return monthrange(year, month)[1]


def participation_for_date(entries: List[str]) -> int:
    return sum(1 for e in entries if (e or "").strip().upper() in {"K", "P"})
