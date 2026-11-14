"""Blind hand labels, used to check the automated coding and the usefulness judge.

    uv run python -m sprint.label make runs/main      # draw the samples (once)
    uv run python -m sprint.label pairs runs/main     # same or different? (60)
    uv run python -m sprint.label useful runs/main    # could it change the choice? (40)
    uv run python -m sprint.label probes-make runs/main   # draw the missing-fact sample (once)
    uv run python -m sprint.label probes runs/main    # does the answer raise this question? (8 practice + 80)
    uv run python -m sprint.label report runs/main    # agreement with the machine

The labeling screens never show codes, arms, models or the judge's answer.
Both commands resume where you stopped.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import textwrap
from collections import defaultdict
from pathlib import Path

from sprint.core import load_tasks
from sprint.score import by_type, load_items

N_PER_STRATUM = 20
N_USEFUL = 34
N_FOREIGN = 6


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", text.lower()) if len(w) > 3}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / max(1, len(a | b))


def load_codes(run_dir: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in (run_dir / "codes").glob("*.json")}


def make(run_dir: Path, tasks, seed: int) -> None:
    rng = random.Random(f"{seed}:labels")
    codes = load_codes(run_dir)
    groups = by_type(load_items(run_dir))
    same, near, far = [], [], []
    for dtype, items in sorted(groups.items()):
        assigned = codes[dtype]["assigned"]
        items = [it for it in items if assigned[it["id"]] != 0]
        bag = {it["id"]: words(it["text"]) for it in items}
        for _ in range(4000):
            a, b = rng.sample(items, 2)
            if a["text"] == b["text"]:
                continue
            pair = {"type": dtype, "a": a["text"], "b": b["text"], "a_id": a["id"], "b_id": b["id"]}
            if assigned[a["id"]] == assigned[b["id"]]:
                same.append(pair)
            else:
                pair["sim"] = jaccard(bag[a["id"]], bag[b["id"]])
                far.append(pair)
    far.sort(key=lambda p: -p["sim"])
    near = far[: len(far) // 50]  # the most similar-looking 2% of different-code pairs
    picks = (
        [dict(p, stratum="same code") for p in rng.sample(same, N_PER_STRATUM)]
        + [dict(p, stratum="different code, similar wording") for p in rng.sample(near, N_PER_STRATUM)]
        + [dict(p, stratum="different code, random") for p in rng.sample(far[len(near) :], N_PER_STRATUM)]
    )
    rng.shuffle(picks)
    for p in picks:
        if rng.random() < 0.5:
            p["a"], p["b"], p["a_id"], p["b_id"] = p["b"], p["a"], p["b_id"], p["a_id"]

    judged = json.loads((run_dir / "useful.json").read_text())
    by_id = {t.id: t for t in tasks}
    real = []
    for task_id, ratings in judged.items():
        book = codes[by_id[task_id].type]["codes"]
        for c, yes in ratings.items():
            c = int(c)
            real.append({"task": task_id, "text": f"{book[c - 1]['label']}: {book[c - 1]['definition']}",
                         "machine": yes, "stratum": "judge yes" if yes else "judge no"})
    yes = [r for r in real if r["machine"]]
    no = [r for r in real if not r["machine"]]
    n_no = min(len(no), N_USEFUL // 2)
    rate = rng.sample(no, n_no) + rng.sample(yes, N_USEFUL - n_no)
    for _ in range(N_FOREIGN):  # a consideration from a different kind of decision: should be a no
        task = rng.choice(tasks)
        other = rng.choice([d for d in codes if d != task.type])
        c = rng.choice(codes[other]["codes"])
        rate.append({"task": task.id, "text": f"{c['label']}: {c['definition']}", "machine": None,
                     "stratum": "planted from another decision"})
    rng.shuffle(rate)
    out = run_dir / "labels"
    out.mkdir(exist_ok=True)
    (out / "pairs_sample.json").write_text(json.dumps(picks, indent=1))
    (out / "useful_sample.json").write_text(json.dumps(rate, indent=1))
    print(f"{len(picks)} pairs and {len(rate)} considerations drawn into {out}")


N_PRACTICE = 8
N_PROBE_PAIRS = 80
PROBE_KEYS = {"a": "asks", "m": "mentions", "n": "absent"}


def probes_make(run_dir: Path, seed: int) -> None:
    """Draw answer-question pairs for the missing-fact check: a few unscored practice pairs
    first, then scored pairs in roughly equal numbers for each of the judge's three labels."""
    from sprint.probes import answer_key, load_answers, load_probes, read_jsonl

    rng = random.Random(f"{seed}:probe-labels")
    answers = {answer_key(a): a for a in load_answers(run_dir)}
    question = {p["id"]: p["question"] for p in load_probes()}
    rows = [r for r in read_jsonl(run_dir / "probe_hits.jsonl")
            if (r["model"], r["task"], r["arm"], r["sample"]) in answers and r["probe"] in question]
    rng.shuffle(rows)
    by_label: dict[str, list] = defaultdict(list)
    for r in rows:
        by_label[r["label"]].append(r)
    labels = sorted(by_label)
    scored = []
    for i, label in enumerate(labels):  # split as evenly as the judge's labels allow
        want = N_PROBE_PAIRS // len(labels) + (1 if i < N_PROBE_PAIRS % len(labels) else 0)
        scored += by_label[label][:want]
        by_label[label] = by_label[label][want:]
    left = [r for label in labels for r in by_label[label]]
    rng.shuffle(left)
    scored += left[: N_PROBE_PAIRS - len(scored)]
    used = {id(r) for r in scored}
    practice = [r for r in left if id(r) not in used][:N_PRACTICE]
    rng.shuffle(scored)

    def entry(r: dict, is_practice: bool) -> dict:
        key = (r["model"], r["task"], r["arm"], r["sample"])
        return {"practice": is_practice, "items": answers[key]["items"], "question": question[r["probe"]],
                "machine": r["label"], "probe": r["probe"], "answer": list(key)}

    sample = [entry(r, True) for r in practice] + [entry(r, False) for r in scored]
    out = run_dir / "labels"
    out.mkdir(exist_ok=True)
    (out / "probes_sample.json").write_text(json.dumps(sample, indent=1))
    print(f"{len(practice)} practice and {len(scored)} scored pairs drawn into {out}")


