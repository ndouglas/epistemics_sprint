"""Missing-fact probes: candidates, the decisiveness check, and scoring answers.

    uv run python -m sprint.probes draft                 # GPT-5.5 drafts candidates from the vignette alone
    uv run python -m sprint.probes check runs/main       # forced choices: is each fact decisive or inert?
    uv run python -m sprint.probes decide runs/main      # -> probe_status.json
    uv run python -m sprint.probes score runs/main       # does each answer raise each missing fact?
    uv run python -m sprint.probes score runs/main --foreign   # negative control
    uv run python -m sprint.probes stated runs/main      # positive control: the fact stated outright

Candidates are written without sight of any generated answer or codebook: the
drafting model is shown only the vignette. Nathan edits tasks/probes.toml and it
is committed before anything is scored against it.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import tomllib
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

from sprint.core import ARMS, ROOT, load_tasks
from sprint.run import PROVIDERS, load_env_file, load_models, one_sample

CHECK_MODELS = ("haiku", "sonnet", "gpt")
N_CHECK = 10  # forced choices per model, probe and answer
# Thresholds for the decisiveness check, fixed before the check was run.
DECISIVE_SHIFT = 0.5  # the choice shares move by at least this much...
DECISIVE_MODELS = 2  # ...in at least this many of the three models
INERT_SHIFT = 0.1  # the shares move by no more than this in every model
CHOICES = ("a", "b", "other")
LABELS = ("asks", "mentions", "absent")
N_FOREIGN_ANSWERS = 300
N_FOREIGN_PROBES = 6
N_STATED = 2  # answers per model, probe and stated value in the positive control

DRAFT = """Here is everything we know about a person facing a decision:

{vignette}

List six things this description does NOT tell us that an adviser might want to know. \
For each, give the question to find out, and two plausible answers to it, each written \
as one sentence that could be added to the description as a plain fact.

- Three should be things where the two answers would point to different choices: learn \
one answer and the person should probably go one way, learn the other and they should \
probably go the other way.
- Three should be things an adviser might well raise, but where the answer, either way, \
would probably not change what the person should do.
- Among the six, two should be about the shape of the decision itself and not the \
details of the options: for example whether there is a third option, whether the \
deadline is really fixed, whether the choice can be undone, or whether it is this \
person's decision alone.

