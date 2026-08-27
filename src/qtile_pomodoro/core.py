from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import socket
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import tomllib

DEFAULTS = {"focus_minutes": 25, "short_break_minutes": 5, "long_break_minutes": 15, "long_break_after": 4}


def config_path() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "qtile-pomodoro" / "config.toml"


def data_path() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "qtile-pomodoro" / "timer.sqlite3"


def socket_path() -> Path:
    return Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / f"qtile-pomodoro-{os.getuid()}.sock"


def remove_stale_socket(path: Path) -> None:
    if not path.exists():
        return
    client = socket.socket(socket.AF_UNIX)
    try:
        client.settimeout(0.1)
        client.connect(str(path))
    except OSError:
        path.unlink(missing_ok=True)
    else:
        raise RuntimeError(f"Timer Service already listens on {path}")
    finally:
        client.close()


def load_config() -> dict[str, int]:
    path = config_path()
    if not path.exists():
        return DEFAULTS.copy()
    with path.open("rb") as file:
        values = {**DEFAULTS, **tomllib.load(file).get("timer", {})}
    for name, value in values.items():
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"timer.{name} must be a positive whole number")
    return values


@dataclass
class State:
    phase: str = "focus"
    status: str = "idle"
    end_at: float | None = None
    remaining: int = DEFAULTS["focus_minutes"] * 60
    completed_in_cycle: int = 0


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS sessions (completed_at TEXT NOT NULL, seconds INTEGER NOT NULL)")
        self.db.commit()

    def load(self, defaults: dict[str, int]) -> State:
        row = self.db.execute("SELECT payload FROM state WHERE id=1").fetchone()
        if row is None:
            return State(remaining=defaults["focus_minutes"] * 60)
        return State(**json.loads(row["payload"]))

    def save(self, state: State) -> None:
        self.db.execute("INSERT INTO state(id,payload) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (json.dumps(asdict(state)),))
        self.db.commit()

    def complete_focus(self, seconds: int) -> None:
        self.db.execute("INSERT INTO sessions(completed_at,seconds) VALUES(?,?)", (datetime.now().astimezone().isoformat(), seconds))
        self.db.commit()

    def report(self) -> dict[str, Any]:
        rows = self.db.execute("SELECT completed_at, seconds FROM sessions ORDER BY completed_at DESC").fetchall()
        now = datetime.now().astimezone()
        day = week = 0
        history = []
        for row in rows:
            stamp = datetime.fromisoformat(row["completed_at"])
            minutes = row["seconds"] // 60
            history.append({"completed_at": row["completed_at"], "minutes": minutes})
            if stamp.date() == now.date(): day += minutes
            if stamp.isocalendar()[:2] == now.isocalendar()[:2]: week += minutes
        return {"today_minutes": day, "week_minutes": week, "history": history}


class Timer:
    def __init__(self):
        self.config = load_config()
        self.store = Store(data_path())
        self.state = self.store.load(self.config)
        self.recover()

    def duration(self, phase: str) -> int:
        return self.config[{"focus": "focus_minutes", "short_break": "short_break_minutes", "long_break": "long_break_minutes"}[phase]] * 60

    def recover(self) -> None:
        if self.state.status == "running" and self.state.end_at and self.state.end_at <= time.time():
            self.finish(recovered=True)
        elif self.state.status == "running" and self.state.end_at:
            self.state.remaining = max(0, round(self.state.end_at - time.time()))
        self.store.save(self.state)

    def notify(self, title: str, body: str) -> None:
        try:
            subprocess.Popen(["notify-send", "--app-name=Qtile Pomodoro", title, body], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass

    def finish(self, recovered: bool = False) -> None:
        if self.state.phase == "focus":
            self.store.complete_focus(self.duration("focus"))
            self.state.completed_in_cycle += 1
            self.state.phase = "long_break" if self.state.completed_in_cycle % self.config["long_break_after"] == 0 else "short_break"
            self.state.status = "running"
            self.state.remaining = self.duration(self.state.phase)
            self.state.end_at = time.time() + self.state.remaining
            self.notify("Focus complete", "Break started")
        else:
            self.state.phase = "focus"
            self.state.status = "resume"
            self.state.remaining = self.duration("focus")
            self.state.end_at = None
            self.notify("Break complete", "Press Space to start work")
        self.store.save(self.state)

    def command(self, name: str) -> dict[str, Any]:
        now = time.time()
        if self.state.status == "running" and self.state.end_at and now >= self.state.end_at:
            self.finish()
        if name == "start":
            if self.state.status != "running":
                self.state.status = "running"; self.state.end_at = now + self.state.remaining
        elif name == "pause" and self.state.status == "running":
            self.state.remaining = max(0, round((self.state.end_at or now) - now)); self.state.status = "paused"; self.state.end_at = None
        elif name == "reset":
            if self.state.phase == "focus":
                self.state.status = "idle"; self.state.remaining = self.duration("focus")
            else:
                self.state.phase = "focus"; self.state.status = "resume"; self.state.remaining = self.duration("focus")
            self.state.end_at = None
        elif name == "skip" and self.state.phase != "focus":
            self.state.phase = "focus"; self.state.status = "running"; self.state.remaining = self.duration("focus"); self.state.end_at = now + self.state.remaining
        elif name == "reload":
            self.config = load_config()
        self.store.save(self.state)
        return self.status()

    def status(self) -> dict[str, Any]:
        if self.state.status == "running" and self.state.end_at:
            self.state.remaining = max(0, round(self.state.end_at - time.time()))
        result = asdict(self.state)
        result["long_break_after"] = self.config["long_break_after"]
        result["overlay"] = self.state.status == "running" and self.state.phase != "focus"
        return result


async def serve() -> None:
    timer = Timer(); path = socket_path(); path.parent.mkdir(parents=True, exist_ok=True)
    remove_stale_socket(path)
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            request = json.loads((await reader.readline()).decode())
            if request["command"] == "stats": response = timer.store.report()
            else: response = timer.command(request.get("command", "status")) if request.get("command") != "status" else timer.status()
            writer.write((json.dumps({"ok": True, "result": response}) + "\n").encode()); await writer.drain()
        except Exception as error:
            writer.write((json.dumps({"ok": False, "error": str(error)}) + "\n").encode())
        finally:
            writer.close(); await writer.wait_closed()
    server = await asyncio.start_unix_server(handle, path)
    print(f"qtile-pomodoro listening on {path}", flush=True)
    async def tick() -> None:
        while True:
            timer.command("status")
            await asyncio.sleep(1)
    ticker = asyncio.create_task(tick())
    try:
        async with server: await server.serve_forever()
    finally:
        ticker.cancel()
        path.unlink(missing_ok=True)
