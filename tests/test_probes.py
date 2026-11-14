import asyncio
import json

from sprint import probe_analyze, probes
from sprint.core import Task
from sprint.label import kappa_cat
from sprint.run import Reply

TASKS = [Task("job-a", "Ana has an offer.", "What to weigh?", "c", "cs", "job"),
         Task("lease-a", "Bo has a lease.", "What to weigh?", "c", "cs", "lease")]
PROBES = [{"id": "job-a-1", "task": "job-a", "question": "Runway?", "answer_a": "Two years of cash.", "answer_b": "Two months of cash."},
          {"id": "lease-a-1", "task": "lease-a", "question": "Pets?", "answer_a": "Pets allowed.", "answer_b": "No pets."}]
OPTIONS = {"job-a": ("take it", "stay"), "lease-a": ("sign", "pass")}
MODELS = {m: {"id": m} for m in probes.CHECK_MODELS}


class Chooser:
    """Picks whichever shown letter names the option `want(prompt)` returns; records prompts."""

    def __init__(self, want):
        self.want, self.prompts = want, []

    async def ask(self, model, messages, schema):
        text = messages[0]["content"]
        self.prompts.append(text)
        target = self.want(text)
        letter = next((l for l in "AB" if f"{l}. {target}" in text), "C")
        return Reply(json.dumps({"choice": letter}), "end_turn", 5, 1, "fake")


def test_shares_shift_and_status():
    a = probes.shares(["a"] * 9 + ["b"])
    b = probes.shares(["b"] * 8 + ["other"] * 2)
    assert a == {"a": 0.9, "b": 0.1, "other": 0.0}
    assert abs(probes.shift(a, b) - 0.9) < 1e-9
    assert probes.shift(a, a) == 0
    assert probes.status_of([0.5, 0.9, 0.0]) == "decisive"
    assert probes.status_of([0.5, 0.4, 0.0]) == "middle"
    assert probes.status_of([0.1, 0.0, 0.05]) == "inert"
    assert probes.status_of([0.1, 0.0, 0.2]) == "middle"


def test_option_order_is_randomized_and_mapped_back():
    assert probes.map_choice("A", False) == "a" and probes.map_choice("B", False) == "b"
    assert probes.map_choice("A", True) == "b" and probes.map_choice("B", True) == "a"
    assert probes.map_choice("C", True) == "other"
    flips = [probes.is_flipped(0, "haiku", "p", "a", s) for s in range(40)]
    assert 5 < sum(flips) < 35 and flips == [probes.is_flipped(0, "haiku", "p", "a", s) for s in range(40)]


def test_check_recovers_the_choice_whatever_the_order_and_resumes(tmp_path):
    out = tmp_path / "probe_check.jsonl"
    # the fact about two months of cash sends everyone to "stay"; otherwise "take it" / "sign"
    want = lambda text: "stay" if "Two months" in text else ("take it" if "Ana" in text else "sign")
    fakes = {m: Chooser(want) for m in probes.CHECK_MODELS}
    first = asyncio.run(probes.run_check(fakes, MODELS, PROBES, TASKS, OPTIONS, out, n=6))
    assert first["ran"] == 3 * (2 * 6 + 2 * 2 * 6) and first["ok"] == first["ran"]
    rows = probes.read_jsonl(out)
    assert {r["flipped"] for r in rows} == {True, False}
    assert all(r["choice"] == "b" for r in rows if r["probe"] == "job-a-1" and r["cond"] == "b")
    assert all(r["choice"] == "a" for r in rows if r["cond"] == "bare")
    assert "Answer with the letter only." in fakes["haiku"].prompts[0] and "C. Something else" in fakes["haiku"].prompts[0]

    again = asyncio.run(probes.run_check(fakes, MODELS, PROBES, TASKS, OPTIONS, out, n=6))
    assert (again["ran"], again["skipped"]) == (0, first["ran"])
    more = asyncio.run(probes.run_check(fakes, MODELS, PROBES, TASKS, OPTIONS, out, n=7))
    assert more["ran"] == 3 * (2 + 2 * 2)

    status = probes.decide(probes.read_jsonl(out), PROBES)
    assert status["probes"]["job-a-1"]["status"] == "decisive"
    assert status["probes"]["job-a-1"]["models"]["gpt"]["shift"] == 1.0
    assert status["probes"]["lease-a-1"]["status"] == "inert"
    assert status["bare"]["job-a"]["sonnet"]["a"] == 1.0