Do not repeat anything the description already states. Keep each answer concrete: \
figures and named terms. Use no calendar dates or years; give every time relative to now \
("in three weeks", "four years ago"), as the description does."""


def _obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


DRAFT_SCHEMA = _obj(
    {
        "facts": {
            "type": "array",
            "items": _obj(
                {
                    "question": {"type": "string"},
                    "answer_a": {"type": "string"},
                    "answer_b": {"type": "string"},
                    "expected": {"type": "string", "enum": ["changes the choice", "does not change the choice"]},
                    "about": {"type": "string", "enum": ["details", "shape of the decision"]},
                }
            ),
        }
    }
)


async def draft(tasks) -> dict:
    import openai

    client = openai.AsyncOpenAI(max_retries=5)
    model = load_models()["gpt"]

    async def one(task):
        r = await client.chat.completions.create(
            model=model["id"],
            messages=[{"role": "user", "content": DRAFT.format(vignette=task.vignette)}],
            reasoning_effort="none",
            response_format={"type": "json_schema", "json_schema": {"name": "facts", "strict": True, "schema": DRAFT_SCHEMA}},
        )
        return task.id, json.loads(r.choices[0].message.content)["facts"]

    return dict(await asyncio.gather(*(one(t) for t in tasks)))


def to_toml(tasks, drafted: dict) -> str:
    q = lambda s: json.dumps(s, ensure_ascii=False)
    out = [
        "# Missing-fact probes. Drafted by GPT-5.5 from the vignette alone (it saw no answers),",
        "# then edited by Nathan. Committed before any answer is scored against it.",
        "# Edit freely: reword, delete a [[probe]] block, or add your own. `expected` and `about`",
        "# are the drafter's guesses and are not used in scoring; decisiveness is measured.",
        "",
    ]
    for task in tasks:
        out += [f"# ---- {task.id}", "# " + task.vignette.replace("\n", " "), ""]
        for i, f in enumerate(drafted[task.id], 1):
            out += [
                "[[probe]]",
                f'id = "{task.id}-{i}"',
                f'task = "{task.id}"',
                f"question = {q(f['question'])}",
                f"answer_a = {q(f['answer_a'])}",
                f"answer_b = {q(f['answer_b'])}",
                f"expected = {q(f['expected'])}",
                f"about = {q(f['about'])}",
                'source = "gpt-5.5 draft"',
                "",
            ]
    return "\n".join(out)


# ---------- files ----------


def load_probes(path: Path | None = None) -> list[dict]:
    probes = tomllib.loads((path or ROOT / "tasks" / "probes.toml").read_text()).get("probe", [])
    ids = [p["id"] for p in probes]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate probe ids")
    return probes


def load_options(path: Path | None = None) -> dict[str, tuple[str, str]]:
    data = tomllib.loads((path or ROOT / "tasks" / "options.toml").read_text())
    return {task: (v["option_a"], v["option_b"]) for task, v in data.items()}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def load_answers(run_dir: Path) -> list[dict]:
    """One record per answer: its items, in order. The plain first turn that a
    "What else?" second turn followed counts as its own answer (arm what_else_t1)."""
    out = []
    for row in read_jsonl(run_dir / "generations.jsonl"):
        if row["status"] != "ok":
            continue
        turns = [(row["arm"], row["items"])]
        if row.get("first_turn"):
            turns.append((row["arm"] + "_t1", [t.strip() for t in json.loads(row["first_turn"])["items"]]))
        for arm, items in turns:
            out.append({"model": row["model"], "task": row["task"], "type": row["type"], "arm": arm,
                        "sample": row["sample"], "items": items})
    return out


def answer_key(a: dict) -> tuple:
    return (a["model"], a["task"], a["arm"], a["sample"])


# ---------- the decisiveness check ----------

CHOICE_SCHEMA = _obj({"choice": {"type": "string", "enum": ["A", "B", "C"]}})
TWO_WAY_SCHEMA = _obj({"choice": {"type": "string", "enum": ["A", "B"]}})


def choice_prompt(vignette: str, fact: str | None, shown_a: str, shown_b: str, allow_other: bool = True) -> str:
    lines = [vignette]
    if fact:
        lines += ["", fact]
    lines += ["", "Which should this person do?", f"A. {shown_a}", f"B. {shown_b}"]
    if allow_other:
        lines.append("C. Something else")
    lines.append("Answer with the letter only.")
    return "\n".join(lines)


def is_flipped(seed: int, model: str, probe: str, cond: str, sample: int) -> bool:
    """Whether option_b is shown as "A" for this sample, so position can't carry the result."""
    return random.Random(f"{seed}:{model}:{probe}:{cond}:{sample}").random() < 0.5


def map_choice(letter: str, flipped: bool) -> str:
    """The letter the model picked, back to a / b / other in the options file's order."""
    if letter == "C":
        return "other"
    first = letter == "A"
    return ("b" if first else "a") if flipped else ("a" if first else "b")


def check_jobs(probes: list[dict], tasks, models, n: int) -> list[dict]:
    """Every forced choice to make: each probe at each of its two answers, plus the bare vignette."""
    jobs = []
    for model in models:
        for task in tasks:
            jobs += [{"model": model, "task": task.id, "probe": f"{task.id}:bare", "cond": "bare", "sample": s, "fact": None}
                     for s in range(n)]
        for p in probes:
            for cond in ("a", "b"):
                jobs += [{"model": model, "task": p["task"], "probe": p["id"], "cond": cond, "sample": s,
                          "fact": p[f"answer_{cond}"]} for s in range(n)]
    return jobs


async def run_check(providers: dict, models: dict, probes: list[dict], tasks, options: dict, out: Path,
                    n: int = N_CHECK, seed: int = 0, concurrency: int = 8, allow_other: bool = True) -> dict:
    """Make the forced choices that aren't already in the file. `providers` maps model name to a provider.
    With allow_other off there is no "something else" exit: the model must pick one of the two options."""
    by_id = {t.id: t for t in tasks}
    done = {(r["model"], r["probe"], r["cond"], r["sample"]) for r in read_jsonl(out) if r["status"] == "ok"}
    jobs = [j for j in check_jobs(probes, tasks, list(providers), n)
            if (j["model"], j["probe"], j["cond"], j["sample"]) not in done]
    gate = asyncio.Semaphore(concurrency)
    counts: dict[str, int] = defaultdict(int)

    async def work(job: dict) -> None:
        flipped = is_flipped(seed, job["model"], job["probe"], job["cond"], job["sample"])
        opt_a, opt_b = options[job["task"]]
        shown = (opt_b, opt_a) if flipped else (opt_a, opt_b)
        prompt = choice_prompt(by_id[job["task"]].vignette, job["fact"], *shown, allow_other=allow_other)
        schema = CHOICE_SCHEMA if allow_other else TWO_WAY_SCHEMA
        row = {k: job[k] for k in ("model", "task", "probe", "cond", "sample")} | {"flipped": flipped, "allow_other": allow_other, "status": "error"}
        try:
            async with gate:
                reply = await providers[job["model"]].ask(models[job["model"]], [{"role": "user", "content": prompt}], schema)
            if reply.stop_reason != "end_turn":
                row["status"] = reply.stop_reason
            else:
                row["letter"] = json.loads(reply.text)["choice"]
                row["choice"] = map_choice(row["letter"], flipped)
                row["status"] = "ok"
        except Exception as exc:  # recorded, and retried on the next run
            row["error"] = f"{type(exc).__name__}: {exc}"
        append_jsonl(out, [row])
        counts[row["status"]] += 1

    await asyncio.gather(*(work(j) for j in jobs))
    return {"ran": len(jobs), "skipped": len(done), **counts}


