"""Every number the report states, computed from the run's files.

    uv run python -m sprint.claims runs/main        # writes results/claims.json and claims.md

The report writes a number as [claim.id=value]; the build refuses to run if a
tagged value differs from the one here.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def one(x: float) -> str:
    return f"{x:.1f}".replace("-0.0", "0.0")


def put(claims: dict, key: str, b, scale: float = 1.0, fmt=one) -> None:
    """A bootstrap triple becomes a point claim and an interval claim."""
    claims[key] = fmt(b[0] * scale)
    claims[key + ".ci"] = f"{fmt(b[1] * scale)} to {fmt(b[2] * scale)}"


def pct(x: float) -> str:
    return f"{x:.0f}%"


def build(run_dir: Path) -> dict:
    r = json.loads((run_dir / "results.json").read_text())
    c: dict[str, str] = {}
    rows = [json.loads(l) for l in (run_dir / "generations.jsonl").read_text().splitlines()]
    status = Counter((x["model"], x["status"]) for x in rows)
    for m in r["models"]:
        c[f"n.{m}.answers"] = str(status[(m, "ok")])
    c["n.answers"] = f"{sum(v for (m, s), v in status.items() if s == 'ok'):,}"
    c["n.not_ok"] = str(sum(v for (m, s), v in status.items() if s != "ok"))
    c["n.retried"] = str(sum(1 for x in rows if x["status"] == "ok" and x["attempts"] > 1))
    c["n.items"] = f"{r['coverage']['items']:,}"
    c["n.unassigned"] = str(r["coverage"]["unassigned"])
    sizes = r["codebook_sizes"].values()
    c["codebook.min"], c["codebook.max"] = str(min(sizes)), str(max(sizes))
    put(c, "obvious.size", r["obvious_sizes"])

    col = r["collapse"]
    for m in r["models"]:
        if m in col:
            put(c, f"collapse.{m}.same", col[m]["same_person"])
            put(c, f"collapse.{m}.two", col[m]["two_people"])
            put(c, f"collapse.{m}.in10", col[m]["distinct_in_10"])
            put(c, f"collapse.{m}.per_answer", col[m]["distinct_per_answer"])
            c[f"collapse.{m}.gain10"] = one(col[m]["saturation"][9] - col[m]["saturation"][8])
    for k, b in col["cross_model"].items():
        put(c, "cross." + k.replace("|", "_"), b)

    for arm, row in r["fixes"].items():
        put(c, f"fix.{arm}.good", row["good_per_answer"])
        put(c, f"fix.{arm}.useful", row["useful_per_answer"])
        put(c, f"fix.{arm}.good10", row["good_in_10"])
        put(c, f"fix.{arm}.in10", row["distinct_in_10"])
        put(c, f"fix.{arm}.same", row["same_person"])
        put(c, f"fix.{arm}.two", row["two_people"])
        put(c, f"fix.{arm}.core", row["obvious_kept"], 100, pct)
        c[f"fix.{arm}.tokens"] = f"{row['output_tokens']:.0f}"
        if "vs_plain" in row:
            put(c, f"vs.{arm}.good", row["vs_plain"]["good_per_answer"])
            put(c, f"vs.{arm}.good10", row["vs_plain"]["good_in_10"])
    for name, row in r.get("contrasts", {}).items():
        put(c, f"contrast.{name}.good", row["good_per_answer"])
        put(c, f"contrast.{name}.good10", row["good_in_10"])

    plog = run_dir / "property_log.json"
    if plog.exists():
        for arm, row in json.loads(plog.read_text()).items():
            put(c, f"props.{arm}.per_answer", row["per_answer"])
            put(c, f"props.{arm}.same", row["same_person_shared"])
            put(c, f"props.{arm}.same_frac", row["same_person_shared_fraction"], 100, pct)
            put(c, f"props.{arm}.in10", row["distinct_in_10"])
            put(c, f"props.{arm}.two", row["two_people_shared"])

    lab = run_dir / "labels" / "report.json"
    if lab.exists():
        for kind, row in json.loads(lab.read_text()).items():
            c[f"labels.{kind}.n"] = str(row["n"])
            c[f"labels.{kind}.agree"] = pct(row["agreement"] * 100)
            c[f"labels.{kind}.kappa"] = f"{row['kappa']:.2f}"
            for s, v in row["by_stratum"].items():
                c[f"labels.{kind}.{s.replace(' ', '_').replace(',', '')}"] = v

    for alt in ("rep", "coarse"):  # the same answers under two other codebook builds
        path = run_dir.parent / alt / "results.json"
        if not path.exists():
            continue
        q = json.loads(path.read_text())
        sizes = q["codebook_sizes"].values()
        c[f"{alt}.codebook.min"], c[f"{alt}.codebook.max"] = str(min(sizes)), str(max(sizes))
        for m in q["models"]:
            put(c, f"{alt}.collapse.{m}.same", q["collapse"][m]["same_person"])
            put(c, f"{alt}.collapse.{m}.two", q["collapse"][m]["two_people"])
        for k, b in q["collapse"]["cross_model"].items():
            put(c, f"{alt}.cross." + k.replace("|", "_"), b)
        for arm, row in q["fixes"].items():
            put(c, f"{alt}.fix.{arm}.good", row["good_per_answer"])
            put(c, f"{alt}.fix.{arm}.nonobvious", row["nonobvious_per_answer"])
            put(c, f"{alt}.fix.{arm}.core", row["obvious_kept"], 100, pct)
        for name, row in q.get("contrasts", {}).items():
            put(c, f"{alt}.contrast.{name}.good", row["good_per_answer"])
    for arm, row in r["fixes"].items():
        put(c, f"fix.{arm}.nonobvious", row["nonobvious_per_answer"])

    # the hand labels against each build's coding of the same 60 pairs
    lab_dir = run_dir / "labels"
    if (lab_dir / "pairs.jsonl").exists():
        from sprint.label import kappa, load_codes
        sample = json.loads((lab_dir / "pairs_sample.json").read_text())
        hand = [json.loads(l) for l in (lab_dir / "pairs.jsonl").read_text().splitlines()]
        c["labels.pairs.hand_same"] = str(sum(h["label"] for h in hand))
        for alt in ("main", "rep", "coarse"):
            if not (run_dir.parent / alt / "codes").exists():
                continue
            codes = load_codes(run_dir.parent / alt)
            got = []
            for h in hand:
                p = sample[h["i"]]
                a = codes[p["type"]]["assigned"]
                got.append((a[p["a_id"]] == a[p["b_id"]] and a[p["a_id"]] != 0, h["label"]))
            c[f"labels.pairs.{alt}.agree"] = pct(100 * sum(x == y for x, y in got) / len(got))
            c[f"labels.pairs.{alt}.kappa"] = f"{kappa(got):.2f}"
            c[f"labels.pairs.{alt}.machine_same"] = str(sum(x for x, _ in got))
            if alt == "main":
                rest = [g for g, h in zip(got, hand) if h["i"] >= 5]
                c["labels.pairs.main.kappa_without_first5"] = f"{kappa(rest):.2f}"
                c["labels.pairs.main.hand_same_machine_diff"] = str(sum(y and not x for x, y in got))
                c["labels.pairs.main.hand_diff_machine_same"] = str(sum(x and not y for x, y in got))
    if (lab_dir / "useful.jsonl").exists():
        sample = json.loads((lab_dir / "useful_sample.json").read_text())
        hand = [json.loads(l) for l in (lab_dir / "useful.jsonl").read_text().splitlines()]
        for name, want in (("judge_yes", True), ("judge_no", False), ("planted", None)):
            rows = [h["label"] for h in hand if sample[h["i"]]["machine"] is want]
            c[f"labels.useful.{name}.hand_yes"] = f"{sum(rows)} of {len(rows)}"
    add_extra(c, run_dir)
    add_probes(c, run_dir)
    return c


def whole(x: float) -> str:
    return f"{x:.0f}".replace("-0", "0") if round(x) == 0 else f"{x:.0f}"


def add_extra(c: dict, run_dir: Path) -> None:
    """Slots, stated-or-brought-in, and the 16-item comparison (sprint.extra)."""
    path = run_dir / "extra.json"
    if not path.exists():
        return
    x = json.loads(path.read_text())
    for m, s in x["slots"].items():
        for i in (0, 7):
            put(c, f"slots.{m}.slot{i + 1}", s["common_share_by_slot"][i], 100, pct)
        put(c, f"slots.{m}.order", s["order_kept"], 100, pct)
        put(c, f"slots.{m}.opener", s["same_opener"], 100, pct)
    for m, o in x["origin"].items():
        put(c, f"origin.{m}.stated", o["stated_per_answer"])
        put(c, f"origin.{m}.brought", o["brought_per_answer"])
        put(c, f"origin.{m}.repeat_stated", o["repeat_stated"], 100, pct)
        put(c, f"origin.{m}.repeat_brought", o["repeat_brought"], 100, pct)
    for kind, row in x["sixteen"].items():
        if kind == "tokens":
            for arm, v in row.items():
                c[f"sixteen.tokens.{arm}"] = whole(v)
            continue
        put(c, f"sixteen.{kind}.distinct", row["distinct"])
        put(c, f"sixteen.{kind}.core", row["obvious_kept"], 100, pct)
        put(c, f"sixteen.{kind}.new", row["new"])
        if "same_person" in row:
            put(c, f"sixteen.{kind}.same", row["same_person"])


def add_probes(c: dict, run_dir: Path) -> None:
    """The missing-fact study (sprint.probes, sprint.probe_analyze)."""
    path = run_dir / "probe_results.json"
    if not path.exists():
        return
    r = json.loads(path.read_text())

    def block(prefix: str, b: dict) -> None:
        for name in ("decisive", "inert", "middle", "decisive_asks", "inert_asks", "middle_asks"):
            if b.get(name):
                put(c, f"{prefix}.{name}", b[name], 100, pct)
        for name in ("decisive_minus_inert", "decisive_minus_inert_asks"):
            if b.get(name):
                put(c, f"{prefix}.{name}", b[name], 100, whole)
                c[f"{prefix}.{name}.types"] = str(b[name][3])

    for st, n in r["n_probes"].items():
        c[f"probe.n.{st}"] = str(n)
    c["probe.n"] = str(sum(r["n_probes"].values()))
    for about, row in r["n_probes_by_about"].items():
        for st, n in row.items():
            c[f"probe.n.{about.split()[0]}.{st}"] = str(n)
    block("probe.plain", r["plain_pooled"])
    for m, b in r["plain_by_model"].items():
        block(f"probe.{m}", b)
    for arm, b in r["by_arm"].items():
        block(f"probe.arm.{arm.replace('+', '_')}", b)
    for arm, b in r["arm_vs_plain"].items():
        put(c, f"probe.vs.{arm.replace('+', '_')}.decisive", b["decisive"], 100, whole)
        put(c, f"probe.vs.{arm.replace('+', '_')}.asks", b["decisive_asks"], 100, whole)
    for band, row in r["by_mean_shift"].items():
        key = band.replace(" to ", "_").replace(".", "")
        c[f"probe.band.{key}.n"] = str(row["probes"])
        c[f"probe.band.{key}.hit"] = pct(100 * row["hit"])
        c[f"probe.band.{key}.asks"] = pct(100 * row["asks"])
    d, i = r["decisive_plain_rates"], r["inert_plain_rates"]
    c["probe.decisive.every_answer"] = str(d["every_answer"])
    c["probe.decisive.below_half"] = str(d["below_half"])
    c["probe.decisive.never_plain"] = str(len(r["never_raised_plain"]))
    c["probe.decisive.never_any"] = str(len(r["never_raised_any_arm"]))
    c["probe.inert.every_answer"] = str(i["every_answer"])
    c["probe.inert.below_half"] = str(i["below_half"])
    c["probe.inert.never"] = str(i["never"])
    for k, n in r["expected_vs_measured"].items():
        e, st = k.split("|")
        c[f"probe.drafter.{'yes' if e == 'changes the choice' else 'no'}.{st}"] = str(n)
    c["probe.drafter.yes"] = str(sum(n for k, n in r["expected_vs_measured"].items() if k.startswith("changes")))
    c["probe.drafter.no"] = str(sum(n for k, n in r["expected_vs_measured"].items() if k.startswith("does not")))
    if "stated" in r:
        put(c, "probe.stated.decisive", r["stated"]["decisive"], 100, pct)
        put(c, "probe.stated.inert", r["stated"]["inert"], 100, pct)
        c["probe.stated.n"] = f"{r['stated']['decisive'][4] + r['stated']['inert'][4]:,}"
    if "foreign" in r:
        c["probe.foreign.hits"], c["probe.foreign.n"] = str(r["foreign"]["hits"]), f"{r['foreign']['n']:,}"
        c["probe.foreign.rate"] = f"{100 * r['foreign']['rate']:.1f}%"

    rb = r.get("robust")
    if rb:
        block("probe.expected", rb["expected_to_change"])
        if rb["expected_not_to_change"].get("inert"):
            put(c, "probe.filler.inert", rb["expected_not_to_change"]["inert"], 100, pct)
        for m, b in rb["leave_one_out"].items():
            put(c, f"probe.loo.{m}.gap", b["decisive_minus_inert"], 100, whole)
            c[f"probe.loo.{m}.n_decisive"] = str(b["n_decisive"])
        c["probe.types.positive"] = f"{rb['by_type']['positive']} of {rb['by_type']['n']}"
        c["probe.types.min_gap"] = whole(100 * rb["by_type"]["min"])
        if "thresholds" in rb:
            c["probe.thresholds.min"] = whole(100 * rb["thresholds"]["min"])
            c["probe.thresholds.max"] = whole(100 * rb["thresholds"]["max"])

    alt = run_dir / "probe_results3.json"  # the same analysis with the three-option check deciding decisive and inert
    if alt.exists():
        q = json.loads(alt.read_text())
        for st, n in q["n_probes"].items():
            c[f"probe3.n.{st}"] = str(n)
        block("probe3.plain", q["plain_pooled"])

    def count(name: str) -> int:
        f = run_dir / name
        return sum(1 for _ in f.open()) if f.exists() else 0

    c["probe.check.calls"] = f"{count('probe_check2.jsonl'):,}"
    c["probe.check3.calls"] = f"{count('probe_check3.jsonl'):,}"
    if count("probe_check3.jsonl"):
        rows = [json.loads(l) for l in (run_dir / "probe_check3.jsonl").open()]
        c["probe.check3.other"] = pct(100 * sum(x.get("choice") == "other" for x in rows) / len(rows))
    hits = run_dir / "probe_hits.jsonl"
    if hits.exists():
        rows = [json.loads(l) for l in hits.open()]
        c["probe.judged.pairs"] = f"{len(rows):,}"
        c["probe.judged.answers"] = f"{len({(x['model'], x['task'], x['arm'], x['sample']) for x in rows}):,}"

    lab = run_dir / "labels" / "report.json"
    if lab.exists():
        row = json.loads(lab.read_text()).get("probes")
        if row:
            c["labels.probes.raised_agree"] = pct(row["raised_agreement"] * 100)
            c["labels.probes.raised_kappa"] = f"{row['raised_kappa']:.2f}"


def main() -> int:
    run_dir = Path(sys.argv[1])
    claims = build(run_dir)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "claims.json").write_text(json.dumps(claims, indent=1))
    (out / "claims.md").write_text("\n".join(f"- `{k}` = {v}" for k, v in claims.items()) + "\n")
    print(f"{len(claims)} claims -> {out / 'claims.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
