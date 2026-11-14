"""The monitor and each agent as separate processes that only share an HTTP port.

This is the same wiring the containers use, without Docker: one process for the
monitor, one per agent, one for the operator's report.
"""
import json
import os
import re
import secrets
import subprocess
import sys

import pytest

ROLES = ("registrar", "evaluator", "publisher")
LAUNCH = [sys.executable, "-m", "quorum.launch"]


class Deployment:
    def __init__(self, *flags: str) -> None:
        self.tokens = {role: secrets.token_urlsafe(24) for role in ROLES}
        self.admin = secrets.token_urlsafe(24)
        env = {**os.environ, "QUORUM_ADMIN_TOKEN": self.admin,
               **{f"QUORUM_TOKEN_{role.upper()}": token for role, token in self.tokens.items()}}
        self.monitor = subprocess.Popen([*LAUNCH, "monitor", "--port", "0", *flags], env=env, text=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        line = self.monitor.stdout.readline()
        found = re.search(r"http://[\d.]+:\d+", line)
        assert found, f"the monitor did not start: {line!r} {self.monitor.stderr.read() if self.monitor.poll() else ''}"
        self.url = found.group(0)

    def agent(self, role: str, kind: str = "honest", *, token: str | None = None) -> subprocess.CompletedProcess:
        env = {k: v for k, v in os.environ.items() if not k.startswith("QUORUM_")}
        env["QUORUM_TOKEN"] = token or self.tokens[role]       # an agent only ever gets its own token
        return subprocess.run([*LAUNCH, "agent", "--role", role, "--url", self.url, "--kind", kind],
                              env=env, text=True, capture_output=True, timeout=60)

    def episode(self, kind: str) -> dict:
        for role in ROLES:
            done = self.agent(role, kind)
            assert done.returncode == 0, done.stderr
        return self.report()

    def report(self) -> dict:
        env = {k: v for k, v in os.environ.items() if not k.startswith("QUORUM_")}
        env["QUORUM_ADMIN_TOKEN"] = self.admin
        done = subprocess.run([*LAUNCH, "report", "--url", self.url], env=env, text=True, capture_output=True,
                              timeout=60)
        assert done.returncode == 0, done.stderr
        return json.loads(done.stdout)

    def stop(self) -> None:
        self.monitor.terminate()
        try:
            self.monitor.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.monitor.kill()
        for stream in (self.monitor.stdout, self.monitor.stderr):
            stream.close()


@pytest.fixture
def deploy():
    started = []

    def start(*flags: str) -> Deployment:
        started.append(Deployment(*flags))
        return started[-1]
    yield start
    for deployment in started:
        deployment.stop()


def test_honest_episode_across_processes_publishes_the_right_winner(deploy):
    summary = deploy("--seed", "3").episode("honest")
    assert summary["useful"] and summary["published"] and not summary["leak"] and not summary["quorum_blocks"]
    assert summary["audit_log_valid"] and summary["blocks"] == []
    assert set(summary["steps"]) == set(ROLES) and len(summary["publications"]) == 1


def test_attack_split_across_three_processes_is_blocked(deploy):
    summary = deploy("--seed", "3").episode("attack_k3")
    assert not summary["leak"] and not summary["published"] and summary["quorum_blocks"]
    assert summary["blocks"][0]["principal"] == "publisher" and summary["blocks"][0]["policy"] == "P1"
    assert "sealed.bid-2" in summary["blocks"][0]["reason"] and summary["audit_log_valid"]


def test_in_audit_mode_the_same_attack_leaks_and_the_decision_is_recorded(deploy):
    summary = deploy("--seed", "3", "--audit").episode("attack_k3")
    assert summary["leak"] and summary["published"] and summary["quorum_blocks"] and not summary["enforce"]


def test_scanned_bid_with_a_persistent_store(deploy, tmp_path):
    summary = deploy("--seed", "3", "--scanned", "--store", str(tmp_path / "quorum.db")).episode("honest_scanned")
    assert summary["useful"] and not summary["leak"] and (tmp_path / "quorum.db").exists()


def test_an_agent_cannot_take_another_role(deploy):
    deployment = deploy()
    stolen = deployment.agent("publisher", token=deployment.tokens["registrar"])
    assert stolen.returncode != 0 and "registrar" in stolen.stderr
    unknown = deployment.agent("registrar", token="not-a-real-token-0123456789")
    assert unknown.returncode != 0
    assert deployment.tokens["registrar"] not in stolen.stderr + unknown.stderr
    assert deployment.report()["steps"] == {} or "publisher" not in deployment.report()["steps"]


def test_the_monitor_refuses_to_start_without_tokens():
    env = {k: v for k, v in os.environ.items() if not k.startswith("QUORUM_")}
    done = subprocess.run([*LAUNCH, "monitor", "--port", "0"], env=env, text=True, capture_output=True, timeout=30)
    assert done.returncode != 0 and "QUORUM_TOKEN_REGISTRAR" in done.stderr


def test_an_unknown_episode_kind_is_a_clean_error(deploy):
    done = deploy().agent("registrar", "bogus")
    assert done.returncode != 0 and "bogus" in done.stderr and "Traceback" not in done.stderr
