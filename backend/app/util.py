from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ago(*, hours: float = 0, minutes: float = 0) -> str:
    stamp = datetime.now(timezone.utc) - timedelta(hours=hours, minutes=minutes)
    return stamp.replace(microsecond=0).isoformat()


def earlier_today(hour: int, minute: int) -> str:
    local = datetime.now().astimezone()
    stamp = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if stamp > local:
        stamp = local - timedelta(hours=2)
    return stamp.isoformat(timespec="seconds")


def nid() -> str:
    return uuid.uuid4().hex[:12]


def snow_sys_id() -> str:
    return uuid.uuid4().hex