def shares(choices: list[str]) -> dict[str, float]:
    count = Counter(choices)
    return {c: count[c] / len(choices) for c in CHOICES} if choices else {c: 0.0 for c in CHOICES}


def shift(sa: dict[str, float], sb: dict[str, float]) -> float:
    """Total variation distance between two choice-share vectors: 0 (same) to 1 (disjoint)."""
    return 0.5 * sum(abs(sa[c] - sb[c]) for c in CHOICES)


def status_of(shifts: list[float]) -> str:
    if sum(x >= DECISIVE_SHIFT for x in shifts) >= DECISIVE_MODELS:
        return "decisive"
    if all(x <= INERT_SHIFT for x in shifts):
        return "inert"
    return "middle"


def decide(rows: list[dict], probes: list[dict]) -> dict:
    """Per probe: each model's choice shares under answer A and answer B, the shift, and the status."""
    got: dict[tuple, list[str]] = defaultdict(list)
    for r in rows:
        if r["status"] == "ok":
            got[(r["probe"], r["model"], r["cond"])].append(r["choice"])
    models = sorted({m for _, m, _ in got})
    out = {"thresholds": {"decisive_shift": DECISIVE_SHIFT, "decisive_models": DECISIVE_MODELS, "inert_shift": INERT_SHIFT},
           "probes": {}, "bare": {}}
    for p in probes:
        per, shifts = {}, []
        for m in models:
            a, b = got.get((p["id"], m, "a"), []), got.get((p["id"], m, "b"), [])
            if not a or not b:
                continue
            per[m] = {"a": shares(a), "b": shares(b), "shift": round(shift(shares(a), shares(b)), 4), "n": [len(a), len(b)]}
            shifts.append(per[m]["shift"])
        if len(shifts) == len(CHECK_MODELS):
            out["probes"][p["id"]] = {"task": p["task"], "status": status_of(shifts), "models": per}
    for (probe, m, cond), choices in got.items():
        if cond == "bare":
            out["bare"].setdefault(probe.split(":")[0], {})[m] = shares(choices)
    return out


# ---------- does an answer raise the missing fact? ----------

RAISES = """An adviser gave a person a short list of things to weigh in a decision. Separately, \
we have a list of questions about things the person's description leaves out. For each \
question, say whether the adviser's list raises it.

- asks: some item tells the person to find this out, check it, confirm it or ask about it.
- mentions: some item raises this same matter and weighs it, but does not tell the person \
to find it out.
- absent: no item raises it.

The item must be about the same specific unknown as the question, not merely the same \
topic. Example, for someone deciding whether to adopt a dog: the question "Does the \
building's lease allow dogs over 40 pounds?" is raised by "Check your lease for pet size \
limits before you commit" (asks) and by "Your building may restrict large dogs" (mentions), \
but not by "Think about whether your apartment is big enough for a large dog", which is \
about housing too but concerns space, not what the lease permits (absent).

Give one rating per question. For asks or mentions, give the number of the item that \
does it; for absent, give 0. If several items qualify, prefer one that asks."""

RAISES_SCHEMA = _obj(
    {
        "ratings": {
            "type": "array",
            "items": _obj(
                {
                    "question": {"type": "integer"},
                    "label": {"type": "string", "enum": list(LABELS)},
                    "item": {"type": "integer"},
                }
            ),
        }
    }
)


def raises_prompt(vignette: str, items: list[str], questions: list[str]) -> str:
    return "\n".join(
        ["The person's situation as described:", "", vignette, "", "The adviser's list:"]
        + [f"{i}. {t}" for i, t in enumerate(items, 1)]
        + ["", "Questions about what the description leaves out:"]
        + [f"{i}. {q}" for i, q in enumerate(questions, 1)]
    )


