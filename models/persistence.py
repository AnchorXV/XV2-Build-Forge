"""
DBXV2 Build Forge — Atomic JSON Persistence.

Implements write-to-temp + ``os.replace`` for crash-safe saves, automatic
``.bak`` rotation, and transparent fallback to the backup when the primary
file is corrupted (PRD §3.5).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from app_config import DATA_FILE

logger = logging.getLogger(__name__)


class AtomicJsonPersistence:
    """Crash-safe JSON file persistence with single-generation backup.

    Write flow:
        1. Serialise *payload* to ``<path>.tmp``.
        2. ``flush()`` + ``fsync()`` to guarantee data is on disk.
        3. Copy the current live file (if it exists) to ``<path>.bak``.
        4. ``os.replace(<path>.tmp, <path>)`` — atomic on NTFS & POSIX.

    Read flow:
        1. Try to load ``<path>``.
        2. On ``json.JSONDecodeError`` or ``OSError``, fall back to ``<path>.bak``
           and log a warning (non-blocking to user).
    """

    def __init__(self, default_path: Optional[Union[str, Path]] = None) -> None:
        self.default_path = Path(default_path) if default_path else None

    def save(
        self,
        path_or_payload: Any,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        """Atomically write *payload* as JSON to *path*.

        Can be called as:
            - ``save(path, payload)``
            - ``save(payload)`` (uses default_path)
        """
        if payload is None and isinstance(path_or_payload, dict):
            p = self.default_path or Path(DATA_FILE)
            data = path_or_payload
        else:
            p = Path(path_or_payload)
            data = payload or {}

        tmp_path = p.with_suffix(p.suffix + ".tmp")
        bak_path = p.with_suffix(p.suffix + ".bak")

        try:
            p.parent.mkdir(parents=True, exist_ok=True)

            # 1. Write to temp
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

            # 2. Rotate backup (copy current live file → .bak)
            if p.exists():
                try:
                    shutil.copy2(str(p), str(bak_path))
                except OSError as backup_err:
                    logger.warning("Failed to create backup %s: %s", bak_path, backup_err)

            # 3. Atomic replace
            os.replace(str(tmp_path), str(p))
            logger.debug("Saved %s successfully.", p)

        except OSError:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise

    def load(self, path: Optional[Union[str, Path]] = None) -> dict[str, Any]:
        """Read and parse the JSON file at *path*.

        Falls back to ``<path>.bak`` if the primary file is corrupted or missing.
        """
        p = Path(path or self.default_path or DATA_FILE)
        bak_path = p.with_suffix(p.suffix + ".bak")

        # Attempt 1: primary file
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(
                    "Primary data file %s corrupted or unreadable (%s). Trying backup...",
                    p,
                    exc,
                )

        # Attempt 2: fallback to .bak
        if bak_path.exists():
            try:
                with open(bak_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info("Successfully recovered data from backup %s", bak_path)
                return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.error("Backup file %s is also unreadable (%s).", bak_path, exc)

        logger.info("No valid data file found at %s; returning empty dictionary.", p)
        return {}

    def backup(self, max_files: int = 10) -> None:
        """Create a timestamped backup of the current data file, keeping at most max_files."""
        p = self.default_path or Path(DATA_FILE)
        if not p.exists():
            return

        backup_dir = p.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.json"

        try:
            shutil.copy2(str(p), str(backup_file))
            logger.info("Created backup: %s", backup_file)
        except OSError as e:
            logger.warning("Failed to create backup: %s", e)
            return

        # Enforce max files retention
        try:
            existing_backups = sorted(
                [f for f in backup_dir.glob("backup_*.json")],
                key=os.path.getmtime
            )
            while len(existing_backups) > max_files:
                oldest = existing_backups.pop(0)
                oldest.unlink()
                logger.debug("Deleted old backup: %s", oldest)
        except OSError as e:
            logger.warning("Failed to rotate backups: %s", e)
