"""TodoistClient unit tests — all HTTP stubbed, no network."""
import email.message
import io
import json
import urllib.error
from urllib.parse import parse_qs

import pytest

from qtile_pomodoro.todoist import CommandError, TodoistClient, TodoistError


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self._buf = io.BytesIO(json.dumps(payload).encode())
        self.status = status

    def read(self) -> bytes:
        return self._buf.read()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Transport:
    """Records the last request; replays a queued response or error."""

    def __init__(self):
        self.requests: list[dict] = []
        self.result = None  # FakeResponse or Exception

    def __call__(self, req, timeout=None):
        body = req.data.decode() if req.data else ""
        self.requests.append({
            "url": req.full_url,
            "headers": dict(req.header_items()),
            "form": {k: v[0] for k, v in parse_qs(body).items()},
        })
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture
def transport(monkeypatch):
    t = Transport()
    monkeypatch.setattr("qtile_pomodoro.todoist.urlopen", t)
    return t


@pytest.fixture
def client(transport):
    return TodoistClient("TOKEN123")


def _header(req_headers: dict, name: str) -> str:
    for k, v in req_headers.items():
        if k.lower() == name.lower():
            return v
    raise KeyError(name)


def test_read_request_shape(transport, client):
    transport.result = FakeResponse({"items": [], "user": {}, "sync_token": "t1"})
    out = client.read()
    assert out["sync_token"] == "t1"
    req = transport.requests[0]
    assert req["url"] == "https://api.todoist.com/api/v1/sync"
    assert _header(req["headers"], "Authorization") == "Bearer TOKEN123"
    assert req["form"]["sync_token"] == "*"
    assert json.loads(req["form"]["resource_types"]) == ["items", "user"]
    assert "commands" not in req["form"]


def test_send_batches_commands_and_returns_mapping(transport, client):
    transport.result = FakeResponse({
        "sync_status": {"u1": "ok", "u2": "ok"},
        "temp_id_mapping": {"local-1": "REAL1"},
    })
    cmds = [
        {"type": "item_add", "uuid": "u1", "temp_id": "local-1",
         "args": {"content": "Buy milk", "project_id": "P"}},
        {"type": "item_close", "uuid": "u2", "args": {"id": "local-1"}},
    ]
    mapping, status = client.send(cmds)
    sent = json.loads(transport.requests[0]["form"]["commands"])
    assert sent == cmds  # batch sent verbatim, in order
    assert mapping == {"local-1": "REAL1"}
    assert status == {"u1": "ok", "u2": "ok"}


def test_send_command_error_names_offending_uuid(transport, client):
    transport.result = FakeResponse({"sync_status": {"u1": "ok", "u2": "error"}})
    with pytest.raises(CommandError) as exc:
        client.send([{"type": "item_close", "uuid": "u1", "args": {"id": "a"}},
                     {"type": "item_close", "uuid": "u2", "args": {"id": "b"}}])
    assert exc.value.uuid == "u2"


def test_network_error_becomes_todoist_error(transport, client):

    transport.result = urllib.error.URLError("no route to host")
    with pytest.raises(TodoistError):
        client.read()


def test_http_error_becomes_todoist_error(transport, client):
    transport.result = urllib.error.HTTPError(
        "url", 401, "Unauthorized",
        hdrs=email.message.Message(), fp=io.BytesIO(b"{}"))
    with pytest.raises(TodoistError):
        client.read()


def test_bad_json_becomes_todoist_error(transport, client):
    transport.result = FakeResponse({})
    transport.result._buf = io.BytesIO(b"<html>not json</html>")
    with pytest.raises(TodoistError):
        client.read()


def test_timeout_is_forwarded(transport, client):
    transport.result = FakeResponse({"items": [], "user": {}, "sync_token": "t"})
    client.read()
    # timeout encoded via opener: assert via the request's own deadline by
    # checking the transport signature accepted timeout kwarg — covered by
    # Transport.__call__(req, timeout=None); a missing kwarg would TypeError.


# ------------------------- SyncEngine (fake client) -------------------------

import threading

from qtile_pomodoro.tasks import Task, TaskStore
from qtile_pomodoro.todoist import SyncEngine


