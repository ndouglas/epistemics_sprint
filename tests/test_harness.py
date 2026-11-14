import asyncio
import json
from pathlib import Path

import pytest

from sprint import core, run
from sprint.core import ARMS, K, Task

TASK = Task("job", "Ana has a job offer.", "What should she weigh?", "consideration", "considerations")
MODEL = {"id": "fake", "thinking": {"type": "disabled"}, "effort": "medium", "price_in": 1.0, "price_out": 2.0}


@pytest.fixture
def arms_dir(tmp_path):
    """A copy of arms/ with the treatment prompt filled in."""
    for f in (core.ROOT / "arms").glob("*.md"):
        (tmp_path / f.name).write_text(f.read_text())
    (tmp_path / "properties.md").write_text("{vignette}\n{ask}\nName properties. Give {k} {item_plural}.")
    return tmp_path


def answer(shape, n=K, tag="x"):
    items = [f"{tag}{i}" for i in range(n)]
    if shape == "responses":
        return json.dumps({"responses": [{"text": i, "probability": 0.1} for i in items]})
    data = {"items": items}
    if shape == "notes":
        data = {"notes": "thinking", **data}
    if shape == "properties":
        data = {"properties": [{"name": "pay", "alternative": "half"}], **data}
    return json.dumps(data)


class Fake:
    """Answers from a queue of (text, stop_reason); records what it was asked."""

    def __init__(self, replies=None):
        self.replies = list(replies or [])
        self.calls = []

    async def ask(self, model, messages, schema):
        self.calls.append((json.loads(json.dumps(messages)), schema))
        shape = next(s for s, sch in core.SCHEMAS.items() if sch == schema)
        text, stop = self.replies.pop(0) if self.replies else (answer(shape), "end_turn")
        return run.Reply(text, stop, 10, 20, "fake")


def test_every_arm_has_a_schema_and_seven_arms():
    assert len(ARMS) == 7
    assert all(a.shape in core.SCHEMAS for a in ARMS.values())


def test_treatment_prompt_refuses_to_run_until_written(tmp_path):
    (tmp_path / "properties.md").write_text(f"{core.TODO_MARK}: write me")
    with pytest.raises(RuntimeError, match="properties.md"):
        core.first_prompt(ARMS["properties"], TASK, {}, tmp_path)


def test_prompts_carry_the_vignette_and_k(arms_dir):
    for arm in ARMS.values():
        draw = core.make_draw(arm, 0, "m", TASK.id, 0)
        text = core.first_prompt(arm, TASK, draw, arms_dir)
        assert "Ana has a job offer." in text and "{" not in text
        assert str(K) in text


def test_nudged_arm_is_the_plain_treatment_plus_three_dimensions(arms_dir):
    base = core.first_prompt(ARMS["properties"], TASK, {}, arms_dir)
    draw = core.make_draw(ARMS["properties_nudged"], 0, "m", TASK.id, 0)
    nudged = core.first_prompt(ARMS["properties_nudged"], TASK, draw, arms_dir)
    assert nudged.startswith(base)
    assert len(draw["dimensions"]) == len(set(draw["dimensions"])) == 3
    assert all(d in nudged for d in draw["dimensions"])


def test_random_word_arm_is_think_diverse_plus_one_line(arms_dir):
    base = core.first_prompt(ARMS["think_diverse"], TASK, {}, arms_dir).splitlines()
    draw = core.make_draw(ARMS["random_word"], 0, "m", TASK.id, 0)
    word = core.first_prompt(ARMS["random_word"], TASK, draw, arms_dir).splitlines()
    extra = [line for line in word if line not in base]
    assert extra == [f"Here is a random word to draw on for inspiration: {draw['word']}."]


def test_draws_repeat_for_a_seed_and_vary_across_samples():
    arm = ARMS["properties_nudged"]
    assert core.make_draw(arm, 1, "m", "t", 3) == core.make_draw(arm, 1, "m", "t", 3)
    draws = {tuple(core.make_draw(arm, 1, "m", "t", s)["dimensions"]) for s in range(10)}
    assert len(draws) > 5
    assert core.make_draw(ARMS["plain"], 1, "m", "t", 0) == {}


def test_parse_each_shape():
    for shape in core.SCHEMAS:
        parsed = core.parse_answer(shape, answer(shape))
        assert parsed["items"] == [f"x{i}" for i in range(K)]
    assert core.parse_answer("properties", answer("properties"))["properties"][0]["name"] == "pay"


def test_tasks_file_defaults_and_overrides(tmp_path):
    f = tmp_path / "t.toml"
    f.write_text(
        'ask = "A?"\nitem = "c"\nitem_plural = "cs"\n'
        '[[task]]\nid = "one"\nvignette = "V1"\n'
        '[[task]]\nid = "two"\nvignette = "V2"\nask = "B?"\ntype = "pair"\n'
    )
    one, two = core.load_tasks(f)
    assert (one.ask, two.ask, two.item) == ("A?", "B?", "c")
    assert (one.type, two.type) == ("one", "pair")
    assert core.load_tasks(core.ROOT / "tasks" / "control.toml")[0].id == "dragon-monster"


def test_what_else_scores_a_second_turn_after_a_fresh_plain_answer():
    fake = Fake([(answer("items", tag="a"), "end_turn"), (answer("items", tag="b"), "end_turn")])
    row = asyncio.run(run.one_sample(fake, "m", MODEL, TASK, ARMS["what_else"], 0, 0))
    assert row["status"] == "ok" and row["items"][0] == "b0"
    roles = [m["role"] for m in fake.calls[1][0]]
    assert roles == ["user", "assistant", "user"]
    assert fake.calls[1][0][1]["content"] == answer("items", tag="a")
    assert "What else?" in fake.calls[1][0][2]["content"]
    assert (row["input_tokens"], row["output_tokens"]) == (20, 40)  # both turns counted


def test_wrong_count_is_retried_then_recorded():
    fake = Fake([(answer("items", n=7), "end_turn"), (answer("items"), "end_turn")])
    row = asyncio.run(run.one_sample(fake, "m", MODEL, TASK, ARMS["plain"], 0, 0))
    assert (row["status"], row["attempts"]) == ("ok", 2)
    fake = Fake([(answer("items", n=9), "end_turn")] * 3)
    row = asyncio.run(run.one_sample(fake, "m", MODEL, TASK, ARMS["plain"], 0, 0))
    assert (row["status"], row["attempts"]) == ("bad_count", 3)


def test_refusal_is_recorded_not_retried():
    fake = Fake([("", "refusal")])
    row = asyncio.run(run.one_sample(fake, "m", MODEL, TASK, ARMS["plain"], 0, 0))
    assert row["status"] == "refusal" and len(fake.calls) == 1


def test_generate_writes_rows_and_resumes(tmp_path):
    out = tmp_path / "g.jsonl"
    arms = [ARMS["plain"], ARMS["think_diverse"]]
    first = asyncio.run(run.generate(Fake(), "m", MODEL, [TASK], arms, 3, out))
    assert first["ran"] == 6 and first["ok"] == 6
    again = asyncio.run(run.generate(Fake(), "m", MODEL, [TASK], arms, 4, out))
    assert (again["ran"], again["skipped"]) == (2, 6)
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == 8 and all(len(r["items"]) == K for r in rows)
    table = run.cost_table(out, {"m": MODEL})
    assert table[0] == ("m", "plain", 4, 40, 80, round(40 / 1e6 + 160 / 1e6, 4))
