import json
import time
import fcntl
from pathlib import Path
from typing import Optional

STATE_DIR = Path.home() / ".kuro_anime"
STATE_FILE = STATE_DIR / "state.json"

_cache = None

KWIK_CACHE_TTL = 7 * 86400


def _ensure():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"codes": {}, "sessions_to_codes": {}, "kwik_cache": {}}))


def _read():
    _ensure()
    global _cache
    if _cache is None:
        with open(STATE_FILE, "r") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            _cache = json.load(f)
    return _cache


def _write(data):
    _ensure()
    global _cache
    with open(STATE_FILE, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        _cache = None
        json.dump(data, f, indent=2)


def save_code(code: str, session_id: str, title: str):
    data = _read()
    data.setdefault("codes", {})[code] = {"session_id": session_id, "title": title}
    data.setdefault("sessions_to_codes", {})[session_id] = code
    _write(data)


def get_code_info(code: str) -> Optional[dict]:
    return _read().get("codes", {}).get(code)


def get_all_codes() -> dict:
    return _read().get("codes", {})


def get_session_code(session_id: str) -> Optional[str]:
    return _read().get("sessions_to_codes", {}).get(session_id)


def get_kwik_cache() -> dict:
    return _read().get("kwik_cache", {})


def set_kwik_cache_entry(kwik_url: str, hls_url: str):
    data = _read()
    data.setdefault("kwik_cache", {})[kwik_url] = {
        "hls_url": hls_url,
        "expires": time.time() + KWIK_CACHE_TTL,
    }
    _write(data)


HISTORY_MAX = 100


def add_history_entry(entry_type: str, query: str, title: str, session_id: str):
    data = _read()
    data.setdefault("history", [])
    data["history"].append({
        "timestamp": time.time(),
        "type": entry_type,
        "query": query,
        "title": title,
        "session_id": session_id,
    })
    data["history"] = data["history"][-HISTORY_MAX:]
    _write(data)


def get_history(limit: int = 20) -> list[dict]:
    return _read().get("history", [])[-limit:][::-1]


def clear_history():
    data = _read()
    data["history"] = []
    _write(data)


