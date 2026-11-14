"""Turn a coded run into the numbers, the table and the figures.

    uv run python -m sprint.analyze runs/main

Every answer becomes the set of considerations (codes) it contains. An item that
fit no code counts as its own one-off consideration: distinct from everything,
never shared, never rated useful. The unit of analysis is the decision type;
intervals are bootstrap intervals over the eight types.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from sprint.core import ARMS, K, load_tasks
from sprint.score import load_items

FIX_MODEL = "haiku"
BOOT = 10000


def load(run_dir: Path, tasks):
    codes = {p.stem: json.loads(p.read_text()) for p in (run_dir / "codes").glob("*.json")}
    useful = json.loads((run_dir / "useful.json").read_text()) if (run_dir / "useful.json").exists() else {}
    answers: dict[tuple, set] = defaultdict(set)  # (model, task, arm, sample) -> codes
    unassigned = total = 0
    for it in load_items(run_dir):
        if it["type"] not in codes:
            continue
        c = codes[it["type"]]["assigned"][it["id"]]
        total += 1
        if c == 0:
            unassigned += 1
            c = "x:" + it["id"]
        answers[(it["model"], it["task"], it["arm"], it["sample"])].add(c)
    tokens = defaultdict(list)
    for line in (run_dir / "generations.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["status"] == "ok":
            tokens[(r["model"], r["arm"])].append(r["output_tokens"])
    return codes, useful, answers, {"items": total, "unassigned": unassigned}, tokens


def samples(answers, model, task, arm) -> list[set]:
    return [s for (m, t, a, _), s in sorted(answers.items(), key=lambda kv: kv[0][3]) if (m, t, a) == (model, task, arm)]


def within(sets: list[set]) -> float:
    return mean(len(a & b) for a, b in itertools.combinations(sets, 2))


def across(xs: list[set], ys: list[set]) -> float:
    return mean(len(a & b) for a in xs for b in ys)


def boot(values: list[float], seed: int = 0) -> tuple[float, float, float]:
    """Mean over decision types with a 95% bootstrap interval over types."""
    rng = random.Random(seed)
    n = len(values)
    means = sorted(mean(rng.choices(values, k=n)) for _ in range(BOOT))
    return mean(values), means[int(0.025 * BOOT)], means[int(0.975 * BOOT)]


def saturation(sets: list[set], perms: int = 200, seed: int = 0) -> list[float]:
    rng = random.Random(seed)
    totals = [0.0] * len(sets)
    for _ in range(perms):
        order = sets[:]
        rng.shuffle(order)
        seen: set = set()
        for i, s in enumerate(order):
            seen |= s
            totals[i] += len(seen)
    return [t / perms for t in totals]


def analyze(run_dir: Path, tasks) -> dict:
    codes, useful, answers, coverage, tokens = load(run_dir, tasks)
    types = [d for d in dict.fromkeys(t.type for t in tasks) if d in codes]
    pair = {d: [t.id for t in tasks if t.type == d] for d in types}
    models = sorted({k[0] for k in answers})
    out: dict = {"coverage": coverage, "types": types, "models": models,
                 "codebook_sizes": {d: len(codes[d]["codes"]) for d in types}}

    def per_type(fn) -> list[float]:
        return [fn(d) for d in types]

    # ---- the collapse, plain prompt ----
    collapse = {}
    for m in models:
        if not samples(answers, m, pair[types[0]][0], "plain"):
            continue
        collapse[m] = {
            "distinct_per_answer": boot(per_type(lambda d: mean(len(s) for t in pair[d] for s in samples(answers, m, t, "plain")))),
            "same_person": boot(per_type(lambda d: mean(within(samples(answers, m, t, "plain")) for t in pair[d]))),
            "two_people": boot(per_type(lambda d: across(*(samples(answers, m, t, "plain") for t in pair[d])))),
            "distinct_in_10": boot(per_type(lambda d: mean(len(set().union(*samples(answers, m, t, "plain"))) for t in pair[d]))),
            "saturation": [mean(col) for col in zip(*(saturation(samples(answers, m, t, "plain")) for d in types for t in pair[d]))],
        }
    plain_models = list(collapse)
    collapse["cross_model"] = {
        f"{a}|{b}": boot(per_type(lambda d: mean(across(samples(answers, a, t, "plain"), samples(answers, b, t, "plain")) for t in pair[d])))
        for a, b in itertools.combinations(plain_models, 2)
    }
    out["collapse"] = collapse

    # ---- fixes table ----
    obvious = {}
    for d in types:
        for t in pair[d]:
            sets = samples(answers, FIX_MODEL, t, "plain")
            count = Counter(c for s in sets for c in s)
            obvious[t] = {c for c, n in count.items() if n >= len(sets) / 2}
    out["obvious_sizes"] = boot(per_type(lambda d: mean(len(obvious[t]) for t in pair[d])))

    # Leave-one-out obvious sets. A plain answer helped define the set it would be scored
    # against, which flatters plain. So plain answer i is scored against the set built from
    # the other nine, and every other arm's answer against each of those ten sets in turn.
    loo = {}
    for d in types:
        for t in pair[d]:
            sets = samples(answers, FIX_MODEL, t, "plain")
            loo[t] = []
            for i in range(len(sets)):
                rest = sets[:i] + sets[i + 1 :]
                count = Counter(c for s in rest for c in s)
                loo[t].append({c for c, n in count.items() if n >= len(rest) / 2})

    def is_useful(t: str, c) -> bool:
        return useful.get(t, {}).get(str(c), False)

    def good(t: str, c) -> bool:  # for the across-ten measures: useful and not in the full obvious set
        return is_useful(t, c) and c not in obvious[t]

    def scored(t: str, arm: str, fn) -> float:
        """Mean over an arm's answers of fn(answer, obvious set), with held-out sets."""
        sets = samples(answers, FIX_MODEL, t, arm)
        if arm == "plain":
            return mean(fn(s, loo[t][i]) for i, s in enumerate(sets))
        return mean(fn(s, o) for s in sets for o in loo[t])

    rows = {}
    measures = {
        "distinct_in_10": lambda arm: lambda d: mean(len(set().union(*samples(answers, FIX_MODEL, t, arm))) for t in pair[d]),
        "useful_in_10": lambda arm: lambda d: mean(sum(is_useful(t, c) for c in set().union(*samples(answers, FIX_MODEL, t, arm))) for t in pair[d]),
        "good_in_10": lambda arm: lambda d: mean(sum(good(t, c) for c in set().union(*samples(answers, FIX_MODEL, t, arm))) for t in pair[d]),
        "good_per_answer": lambda arm: lambda d: mean(scored(t, arm, lambda s, o, t=t: sum(is_useful(t, c) and c not in o for c in s)) for t in pair[d]),
        "obvious_per_answer": lambda arm: lambda d: mean(scored(t, arm, lambda s, o: len(s & o)) for t in pair[d]),
        "distinct_per_answer": lambda arm: lambda d: mean(len(s) for t in pair[d] for s in samples(answers, FIX_MODEL, t, arm)),
        "useful_per_answer": lambda arm: lambda d: mean(sum(is_useful(t, c) for c in s) for t in pair[d] for s in samples(answers, FIX_MODEL, t, arm)),
        "nonobvious_per_answer": lambda arm: lambda d: mean(scored(t, arm, lambda s, o: len(s - o)) for t in pair[d]),
        "obvious_kept": lambda arm: lambda d: mean(scored(t, arm, lambda s, o: len(s & o) / max(1, len(o))) for t in pair[d]),
        "same_person": lambda arm: lambda d: mean(within(samples(answers, FIX_MODEL, t, arm)) for t in pair[d]),
        "two_people": lambda arm: lambda d: across(*(samples(answers, FIX_MODEL, t, arm) for t in pair[d])),
    }
    arms = [a for a in ARMS if ARMS[a].k == K and samples(answers, FIX_MODEL, pair[types[0]][0], a)]
    by_type_values = {a: {name: per_type(fn(a)) for name, fn in measures.items()} for a in arms}
    for a in arms:
        row = {name: boot(v) for name, v in by_type_values[a].items()}
        if a != "plain":
            row["vs_plain"] = {
                name: boot([x - y for x, y in zip(by_type_values[a][name], by_type_values["plain"][name])])
                for name in measures
            }
        row["output_tokens"] = mean(tokens[(FIX_MODEL, a)])
        row["n_answers"] = len(tokens[(FIX_MODEL, a)])
        rows[a] = row
    out["fixes"] = rows
    if "properties" in arms and "what_else" in arms:
        out["contrasts"] = {
            f"{x}_minus_{y}": {name: boot([p - q for p, q in zip(by_type_values[x][name], by_type_values[y][name])]) for name in measures}
            for x, y in [("properties_nudged", "what_else"), ("properties_nudged", "properties"), ("think_diverse", "properties"), ("random_word", "think_diverse")]
            if x in arms and y in arms
        }
    (run_dir / "results.json").write_text(json.dumps(out, indent=1))
    return out


