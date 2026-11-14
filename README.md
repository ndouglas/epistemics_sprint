# Do askers all get the same considerations?

Apart AI x Epistemics sprint, Nov 13–15, 2026. The design is in

## Layout

- `tasks/decisions.toml`: 8 decision types, two people each, 16 vignettes (frozen before any treatment run).
- `tasks/control.toml`: idea tasks (a dragon monster, a rain haiku) as the positive control.
- `arms/*.md`: one prompt per arm. `properties.md` is the treatment, in Nathan's words.
- `data/`: the 29 dimension names and the seed-word list.
- `models.toml`: model ids, thinking and effort settings, prices.
- `sprint/core.py`: tasks, arms, seeded draws, prompts, parsing.
- `sprint/run.py`: the runner.
- `runs/<name>/generations.jsonl`: one row per sample, with the full prompt, the draw, the raw answer, the items and the token counts.

## Arms

| Name | Design # | Answer shape |
|------|----------|--------------|
| `plain` | 1 | items |
| `think_diverse` | 2 | notes, items |
| `verbalized` | 3 | responses with probabilities |
| `what_else` | 4 | items (second turn, after a fresh plain answer) |
| `random_word` | 5 | notes, items |
| `properties` | 6a | properties, items |
| `properties_nudged` | 6b | properties, items |

Every arm returns exactly 8 items. A sample with the wrong count is retried twice, then recorded as `bad_count`.

## Use

```sh
uv sync
cp .env.example .env        # then put the API key in it

uv run pytest -q                                             # no network
uv run python -m sprint.run show --tasks tasks/control.toml  # print every arm's prompt, no API calls
uv run python -m sprint.run generate --model haiku --tasks tasks/control.toml --samples 2 --run smoke
uv run python -m sprint.run cost runs/smoke
```

`generate` is resumable: rerun the same command and it skips samples that already have an `ok` row.
Useful flags: `--arms plain,properties`, `--limit-tasks 2`, `--samples 10`, `--seed 0`, `--concurrency 8`.

## Notes

- No fallback model. If the named model declines, the row is recorded as a refusal.
- Thinking is off on both models and effort is set to `medium` outright, so no arm gets hidden reasoning. Output tokens are logged per sample.
- All seven arms run on Sonnet. Haiku and one non-Anthropic model run `--arms plain` only, for the cross-model overlap.
- These models reject a non-default temperature, so there is no temperature arm.

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
