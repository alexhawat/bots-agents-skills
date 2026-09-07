"""headless_runner: subprocess error mapping to HeadlessRunnerError."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from _lib import headless_runner as hr
from _lib.errors import HeadlessRunnerError


def _fake_run(returncode: int, stdout: str, stderr: str = ""):
    def fake(cmd, cwd=None, env=None, capture_output=False, text=False):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    return fake


def test_nonzero_exit_with_json_stdout_raises_typed_error(monkeypatch):
    monkeypatch.setattr(hr.subprocess, "run", _fake_run(1, '{"ok": false, "error": "boom"}'))
    with pytest.raises(HeadlessRunnerError) as ei:
        hr.run_headless("list-chats", {"limit": 5})
    assert ei.value.exit_code == 1
    assert ei.value.payload == {"ok": False, "error": "boom"}
    assert "boom" in str(ei.value)


def test_nonzero_exit_with_empty_stdout_maps_to_error_payload(monkeypatch):
    monkeypatch.setattr(hr.subprocess, "run", _fake_run(2, ""))
    with pytest.raises(HeadlessRunnerError) as ei:
        hr.run_headless("list-chats")
    assert ei.value.exit_code == 2
    assert ei.value.payload["ok"] is False
    assert "empty stdout" in ei.value.payload["error"]


def test_nonzero_exit_with_non_json_stdout_maps_to_error_payload(monkeypatch):
    monkeypatch.setattr(hr.subprocess, "run", _fake_run(1, "node crashed\nnot json"))
    with pytest.raises(HeadlessRunnerError) as ei:
        hr.run_headless("list-chats")
    assert ei.value.payload["error"] == "non-json stdout"


def test_success_returns_parsed_last_json_line(monkeypatch):
    out = 'some log line\n{"ok": true, "chats": []}\n'
    monkeypatch.setattr(hr.subprocess, "run", _fake_run(0, out))
    assert hr.run_headless("list-chats") == {"ok": True, "chats": []}


def test_display_fallback_is_noted_on_stderr(monkeypatch, capsys):
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr(hr.subprocess, "run", _fake_run(0, '{"ok": true}'))
    hr.run_headless("list-chats")
    assert ":30" in capsys.readouterr().err


def test_display_is_not_forced_when_already_set(monkeypatch, capsys):
    seen = {}

    def fake(cmd, cwd=None, env=None, capture_output=False, text=False):
        seen["display"] = env.get("DISPLAY")
        return SimpleNamespace(returncode=0, stdout='{"ok": true}', stderr="")

    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.setattr(hr.subprocess, "run", fake)
    hr.run_headless("list-chats")
    assert seen["display"] == ":99"
    assert ":30" not in capsys.readouterr().err