def fmt(b) -> str:
    return f"{b[0]:.2f} [{b[1]:.2f}, {b[2]:.2f}]"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sprint.analyze")
    p.add_argument("run_dir", type=Path)
    p.add_argument("--tasks", type=Path, default=Path("tasks/decisions.toml"))
    args = p.parse_args(argv)
    r = analyze(args.run_dir, load_tasks(args.tasks))
    print("coverage", r["coverage"], "codebooks", r["codebook_sizes"])
    for m, c in r["collapse"].items():
        if m == "cross_model":
            for names, b in c.items():
                print(f"cross-model {names}: shared of {K}: {fmt(b)}")
        else:
            print(f"{m} plain: distinct/answer {fmt(c['distinct_per_answer'])}  same person {fmt(c['same_person'])}  "
                  f"two people {fmt(c['two_people'])}  distinct in 10 {fmt(c['distinct_in_10'])}")
            print("   saturation", [round(x, 1) for x in c["saturation"]])
    print("obvious set size", fmt(r["obvious_sizes"]))
    for a, row in r["fixes"].items():
        print(f"{a:18} good/10 {fmt(row['good_in_10'])}  good/answer {fmt(row['good_per_answer'])}  "
              f"distinct/10 {fmt(row['distinct_in_10'])}  same {fmt(row['same_person'])}  two {fmt(row['two_people'])}  "
              f"core kept {row['obvious_kept'][0]:.2f}  tokens {row['output_tokens']:.0f}")
    for name, c in r.get("contrasts", {}).items():
        print(name, "good/10", fmt(c["good_in_10"]), "good/answer", fmt(c["good_per_answer"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