def show_probe(s: dict) -> None:
    if s["practice"]:
        print("PRACTICE (not scored; talk these over before the scored ones start)")
    for i, item in enumerate(s["items"], 1):
        print(textwrap.fill(f"{i}. {item}", 88, initial_indent="   ", subsequent_indent="      "))
    print(f"\nQuestion:\n{wrap(s['question'])}")


def kappa_cat(pairs: list[tuple]) -> float:
    """Cohen's kappa for two raters over any number of categories."""
    n = len(pairs)
    agree = sum(a == b for a, b in pairs) / n
    cats = {c for pair in pairs for c in pair}
    chance = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return (agree - chance) / (1 - chance) if chance < 1 else 1.0


def probes_report(out: Path) -> dict | None:
    """Agreement with the judge on the scored pairs only; practice pairs are left out."""
    if not (out / "probes.jsonl").exists():
        return None
    sample = json.loads((out / "probes_sample.json").read_text())
    rows = [json.loads(l) for l in (out / "probes.jsonl").read_text().splitlines()]
    got = [(sample[r["i"]]["machine"], r["label"]) for r in rows if not sample[r["i"]]["practice"]]
    if not got:
        return None
    raised = [(m != "absent", h != "absent") for m, h in got]
    strata = defaultdict(list)
    for m, h in got:
        strata[f"judge {m}"].append(m == h)
    return {"n": len(got), "agreement": sum(m == h for m, h in got) / len(got), "kappa": kappa_cat(got),
            "raised_agreement": sum(m == h for m, h in raised) / len(raised), "raised_kappa": kappa_cat(raised),
            "by_stratum": {k: f"{sum(v)}/{len(v)}" for k, v in sorted(strata.items())}}


def wrap(text: str) -> str:
    return textwrap.fill(text, 88, initial_indent="   ", subsequent_indent="   ")


def run_labels(sample_path: Path, out_path: Path, show, prompt: str, keys: dict[str, object]) -> None:
    sample = json.loads(sample_path.read_text())
    done = out_path.read_text().splitlines() if out_path.exists() else []
    for i in range(len(done), len(sample)):
        print(f"\n[{i + 1}/{len(sample)}]")
        show(sample[i])
        while (answer := input(prompt).strip().lower()) not in keys:
            pass
        with out_path.open("a") as f:
            f.write(json.dumps({"i": i, "label": keys[answer]}) + "\n")
    print("\nDone. Thank you.")


