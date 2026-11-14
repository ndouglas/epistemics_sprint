"""Property-log numbers, the figures and the side-by-side example.

    uv run python -m sprint.figures runs/main
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sprint.analyze import across, boot, load, samples, within
from sprint.core import load_tasks

LABEL = {
    "plain": "Plain", "verbalized": "Verbalized sampling", "properties": "Properties (6a)",
    "properties_nudged": "Properties + dice (6b)", "random_word": "Random word",
    "think_diverse": "Think first, be diverse", "what_else": '"What else?" (2nd turn)',
}
OFFSET = {"properties": (-6, -12, "right"), "properties_nudged": (6, 8, "left"), "random_word": (-6, -12, "right"),
          "think_diverse": (6, 6, "left"), "verbalized": (8, 1, "left"), "plain": (7, -9, "left")}
MODEL = {"haiku": "Haiku 5.5", "sonnet": "Sonnet 5.5", "gpt": "GPT-5.5"}


def property_log(run_dir: Path, tasks) -> dict:
    types = list(dict.fromkeys(t.type for t in tasks))
    pair = {d: [t.id for t in tasks if t.type == d] for d in types}
    sets: dict[tuple, set] = defaultdict(set)
    for d in types:
        data = json.loads((run_dir / "property_codes" / f"{d}.json").read_text())
        for item_id, code in data["assigned"].items():
            model, task, arm, sample, _ = item_id.split("|")
            sets[(task, arm, int(sample))].add(code if code else "x:" + item_id)
    out = {}
    for arm in ("properties", "properties_nudged"):
        def got(t):
            return [s for (tt, a, _), s in sorted(sets.items(), key=lambda kv: kv[0][2]) if (tt, a) == (t, arm)]
        out[arm] = {
            "per_answer": boot([mean(len(s) for t in pair[d] for s in got(t)) for d in types]),
            "same_person_shared": boot([mean(within(got(t)) for t in pair[d]) for d in types]),
            "same_person_shared_fraction": boot([mean(within(got(t)) / mean(len(s) for s in got(t)) for t in pair[d]) for d in types]),
            "distinct_in_10": boot([mean(len(set().union(*got(t))) for t in pair[d]) for d in types]),
            "two_people_shared": boot([across(got(pair[d][0]), got(pair[d][1])) for d in types]),
        }
    return out


def example(run_dir: Path, tasks, task_id: str = "job-offer-a") -> str:
    """Two real plain answers to the same vignette, marked where they share a consideration."""
    task = next(t for t in tasks if t.id == task_id)
    data = json.loads((run_dir / "codes" / f"{task.type}.json").read_text())
    rows = {}
    for line in (run_dir / "generations.jsonl").read_text().splitlines():
        r = json.loads(line)
        if (r["model"], r["task"], r["arm"]) == ("sonnet", task_id, "plain"):
            rows[r["sample"]] = [(data["assigned"][f"sonnet|{task_id}|plain|{r['sample']}|{i}"], t) for i, t in enumerate(r["items"])]
    # show a typical pair, not a flattering one: the first pair whose overlap is the median over all pairs
    import itertools
    from statistics import median_low
    pairs = {(i, j): len({c for c, _ in rows[i]} & {c for c, _ in rows[j]}) for i, j in itertools.combinations(sorted(rows), 2)}
    target = median_low(pairs.values())
    i, j = next(k for k, v in pairs.items() if v == target)
    rows = {0: rows[i], 1: rows[j]}
    shared = {c for c, _ in rows[0]} & {c for c, _ in rows[1]}
    lines = [task.vignette, ""]
    for s in (0, 1):
        lines.append(f"Ask {s + 1}:")
        lines += [f"  [{'shared' if c in shared else 'only here'}] {data['codes'][c - 1]['label'] if c else '(uncoded)'} :: {t}" for c, t in rows[s]]
        lines.append("")
    lines.append(f"shared considerations: {len(shared)}")
    return "\n".join(lines)


def main() -> int:
    run_dir = Path(sys.argv[1])
    tasks = load_tasks(Path("tasks/decisions.toml"))
    r = json.loads((run_dir / "results.json").read_text())
    figs = run_dir / "figures"
    figs.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    ink, accent, soft = "#222222", "#2a6f97", "#9db4c0"

    # Figure 1: the three overlaps and the saturation curve
    c = r["collapse"]
    models = [m for m in ("haiku", "sonnet", "gpt") if m in c]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw={"width_ratios": [1.25, 1]})
    bars = [(f"Same person, {MODEL[m]} twice", c[m]["same_person"], accent) for m in models]
    bars += [(f"Same person, {MODEL[x]} then {MODEL[y]}", v, soft) for k, v in c["cross_model"].items() for x, y in [k.split("|")]]
    bars += [(f"Two different people, {MODEL[m]}", c[m]["two_people"], "#c9ada7") for m in models]
    ys = range(len(bars))[::-1]
    for y, (name, (mid, lo, hi), color) in zip(ys, bars):
        a.barh(y, mid, color=color, height=0.72)
        a.plot([lo, hi], [y, y], color=ink, lw=1)
        a.text(hi + 0.12, y, f"{mid:.1f}", va="center", color=ink)
    a.set_yticks(list(ys), [n for n, _, _ in bars])
    a.set_xlim(0, 8)
    a.set_xlabel("Considerations shared by two answers (of 8)")
    for m, color in zip(models, (accent, ink, "#bc6c25")):
        b.plot(range(1, 11), c[m]["saturation"], marker="o", ms=3, color=color, label=MODEL[m])
    b.set_xlabel("Times the same person asks")
    b.set_ylabel("Distinct considerations so far")
    b.set_ylim(0, None)
    b.set_xticks(range(1, 11))
    b.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figs / "collapse.pdf")
    fig.savefig(figs / "collapse.png", dpi=200)

    # Figure 2: what each fix adds and what it costs
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    for arm, row in r["fixes"].items():
        x, y = row["obvious_kept"][0] * 100, row["good_per_answer"][0]
        ax.plot([x, x], row["good_per_answer"][1:], color=soft, lw=1)
        ax.plot([row["obvious_kept"][1] * 100, row["obvious_kept"][2] * 100], [y, y], color=soft, lw=1)
        ax.scatter([x], [y], color=accent if arm.startswith("properties") else ink, zorder=3, s=22)
        dx, dy, ha = OFFSET.get(arm, (5, 5, "left"))
        ax.annotate(LABEL[arm], (x, y), textcoords="offset points", xytext=(dx, dy), fontsize=8, ha=ha)
    ax.set_xlabel("Share of the obvious considerations an answer keeps (%)")
    ax.set_ylabel("Useful non-obvious considerations\nper answer (of 8)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 6)
    fig.tight_layout()
    fig.savefig(figs / "fixes.pdf")
    fig.savefig(figs / "fixes.png", dpi=200)

    props = property_log(run_dir, tasks)
    (run_dir / "property_log.json").write_text(json.dumps(props, indent=1))
    for arm, row in props.items():
        print(arm, {k: f"{v[0]:.2f} [{v[1]:.2f}, {v[2]:.2f}]" for k, v in row.items()})
    (run_dir / "example.txt").write_text(example(run_dir, tasks))
    print((run_dir / "example.txt").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