class FakeJudge:
    def __init__(self, label_for):
        self.label_for, self.users = label_for, []

    async def ask(self, system, user, schema):
        self.users.append(user)
        qs = user.split("leaves out:\n")[1].splitlines()
        return {"ratings": [{"question": i, "label": self.label_for(q), "item": 2} for i, q in enumerate(qs, 1)]}


def test_score_writes_one_row_per_answer_and_probe_and_resumes(tmp_path):
    out = tmp_path / "hits.jsonl"
    answers = [{"model": "haiku", "task": "job-a", "type": "job", "arm": "plain", "sample": s, "items": ["x", "y"]} for s in range(3)]
    per_task = {"job-a": [PROBES[0], dict(PROBES[0], id="job-a-2", question="Vesting?")]}
    judge = FakeJudge(lambda q: "asks" if "Runway" in q else "absent")
    run = lambda: asyncio.run(probes.score_answers(judge, answers, lambda a: per_task[a["task"]], lambda a: "V", out))
    assert run() == {"scored": 3}
    rows = probes.read_jsonl(out)
    assert len(rows) == 6
    assert {(r["probe"], r["label"], r["item"]) for r in rows} == {("job-a-1", "asks", 2), ("job-a-2", "absent", 0)}
    assert "haiku" not in judge.users[0] and "plain" not in judge.users[0]  # the judge never sees model or arm
    assert run() == {"skipped": 3}


def test_hit_rate_arithmetic(tmp_path):
    cls = {"job-a-1": "decisive", "job-a-2": "inert", "lease-a-1": "decisive", "lease-a-2": "inert"}
    (tmp_path / "probe_status.json").write_text(json.dumps({"probes": {p: {"status": s} for p, s in cls.items()}}))
    labels = {  # per probe: labels across four plain answers
        "job-a-1": ["asks", "mentions", "absent", "absent"],  # 2/4
        "job-a-2": ["absent", "absent", "absent", "mentions"],  # 1/4
        "lease-a-1": ["asks", "asks", "asks", "absent"],  # 3/4
        "lease-a-2": ["absent"] * 4,  # 0/4
    }
    rows = [{"model": "haiku", "task": p.rsplit("-", 1)[0], "arm": "plain", "sample": s, "probe": p, "label": l, "item": 0}
            for p, ls in labels.items() for s, l in enumerate(ls)]
    # a two-turn pair for one sample: the second turn asks what the first turn missed
    rows += [{"model": "haiku", "task": "job-a", "arm": "what_else_t1", "sample": 0, "probe": "job-a-1", "label": "absent", "item": 0},
             {"model": "haiku", "task": "job-a", "arm": "what_else", "sample": 0, "probe": "job-a-1", "label": "asks", "item": 3}]
    (tmp_path / "probe_hits.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    all_probes = [{"id": p, "task": p.rsplit("-", 1)[0], "question": p, "about": "details"} for p in cls]
    r = probe_analyze.analyze(tmp_path, TASKS, all_probes)
    pooled = r["plain_pooled"]
    assert abs(pooled["decisive"][0] - (0.5 + 0.75) / 2) < 1e-9
    assert abs(pooled["inert"][0] - (0.25 + 0.0) / 2) < 1e-9
    assert abs(pooled["decisive_minus_inert"][0] - 0.5) < 1e-9
    assert abs(pooled["decisive_asks"][0] - (0.25 + 0.75) / 2) < 1e-9
    assert r["by_arm"][probe_analyze.COMBINED]["decisive"][0] == 1.0
    assert r["never_raised_plain"] == [] and r["per_probe"]["lease-a-2"]["plain"] == [0, 4]
    assert r["n_probes"] == {"decisive": 2, "inert": 2}


def test_kappa_for_three_labels():
    same = [("asks", "asks"), ("mentions", "mentions"), ("absent", "absent")]
    assert kappa_cat(same) == 1.0
    assert abs(kappa_cat(same + [("asks", "absent"), ("absent", "asks")])) < 1.0
