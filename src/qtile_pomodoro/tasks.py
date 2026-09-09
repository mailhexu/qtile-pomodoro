"""Pure-stdlib task store for the Qtile task overlay (no Qtile imports)."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


def tasks_path() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "qtile-pomodoro" / "tasks.json"


@dataclass
class Task:
    id: str
    title: str
    created_at: str
    completed_at: str | None = None
    origin: str = "local"  # "todoist" once synced (absent in old files)

    @classmethod
    def new(cls, title: str) -> "Task":
        return cls(id=uuid.uuid4().hex[:12], title=title,
                   created_at=datetime.now().astimezone().isoformat())


@dataclass
class UndoAction:
    """One reversible local mutation; never persisted (Story 7)."""
    kind: str    # "complete" | "move"
    task_id: str
    source: str  # list name before the mutation: "today" | "inbox"

@dataclass
class TaskStore:
    path: Path = field(default_factory=tasks_path)
    def __post_init__(self) -> None:
        self.inbox: list[Task] = []
        self.today: list[Task] = []
        self.completed: list[Task] = []
        self.sync: dict = {"queue": [], "token": None, "revision": 0}
        self._overflow = False
        self.engine = None  # SyncEngine when a Todoist token is configured
        self.reload()

    def reload(self) -> None:
        self.inbox, self.today, self.completed = [], [], []
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
            self.inbox = [Task(**t) for t in data.get("inbox", [])]
            self.today = [Task(**t) for t in data.get("today", [])]
            self.completed = [Task(**t) for t in data.get("completed", [])]
            sync = data.get("sync")
            if isinstance(sync, dict):  # additive; absent pre-migration
                self.sync = {"queue": list(sync.get("queue", [])),
                             "token": sync.get("token"),
                             "revision": int(sync.get("revision", 0))}
        except (ValueError, TypeError, KeyError, AttributeError, OSError):
            corrupt = self.path.with_suffix(".json.corrupt")
            os.replace(self.path, corrupt)
            self.inbox, self.today, self.completed = [], [], []
            self.sync = {"queue": [], "token": None, "revision": 0}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1,
                   "inbox": [asdict(t) for t in self.inbox],
                   "today": [asdict(t) for t in self.today],
                   "completed": [asdict(t) for t in self.completed]}
        if self.sync["queue"] or self.sync["token"] is not None:
            payload["sync"] = self.sync
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        os.replace(tmp, self.path)

    # -- mutations --------------------------------------------------------

    def add(self, title: str, target: str) -> Task:
        task = Task.new(title)
        dest = self.today if target == "today" else self.inbox
        args = {"content": title}
        if target == "today":
            args["due"] = {"string": "today"}
        if self.engine:
            self.engine.enqueue("item_add", args,
                                lambda: dest.append(task), temp_id=task.id)
        else:
            dest.append(task)
            self._save()
        return task

    def complete(self, task_id: str) -> UndoAction | None:
        action: UndoAction | None = None
        def _apply() -> None:
            nonlocal action
            for name in ("today", "inbox"):
                source = getattr(self, name)
                for i, task in enumerate(source):
                    if task.id == task_id:
                        task.completed_at = datetime.now().astimezone().isoformat()
                        self.completed.append(source.pop(i))
                        action = UndoAction("complete", task_id, name)
                        return
        if self.engine:
            self.engine.enqueue("item_close", {"id": task_id}, _apply)
            return None  # sync path: cloud undo out of scope (ADR-009)
        _apply()
        self._save()
        return action

    def move(self, task_id: str) -> UndoAction | None:
        to_today = any(t.id == task_id for t in self.inbox)
        action: UndoAction | None = None
        source, dest = ("inbox", "today") if to_today else ("today", "inbox")
        def _apply() -> None:
            nonlocal action
            src = getattr(self, source)
            for i, task in enumerate(src):
                if task.id == task_id:
                    getattr(self, dest).append(src.pop(i))
                    action = UndoAction("move", task_id, source)
                    return
        if self.engine:
            due = {"string": "today"} if to_today else None
            self.engine.enqueue("item_update", {"id": task_id, "due": due}, _apply)
            return None
        _apply()
        self._save()
        return action

    def undo(self, action: UndoAction) -> bool:
        """Reverse one local mutation; False when the state moved on."""
        if action.kind == "complete":
            for i, task in enumerate(self.completed):
                if task.id == action.task_id:
                    task.completed_at = None
                    getattr(self, action.source).append(self.completed.pop(i))
                    self._save()
                    return True
            return False
        for name in ("today", "inbox"):
            lst = getattr(self, name)
            for i, task in enumerate(lst):
                if task.id == action.task_id:
                    if name == action.source:
                        return False  # already home: action is stale
                    getattr(self, action.source).append(lst.pop(i))
                    self._save()
                    return True
        return False

    @property
    def today_count(self) -> int:
        return len(self.today)