def kappa(pairs: list[tuple[bool, bool]]) -> float:
    n = len(pairs)
    agree = sum(a == b for a, b in pairs) / n
    pa = sum(a for a, _ in pairs) / n
    pb = sum(b for _, b in pairs) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    return (agree - chance) / (1 - chance) if chance < 1 else 1.0


def report(run_dir: Path) -> dict:
    out = run_dir / "labels"
    codes = load_codes(run_dir)
    result = {}
    if (out / "pairs.jsonl").exists():
        sample = json.loads((out / "pairs_sample.json").read_text())
        rows = [json.loads(l) for l in (out / "pairs.jsonl").read_text().splitlines()]
        got, strata = [], defaultdict(list)
        for r in rows:
            p = sample[r["i"]]
            a = codes[p["type"]]["assigned"]
            machine = a[p["a_id"]] == a[p["b_id"]]
            got.append((machine, r["label"]))
            strata[p["stratum"]].append(machine == r["label"])
        result["pairs"] = {"n": len(got), "agreement": sum(a == b for a, b in got) / len(got), "kappa": kappa(got),
                           "by_stratum": {k: f"{sum(v)}/{len(v)}" for k, v in strata.items()}}
    if (out / "useful.jsonl").exists():
        sample = json.loads((out / "useful_sample.json").read_text())
        rows = [json.loads(l) for l in (out / "useful.jsonl").read_text().splitlines()]
        got, strata = [], defaultdict(list)
        for r in rows:
            s = sample[r["i"]]
            if s["machine"] is None:
                strata[s["stratum"]].append(r["label"] is False)
            else:
                got.append((s["machine"], r["label"]))
                strata[s["stratum"]].append(s["machine"] == r["label"])
        result["useful"] = {"n": len(got), "agreement": sum(a == b for a, b in got) / len(got), "kappa": kappa(got),
                            "by_stratum": {k: f"{sum(v)}/{len(v)}" for k, v in strata.items()}}
    if (probes := probes_report(out)) is not None:
        result["probes"] = probes
    (out / "report.json").write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sprint.label")
    p.add_argument("cmd", choices=["make", "pairs", "useful", "probes-make", "probes", "report"])
    p.add_argument("run_dir", type=Path)
    p.add_argument("--tasks", type=Path, default=Path("tasks/decisions.toml"))
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)
    tasks = load_tasks(args.tasks)
    out = args.run_dir / "labels"
    if args.cmd == "make":
        make(args.run_dir, tasks, args.seed)
    if args.cmd == "pairs":
        print("Do these two sentences tell the person to weigh the SAME thing?\n"
              "Same: same consideration, even with different wording or detail.\n"
              "Different: someone who had heard one would learn something new from the other.")
        run_labels(out / "pairs_sample.json", out / "pairs.jsonl",
                   lambda s: print(f"A:\n{wrap(s['a'])}\nB:\n{wrap(s['b'])}"),
                   "same or different? [s/d] ", {"s": True, "d": False})
    if args.cmd == "useful":
        by_id = {t.id: t for t in tasks}
        print("Could weighing this plausibly change what this person chooses, or how they go about\n"
              "choosing? No if it doesn't apply to them, is too generic, or couldn't move the decision.")
        run_labels(out / "useful_sample.json", out / "useful.jsonl",
                   lambda s: print(f"{wrap(by_id[s['task']].vignette)}\n\nConsideration:\n{wrap(s['text'])}"),
                   "could change the choice? [y/n] ", {"y": True, "n": False})
    if args.cmd == "probes-make":
        probes_make(args.run_dir, args.seed)
    if args.cmd == "probes":
        print("Does any item in the list raise this question? It must be the same specific unknown,\n"
              "not just the same topic.\n"
              "  a: an item tells the person to find it out, check it or ask about it\n"
              "  m: an item raises the same matter and weighs it, without telling them to find it out\n"
              "  n: no item raises it")
        run_labels(out / "probes_sample.json", out / "probes.jsonl", show_probe,
                   "Does any item raise this? [a]sks them to find it out / [m]entions it / [n]o ", PROBE_KEYS)
    if args.cmd == "report":
        report(args.run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