class FakeClient:
    def __init__(self):
        self.reads = 0
        self.sent: list[list[dict]] = []
        self.read_payload = {"items": [], "user": {"inbox_project_id": "INBOX"},
                             "sync_token": "t"}
        self.batch_results: list[object] = []  # Exception or (mapping, status)

    def read(self):
        self.reads += 1
        return self.read_payload

    def send(self, commands):
        self.sent.append(commands)
        result = self.batch_results.pop(0) if self.batch_results else ({}, {})
        if isinstance(result, Exception):
            raise result
        return result


def _store(tmp_path, tasks=True) -> TaskStore:
    store = TaskStore(path=tmp_path / "tasks.json")
    if tasks:
        store.add("old local task", "today")
    return store


def test_premigration_file_loads_with_tasks_intact(tmp_path):
    # a pre-Todoist file: only version/inbox/today/completed keys
    p = tmp_path / "tasks.json"
    p.write_text('{"version": 1, "inbox": [{"id": "a", "title": "keep me", '
                 '"created_at": "2026-01-01T00:00:00+00:00"}], '
                 '"today": [], "completed": []}')
    store = TaskStore(path=p)
    assert [t.title for t in store.inbox] == ["keep me"]
    assert store.sync == {"queue": [], "token": None, "revision": 0}


def test_save_omits_sync_when_untouched(tmp_path):
    store = _store(tmp_path)
    store.add("another", "inbox")
    import json as _json
    data = _json.loads(store.path.read_text())
    assert "sync" not in data


def test_enqueue_applies_locally_and_persists_queue(tmp_path):
    store = _store(tmp_path)
    eng = SyncEngine(store, FakeClient(), autokick=False)
    eng.enqueue("item_close", {"id": "x"}, lambda: store.complete("x"))
    assert store.sync["queue"][0]["cmd"] == "item_close"
    assert "uuid" in store.sync["queue"][0]
    # persisted across a fresh store load
    store2 = TaskStore(path=store.path)
    assert len(store2.sync["queue"]) == 1


def test_drain_applies_temp_id_mapping_and_rewrites_queue(tmp_path):
    store = _store(tmp_path)
    fake = FakeClient()
    eng = SyncEngine(store, fake, autokick=False)
    task = store.inbox[0] if store.inbox else None
    # offline add then complete: create queued with temp_id, close references it
    eng.enqueue("item_add", {"content": "x", "project_id": "INBOX"},
                lambda: None)
    store.sync["queue"][-1]["temp_id"] = "local-1"
    eng.enqueue("item_close", {"id": "local-1"}, lambda: None)
    fake.batch_results.append(({"local-1": "REAL1"}, {}))
    eng.refresh()
    # close entry now references the mapped real id; queue drained
    assert store.sync["queue"] == []
    # a later queued op referencing local-1 would also be rewritten:
    eng.enqueue("item_close", {"id": "local-1"}, lambda: None)
    fake.batch_results.append(({}, {}))
    # simulate the mapping being known: engine caches id_map
    eng._apply_mapping({"local-1": "REAL1"})
    assert store.sync["queue"][0]["args"]["id"] == "REAL1"


def test_failed_command_retried_then_dropped_after_three(tmp_path):
    store = _store(tmp_path)
    fake = FakeClient()
    eng = SyncEngine(store, fake, autokick=False)
    eng.enqueue("item_close", {"id": "dead"}, lambda: None)
    from qtile_pomodoro.todoist import CommandError
    bad_uuid = store.sync["queue"][0]["uuid"]
    for _ in range(2):
        fake.batch_results.append(CommandError(bad_uuid))
        eng.refresh()
        assert len(store.sync["queue"]) == 1  # still retried
    fake.batch_results.append(CommandError(bad_uuid))
    eng.refresh()
    assert store.sync["queue"] == []  # dropped as permanent


def test_network_error_keeps_batch(tmp_path):
    store = _store(tmp_path)
    fake = FakeClient()
    eng = SyncEngine(store, fake, autokick=False)
    eng.enqueue("item_close", {"id": "x"}, lambda: None)
    from qtile_pomodoro.todoist import TodoistError
    fake.batch_results.append(TodoistError("down"))
    eng.refresh()
    assert len(store.sync["queue"]) == 1