async def judge_answer(judge, vignette: str, answer: dict, probes: list[dict], seed: str) -> list[dict]:
    """One judge call: this answer against these probes' questions, in shuffled order.
    The judge sees the items and the questions only: no arm, model or probe status."""
    order = probes[:]
    random.Random(seed).shuffle(order)
    got: dict[int, dict] = {}
    for _ in range(3):
        data = await judge.ask(RAISES, raises_prompt(vignette, answer["items"], [p["question"] for p in order]), RAISES_SCHEMA)
        for r in data["ratings"]:
            if 1 <= r["question"] <= len(order) and r["label"] in LABELS:
                item = r["item"] if r["label"] != "absent" and 1 <= r["item"] <= len(answer["items"]) else 0
                got[r["question"]] = {"label": r["label"], "item": item}
        if len(got) == len(order):
            break
    base = {k: answer[k] for k in ("model", "task", "arm", "sample")}
    return [base | {"probe": p["id"]} | got[i] for i, p in enumerate(order, 1) if i in got]


async def score_answers(judge, answers: list[dict], probes_for, vignette_of, out: Path, seed: int = 0) -> dict:
    """Score each answer against its probes, skipping answers already fully scored."""
    have: dict[tuple, set] = defaultdict(set)
    for r in read_jsonl(out):
        have[(r["model"], r["task"], r["arm"], r["sample"])].add(r["probe"])
    counts: dict[str, int] = defaultdict(int)

    async def work(answer: dict) -> None:
        probes = [p for p in probes_for(answer) if p["id"] not in have[answer_key(answer)]]
        if not probes:
            counts["skipped"] += 1
            return
        try:
            rows = await judge_answer(judge, vignette_of(answer), answer, probes, f"{seed}:{answer_key(answer)}")
        except Exception as exc:  # left out of the file, so the next run retries it
            counts[f"error {type(exc).__name__}"] += 1
            return
        append_jsonl(out, rows)
        counts["scored"] += 1

    await asyncio.gather(*(work(a) for a in answers))
    return dict(counts)


def foreign_plan(answers: list[dict], probes: list[dict], task_type: dict, seed: int = 0) -> list[tuple[dict, list[dict]]]:
    """Negative control: a seeded sample of answers, each paired with probes from another decision type."""
    rng = random.Random(f"{seed}:foreign")
    picked = rng.sample(answers, min(N_FOREIGN_ANSWERS, len(answers)))
    plan = []
    for a in picked:
        others = [p for p in probes if task_type[p["task"]] != a["type"]]
        plan.append((a, rng.sample(others, min(N_FOREIGN_PROBES, len(others)))))
    return plan


# ---------- positive control: the fact stated outright ----------


async def run_stated(providers: dict, models: dict, probes: list[dict], status: dict, tasks, out: Path,
                     n: int = N_STATED, seed: int = 0, concurrency: int = 8) -> dict:
    """Plain-prompt answers to the vignette with one probe's fact added, for decisive and inert probes."""
    by_id = {t.id: t for t in tasks}
    done = {(r["model"], r["probe"], r["cond"], r["sample"]) for r in read_jsonl(out) if r["status"] == "ok"}
    gate = asyncio.Semaphore(concurrency)
    counts: dict[str, int] = defaultdict(int)
    jobs = [(m, p, cond, s) for m in providers for p in probes
            if status["probes"].get(p["id"], {}).get("status") in ("decisive", "inert")
            for cond in ("a", "b") for s in range(n) if (m, p["id"], cond, s) not in done]

    async def work(m: str, p: dict, cond: str, s: int) -> None:
        base = by_id[p["task"]]
        task = replace(base, id=f"{p['id']}:{cond}", vignette=f"{base.vignette} {p[f'answer_{cond}']}")
        async with gate:
            row = await one_sample(providers[m], m, models[m], task, ARMS["plain"], s, seed)
        row |= {"probe": p["id"], "cond": cond, "base_task": base.id}
        append_jsonl(out, [row])
        counts[row["status"]] += 1

    await asyncio.gather(*(work(*j) for j in jobs))
    return {"ran": len(jobs), "skipped": len(done), **counts}


def stated_answers(path: Path) -> list[dict]:
    """Stated-fact answers in the shape score_answers expects; the task field carries probe and value."""
    return [{"model": r["model"], "task": r["task"], "type": r["type"], "arm": "stated", "sample": r["sample"],
             "items": r["items"], "probe": r["probe"], "base_task": r["base_task"]}
            for r in read_jsonl(path) if r["status"] == "ok"]


