"""Todoist Unified API v1 client — stdlib only.

All reads and writes go through POST /api/v1/sync (see the architecture
doc): full-sync reads, batched writes with Command UUID idempotency and
temp_id create-remapping. No retry logic here — the SyncEngine's
persistent queue is the retry.
"""
import datetime
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from urllib.request import urlopen
from typing import Any

from qtile_pomodoro.tasks import Task

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

# ---------------------------- sync engine ---------------------------------

QUEUE_CAP = 100
DROP_AFTER_FAILURES = 3


class SyncEngine:
    """Cache <-> Todoist coherence: queue-as-retry, one worker thread.

    The lock guards in-memory cache/queue mutation and file writes only;
    it never spans a network call. `refresh()` is the synchronous worker
    body (testable); the widget layer runs it on a thread and receives
    completion via qtile.call_soon_threadsafe.
    """

    def __init__(self, store, client, autokick: bool = True):
        self.store = store
        self.client = client
        self._lock = threading.RLock()
        self._dirty = False
        self._running = False
        self._autokick = autokick  # False in tests driving refresh() directly
        self._done: list[tuple] = []  # (callback, qtile) awaiting completion

    # -- UI thread --------------------------------------------------------

    def enqueue(self, cmd: str, args: dict, local_apply, temp_id: str | None = None):
        """Apply a mutation locally, queue it for Todoist, persist, kick."""
        with self._lock:
            local_apply()
            if len(self.store.sync["queue"]) >= QUEUE_CAP:
                self.store._overflow = True  # newest dropped, indicator shows !
            else:
                entry = {"cmd": cmd, "uuid": uuid.uuid4().hex, "args": args}
                if temp_id is not None:
                    entry["temp_id"] = temp_id
                self.store.sync["queue"].append(entry)
            self._dirty = True
            self.store._save()
        if self._autokick:
            self.kick()  # write-through: mutations reach Todoist in-session

    def refresh_async(self, done=None, qtile=None) -> None:
        """Single-flight worker refresh; optional threadsafe completion."""
        with self._lock:
            if done is not None:
                self._done.append((done, qtile))
            if self._running:
                return  # running worker fires our callback at completion
            self._running = True

        def run() -> None:
            try:
                while True:
                    self.refresh()
                    with self._lock:  # atomic vs enqueue's set-then-kick;
                        if not self._dirty:  # also covers failed reads that
                            break  # skipped refresh's own chained check
            finally:
                with self._lock:
                    self._running = False
                    callbacks, self._done = self._done, []
            for cb, qt in callbacks:
                if qt is not None:
                    qt.call_soon_threadsafe(cb)
                else:
                    cb()

        threading.Thread(target=run, daemon=True).start()


    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self.store.sync["queue"])

    # -- worker -----------------------------------------------------------

    def refresh(self) -> None:
        """Drain the queue, full-sync read, reconcile. Idempotent."""
        with self._lock:
            self._dirty = False
            batch = list(self.store.sync["queue"])
        if batch:
            self._drain(batch)
        try:
            data = self.client.read()
        except TodoistError:
            return  # cache + queue stay usable; retry next refresh
        with self._lock:
            self._reconcile(data)
            self.store.sync["token"] = data.get("sync_token")
            self.store.sync["revision"] += 1
            self.store._save()
            chained = self._dirty
        if chained:
            self.refresh()

    @staticmethod
    def _wire(entry: dict) -> dict:
        """v1 wire shape: {type, uuid, [temp_id], args} — internal keys dropped."""
        cmd = {"type": entry["cmd"], "uuid": entry["uuid"],
               "args": entry["args"]}
        if "temp_id" in entry:
            cmd["temp_id"] = entry["temp_id"]
        return cmd

    def _drain(self, batch: list[dict]) -> None:
        try:
            mapping, _ = self.client.send([self._wire(e) for e in batch])
        except CommandError as exc:
            with self._lock:
                kept = []
                for entry in self.store.sync["queue"]:
                    if entry.get("uuid") == exc.uuid:
                        entry["failures"] = entry.get("failures", 0) + 1
                        if entry["failures"] < DROP_AFTER_FAILURES:
                            kept.append(entry)  # retry; uuid makes it safe
                    else:
                        kept.append(entry)  # server may have applied it;
                self.store.sync["queue"] = kept  # same-uuid resend is a no-op
                self.store._save()
            return
        except TodoistError:
            return  # network down: whole batch stays queued
        with self._lock:
            self._apply_mapping(mapping)
            sent = {e["uuid"] for e in batch}
            # keep only entries enqueued AFTER our snapshot (late UI writes)
            self.store.sync["queue"] = [e for e in self.store.sync["queue"]
                                        if e["uuid"] not in sent]
            self.store._save()


    def _apply_mapping(self, mapping: dict[str, str]) -> None:
        """temp_id -> real id: rewrite task ids and remaining queued args."""
        if not mapping:
            return
        self._id_map.update(mapping)
        for lst in (self.store.inbox, self.store.today, self.store.completed):
            for task in lst:
                if task.id in mapping:
                    task.id = mapping[task.id]
                    task.origin = "todoist"
        for entry in self.store.sync["queue"]:
            ref = entry["args"].get("id")
            if ref in mapping:
                entry["args"]["id"] = mapping[ref]

    def _reconcile(self, data: dict) -> None:
        """Set-replace todoist-origin tasks; local + pending survive."""
        store = self.store
        inbox_id = (data.get("user") or {}).get("inbox_project_id")
        today = datetime.date.today().isoformat()
        pending = {e["args"].get("id") for e in store.sync["queue"]}
        pending |= {e.get("temp_id") for e in store.sync["queue"]}
        pending.discard(None)
        new_inbox: list[Task] = []
        new_today: list[Task] = []
        for item in data.get("items", []):
            if item.get("checked") or item.get("is_deleted"):
                continue  # completed/deleted elsewhere: drop from lists
            task = Task(id=item["id"], title=item.get("content", ""),
                        created_at=item.get("added_at") or "",
                        origin="todoist")
            due = (item.get("due") or {}).get("date")
            if inbox_id and item.get("project_id") == inbox_id:
                new_inbox.append(task)
            elif due and due <= today:  # overdue included (Today view)
                new_today.append(task)
        fetched = {t.id for t in new_inbox + new_today}
        def survives(t: Task) -> bool:
            return (t.origin == "local" or t.id in pending) \
                and t.id not in fetched
        new_inbox.extend(t for t in store.inbox if survives(t))
        new_today.extend(t for t in store.today if survives(t))
        store.inbox = new_inbox
        store.today = new_today
