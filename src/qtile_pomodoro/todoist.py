"""Todoist Unified API v1 client — stdlib only.

All reads and writes go through POST /api/v1/sync (see the architecture
doc): full-sync reads, batched writes with Command UUID idempotency and
temp_id create-remapping. No retry logic here — the SyncEngine's
persistent queue is the retry.
"""
import json
import urllib.error
import urllib.parse
from urllib.request import urlopen
from typing import Any

API_URL = "https://api.todoist.com/api/v1/sync"
TIMEOUT = 8


class TodoistError(Exception):
    """Transport, HTTP, or parse failure."""


class CommandError(TodoistError):
    """A command in an accepted batch failed server-side."""

    def __init__(self, uuid: str):
        super().__init__(f"command {uuid} failed")
        self.uuid = uuid


class TodoistClient:
    def __init__(self, token: str):
        self._token = token
    def _sync(self, fields: dict[str, str]) -> dict[str, Any]:
        data = "&".join(
            f"{k}={urllib.parse.quote(v)}" for k, v in fields.items()
        ).encode()
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read()
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise TodoistError(str(exc)) from exc
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError) as exc:
            raise TodoistError(f"bad response: {exc}") from exc
        if not isinstance(payload, dict):
            raise TodoistError("non-object response")
        return payload

    def read(self) -> dict[str, Any]:
        """Full sync read: items + user (inbox_project_id) + new token."""
        return self._sync({
            "sync_token": "*",
            "resource_types": json.dumps(["items", "user"]),
        })

    def send(self, commands: list[dict[str, Any]]):
        """Apply a command batch. Returns (temp_id_mapping, sync_status).

        Raises CommandError naming the first failed uuid after the batch
        is parsed — the server applies the rest of the batch regardless.
        """
        payload = self._sync({"commands": json.dumps(commands)})
        status = payload.get("sync_status") or {}
        for uuid, result in status.items():
            if result != "ok":
                raise CommandError(uuid)
        return payload.get("temp_id_mapping") or {}, status
