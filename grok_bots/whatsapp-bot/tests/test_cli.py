"""cli.py: die/ok/add_auth_args helpers."""
from __future__ import annotations

import argparse

import pytest

from _lib.cli import add_auth_args, die, ok


def test_die_prints_to_stderr_and_exits(capsys):
    with pytest.raises(SystemExit) as ei:
        die("bad args", 1)
    assert ei.value.code == 1
    captured = capsys.readouterr()
    assert "bad args" in captured.err
    assert captured.out == ""


def test_die_default_code_is_1():
    with pytest.raises(SystemExit) as ei:
        die("x")
    assert ei.value.code == 1


def test_ok_prints_to_stdout(capsys):
    ok("all good")
    assert capsys.readouterr().out.strip() == "all good"


def test_add_auth_args_adds_no_probe_flag():
    ap = argparse.ArgumentParser()
    add_auth_args(ap)
    assert ap.parse_args([]).no_probe is False
    assert ap.parse_args(["--no-probe"]).no_probe is True
