"""The Jev adapter feeds the unchanged monitors: same state, score = 10 * P(yes), cached."""
from quorum.eval import jev, monitors


def test_call_turns_the_probability_into_the_score_the_monitors_parse(tmp_path, monkeypatch):
    monkeypatch.setattr(jev, "CACHE", tmp_path)
    seen = []
    def post(body):
        seen.append(body)
        return {"model": "typesafe/jev-test", "answers": {"q": {"type": "noul", "noul": 0.37}}}
    steps = [{"tool": "open_bid", "args": {"ref": "bid-2"}, "result": 512345678}]
    score, reason = monitors.m1(steps, "jev", "evaluator", call=lambda m, msgs, **k: jev.call(m, msgs, post=post))
    assert score == 3.7 and "0.37" in reason
    state = seen[0]["state"]
    assert "open_bid" in state and "SCORE" not in state and monitors.SYSTEM in state
    assert seen[0]["questions"]["q"]["type"] == "noul"
    # second identical call comes from the cache, not the network
    monitors.m1(steps, "jev", "evaluator", call=lambda m, msgs, **k: jev.call(m, msgs, post=None))
    assert len(seen) == 1
