"""Score a run: build one codebook per decision type, assign every item to a code,
and judge which codes could matter for each person. All of it is blind to arm
and model: the judge only ever sees item text.

    uv run python -m sprint.score code runs/main
    uv run python -m sprint.score judge runs/main --tasks tasks/decisions.toml
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
from collections import defaultdict
from pathlib import Path

from sprint.core import load_tasks
from sprint.run import load_env_file, load_models

JUDGE = "sonnet"
INDUCE_SAMPLE = 500  # items shown when the codebook is first drafted
BATCH = 30  # items per assignment call
MAX_TOKENS = 16000

SAME_RULE = (
    "Two items belong under the same consideration when they tell the person to weigh "
    "the same thing, even if the wording, the detail or the suggested next step differs. "
    "They belong under different considerations when someone who had already heard one "
    "would learn something new to weigh from the other."
)


def _obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


CODEBOOK_SCHEMA = _obj(
    {
        "considerations": {
            "type": "array",
            "items": _obj({"label": {"type": "string"}, "definition": {"type": "string"}}),
        }
    }
)
ASSIGN_SCHEMA = _obj(
    {
        "assignments": {
            "type": "array",
            "items": _obj({"item": {"type": "integer"}, "consideration": {"type": "integer"}}),
        }
    }
)
JUDGE_SCHEMA = _obj(
    {
        "ratings": {
            "type": "array",
            "items": _obj({"consideration": {"type": "integer"}, "could_change_choice": {"type": "boolean"}}),
        }
    }
)


class Judge:
    def __init__(self, concurrency: int = 8) -> None:
        import anthropic

        load_env_file()
        self.model = load_models()[JUDGE]
        self.client = anthropic.AsyncAnthropic(max_retries=6)
        self.gate = asyncio.Semaphore(concurrency)
        self.usage: dict[str, int] = defaultdict(int)

    async def ask(self, system: str, user: str, schema: dict) -> dict:
        async with self.gate:
            r = await self.client.messages.create(
                model=self.model["id"],
                max_tokens=MAX_TOKENS,
                thinking=self.model["thinking"],
                output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user}],
            )
        u = r.usage
        self.usage["input"] += u.input_tokens
        self.usage["output"] += u.output_tokens
        self.usage["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
        self.usage["cache_write"] += getattr(u, "cache_creation_input_tokens", 0) or 0
        if r.stop_reason != "end_turn":
            raise RuntimeError(f"judge stopped with {r.stop_reason}")
        return json.loads(next(b.text for b in r.content if b.type == "text"))


def load_items(run_dir: Path) -> list[dict]:
    """One record per generated item, with a stable id. Only ok rows count."""
    items = []
    for line in (run_dir / "generations.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["status"] != "ok":
            continue
        turns = [(row["arm"], row["items"])]
        if row.get("first_turn"):  # the plain answer that a "What else?" second turn followed
            turns.append((row["arm"] + "_t1", [t.strip() for t in json.loads(row["first_turn"])["items"]]))
        for arm, texts in turns:
          for idx, text in enumerate(texts):
            items.append(
                  {
                      "id": f"{row['model']}|{row['task']}|{arm}|{row['sample']}|{idx}",
                      "type": row["type"],
                      "task": row["task"],
                      "model": row["model"],
                      "arm": arm,
                      "sample": row["sample"],
                      "idx": idx,
                      "text": text,
                  }
              )
    return items


def by_type(items: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        out[it["type"]].append(it)
    return out


def codebook_text(codes: list[dict]) -> str:
    return "\n".join(f"{i}. {c['label']}: {c['definition']}" for i, c in enumerate(codes, 1))


def vignettes_text(tasks, dtype: str) -> str:
    return "\n\n".join(t.vignette for t in tasks if t.type == dtype)


# ---------- codebook ----------

INDUCE = """You are building a codebook of considerations for a kind of personal decision.

Below are sentences that advisers wrote for two different people facing this kind of \
decision. Each sentence names something the person should weigh. Many sentences say the \
same thing in different words.

Write the list of distinct considerations these sentences contain. {same_rule}

Keep each consideration at the level of one thing to weigh (for example "whether the \
stock options are likely to be worth anything"), not a broad theme ("money") and not a \
single sentence's exact detail. When you are unsure whether two points are the same \
consideration, keep them separate.

