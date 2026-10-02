from __future__ import annotations

import json
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from app_config import DATA_FILE

logger = logging.getLogger(__name__)


class AtomicJsonPersistence:

    def __init__(self, default_path: Optional[Union[str, Path]] = None) -> None:
        self.default_path = Path(default_path) if default_path else None

    def save(
        self,
        path_or_payload: Any,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
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

            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

            if p.exists():
                try:
                    self._replace_with_retry(p, bak_path)
                except OSError as backup_err:
                    logger.warning(
                        "Failed to rotate backup %s: %s", bak_path, backup_err
                    )

            self._replace_with_retry(tmp_path, p)
            logger.debug("Saved %s successfully.", p)

        except OSError:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise

    @staticmethod
    def _replace_with_retry(src: Path, dst: Path, attempts: int = 5) -> None:
        last_exc: Optional[OSError] = None
        for i in range(attempts):
            try:
                os.replace(str(src), str(dst))
                return
            except PermissionError as exc:
                last_exc = exc
                if i < attempts - 1:
                    time.sleep(0.1 * (i + 1))
        if last_exc is not None:
            raise last_exc

    def load(self, path: Optional[Union[str, Path]] = None) -> dict[str, Any]:
        p = Path(path or self.default_path or DATA_FILE)
        bak_path = p.with_suffix(p.suffix + ".bak")

        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
                logger.warning(
                    "Primary data file %s root is not a dict (%s); trying backup...",
                    p, type(data).__name__,
                )
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(
                    "Primary data file %s corrupted or unreadable (%s). Trying backup...",
                    p, exc,
                )

        if bak_path.exists():
            try:
                with open(bak_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    logger.info("Successfully recovered data from backup %s", bak_path)
                    return data
                logger.warning(
                    "Backup %s root is not a dict (%s) either.",
                    bak_path, type(data).__name__,
                )
            except (json.JSONDecodeError, OSError) as exc:
                logger.error("Backup file %s is also unreadable (%s).", bak_path, exc)

        logger.info("No valid data file found at %s; returning empty dictionary.", p)
        return {}

    def backup(self, max_files: int = 10) -> None:
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

        try:
            existing_backups = sorted(
                [f for f in backup_dir.glob("backup_*.json")],
                key=os.path.getmtime,
            )
            while len(existing_backups) > max_files:
                oldest = existing_backups.pop(0)
                oldest.unlink()
                logger.debug("Deleted old backup: %s", oldest)
        except OSError as e:
            logger.warning("Failed to rotate backups: %s", e)