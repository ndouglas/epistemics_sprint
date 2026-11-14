"""The missing-fact study's numbers.

    uv run python -m sprint.probe_analyze runs/main

A hit is an answer that raises a probe's question (the judge's "asks" or "mentions").
Rates are computed per decision type, then averaged over types; intervals are
bootstrap intervals over the types. The contrast named in advance is the hit rate
for decisive probes minus the hit rate for inert ones, on the plain prompt, pooled
over the three models and paired by decision type.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from sprint.analyze import boot
from sprint.core import ARMS, K, load_tasks
from sprint.probes import load_probes, read_jsonl

FIX_MODEL = "haiku"
RANK = {"absent": 0, "mentions": 1, "asks": 2}
COMBINED = "plain+what_else"


def is_hit(row: dict) -> bool:
    return row["label"] != "absent"


def is_ask(row: dict) -> bool:
    return row["label"] == "asks"


def with_combined(rows: list[dict]) -> list[dict]:
    """Add one row per (model, task, sample, probe) for the two-turn briefing: the plain
    first turn and the "What else?" second turn read together, taking the stronger label."""
    pair: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        if r["arm"] in ("what_else", "what_else_t1"):
            pair[(r["model"], r["task"], r["sample"], r["probe"])][r["arm"]] = r
    extra = []
    for (model, task, sample, probe), both in pair.items():
        if len(both) == 2:
            best = max(both.values(), key=lambda r: RANK[r["label"]])
            extra.append({"model": model, "task": task, "arm": COMBINED, "sample": sample, "probe": probe,
                          "label": best["label"], "item": best["item"]})
    return rows + extra


def type_counts(rows: list[dict], task_type: dict, keep, hit=is_hit) -> dict[str, tuple[int, int]]:
    """Per decision type: (hits, rows) among the rows that `keep` selects."""
    out: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in rows:
        if keep(r):
            c = out[task_type[r["task"]]]
            c[0] += hit(r)
            c[1] += 1
    return {d: (h, n) for d, (h, n) in out.items()}


def rate(counts: dict[str, tuple[int, int]]):
    """Mean over decision types of the per-type hit rate, with a bootstrap interval; None if no rows."""
    values = [h / n for h, n in counts.values() if n]
    return list(boot(values)) + [len(values), sum(n for _, n in counts.values())] if values else None


def paired_difference(a: dict[str, tuple[int, int]], b: dict[str, tuple[int, int]]):
    """Mean over types (those with rows in both) of rate a minus rate b, with a bootstrap interval."""
    both = [d for d in a if d in b and a[d][1] and b[d][1]]
    diffs = [a[d][0] / a[d][1] - b[d][0] / b[d][1] for d in both]
    return list(boot(diffs)) + [len(diffs)] if diffs else None


def block(rows: list[dict], task_type: dict, cls: dict, keep) -> dict:
    """Decisive and inert hit rates, asks-only rates and their paired differences, for the rows `keep` selects."""
    out = {}
    counts = {}
    for name in ("decisive", "inert", "middle"):
        sel = lambda r, name=name: keep(r) and cls.get(r["probe"]) == name
        counts[name] = type_counts(rows, task_type, sel)
        out[name] = rate(counts[name])
        out[name + "_asks"] = rate(type_counts(rows, task_type, sel, is_ask))
    out["decisive_minus_inert"] = paired_difference(counts["decisive"], counts["inert"])
    asks = {n: type_counts(rows, task_type, lambda r, n=n: keep(r) and cls.get(r["probe"]) == n, is_ask) for n in ("decisive", "inert")}
    out["decisive_minus_inert_asks"] = paired_difference(asks["decisive"], asks["inert"])
    return out


def analyze(run_dir: Path, tasks, probes: list[dict], status_file: str = "probe_status.json", out_file: str = "probe_results.json") -> dict:
    task_type = {t.id: t.type for t in tasks}
    status = json.loads((run_dir / status_file).read_text())
    cls = {pid: v["status"] for pid, v in status["probes"].items()}
    about = {p["id"]: p.get("about", "details") for p in probes}
    question = {p["id"]: p["question"] for p in probes}
    rows = with_combined(read_jsonl(run_dir / "probe_hits.jsonl"))
    models = sorted({r["model"] for r in rows})
    plain = lambda r: r["arm"] == "plain"

    out: dict = {
        "n_probes": dict(sorted({s: sum(v == s for v in cls.values()) for s in set(cls.values())}.items())),
        "n_probes_by_about": {a: {s: sum(1 for p, v in cls.items() if v == s and about.get(p) == a) for s in ("decisive", "inert", "middle")}
                              for a in sorted(set(about.values()))},
        "plain_pooled": block(rows, task_type, cls, plain),
        "plain_by_model": {m: block(rows, task_type, cls, lambda r, m=m: plain(r) and r["model"] == m) for m in models},
        "by_about": {a: block(rows, task_type, cls, lambda r, a=a: plain(r) and about.get(r["probe"]) == a)
                     for a in sorted(set(about.values()))},
    }
    arms = [a for a in list(ARMS) + [COMBINED] if any(r["arm"] == a and r["model"] == FIX_MODEL for r in rows)]
    out["by_arm"] = {a: block(rows, task_type, cls, lambda r, a=a: r["arm"] == a and r["model"] == FIX_MODEL) for a in arms}

    # each arm against plain on the same model: decisive probes raised, and asked about, paired by type
    def decisive_counts(arm, hit):
        return type_counts(rows, task_type, lambda r: r["arm"] == arm and r["model"] == FIX_MODEL and cls.get(r["probe"]) == "decisive", hit)

    out["arm_vs_plain"] = {a: {"decisive": paired_difference(decisive_counts(a, is_hit), decisive_counts("plain", is_hit)),
                               "decisive_asks": paired_difference(decisive_counts(a, is_ask), decisive_counts("plain", is_ask))}
                           for a in arms if a != "plain"}

    # does the hit rate rise with how far the fact moves the choice? (all probes, plain, pooled)
    shift = {pid: sum(m["shift"] for m in v["models"].values()) / len(v["models"]) for pid, v in status["probes"].items() if v.get("models")}
    bands = {"0 to 0.1": (0, 0.1), "0.1 to 0.5": (0.1, 0.5), "0.5 to 1": (0.5, 1.01)}
    out["by_mean_shift"] = {}
    for name, (lo, hi) in bands.items():
        ids = {pid for pid, x in shift.items() if (lo <= x < hi if lo else x <= hi)}
        sel = [r for r in rows if plain(r) and r["probe"] in ids]
        if sel:
            out["by_mean_shift"][name] = {"probes": len(ids), "hit": sum(is_hit(r) for r in sel) / len(sel), "asks": sum(is_ask(r) for r in sel) / len(sel)}

    # which decisive facts does nobody raise?
    per_probe: dict[str, dict[str, list[int]]] = defaultdict(lambda: {"plain": [0, 0], "any": [0, 0]})
    for r in rows:
        if r["arm"] == COMBINED:
            continue
        for scope in (["plain", "any"] if plain(r) else ["any"]):
            per_probe[r["probe"]][scope][0] += is_hit(r)
            per_probe[r["probe"]][scope][1] += 1
    out["per_probe"] = {pid: {"status": cls.get(pid), "about": about.get(pid), "question": question.get(pid),
                              "plain": v["plain"], "any": v["any"]} for pid, v in sorted(per_probe.items())}
    decisive = [pid for pid, s in cls.items() if s == "decisive" and pid in per_probe]
    plain_rates = sorted(per_probe[pid]["plain"][0] / per_probe[pid]["plain"][1] for pid in decisive if per_probe[pid]["plain"][1])
    out["decisive_plain_rates"] = {"min": plain_rates[0] if plain_rates else None, "below_half": sum(x < 0.5 for x in plain_rates),
                                   "every_answer": sum(x == 1 for x in plain_rates), "n": len(plain_rates)}
    inert_ids = [pid for pid, s in cls.items() if s == "inert" and pid in per_probe]
    inert_rates = [per_probe[pid]["plain"][0] / per_probe[pid]["plain"][1] for pid in inert_ids if per_probe[pid]["plain"][1]]
    out["inert_plain_rates"] = {"never": sum(x == 0 for x in inert_rates), "below_half": sum(x < 0.5 for x in inert_rates),
                                "every_answer": sum(x == 1 for x in inert_rates), "n": len(inert_rates)}
    out["expected_vs_measured"] = {f"{e}|{st}": sum(1 for q in probes if q.get("expected") == e and cls.get(q["id"]) == st)
                                   for e in sorted({q["expected"] for q in probes if q.get("expected")}) for st in ("decisive", "middle", "inert")}
    out["never_raised_plain"] = [{"probe": pid, "question": question.get(pid), "answers": per_probe[pid]["plain"][1]}
                                 for pid in decisive if per_probe[pid]["plain"][0] == 0]
    out["never_raised_any_arm"] = [{"probe": pid, "question": question.get(pid), "answers": per_probe[pid]["any"][1]}
                                   for pid in decisive if per_probe[pid]["any"][0] == 0]

    # controls
    stated = read_jsonl(run_dir / "probe_hits_stated.jsonl")
    if stated:
        probe_task = {p["id"]: p["task"] for p in probes}
        st_type = {r["task"]: task_type[probe_task[r["probe"]]] for r in stated if r["probe"] in probe_task}
        stated = [r for r in stated if r["probe"] in probe_task]
        out["stated"] = {name: rate(type_counts(stated, st_type, lambda r, name=name: cls.get(r["probe"]) == name))
                         for name in ("decisive", "inert")}
    foreign = read_jsonl(run_dir / "probe_hits_foreign.jsonl")
    if foreign:
        hits = sum(is_hit(r) for r in foreign)
        out["foreign"] = {"hits": hits, "n": len(foreign), "rate": hits / len(foreign),
                          "by_type": rate(type_counts(foreign, task_type, lambda r: True))}
    (run_dir / out_file).write_text(json.dumps(out, indent=1))
    return out


def fmt(b) -> str:
    return "n/a" if b is None else f"{100 * b[0]:.0f}% [{100 * b[1]:.0f}, {100 * b[2]:.0f}]"


def show(name: str, b: dict) -> None:
    print(f"{name:22} decisive {fmt(b['decisive'])}  inert {fmt(b['inert'])}  difference {fmt(b['decisive_minus_inert'])}"
          f"  | asks only: {fmt(b['decisive_asks'])} vs {fmt(b['inert_asks'])}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sprint.probe_analyze")
    p.add_argument("run_dir", type=Path)
    p.add_argument("--tasks", type=Path, default=Path("tasks/decisions.toml"))
    p.add_argument("--status", default="probe_status.json", help="which decisive/inert classification to use")
    p.add_argument("--out", default="probe_results.json")
    args = p.parse_args(argv)
    r = analyze(args.run_dir, load_tasks(args.tasks), load_probes(), args.status, args.out)
    print("probes", r["n_probes"], "by about", r["n_probes_by_about"])
    show(f"plain, pooled (of {K})", r["plain_pooled"])
    for m, b in r["plain_by_model"].items():
        show(f"plain, {m}", b)
    for a, b in r["by_about"].items():
        show(f"plain, about {a[:12]}", b)
    for a, b in r["by_arm"].items():
        show(f"{FIX_MODEL} {a}", b)
    for a, b in r["arm_vs_plain"].items():
        print(f"{FIX_MODEL} {a:18} minus plain, decisive raised {fmt(b['decisive'])}  asked {fmt(b['decisive_asks'])}")
    print("by mean shift", r["by_mean_shift"])
    print("decisive probes, plain hit rates", r["decisive_plain_rates"], " inert", r["inert_plain_rates"])
    print("drafter's guess against the check", r["expected_vs_measured"])
    b = r["plain_pooled"]
    print("middle probes, plain pooled:", fmt(b["middle"]), " asks", fmt(b["middle_asks"]))
    if "stated" in r:
        print("fact stated (positive control): decisive", fmt(r["stated"]["decisive"]), " inert", fmt(r["stated"]["inert"]))
    if "foreign" in r:
        print(f"probes from another decision (negative control): {r['foreign']['hits']}/{r['foreign']['n']}")
    print(f"decisive facts no plain answer raised: {len(r['never_raised_plain'])}; no answer on any arm: {len(r['never_raised_any_arm'])}")
    for x in r["never_raised_any_arm"]:
        print("  -", x["probe"], x["question"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
