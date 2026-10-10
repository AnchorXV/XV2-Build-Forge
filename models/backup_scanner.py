from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


BACKUP_NAME_RE = re.compile(r"^backup_(\d{8})_(\d{6})\.json$")


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    timestamp: Optional[datetime]
    size_bytes: int
    sheets_count: int
    presets_count: int
    characters_count: int

    def display_label(self) -> str:
        if self.timestamp:
            ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts = self.path.stem
        return f"{ts}   ({self.sheets_count} sheets · {self.presets_count} presets)"

    def preview_text(self) -> str:
        kb = self.size_bytes / 1024
        return (
            f"Sheets: {self.sheets_count}  ·  Presets: {self.presets_count}  ·  "
            f"Characters: {self.characters_count}  ·  Size: {kb:.1f} KB"
        )

    def _sort_key(self) -> float:
        if self.timestamp:
            return self.timestamp.timestamp()
        try:
            return self.path.stat().st_mtime
        except OSError:
            return 0.0


def _parse_timestamp_from_name(name: str) -> Optional[datetime]:
    m = BACKUP_NAME_RE.match(name)
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)}_{m.group(2)}", "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def _read_backup_summary(path: Path) -> tuple[int, int, int]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return (0, 0, 0)

    if not isinstance(data, dict):
        return (0, 0, 0)

    rosters = data.get("rosters", {})
    if not isinstance(rosters, dict):
        return (0, 0, 0)

    sheets = len(rosters)
    presets = sum(len(v) for v in rosters.values() if isinstance(v, list))

    chars = data.get("characters", [])
    chars_count = len(chars) if isinstance(chars, list) else 0

    return (sheets, presets, chars_count)


def list_backups(data_file: Path, max_items: int = 30) -> list[BackupInfo]:
    backup_dir = data_file.parent / "backups"
    if not backup_dir.exists():
        return []

    result: list[BackupInfo] = []
    for p in backup_dir.glob("backup_*.json"):
        if not p.is_file():
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue

        ts = _parse_timestamp_from_name(p.name)
        sheets, presets, chars = _read_backup_summary(p)
        result.append(BackupInfo(
            path=p,
            timestamp=ts,
            size_bytes=size,
            sheets_count=sheets,
            presets_count=presets,
            characters_count=chars,
        ))

    result.sort(key=lambda b: b._sort_key(), reverse=True)
    return result[:max_items]