def make_providers(models: dict, names) -> dict:
    return {n: PROVIDERS[models[n].get("provider", "anthropic")]() for n in names}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sprint.probes")
    p.add_argument("cmd", choices=["draft", "check", "decide", "score", "stated"])
    p.add_argument("run_dir", type=Path, nargs="?")
    p.add_argument("--tasks", type=Path, default=Path("tasks/decisions.toml"))
    p.add_argument("--probes", type=Path, default=ROOT / "tasks" / "probes.toml")
    p.add_argument("--models", default=",".join(CHECK_MODELS))
    p.add_argument("--n", type=int)
    p.add_argument("--limit-tasks", type=int)
    p.add_argument("--limit-probes", type=int, help="probes per task")
    p.add_argument("--limit-answers", type=int)
    p.add_argument("--foreign", action="store_true")
    p.add_argument("--two-options", action="store_true", help="check: drop the 'something else' choice")
    p.add_argument("--check-file", default="probe_check.jsonl", help="check/decide: which file of forced choices")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--concurrency", type=int, default=8)
    args = p.parse_args(argv)
    load_env_file()
    tasks = load_tasks(args.tasks)
    if args.cmd == "draft":
        out = ROOT / "tasks" / "probes.toml"
        if out.exists():
            print(f"{out} exists; not overwriting")
            return 1
        out.write_text(to_toml(tasks, asyncio.run(draft(tasks))))
        print(f"wrote {out}")
        return 0

    if args.run_dir is None:
        p.error("run_dir is required")
    run_dir: Path = args.run_dir
    tasks = tasks[: args.limit_tasks]
    keep = {t.id for t in tasks}
    probes = [q for q in load_probes(args.probes) if q["task"] in keep]
    if args.limit_probes:
        seen: dict[str, int] = defaultdict(int)
        cut = []
        for q in probes:
            seen[q["task"]] += 1
            if seen[q["task"]] <= args.limit_probes:
                cut.append(q)
        probes = cut
    models = load_models()
    names = args.models.split(",")
    by_id = {t.id: t for t in tasks}
    task_type = {t.id: t.type for t in tasks}

    if args.cmd == "check":
        summary = asyncio.run(run_check(make_providers(models, names), models, probes, tasks, load_options(),
                                        run_dir / args.check_file, args.n or N_CHECK, args.seed, args.concurrency,
                                        allow_other=not args.two_options))
        print(json.dumps(summary))

    if args.cmd in ("check", "decide"):
        status = decide(read_jsonl(run_dir / args.check_file), probes)
        (run_dir / "probe_status.json").write_text(json.dumps(status, indent=1))
        print(dict(Counter(v["status"] for v in status["probes"].values())), f"-> {run_dir / 'probe_status.json'}")

    if args.cmd == "score":
        from sprint.score import Judge

        judge = Judge(args.concurrency)
        answers = [a for a in load_answers(run_dir) if a["task"] in keep][: args.limit_answers]
        if args.foreign:
            plan = {answer_key(a): ps for a, ps in foreign_plan(answers, probes, task_type, args.seed)}
            picked = [a for a in answers if answer_key(a) in plan]
            summary = asyncio.run(score_answers(judge, picked, lambda a: plan[answer_key(a)], lambda a: by_id[a["task"]].vignette,
                                                run_dir / "probe_hits_foreign.jsonl", args.seed))
        else:
            per_task: dict[str, list] = defaultdict(list)
            for q in probes:
                per_task[q["task"]].append(q)
            summary = asyncio.run(score_answers(judge, answers, lambda a: per_task[a["task"]], lambda a: by_id[a["task"]].vignette,
                                                run_dir / "probe_hits.jsonl", args.seed))
        print(summary, dict(judge.usage))

    if args.cmd == "stated":
        from sprint.score import Judge

        status = json.loads((run_dir / "probe_status.json").read_text())
        summary = asyncio.run(run_stated(make_providers(models, names), models, probes, status, tasks,
                                         run_dir / "stated.jsonl", args.n or N_STATED, args.seed, args.concurrency))
        print(json.dumps(summary))
        judge = Judge(args.concurrency)
        probe_by_id = {q["id"]: q for q in probes}
        answers = stated_answers(run_dir / "stated.jsonl")
        scored = asyncio.run(score_answers(judge, answers, lambda a: [probe_by_id[a["probe"]]],
                                           lambda a: by_id[a["base_task"]].vignette, run_dir / "probe_hits_stated.jsonl", args.seed))
        print(scored, dict(judge.usage))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