Write each consideration so it does not name either person or their particular figures. \
When sentences written for the two people raise the same kind of thing (a deadline to \
answer by, how stable the other party is, negotiating the terms), that is one \
consideration, not one per person. A consideration that only arises for one of them (a \
pension about to vest, say) is still one consideration, stated generally.

Give each a short label and a one-sentence definition. Cover every sentence.

The two people:

{vignettes}"""

EXTEND = """You are extending a codebook of considerations for a kind of personal decision. \
{same_rule}

The sentences in the message did not fit any consideration already in the codebook below. \
Write the additional distinct considerations they contain, each with a short label and a \
one-sentence definition, stated generally without naming a person or their figures. Do not repeat a consideration the codebook already has.

Codebook so far:
{codebook}"""


async def build_codebook(judge: Judge, dtype: str, items: list[dict], vignettes: str, seed: int, P: dict) -> list[dict]:
    rng = random.Random(f"{seed}:{dtype}:induce")
    sample = rng.sample(items, min(INDUCE_SAMPLE, len(items)))
    system = P["induce"].format(same_rule=SAME_RULE, vignettes=vignettes)
    user = "\n".join(f"- {it['text']}" for it in sample)
    data = await judge.ask(system, user, CODEBOOK_SCHEMA)
    return data["considerations"]


# ---------- assignment ----------

ASSIGN = """You are sorting sentences under a codebook of considerations for a kind of \
personal decision. {same_rule}

For each numbered sentence in the message, give the number of the one consideration it \
belongs under. If a sentence makes more than one point, use the point it leads with. If \
it fits no consideration in the codebook, give 0. Return one assignment per sentence.

Codebook:
{codebook}"""


async def assign_batch(judge: Judge, system: str, batch: list[dict], n_codes: int) -> dict[str, int]:
    user = "\n".join(f"{i}. {it['text']}" for i, it in enumerate(batch, 1))
    out: dict[str, int] = {}
    for _ in range(3):
        data = await judge.ask(system, user, ASSIGN_SCHEMA)
        for a in data["assignments"]:
            if 1 <= a["item"] <= len(batch) and 0 <= a["consideration"] <= n_codes:
                out[batch[a["item"] - 1]["id"]] = a["consideration"]
        if len(out) == len(batch):
            return out
    for it in batch:  # anything still missing counts as unassigned
        out.setdefault(it["id"], 0)
    return out


async def assign_all(judge: Judge, codes: list[dict], items: list[dict], seed: str, P: dict) -> dict[str, int]:
    system = P["assign"].format(same_rule=SAME_RULE, codebook=codebook_text(codes))
    order = items[:]
    random.Random(seed).shuffle(order)  # arms and models are mixed within every batch
    batches = [order[i : i + BATCH] for i in range(0, len(order), BATCH)]
    first, rest = batches[0], batches[1:]
    result = await assign_batch(judge, system, first, len(codes))  # warms the cache
    for part in await asyncio.gather(*(assign_batch(judge, system, b, len(codes)) for b in rest)):
        result.update(part)
    return result


async def code_type(judge: Judge, run_dir: Path, dtype: str, items: list[dict], vignettes: str, seed: int, P: dict | None = None) -> dict:
    P = P or CONSIDERATIONS
    out = run_dir / P["folder"] / f"{dtype}.json"
    if out.exists():  # codebook is fixed; sort any items that arrived since under it
        data = json.loads(out.read_text())
        new = [it for it in items if it["id"] not in data["assigned"]]
        if new:
            data["assigned"].update(await assign_all(judge, data["codes"], new, f"{seed}:{dtype}:late{len(data['assigned'])}", P))
            data["rounds"].append({"late_items": len(new), "unassigned": sum(1 for it in new if data["assigned"][it["id"]] == 0)})
            out.write_text(json.dumps(data, indent=1))
            print(dtype, data["rounds"][-1], flush=True)
        return data
    codes = await build_codebook(judge, dtype, items, vignettes, seed, P)
    assigned = await assign_all(judge, codes, items, f"{seed}:{dtype}:a1", P)
    rounds = [{"codes": len(codes), "unassigned": sum(1 for v in assigned.values() if v == 0)}]
    for r in range(2):  # extend the codebook with whatever fit nothing, at most twice
        left = [it for it in items if assigned[it["id"]] == 0]
        if len(left) <= max(5, len(items) // 200):
            break
        system = P["extend"].format(same_rule=SAME_RULE, codebook=codebook_text(codes))
        more = await judge.ask(system, "\n".join(f"- {it['text']}" for it in left[:600]), CODEBOOK_SCHEMA)
        codes = codes + more["considerations"]
        assigned.update(await assign_all(judge, codes, left, f"{seed}:{dtype}:a{r + 2}", P))
        rounds.append({"codes": len(codes), "unassigned": sum(1 for v in assigned.values() if v == 0)})
    data = {"type": dtype, "codes": codes, "assigned": assigned, "rounds": rounds}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1))
    print(dtype, rounds, flush=True)
    return data


# ---------- the property log (arms 6a and 6b) ----------

P_INDUCE = """Below are short descriptions of properties of a situation. Advisers were asked to \
name the properties of a person's decision that mattered, and these are the properties \
they named, for two different people facing the same kind of decision.

