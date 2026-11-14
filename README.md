# Does the briefing raise what would change the decision?

Code, data and report for a project done at the Apart Research AI x Epistemics sprint,
November 13 to 15, 2026. The report is [`report/build/report.pdf`](report/build/report.pdf).

Sixteen short vignettes describe a person facing a decision. Three models (Claude Haiku 5.5,
Claude Sonnet 5.5, GPT-5.5) are asked what the person should weigh. The project asks whether
those briefings raise the facts the vignette leaves out that would change the choice, more
often than the ones that would not, and how much the lists repeat from one ask to the next.

## Layout

- `tasks/decisions.toml`: 8 decision types, two people each, 16 vignettes. `tasks/options.toml`: the two options each vignette poses.
- `tasks/probes.toml`: 94 missing-fact probes, each a question with two possible answers.
- `arms/*.md`: one prompt per arm. `data/`: the 29 dimension names and the random-word list.
- `models.toml`: model ids and settings.
- `sprint/`: the code. `run.py` generates answers; `score.py` builds codebooks and judges relevance; `analyze.py` and `extra.py` compute the repetition numbers; `probes.py` drafts probes, runs the forced-choice check and the judge; `probe_analyze.py` computes the missing-fact numbers; `label.py` is the blind labeling tool; `claims.py` gathers every number the report states; `build_report.py` checks the report against them and renders it.
- `runs/main/`: every generated answer, forced choice, judge rating and hand label. `runs/rep` and `runs/coarse` are the two other codebook builds.
- `results/claims.md`: every number in the report, by id.
- `report/report.md`: the report's source. A number is written `[claim.id=value]`, and the build fails if it differs from the data.

## Reproduce the numbers (no API calls)

```sh
uv sync
uv run pytest -q
uv run python -m sprint.analyze runs/main
uv run python -m sprint.extra runs/main
uv run python -m sprint.probes decide runs/main --check-file probe_check2.jsonl
uv run python -m sprint.probe_analyze runs/main
uv run python -m sprint.figures runs/main
uv run python -m sprint.label report runs/main
uv run python -m sprint.claims runs/main
uv run python -m sprint.build_report        # needs pandoc and xelatex
```

## Rerun from scratch (API calls)

```sh
cp .env.example .env        # then add ANTHROPIC_API_KEY and OPENAI_API_KEY
uv run python -m sprint.run show --tasks tasks/decisions.toml     # print every prompt, no calls
uv run python -m sprint.run generate --model haiku --samples 10 --run main
uv run python -m sprint.run generate --model sonnet --arms plain --samples 10 --run main
uv run python -m sprint.run generate --model gpt --arms plain --samples 10 --run main
```

`generate` is resumable. The scoring commands are listed at the top of `sprint/score.py`
and `sprint/probes.py`.

## Notes

- No fallback model. If a model declines, the row is recorded as a refusal.
- Extended reasoning is off for every model, so no arm gets hidden reasoning.
- The arms other than `plain` ran on Haiku 5.5 only. In a pilot, Sonnet 5.5 refused the arms that ask it to write out its reasoning, and that was not worked around.
- Each arm returns a fixed number of items. A sample with the wrong count is retried twice, then recorded as `bad_count`.

## Missing-fact study: fixed before it ran (Nov 14)

Added after an adversarial review of the first analysis. Question: when a fact that
would change the decision is missing from the vignette, does a briefing raise it, more
often than it raises a missing fact that would not change the decision?

- **Probes** (`tasks/probes.toml`): drafted by GPT-5.5 from the vignette alone, edited by
  Nathan without looking at any generated answer, committed before any answer is scored.
- **Decisive or inert is measured.** Each probe has two possible answers. Three models
  each make a forced choice between the vignette's two options (`tasks/options.toml`)
  under each answer, 10 times. Shift = total-variation distance between the choice
  shares under the two answers. Decisive: shift >= 0.5 in at least 2 of 3 models.
  Inert: shift <= 0.1 in all 3. Anything else is set aside as "middle."
- **Primary check has two options only.** In a smoke test with invented inputs the models
  chose "something else" in 26 of 30 forced choices when it was offered, which would
  hide most shifts. So the two-option version defines decisive and inert; the
  three-option version is run as well and reported as a sensitivity check.
- **Scoring:** a judge that sees only the vignette, an answer's items and the probe
  questions marks each question as asked about, mentioned or absent. It never sees the
  arm, the model, the probe's answers or its status. A hit is "asks" or "mentions."
- **The one pre-named contrast:** hit rate on decisive probes minus hit rate on inert
  probes, plain prompt, three models pooled, paired by decision type, bootstrap over
  the eight types.
- **Controls:** the fact stated in the vignette (should be used); probes from a
  different decision type (should not hit); about 80 judge calls labeled blind by
  Nathan after 8 practice pairs.
- **Secondary, exploratory:** by model, by arm, 8 against 16 items, probes about the
  shape of the decision against probes about details, "asks" against "mentions," and
  the list of decisive probes that no answer raised.
