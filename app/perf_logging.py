"""Persist timing diagnostics (HTTP, LLM, client-reported). Best-effort; failures never raise."""
import json
from typing import Any

from sqlalchemy.orm import Session

from app.database import PerformanceLog, SessionLocal

MAX_LOG_ROWS = 2000


def _prune_if_needed(db: Session) -> None:
    n = db.query(PerformanceLog).count()
    if n <= MAX_LOG_ROWS:
        return
    to_remove = n - MAX_LOG_ROWS
    ids = [
        r[0]
        for r in db.query(PerformanceLog.id)
        .order_by(PerformanceLog.id.asc())
        .limit(to_remove)
        .all()
    ]
    if not ids:
        return
    db.query(PerformanceLog).filter(PerformanceLog.id.in_(ids)).delete(synchronize_session=False)
    db.commit()


def log_performance_event(
    category: str,
    event_name: str,
    duration_ms: float,
    *,
    exam_session_id: int | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    db = SessionLocal()
    try:
        meta_s: str | None = None
        if meta:
            meta_s = json.dumps(meta, ensure_ascii=False)
            if len(meta_s) > 8000:
                meta_s = meta_s[:8000] + "…"
        row = PerformanceLog(
            category=category,
            event_name=event_name[:512],
            duration_ms=float(duration_ms),
            exam_session_id=exam_session_id,
            meta_json=meta_s,
        )
        db.add(row)
        db.commit()
        _prune_if_needed(db)
    except Exception:
        db.rollback()
    finally:
        db.close()
