"""Three descriptive analyses of the coded answers that the main tables do not cover.

    uv run python -m sprint.extra runs/main        # writes runs/main/extra.json

1. Slots: is a plain answer ranked? For each position 1 to 8, the share of items that
   are among that model's own common considerations for the vignette (in at least half of
   its ten plain answers); how often two answers keep their shared considerations in the
   same order; how often an answer opens with the vignette's most common opener.
2. Stated or brought in: considerations that come from a detail the vignette states
   against ones the model brought in (runs/main/anchored.json), and how often each kind
   reappears when the person asks again.
3. Sixteen: one plain answer of 16 items against a plain answer plus "What else?",
   and against two or three separate plain answers read together.
"""

from __future__ import annotations

import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from sprint.analyze import boot, load, samples
from sprint.core import load_tasks
from sprint.score import load_items

FIX_MODEL = "haiku"


def ordered_codes(run_dir: Path, codes: dict) -> dict[tuple, list]:
    """(model, task, arm, sample) -> the answer's codes in the order the items were given."""
    out: dict[tuple, dict[int, object]] = defaultdict(dict)
    for it in load_items(run_dir):
        if it["type"] in codes:
            c = codes[it["type"]]["assigned"][it["id"]]
            out[(it["model"], it["task"], it["arm"], it["sample"])][it["idx"]] = c if c else "x:" + it["id"]
    return {k: [v[i] for i in sorted(v)] for k, v in out.items()}


def concordant(a: list, b: list) -> tuple[int, int]:
    """Among considerations both answers contain once: pairs kept in the same order, and all pairs."""
    shared = [c for c in a if c in b and a.count(c) == 1 and b.count(c) == 1]
    same = total = 0
    for x, y in itertools.combinations(shared, 2):
        total += 1
        same += (a.index(x) < a.index(y)) == (b.index(x) < b.index(y))
    return same, total


def analyze(run_dir: Path, tasks) -> dict:
    codes, useful, answers, _, tokens = load(run_dir, tasks)
    types = [d for d in dict.fromkeys(t.type for t in tasks) if d in codes]
    pair = {d: [t.id for t in tasks if t.type == d] for d in types}
    order = ordered_codes(run_dir, codes)
    models = sorted({k[0] for k in answers})

    def per(fn):  # mean over a type's vignettes, then a bootstrap over types
        return list(boot([mean(fn(t) for t in pair[d]) for d in types]))

    def lists(m: str, t: str, arm: str = "plain") -> list[list]:
        return [v for (mm, tt, a, _), v in sorted(order.items(), key=lambda kv: kv[0][3]) if (mm, tt, a) == (m, t, arm)]

    # ---- 1. slots ----
    slots = {}
    for m in models:
        def common(t):
            ls = lists(m, t)
            n = Counter(c for l in ls for c in set(l))
            return {c for c, k in n.items() if k >= len(ls) / 2}

        def share_at(i):
            return per(lambda t: mean(l[i] in common(t) for l in lists(m, t) if len(l) > i))

        def order_kept(t):
            same = total = 0
            for a, b in itertools.combinations(lists(m, t), 2):
                s, n = concordant(a, b)
                same, total = same + s, total + n
            return same / total

        def same_opener(t):
            ls = lists(m, t)
            return Counter(l[0] for l in ls).most_common(1)[0][1] / len(ls)

        slots[m] = {"common_share_by_slot": [share_at(i) for i in range(8)],
                    "order_kept": per(order_kept), "same_opener": per(same_opener)}

    # ---- 2. stated or brought in ----
    anchored = json.loads((run_dir / "anchored.json").read_text())

    def stated(t, c) -> bool:
        return anchored.get(t, {}).get(str(c), False)

    def repeat(m, t, flag) -> float:
        num = den = 0
        for a, b in itertools.permutations(samples(answers, m, t, "plain"), 2):
            xs = [c for c in a if stated(t, c) == flag]
            den += len(xs)
            num += sum(c in b for c in xs)
        return num / max(1, den)

    origin = {}
    for m in models:
        S = lambda t, m=m: samples(answers, m, t, "plain")
        origin[m] = {
            "stated_per_answer": per(lambda t: mean(sum(stated(t, c) for c in s) for s in S(t))),
            "brought_per_answer": per(lambda t: mean(sum(not stated(t, c) for c in s) for s in S(t))),
            "repeat_stated": per(lambda t: repeat(m, t, True)),
            "repeat_brought": per(lambda t: repeat(m, t, False)),
            "distinct10_stated": per(lambda t: sum(stated(t, c) for c in set().union(*S(t)))),
            "distinct10_brought": per(lambda t: sum(not stated(t, c) for c in set().union(*S(t)))),
        }

    # ---- 3. sixteen ----
    S = lambda t, arm: samples(answers, FIX_MODEL, t, arm)

    def obvious(t):
        sets = S(t, "plain")
        n = Counter(c for s in sets for c in s)
        return {c for c, k in n.items() if k >= len(sets) / 2}

    def briefings(t, kind):
        if kind == "plain":
            return S(t, "plain")
        if kind == "plain16":
            return S(t, "plain16")
        if kind == "plain_what_else":
            return [a | b for a, b in zip(S(t, "what_else_t1"), S(t, "what_else"))]
        n = int(kind[-1])  # plain_x2, plain_x3: that many separate plain answers read together
        return [set().union(*combo) for combo in itertools.combinations(S(t, "plain"), n)]

    sixteen = {}
    for kind in ("plain", "plain_x2", "plain_x3", "plain16", "plain_what_else"):
        if not briefings(pair[types[0]][0], kind):
            continue
        sixteen[kind] = {
            "distinct": per(lambda t: mean(len(s) for s in briefings(t, kind))),
            "obvious_kept": per(lambda t: mean(len(s & obvious(t)) / len(obvious(t)) for s in briefings(t, kind))),
            "new": per(lambda t: mean(sum(useful.get(t, {}).get(str(c), False) and c not in obvious(t) for c in s) for s in briefings(t, kind))),
            "brought": per(lambda t: mean(sum(not stated(t, c) for c in s) for s in briefings(t, kind))),
        }
        if kind in ("plain16", "plain_what_else"):
            sixteen[kind]["same_person"] = per(lambda t: mean(len(a & b) for a, b in itertools.combinations(briefings(t, kind), 2)))
    sixteen["tokens"] = {a: mean(tokens[(FIX_MODEL, a)]) for a in ("plain", "plain16", "what_else") if tokens.get((FIX_MODEL, a))}

    out = {"slots": slots, "origin": origin, "sixteen": sixteen}
    (run_dir / "extra.json").write_text(json.dumps(out, indent=1))
    return out


def main() -> int:
    run_dir = Path(sys.argv[1])
    r = analyze(run_dir, load_tasks(Path("tasks/decisions.toml")))
    for m, s in r["slots"].items():
        print(m, "common share by slot", [round(100 * b[0]) for b in s["common_share_by_slot"]],
              "order kept", round(100 * s["order_kept"][0]), "same opener", round(100 * s["same_opener"][0]))
    for m, o in r["origin"].items():
        print(m, {k: round(v[0], 2) for k, v in o.items()})
    for k, v in r["sixteen"].items():
        print(k, {a: round(b[0], 2) for a, b in v.items()} if k != "tokens" else v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
