"""Session persistence and collaboration primitives for the Command Center.

This module provides a tiny persistence layer that is intentionally
implementation-agnostic so it can be invoked either directly from Python
or via a lightweight CLI bridge. The storage backend is a JSON document
on disk which keeps the data model intentionally transparent for the
Stage 2 UI review.

Data model
==========
Each session document is stored under the key ``sessions`` with the
following layout::

    {
        "sessions": {
            "session-id": {
                "id": "session-id",
                "name": "Exploration run",  # optional display name
                "mission_id": "mission-42",
                "engine": "igsoa_gw",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:34:56Z",
                "payload": {...},  # arbitrary mission snapshot
                "collaborators": ["alice@example.com"],
                "notes": [
                    {
                        "id": "uuid",
                        "author": "alice@example.com",
                        "content": "Next steps...",
                        "created_at": "2025-01-01T12:05:00Z"
                    }
                ]
            }
        }
    }

To support collaboration primitives during the Stage 2 review window the
module exposes helpers for listing, retrieving, updating and annotating
sessions. A minimal CLI layer is also exposed so the Node.js API can
proxy requests without embedding the persistence logic.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, MutableMapping, Optional
import sys
import time
import uuid

STORE_FILENAME = os.environ.get("COMMAND_CENTER_SESSION_STORE", "sessions.json")
STORE_PATH = Path(__file__).resolve().parent / STORE_FILENAME


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_store() -> Dict[str, Any]:
    if not STORE_PATH.exists():
        return {"sessions": {}}
    try:
        with STORE_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        # Corruption fallback: keep a backup and reset.
        backup_path = STORE_PATH.with_suffix(".corrupt")
        STORE_PATH.replace(backup_path)
        return {"sessions": {}}


def _dump_store(store: MutableMapping[str, Any]) -> None:
    tmp_path = STORE_PATH.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=False, indent=2, sort_keys=True)
    tmp_path.replace(STORE_PATH)


def list_sessions() -> Iterable[Dict[str, Any]]:
    store = _load_store()
    sessions = store.get("sessions", {})
    return sorted(sessions.values(), key=lambda item: item.get("updated_at", ""), reverse=True)


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    store = _load_store()
    return store.get("sessions", {}).get(session_id)


def save_session(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if not session_id:
        raise ValueError("session_id must be provided")

    store = _load_store()
    sessions = store.setdefault("sessions", {})
    now = _utc_now()
    session = sessions.get(session_id, {
        "id": session_id,
        "created_at": now,
        "notes": [],
    })

    session.update({
        "name": payload.get("name", session.get("name")),
        "mission_id": payload.get("mission_id", session.get("mission_id")),
        "engine": payload.get("engine", session.get("engine")),
        "payload": payload.get("payload", session.get("payload", {})),
        "collaborators": payload.get("collaborators", session.get("collaborators", [])),
        "updated_at": now,
    })
    sessions[session_id] = session
    _dump_store(store)
    return session


def append_note(session_id: str, author: str, content: str) -> Dict[str, Any]:
    if not content.strip():
        raise ValueError("content cannot be empty")

    store = _load_store()
    sessions = store.setdefault("sessions", {})
    if session_id not in sessions:
        raise KeyError(f"Session '{session_id}' not found")

    session = sessions[session_id]
    note = {
        "id": uuid.uuid4().hex,
        "author": author or "anonymous",
        "content": content,
        "created_at": _utc_now(),
    }
    session.setdefault("notes", []).append(note)
    session["updated_at"] = note["created_at"]
    _dump_store(store)
    return note


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------


def _read_payload_from_stdin() -> Dict[str, Any]:
    data = sys.stdin.read().strip()
    if not data:
        return {}
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise SystemExit(json.dumps({"status": "error", "error": f"Invalid JSON payload: {exc}"}))


def _emit(result: Dict[str, Any], *, success: bool = True) -> None:
    payload = {"status": "ok" if success else "error", **result}
    json.dump(payload, sys.stdout, ensure_ascii=False)


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Session store CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("session_id")

    save_parser = subparsers.add_parser("save")
    save_parser.add_argument("session_id")

    note_parser = subparsers.add_parser("note")
    note_parser.add_argument("session_id")

    args = parser.parse_args(argv)

    try:
        if args.command == "list":
            sessions = list_sessions()
            _emit({"sessions": sessions})
        elif args.command == "get":
            session = get_session(args.session_id)
            if session is None:
                _emit({"error": f"Session '{args.session_id}' not found"}, success=False)
            else:
                _emit({"session": session})
        elif args.command == "save":
            payload = _read_payload_from_stdin()
            session = save_session(args.session_id, payload)
            _emit({"session": session})
        elif args.command == "note":
            payload = _read_payload_from_stdin()
            note = append_note(args.session_id, payload.get("author", ""), payload.get("content", ""))
            _emit({"note": note})
        else:
            _emit({"error": f"Unknown command '{args.command}'"}, success=False)
    except Exception as exc:  # pragma: no cover - defensive top-level safeguard
        _emit({"error": str(exc)}, success=False)


if __name__ == "__main__":
    main()