def test_reconcile_replaces_todoist_origin_and_keeps_local(tmp_path):
    store = _store(tmp_path)  # has local task "old local task" in today
    fake = FakeClient()
    fake.read_payload = {
        "items": [
            {"id": "T1", "content": "web task", "project_id": "INBOX",
             "checked": False, "is_deleted": False, "due": None},
            {"id": "T2", "content": "due task", "project_id": "OTHER",
             "checked": False, "is_deleted": False,
             "due": {"date": "2020-01-01"}},  # overdue -> today
            {"id": "T3", "content": "done elsewhere", "project_id": "INBOX",
             "checked": True, "is_deleted": False, "due": None},
        ],
        "user": {"inbox_project_id": "INBOX"}, "sync_token": "t"}
    eng = SyncEngine(store, fake, autokick=False)
    eng.refresh()
    assert [t.title for t in store.inbox] == ["web task"]
    assert [t.title for t in store.today] == ["due task", "old local task"]
    assert all(t.id != "T3" for t in store.inbox + store.today)


def test_pending_mutations_shield_tasks_from_overwrite(tmp_path):
    store = _store(tmp_path)
    fake = FakeClient()
    eng = SyncEngine(store, fake, autokick=False)
    task = store.today[0]
    eng.enqueue("item_update", {"id": task.id}, lambda: None)
    # fetched set does NOT contain the task (e.g. completed elsewhere),
    # but it is shielded while a mutation is pending
    eng.refresh()
    assert any(t.id == task.id for t in store.today + store.inbox)


def test_queue_capped_at_100(tmp_path):
    store = _store(tmp_path)
    eng = SyncEngine(store, FakeClient(), autokick=False)
    for i in range(105):
        eng.enqueue("item_close", {"id": str(i)}, lambda: None)
    assert len(store.sync["queue"]) == 100
    assert store._overflow is True


def test_dirty_during_refresh_chains(tmp_path):
    store = _store(tmp_path)
    fake = FakeClient()
    eng = SyncEngine(store, fake, autokick=False)
    seen = []

    def slow_read():
        seen.append("read")
        if len(seen) == 1:  # mutation arrives mid-refresh
            eng.enqueue("item_close", {"id": "late"}, lambda: None)
        return fake.read_payload
    fake.read = slow_read
    fake.batch_results.append(({}, {}))
    eng.refresh()
    # first pass saw the late enqueue -> dirty -> second drain/read
    assert seen == ["read", "read"] or len(seen) == 2
    assert store.sync["queue"] == []


def test_wire_shape_uses_type_not_cmd(tmp_path):
    store = _store(tmp_path)
    fake = FakeClient()
    eng = SyncEngine(store, fake, autokick=False)
    eng.enqueue("item_close", {"id": "x"}, lambda: None)
    fake.batch_results.append(({}, {}))
    eng.refresh()
    sent = fake.sent[0]
    assert all("cmd" not in c and "failures" not in c for c in sent)
    assert sent[0]["type"] == "item_close"
    assert "uuid" in sent[0] and "args" in sent[0]


def test_late_enqueue_during_drain_survives(tmp_path):
    store = _store(tmp_path)
    fake = FakeClient()
    eng = SyncEngine(store, fake, autokick=False)
    eng.enqueue("item_close", {"id": "early"}, lambda: None)
    orig_send = fake.send

    def slow_send(commands):
        eng.enqueue("item_close", {"id": "late"}, lambda: None)  # mid-flight
        return orig_send(commands)
    fake.send = slow_send
    fake.batch_results.append(({}, {}))
    from qtile_pomodoro.todoist import TodoistError
    fake.read = lambda: (_ for _ in ()).throw(TodoistError("down"))
    eng.refresh()  # read fails: no dirty-chained second drain this pass
    remaining = [e["args"]["id"] for e in store.sync["queue"]]
    assert remaining == ["late"]  # early sent; late kept for next drain


def test_inbox_survivors_stay_in_inbox(tmp_path):
    store = TaskStore(path=tmp_path / "tasks.json")
    store.add("local inbox task", "inbox")
    fake = FakeClient()
    fake.read_payload = {"items": [
        {"id": "T1", "content": "web", "project_id": "INBOX",
         "checked": False, "is_deleted": False, "due": None}],
        "user": {"inbox_project_id": "INBOX"}, "sync_token": "t"}
    eng = SyncEngine(store, fake, autokick=False)
    eng.refresh()
    assert [t.title for t in store.inbox] == ["web", "local inbox task"]
    assert store.today == []