Write the list of distinct properties these descriptions name. Two descriptions name the \
same property when they pick out the same feature of the situation (the deadline, the \
size of the pay gap, who else is affected), whatever value or detail they attach to it. \
State each property generally, without naming either person or their figures; when both \
people's descriptions pick out the same kind of feature, that is one property. Give each \
a short label and a one-sentence definition. Cover every description.

The two people:

{vignettes}"""

P_EXTEND = """You are extending a list of properties of a kind of personal decision. The \
descriptions in the message did not fit any property already listed below. Write the \
additional distinct properties they name, each with a short label and a one-sentence \
definition, stated generally. Do not repeat a property already listed.

Properties so far:
{codebook}"""

P_ASSIGN = """You are sorting descriptions under a list of properties of a kind of personal \
decision. Two descriptions belong under the same property when they pick out the same \
feature of the situation, whatever value or detail they attach to it.

For each numbered description in the message, give the number of the one property it \
belongs under (the field is called "consideration"). If it fits none, give 0. Return one \
assignment per description.

Properties:
{codebook}"""

CONSIDERATIONS = {"induce": INDUCE, "extend": EXTEND, "assign": ASSIGN, "folder": "codes"}
PROPERTIES = {"induce": P_INDUCE, "extend": P_EXTEND, "assign": P_ASSIGN, "folder": "property_codes"}


def load_properties(run_dir: Path) -> list[dict]:
    """One record per property named in a 6a or 6b answer."""
    out = []
    for line in (run_dir / "generations.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["status"] != "ok" or not row.get("properties"):
            continue
        for idx, prop in enumerate(row["properties"]):
            out.append({"id": f"{row['model']}|{row['task']}|{row['arm']}|{row['sample']}|{idx}", "type": row["type"],
                        "task": row["task"], "model": row["model"], "arm": row["arm"], "sample": row["sample"],
                        "idx": idx, "text": prop["name"]})
    return out


# ---------- usefulness ----------

USEFUL = """A person is making a decision. Their situation:

{vignette}

Below is a numbered list of considerations someone might raise with them. For each one, \
answer one question: could weighing this plausibly change what this person chooses, or \
how they go about choosing? Answer no when the consideration does not apply to this \
person's situation, is too generic to bear on the choice, or could not move the decision \
either way. Judge each consideration on its own; whether it is obvious or unusual does \
not matter."""


async def judge_task(judge: Judge, vignette: str, entries: list[tuple[int, str]]) -> dict[int, bool]:
    system = USEFUL.format(vignette=vignette)
    user = "\n".join(f"{n}. {text}" for n, text in entries)
    out: dict[int, bool] = {}
    for _ in range(3):
        data = await judge.ask(system, user, JUDGE_SCHEMA)
        valid = {n for n, _ in entries}
        out.update({r["consideration"]: r["could_change_choice"] for r in data["ratings"] if r["consideration"] in valid})
        if len(out) == len(entries):
            break
    return out


ANCHOR = """A person is making a decision. Here is everything we were told about their situation:

{vignette}

Below is a numbered list of considerations an adviser raised. Sort each one:

- from a stated detail (true): the consideration is about a specific thing the description \
states, such as a figure, a deadline, a named circumstance or a person it mentions. Had the \
description left that detail out, the adviser would have had no reason to raise it.
- brought in (false): the description does not mention it. The adviser raised it from \
general knowledge of this kind of decision.

A consideration that applies general knowledge to a stated detail (what stock options are \
usually worth, when the description mentions stock options) is from a stated detail."""

ANCHOR_SCHEMA = _obj(
    {
        "ratings": {
            "type": "array",
            "items": _obj({"consideration": {"type": "integer"}, "from_stated_detail": {"type": "boolean"}}),
        }
    }
)


