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

    @classmethod
    def new(cls, title: str) -> "Task":
        return cls(id=uuid.uuid4().hex[:12], title=title,
                   created_at=datetime.now().astimezone().isoformat())


@dataclass
class TaskStore:
    path: Path = field(default_factory=tasks_path)
    def __post_init__(self) -> None:
        self.inbox: list[Task] = []
        self.today: list[Task] = []
        self.completed: list[Task] = []
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
        except (ValueError, TypeError, KeyError, AttributeError, OSError):
            corrupt = self.path.with_suffix(".json.corrupt")
            os.replace(self.path, corrupt)
            self.inbox, self.today, self.completed = [], [], []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1,
                   "inbox": [asdict(t) for t in self.inbox],
                   "today": [asdict(t) for t in self.today],
                   "completed": [asdict(t) for t in self.completed]}
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        os.replace(tmp, self.path)

    # -- mutations --------------------------------------------------------

    def add(self, title: str, target: str) -> Task:
        task = Task.new(title)
        (self.today if target == "today" else self.inbox).append(task)
        self._save()
        return task

    def complete(self, task_id: str) -> None:
        for i, task in enumerate(self.today):
            if task.id == task_id:
                task.completed_at = datetime.now().astimezone().isoformat()
                self.completed.append(self.today.pop(i))
                self._save()
                return
        for i, task in enumerate(self.inbox):
            if task.id == task_id:
                task.completed_at = datetime.now().astimezone().isoformat()
                self.completed.append(self.inbox.pop(i))
                self._save()
                return

    def move(self, task_id: str) -> None:
        for i, task in enumerate(self.today):
            if task.id == task_id:
                self.inbox.append(self.today.pop(i))
                self._save()
                return
        for i, task in enumerate(self.inbox):
            if task.id == task_id:
                self.today.append(self.inbox.pop(i))
                self._save()
                return

    @property
    def today_count(self) -> int:
        return len(self.today)