async def anchor_task(judge: Judge, vignette: str, entries: list[tuple[int, str]]) -> dict[int, bool]:
    system = ANCHOR.format(vignette=vignette)
    user = "\n".join(f"{n}. {text}" for n, text in entries)
    out: dict[int, bool] = {}
    for _ in range(3):
        data = await judge.ask(system, user, ANCHOR_SCHEMA)
        valid = {n for n, _ in entries}
        out.update({r["consideration"]: r["from_stated_detail"] for r in data["ratings"] if r["consideration"] in valid})
        if len(out) == len(entries):
            break
    return out


async def main_async(args) -> None:
    run_dir: Path = args.run_dir
    tasks = load_tasks(args.tasks)
    items = load_items(run_dir)
    judge = Judge(args.concurrency)
    if args.grain == "coarse":  # sensitivity check: merge when unsure, instead of split
        fine = "When you are unsure whether two points are the same \\\nconsideration, keep them separate."
        fine = fine.replace("\\\n", "")
        assert fine in CONSIDERATIONS["induce"]
        CONSIDERATIONS["induce"] = CONSIDERATIONS["induce"].replace(
            fine, "When you are unsure whether two points are the same consideration, treat them as one: "
            "closely related points (two angles on the same worry, or the same point with a different next step) "
            "belong under a single consideration.")
    groups = by_type(items)
    if args.only:
        groups = {k: v for k, v in groups.items() if k in args.only.split(",")}

    if args.cmd == "code":
        await asyncio.gather(
            *(code_type(judge, run_dir, d, its, vignettes_text(tasks, d), args.seed) for d, its in groups.items())
        )

    if args.cmd == "props":
        pgroups = by_type(load_properties(run_dir))
        await asyncio.gather(
            *(code_type(judge, run_dir, d, its, vignettes_text(tasks, d), args.seed, PROPERTIES) for d, its in pgroups.items())
        )

    if args.cmd == "anchor":
        out = run_dir / "anchored.json"
        anchored = json.loads(out.read_text()) if out.exists() else {}

        async def one_anchor(task) -> None:
            data = json.loads((run_dir / "codes" / f"{task.type}.json").read_text())
            used = sorted({data["assigned"][it["id"]] for it in groups[task.type] if it["task"] == task.id} - {0})
            have = anchored.get(task.id, {})
            used = [c for c in used if str(c) not in have]
            if not used:
                return
            entries = [(c, f"{data['codes'][c - 1]['label']}: {data['codes'][c - 1]['definition']}") for c in used]
            random.Random(f"{args.seed}:{task.id}:anchor:{len(have)}").shuffle(entries)
            ratings = await anchor_task(judge, task.vignette, entries)
            anchored[task.id] = {str(k): v for k, v in sorted(({int(k): v for k, v in have.items()} | ratings).items())}

        await asyncio.gather(*(one_anchor(t) for t in tasks if t.type in groups))
        out.write_text(json.dumps(anchored, indent=1))

    if args.cmd == "judge":
        out = run_dir / "useful.json"
        useful = json.loads(out.read_text()) if out.exists() else {}

        async def one(task) -> None:
            data = json.loads((run_dir / "codes" / f"{task.type}.json").read_text())
            used = sorted({data["assigned"][it["id"]] for it in groups[task.type] if it["task"] == task.id} - {0})
            have = useful.get(task.id, {})
            used = [c for c in used if str(c) not in have]  # only what hasn't been rated yet
            if not used:
                return
            entries = [(c, f"{data['codes'][c - 1]['label']}: {data['codes'][c - 1]['definition']}") for c in used]
            random.Random(f"{args.seed}:{task.id}:{len(have)}").shuffle(entries)
            ratings = await judge_task(judge, task.vignette, entries)
            merged = {int(k): v for k, v in have.items()} | ratings
            useful[task.id] = {str(k): v for k, v in sorted(merged.items())}

        await asyncio.gather(*(one(t) for t in tasks if t.type in groups))
        out.write_text(json.dumps(useful, indent=1))

    print(dict(judge.usage))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sprint.score")
    p.add_argument("cmd", choices=["code", "props", "judge", "anchor"])
    p.add_argument("run_dir", type=Path)
    p.add_argument("--tasks", type=Path, default=Path("tasks/decisions.toml"))
    p.add_argument("--only", help="comma-separated decision types")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--grain", choices=["fine", "coarse"], default="fine")
    p.add_argument("--concurrency", type=int, default=8)
    asyncio.run(main_async(p.parse_args(argv)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
