---
title: "Does the Briefing Raise What Would Change the Decision? Missing Facts in LLM Decision Advice"
author: |
  Nathan Douglas\
  Independent
abstract: |
  The sprint asks whether an AI briefing for a personal decision surfaces "the considerations that actually matter," and how one would know. For 16 decision vignettes, a model drafted and the author edited [probe.n=94] questions about facts the vignette leaves out, each with two possible answers. Three models made a forced choice between the person's two options under each answer; a fact is decisive if the answer flips the choice of at least two models and inert if it moves none. We checked whether briefings from the same three models, asked what the person should weigh, raise those facts. On a plain prompt, an automated judge found decisive facts raised in [probe.plain.decisive=94%] of cases and inert ones in [probe.plain.inert=56%]. The gap named in advance is [probe.plain.decisive_minus_inert=40] points; it is [probe.expected.decisive_minus_inert=26] with filler questions set aside, and it holds for each model. The author's blind labels were stricter than the judge about what counts as mentioning a fact, so the levels are uncertain. The clearer finding is that briefings seldom say what to do about a decisive unknown: [probe.plain.decisive_asks=30%] told the person to find it out. On one small model, prompts for variety did not reliably raise more decisive facts; a list twice as long asked about more of them. A person who asks twice, or asks another vendor's model, gets most of the same list back. The main limit: decisive means a fact flips these models' recommendation. Inert facts can still matter, and no person's choice or outcome was observed.
---

# 1. Introduction

People now ask language models what to think about before accepting a job, signing a lease or lending money to a relative. The sprint's prompt for epistemic products asks whether such a briefing "surface[s] the considerations that actually matter," and adds: how would you know? The second question is the hard one. Nearly everything a current model writes about a decision is relevant, so relevance does not separate a good briefing from a poor one, and a list can be made more varied by leaving out what matters most. An earlier measure in this project could count new considerations but not say whether they mattered.

We take a briefing's job to be leaving the person better placed to choose, and we measure a narrower thing. A short description of a decision leaves facts out, and some of them would change the advice. If the roof must be replaced this year for $28,000, all three models we tested say to keep renting; if it has five years left, two of them say to make the offer. A briefing that surfaces what matters should raise missing facts like that one more often than missing facts that change nothing. People are poor at noticing what a list leaves out (Fischhoff et al., 1978), so they are unlikely to supply these themselves.

We contribute a way to score a briefing against a reference standard (missing-fact probes whose status is measured by forced choice, with one contrast named in advance), a result on three current models (Section 4.1), a check on six prompts for variety (4.2) and a description of how much the lists repeat (4.3).

# 2. Related Work

**Decision briefings.** Cotton-Barratt et al. (2026), the design sketch this track draws on, list identifying critical uncertainties among the jobs of a deep briefing. The sprint suggests grading briefings against an expert's rubric; our method needs no expert, at the cost of a weaker standard.

**Shared models, shared outcomes.** When many decision-makers rely on one algorithm, overall decision quality can fall (Kleinberg and Raghavan, 2021) and the same individuals can be failed repeatedly (Bommasani et al., 2022). Goel et al. (2025) find that language models' mistakes grow more alike with capability, and Jiang et al. (2025) that models give similar answers to open-ended questions, within and across models. Section 4.3 measures this sameness in decision advice. Prompts for diversity such as verbalized sampling (Zhang et al., 2025) and chain-of-thought (Meincke et al., 2024) are scored on diversity; Section 4.2 scores six such prompts on decisive facts.

**Asking for what is missing.** QuestBench (Li et al., 2025) finds that models often cannot identify the one question needed to solve an underspecified reasoning problem, even when they can solve the fully specified version. ClarifyMT-Bench (Luo et al., 2025) reports that models in dialogue tend to answer before clarifying. Those tasks have a known missing variable and a correct answer; ours has neither.

# 3. Methods

**Decisions.** Sixteen vignettes of four sentences: 8 decision types (job offer, lease, first home, part-time graduate school, lending money to family, care for an aging parent, going freelance, moving for a partner's job), each with two people who differ in age, money and dependents, and each posing a choice between two courses of action. Every prompt asks, "What should this person weigh in making this decision?" and requires a fixed number of one-sentence considerations. We call a model's list a *briefing*.

**Prompts.** *Plain*: the vignette and the question, 8 items. Six prompts meant to widen the list, also 8 items: *think first, be diverse* (non-obvious considerations from different angles, after notes); *verbalized sampling*; *"What else?"*, a second turn after a plain briefing asking for 8 more; *random word*, think-first plus a random noun; a *property-substitution* prompt (name a few properties of the situation, change each, see what moves, then answer); and the same with three randomly drawn dimension names. Property substitution is one step of a practice taken from ideonomy (Gunkel; Kind); this is not a test of that practice. We later added *plain, 16 items*. Appendix B gives the wording.

**Models and samples.** All prompts ran on Claude Haiku 5.5, ten samples per vignette. The plain prompt also ran on Claude Sonnet 5.5 and GPT-5.5. Extended reasoning was off and sampling settings were the API defaults. This gave [n.answers=1,600] briefings and no refusals. The widening prompts ran on Haiku because, in a pilot on other tasks, Sonnet 5.5 refused prompts that ask it to write out its reasoning; we did not work around that.

**Missing-fact probes.** GPT-5.5 was shown each vignette alone and asked for six things it does not say that an adviser might want to know. Each *probe* is a question with two plausible answers, each a sentence that could be added to the vignette as a fact. The drafter was asked for some probes whose answer would change the choice, some whose answer would not (*fillers*), and some about the shape of the decision (is there a third option, is the deadline fixed). The author edited the list without consulting the briefings and dropped a few, leaving [probe.n=94]. The probes and the analysis plan were committed before any briefing was scored (Appendix C).

**Which probes are decisive.** We did not take the drafter's word. For each probe, each of the three models made a forced choice between the vignette's two options with answer A added to the vignette, and again with answer B, ten times each, with the order of the options randomized ([probe.check.calls=6,120] choices, including the vignette with no fact added). For each model, a probe's *shift* is how far the share of choices for one option moves between answer A and answer B. A probe is *decisive* if the shift is at least 0.5 for at least two of the three models, *inert* if it is at most 0.1 for all three, and otherwise *middle*. This gave [probe.n.decisive=22] decisive, [probe.n.inert=39] inert and [probe.n.middle=33] middle probes. The drafter's guesses were weak: of [probe.drafter.yes=65] probes it expected to change the choice, [probe.drafter.yes.decisive=21] were decisive and [probe.drafter.yes.inert=25] inert.

**Does a briefing raise the probe?** A judge (Sonnet 5.5) saw the vignette, one briefing and that vignette's probe questions, and marked each question *asks* (an item tells the person to find this out, check it or confirm it), *mentions* (an item raises the same matter without saying to find it out) or *absent*. It was told the item must concern the same specific unknown, not just the same topic. It never saw the prompt, the model, the probe's two answers or its status. A probe is *raised* if the label is asks or mentions. The judge rated [probe.judged.answers=1,760] lists (the [n.answers=1,600] briefings and the 160 plain first turns that the "What else?" turns followed), [probe.judged.pairs=10,340] list-question pairs.

**The contrast, named in advance.** The share of decisive probes raised minus the share of inert probes raised, on the plain prompt, pooled over the three models. The plan also named by-model, by-prompt and 8-against-16 comparisons as exploratory.

**Controls.** (a) *Fact stated:* for each decisive or inert probe we added each of its answers in turn to the vignette and collected plain briefings from each model ([probe.stated.n=732]); the judge, shown the original vignette, should find the matter raised. (b) *Foreign probes:* the judge rated briefings against probes written for a different decision type ([probe.foreign.n=1,800] pairs); it should find almost nothing. This is an easy negative and does not test near misses on the same topic. (c) *Hand labels:* the author labeled 80 list-question pairs blind to the judge's rating and before he was shown the study's results (Appendix D).

**Coding considerations.** For Section 4.3, Sonnet 5.5 built a codebook of distinct considerations for each decision type ([codebook.min=31] to [codebook.max=47] codes) and sorted every sentence under one code without seeing the prompt or model. A consideration is *obvious* for a vignette if it appears in at least half of Haiku's plain briefings for it (leaving out the briefing being scored), and *new* if it is not obvious and a judge rated it relevant. A further judge marked each as resting on a stated detail or brought in from outside. Hand labels agreed only moderately with the coding (Cohen's kappa, a chance-corrected agreement, [labels.pairs.main.kappa=0.39] to [labels.pairs.rep.kappa=0.63] across three codebook builds, below our bar of 0.7); the overlap findings held in all three (Appendix E).

**Statistics.** The unit is the decision type. Rates are computed per type and averaged over types; brackets are 95% percentile bootstrap intervals over types, which run narrow with so few units. One type (parent care) has no decisive probe, so differences involving decisive probes are paired over [probe.plain.decisive_minus_inert.types=7] types and can differ by a point or two from the difference of the rates shown.

# 4. Results

## 4.1 Plain briefings raise decisive probes more often than inert ones

![Left: share of plain briefings that raise a probe; the dark part of each bar is briefings that tell the person to find it out. Right: the same for decisive probes under each prompt on Haiku 5.5. Whiskers are 95% bootstrap intervals over decision types for the full bar. Ratings are the automated judge's.](figures/probes.png){width=84%}

On the plain prompt, by the judge's ratings, a briefing raised a decisive probe [probe.plain.decisive=94%] of the time [[probe.plain.decisive.ci=87% to 99%]] and an inert one [probe.plain.inert=56%] of the time [[probe.plain.inert.ci=46% to 67%]] ([probe.plain.inert_paired=54%] in the seven paired types). The difference named in advance is [probe.plain.decisive_minus_inert=40] points [[probe.plain.decisive_minus_inert.ci=31 to 49]]. It holds for each model (Figure 1): Haiku [probe.haiku.decisive=88%] against [probe.haiku.inert=47%], Sonnet [probe.sonnet.decisive=96%] against [probe.sonnet.inert=59%], GPT-5.5 [probe.gpt.decisive=97%] against [probe.gpt.inert=63%].

There is a step and no slope: middle probes were raised [probe.plain.middle=57%] of the time, the same as inert ones. Of the [probe.n.decisive=22] decisive probes, [probe.decisive.every_answer=16] were raised by all 30 plain briefings for their vignette, and only [probe.decisive.never_plain=1] by fewer than half. That one was raised by none of the 30: whether Maya, weighing a startup offer against her current job, has any other prospect in hand. (Told she has a final interview next week, two of the three models switched from "accept" to "stay.") It was the only decisive probe about an option outside the two on the table.

**Controls.** With the fact stated in the vignette, briefings raised the matter [probe.stated.decisive=99%] (decisive) and [probe.stated.inert=95%] (inert) of the time, so the judge finds a matter when it is there. Against probes from a different decision type it marked [probe.foreign.hits=63] of [probe.foreign.n=1,800] as raised ([probe.foreign.rate=3.5%]).

**The gap survives four checks, at 26 to 44 points.** Checks 1 to 3 were added after an AI review of the first draft. (1) *Fillers.* Inert probes that the drafter meant as fillers were raised only [probe.filler.inert=32%] of the time. Among probes the drafter expected to matter, the gap is [probe.expected.decisive_minus_inert=26] points [[probe.expected.decisive_minus_inert.ci=17 to 37]] ([probe.expected.decisive=94%] against [probe.expected.inert=70%]); about a third of the planned gap comes from fillers. (2) *Circularity.* If two models define decisive and inert and the third model's briefings are scored, the gap is [probe.loo.haiku.gap=44] points for Haiku, [probe.loo.sonnet.gap=41] for Sonnet and [probe.loo.gpt.gap=36] for GPT-5.5 (on [probe.loo.haiku.n_decisive=18], [probe.loo.sonnet.n_decisive=9] and [probe.loo.gpt.n_decisive=7] decisive probes), so a model raises what moves the other models' choices. (3) *Types and thresholds.* The gap is positive in [probe.types.positive=7 of 7] decision types (smallest [probe.types.min_gap=19] points) and stays between [probe.thresholds.min=33] and [probe.thresholds.max=45] points across other cutoffs for decisive (0.3 to 0.8) and inert (0 to 0.2). (4) *A third option.* With "something else" offered in the forced choice, which the models chose [probe.check3.other=59%] of the time, many probes change group and the gap is [probe3.plain.decisive_minus_inert=37] points [[probe3.plain.decisive_minus_inert.ci=10 to 62]]. The plan named the two-option version as primary.

**Hand labels: the levels are uncertain.** On 80 list-question pairs labeled blind, the author agreed with the judge on raised against absent in [labels.probes.raised_agree=79%] (kappa [labels.probes.raised_kappa=0.57]). He called raised [labels.probes.judge_asks.hand_raised=24 of 27] of the judge's "asks" and [labels.probes.judge_absent.hand_raised=2 of 27] of its "absent," but only [labels.probes.judge_mentions.hand_raised=14 of 26] of its "mentions": where the judge saw the same unknown, he often saw only the same topic. Applying those shares to the judge's ratings puts plain briefings near [labels.probes.hand_standard.decisive=62%] for decisive probes and [labels.probes.hand_standard.inert=38%] for inert ones. This restatement cannot test the gap, since it assumes the judge is equally lenient on both kinds; the only direct evidence is that he rejected [labels.probes.decisive.judge_raised_hand_absent=2 of 12] of the judge's "raised" calls on decisive probes and [labels.probes.inert.judge_raised_hand_absent=8 of 20] on inert ones. One human rater cannot settle which reading of "mentions" is right. Neither reading contradicts the direction of the contrast; the rates themselves are uncertain.

**Mentioning is not asking.** A briefing can raise a missing fact by weighing it ("the roof may be a major cost") or by telling the person to find it out ("get a roofer's estimate before Sunday"). Plain briefings told the person to find out a decisive probe's fact [probe.plain.decisive_asks=30%] of the time [[probe.plain.decisive_asks.ci=22% to 38%]], against [probe.plain.inert_asks=11%] for inert ones. The models differ here more than anywhere else: Sonnet [probe.sonnet.decisive_asks=44%], Haiku [probe.haiku.decisive_asks=26%], GPT-5.5 [probe.gpt.decisive_asks=20%]. This is the rating on which the judge and the author agreed best.

## 4.2 Prompts that make the list less obvious do not raise more decisive probes

| Prompt (Haiku 5.5) | New per briefing | Decisive raised | Inert raised | Decisive: told to find out |
|:------------------------|---:|---:|---:|---:|
| Plain, 8 items | [fix.plain.good=2.3] | [probe.arm.plain.decisive=88%] | [probe.arm.plain.inert=47%] | [probe.arm.plain.decisive_asks=26%] |
| Verbalized sampling | [fix.verbalized.good=2.8] | [probe.arm.verbalized.decisive=87%] | [probe.arm.verbalized.inert=40%] | [probe.arm.verbalized.decisive_asks=15%] |
| Property substitution | [fix.properties.good=3.1] | [probe.arm.properties.decisive=89%] | [probe.arm.properties.inert=44%] | [probe.arm.properties.decisive_asks=35%] |
| Same, + random dimensions | [fix.properties_nudged.good=3.1] | [probe.arm.properties_nudged.decisive=87%] | [probe.arm.properties_nudged.inert=46%] | [probe.arm.properties_nudged.decisive_asks=27%] |
| Random word | [fix.random_word.good=3.9] | [probe.arm.random_word.decisive=87%] | [probe.arm.random_word.inert=40%] | [probe.arm.random_word.decisive_asks=19%] |
| Think first, be diverse | [fix.think_diverse.good=4.0] | [probe.arm.think_diverse.decisive=79%] | [probe.arm.think_diverse.inert=41%] | [probe.arm.think_diverse.decisive_asks=21%] |
| "What else?" turn, read alone | [fix.what_else.good=5.2] | [probe.arm.what_else.decisive=45%] | [probe.arm.what_else.inert=31%] | [probe.arm.what_else.decisive_asks=8%] |
| Plain, then "What else?" (16 items) | n/a | [probe.arm.plain_what_else.decisive=96%] | [probe.arm.plain_what_else.inert=61%] | [probe.arm.plain_what_else.decisive_asks=33%] |
| Plain, 16 items | n/a | [probe.arm.plain16.decisive=96%] | [probe.arm.plain16.inert=57%] | [probe.arm.plain16.decisive_asks=45%] |

Table: Each prompt on Haiku 5.5, means over decision types, by the judge's ratings. *New per briefing*: relevant considerations outside the vignette's obvious ones (of 8; not scored for 16-item lists). *Decisive raised*, *Inert raised*: share of such probes a briefing raises. *Told to find out*: share of decisive probes it tells the person to find out.

Before the probes existed we had scored the six widening prompts by new considerations per briefing. On that score all beat plain, from verbalized sampling (+[vs.verbalized.good=0.5]) to the "What else?" turn (+[vs.what_else.good=2.8]), though "obvious" is defined from plain briefings, so part of that is built in. The probes give a different picture (Table 1). No widening prompt raised reliably more decisive probes than plain. The prompt that scored highest on new considerations, the "What else?" turn read without the briefing before it, raised about half as many ([probe.arm.what_else.decisive=45%]); it had been told not to repeat the first list. Think-first did not reliably differ from plain ([probe.vs.think_diverse.decisive=-9] points, lower in [probe.vs.think_diverse.decisive.lower=3 of 7] types).

What length changed was asking. A plain 16-item list told the person to find out decisive facts [probe.arm.plain16.decisive_asks=45%] of the time, [probe.vs.plain16.asks=19] points more than the 8-item list and higher in [probe.vs.plain16.asks.higher=7 of 7] types. It raised [probe.arm.plain16.decisive=96%] against [probe.arm.plain.decisive=88%], but that difference is higher in only [probe.vs.plain16.decisive.higher=4 of 7] types and mostly comes from one. It also raised more inert probes, so it is longer, not more selective: the gap between decisive and inert, paired by type, stayed between [probe.arm.think_diverse.decisive_minus_inert=36] and [probe.arm.verbalized.decisive_minus_inert=49] points for every prompt except the "What else?" turn alone.

These are about 16 unadjusted comparisons on seven units, so none is firm. Two others were consistent across types: property substitution, the author's own prompt, told the person to find out decisive facts more often than plain (+[probe.vs.properties.asks=9] points, higher in [probe.vs.properties.asks.higher=7 of 7] types), and verbalized sampling less often ([probe.vs.verbalized.asks=-11], lower in [probe.vs.verbalized.asks.lower=7 of 7]).

## 4.3 Asking again returns most of the same list

**Across asks and across vendors.** Two plain briefings for the same vignette from the same model share [collapse.haiku.same=5.3] of 8 considerations on Haiku, [collapse.sonnet.same=5.4] on Sonnet and [collapse.gpt.same=5.2] on GPT-5.5 (Appendix E, Figure 2). Briefings from two different models share [cross.gpt_haiku=4.6] to [cross.haiku_sonnet=4.8]. Taking the question to another vendor's model is close to asking the first one again, so their agreement is weak evidence that the list is complete. The lists are fitted to the person: two people facing the same kind of decision share only [collapse.sonnet.two=1.5] of 8 (Sonnet; the others are alike). Ten asks of one model reach [collapse.sonnet.in10=16.1] distinct considerations, twice what one briefing holds.

**Most of it rests on what the vignette states.** About [origin.haiku.stated=6.2] of the roughly 8 considerations in a Haiku briefing rest on a detail the vignette states, and those reappear on a second ask [origin.haiku.repeat_stated=72%] of the time. The [origin.haiku.brought=1.6] brought in from outside reappear [origin.haiku.repeat_brought=41%] of the time.

# 5. Discussion and Limitations

On these vignettes plain briefings are selective toward facts that move the models' choice. By the judge's reading few decisive facts go unraised, which we did not expect; by the author's stricter reading, more than a third may. Briefings tell the person to find a decisive fact out about a third of the time. We cannot say whether that is too few: some decisive facts the person already knows (their other prospects, their savings), and for those a mention is enough.

**Limits.**

1. *Decisive means "flips the models' recommendation," and inert does not mean unimportant.* The models that write the briefings also define what is decisive. Leaving one model out shows a model raises what moves the others, but the three may share blind spots, and facts that matter to a person but move no model are invisible here. Several inert probes plainly matter (how much care a parent needs, whether a third option exists), and briefings were arguably right to raise them. A larger gap is therefore not a better briefing. The fix is the choices of people who have faced the decision, or outcomes.
2. *The probes come from a model,* so facts no model would think of are not in the set. The author edited them but did not write them. Each probe's two answers were chosen to be far apart, with no estimate of how likely each is.
3. *A two-option forced choice cannot see everything.* Facts about the shape of the decision (a third option, a soft deadline) rarely shift a choice between two fixed options: only [probe.n.shape.decisive=2] of the 30 such probes were decisive.
4. *Raised is a loose bar.* A briefing that walks through each stated detail will mention the unknowns attached to it, which may be habit and not judgment about what matters. Telling the person to find out is the stricter measure and the one the author's labels supported, though the judge also counts "confirm" or "check" as asking.
5. *Small and invented.* Sixteen vignettes written by a model, ten samples each, [probe.n.decisive=22] decisive probes over [probe.plain.decisive_minus_inert.types=7] decision types. The judges are models, checked by one person who knew the hypotheses (Appendix D).
6. *The prompt comparison is exploratory:* one small model, one wording per prompt. The missing-fact study itself was designed partway through, after an AI review of the first analysis, and committed before it ran (Appendix C).

# 6. Conclusion

Whether a briefing surfaces what matters can be approximated by asking what the description leaves out, measuring which of those facts flip a model's choice, and checking whether the briefing raises them. On that test, plain briefings from three current models raise decisive facts more often than inert ones and tell the person to find them out about a third of the time; on one small model, in an exploratory comparison, prompts for variety did not help and a longer list asked about more of them. Most of the list repeats from one ask or vendor to the next. The step that would make the method trustworthy is replacing the models' forced choice with people's.

<!-- appendices -->

# Code and Data

Code, prompts, vignettes, probes, every briefing, forced choice, judge rating, hand label and the register of claims are at <https://github.com/ndouglas/epistemics_sprint>. `uv run python -m sprint.build_report` checks every tagged number in this report against the data before rendering it; counts written out in the prose were checked by hand.

# References

- Bommasani, R., Creel, K. A., Kumar, A., Jurafsky, D., & Liang, P. (2022). Picking on the same person: Does algorithmic monoculture lead to outcome homogenization? *NeurIPS 2022*. arXiv:2211.13972.
- Cotton-Barratt, O., Vaintrob, L., Sourbut, O., & Hadshar, R. (2026). Design sketches: Angels-on-the-shoulder. Forethought. https://www.forethought.org/research/design-sketches-angels-on-the-shoulder
- Fischhoff, B., Slovic, P., & Lichtenstein, S. (1978). Fault trees: Sensitivity of estimated failure probabilities to problem representation. *Journal of Experimental Psychology: Human Perception and Performance*, 4(2), 330–344.
- Goel, S., Strüber, J., Auzina, I. A., Chandra, K. K., Kumaraguru, P., Kiela, D., Prabhu, A., Bethge, M., & Geiping, J. (2025). Great models think alike and this undermines AI oversight. *ICML 2025*, PMLR 267. arXiv:2502.04313.
- Gunkel, P. *Ideonomy: The Science of Ideas.* Unpublished manuscripts.
- Jiang, L., et al. (2025). Artificial Hivemind: The open-ended homogeneity of language models (and beyond). arXiv:2510.22954.
- Kind, G. Ideonomy. https://gracekind.net/writing/ideonomy/intro
- Kleinberg, J., & Raghavan, M. (2021). Algorithmic monoculture and social welfare. *PNAS*, 118(22), e2018340118.
- Li, B. Z., Kim, B., & Wang, Z. (2025). QuestBench: Can LLMs ask the right question to acquire information in reasoning tasks? *NeurIPS 2025 Datasets and Benchmarks*. arXiv:2503.22674.
- Luo, S., Huang, Y., Li, M., Meng, S., Liu, F., Hu, Z., Feng, J., & Liu, Q. (2025). ClarifyMT-Bench: Benchmarking and improving multi-turn clarification for conversational large language models. arXiv:2512.21120.
- Meincke, L., Mollick, E. R., & Terwiesch, C. (2024). Prompting diverse ideas: Increasing AI idea variance. arXiv:2402.01727.
- Zhang, J., Yu, S., Chong, D., Sicilia, A., Tomz, M. R., Manning, C. D., & Shi, W. (2025). Verbalized sampling: How to mitigate mode collapse and unlock LLM diversity. arXiv:2510.01171.

# Appendix A. Limitations and Dual-Use / Ethical Considerations

Section 5 lists the limits of the evidence. This appendix covers how the work could mislead or be misused.

**The headline could be over-read as "AI decision advice is fine."** The result is that briefings raise the facts that flip the same models' forced choices on invented vignettes. It does not show that people who follow such briefings decide better, that the briefings are accurate, or that they cover what matters to a particular person. A product team should not cite it as validation.

**The method can be gamed.** A briefing could be tuned to score well on a known probe set, or padded to raise everything: the 16-item list raises more inert facts as well. The gap can be raised by dropping inert facts that matter, the same fault Section 4.2 finds in a count of new considerations, and the find-out rate by phrasing every item as "confirm X." Any use of the score should report the inert rate beside the decisive rate, read what was dropped, and keep probes unseen by whoever tunes the prompt. A score built from a model's own sensitivities can also entrench that model's blind spots, since facts it does not respond to never count against it.

**Nudging people to ask more has costs.** Telling someone to "find out" a fact before deciding can be good advice or a way to delay and offload. Finding out is worth it only when the fact is unknown to the person, cheap to get and likely to change the choice; for inert facts it sends people on errands that change nothing.

**Sameness cuts both ways.** Section 4.3 treats repetition across asks and vendors as a risk, because a person cannot get an independent second view. It is also a virtue: the same question gets the same advice, and outsiders can audit a shared list. Deliberately varying which considerations reach which people would let whoever controls the variation steer decisions without any single briefing looking wrong. We would want any such system logged and open to audit.

**Advice domains.** The vignettes touch money, housing, elder care and relationships. The briefings were generated for invented people and were not checked for correctness; nothing here is advice. No human participants were involved, and the vignettes describe no real person.

**Dual use.** We see little direct misuse potential in a scoring method for advice lists. The probe-and-forced-choice step does show which single added facts flip a model's recommendation, which could help someone craft a description that steers a model's advice.

# Appendix B. Prompts

The plain prompt is the vignette, the question, and "Give exactly 8 considerations, one sentence each." The other prompts add the text below to the same opening. All prompts, the 16 vignettes, the 29 dimension names and the 110 random words are in the repository as run.

**Think first, be diverse.** "Aim for considerations that are non-obvious and unconventional, beyond what most people would list first. Be diverse: each one should come from a different angle than the others. Before you answer, think it through in the `notes` field. Take your time there and work out what you want to say and why."

**Random word.** As above, with "Here is a random word to draw on for inspiration: (word)."

**"What else?"** Second turn: "What else? Give exactly 8 more considerations that you haven't mentioned yet, one sentence each."

**Property substitution.** "Before you answer, work through it this way, recording what you do in the `properties` field. First ask what this situation is, to this person, at this time. Not the kind of situation in general: this one, for them, now. Then name a few properties of the situation that matter from where they stand. Pick properties that can vary independently of each other. For each property, change its value to something else and see what happens to the rest of the situation: what else has to move, and what the change shows. Record each property's `name` and the `alternative` value you tried. Then give exactly 8 considerations, one sentence each, drawing on what the variations showed."

**Property substitution + random dimensions.** The same, then "As you choose which properties to look at, let these dimensions steer you: (three names)." The names are drawn from a list of 29 such as scope, reversibility and rate.

**Verbalized sampling** uses the standard wording from its authors' repository, with 8 responses.

**Forced choice.** The vignette, then one probe answer as a sentence, then "Which should this person do?" with the two options lettered A and B in random order and "Answer with the letter only."

**Judge.** "An adviser gave a person a short list of things to weigh in a decision. Separately, we have a list of questions about things the person's description leaves out. For each question, say whether the adviser's list raises it. *asks*: some item tells the person to find this out, check it, confirm it or ask about it. *mentions*: some item raises this same matter and weighs it, but does not tell the person to find it out. *absent*: no item raises it. The item must be about the same specific unknown as the question, not merely the same topic." An example about adopting a dog follows; the full text is in the repository.

# Appendix C. The missing-fact study: plan, probes and departures

**What was fixed, and when.** All times are US Eastern on Saturday, November 14. The vignettes and the seven 8-item prompts were committed at 10:51, before any prompt was run on a vignette (smoke runs on two unrelated idea tasks came earlier). After an adversarial review of the first analysis concluded that it measured novelty and not importance, we wrote the missing-fact plan into the repository's README and committed it with the scoring code while the probes were still being edited (commit `906ee4b`, 13:06). The probes were committed after the author's edits and before any answer was judged against them (`845ad25`, 15:09). The main judging finished before the forced choices did, so no probe's status existed while it ran; the two control runs were judged afterward. Commit messages were edited before the repository was published, to remove links to the working session; contents, order and dates are unchanged, and the hashes above are those of the published history. The plan named: how probes are drafted and edited; the forced-choice check and its thresholds (0.5 in two of three models; 0.1 in all three); the two-option check as primary and the three-option check as a sensitivity analysis, chosen after a smoke test on invented inputs in which models picked "something else" in 26 of 30 choices; the judge's three labels; the one contrast; and the three controls.

**Departures and things done after seeing data.** (1) The drafter put calendar dates in many answers, which read as being in the past. The drafting model rewrote 61 answer lines into relative time; the author checked them and repaired those that no longer fit the vignette. This was before the freeze. (2) The plan said the bootstrap would run over eight decision types; one type has no decisive probe, so differences are paired over seven. (3) The plan named the comparisons by model, by prompt and of 8 against 16 items as exploratory. The comparison of the drafter's guesses with the measured status and the comparison with "new per briefing" were not in the plan, and the checks on the contrast other than the three-option run were added after an AI review of the first draft. (4) The author discussed his eight unscored practice labels with Claude before labeling the scored pairs, and after the results he marked three of his blind labels as mistakes; those are reported separately in Appendix D and not used in the main text.

**Examples of probes.**

| Status | Vignette | Question | Answer A / Answer B |
|:-----------|:---------|:----------------|:----------------------|
| Decisive | First home | What would the roof replacement likely cost and how soon is it needed? | Must be replaced within 12 months at $28,000 / can last five more years, about $11,000 |
| Decisive, never raised (plain) | Job offer | Is there a third active option besides staying and taking the startup offer? | A final interview next Tuesday for a $90,000 role at an insurer / no other applications or offers |
| Inert, always raised | Moving for a partner | Has the boyfriend made a concrete commitment about their future together? | He has bought a ring and wants to marry within a year / he will not discuss engagement for two more years |
| Inert, never raised | Parent care | What is the assisted living facility's pet policy? | One cat allowed with a deposit / no pets |

The third row shows what inert does and does not mean: all three models recommended the same option under either answer, and every plain briefing raised the question anyway. A reader may well think the briefings were right to.

# Appendix D. Hand labels

**Labels for the missing-fact judge.** In a terminal tool that showed the vignette, one briefing and one probe question (never the judge's rating, the prompt, the model or the probe's status), the author marked each pair asks, mentions or absent. The sample was drawn in roughly equal numbers from each of the judge's three labels, across all prompts and models. The first [labels.probes.practice=8] pairs were unscored practice, which he discussed with Claude to settle where the line falls; Claude had by then seen the study's results but did not look at the judge's ratings for those pairs. The 80 scored pairs followed without discussion. The results were computed and written up while he labeled and were kept from him until he finished; beforehand he had been told only how many probes fell in each group, how the drafter's guesses fared and the foreign-probe rate. He had seen the earlier repetition results. Exact agreement on three labels was [labels.probes.agree=71%] (kappa [labels.probes.kappa=0.57]); on raised against absent, [labels.probes.raised_agree=79%] (kappa also [labels.probes.raised_kappa=0.57]). By the judge's label he agreed exactly on [labels.probes.judge_asks.hand_same=22 of 27] asks, [labels.probes.judge_mentions.hand_same=10 of 26] mentions and [labels.probes.judge_absent.hand_same=25 of 27] absent. Of the 26 pairs the judge called mentions, he called 12 absent and 4 asks. The judge's "asks" and "absent" held up; about half of its "mentions" were same-topic near misses by the author's reading. He was unsure of several, and a second human rater would be needed to say whether the judge is lenient or he is strict.

*After the results.* Once the labels were scored, the author read the pairs where he and the judge disagreed, discussed them with Claude, and judged [labels.probes.revised.n=3] of his own "absent" labels to be mistakes (a list that proposed a trial period or delayed start, for the question about a third option; one that told the person to assess the care needed; one that told them to research moving costs). These corrections are not blind, are stored in a separate file, and change nothing in the main text. With them, agreement on raised against absent is [labels.probes.revised.raised_agree=82%] (kappa [labels.probes.revised.raised_kappa=0.64]), he calls raised [labels.probes.revised.judge_mentions.hand_raised=16 of 26] of the judge's mentions, and the restated rates become [labels.probes.revised.hand_standard.decisive=68%] and [labels.probes.revised.hand_standard.inert=42%], a gap of [labels.probes.revised.hand_standard.gap=25] points. The restated rates in Section 4.1 apply, for each of the judge's three ratings, the share he called raised to the judge's mix of ratings on the plain prompt, pooled over briefings. Those shares come from pairs drawn across all prompts and probe groups, not from plain briefings alone.

**Earlier labels, for the coding in Section 4.3.** The author labeled 60 pairs of sentences as the same consideration or different, blind to the codes, a third of them chosen to be the coder's hardest cases (different codes, most similar wording). He agreed with the main coding on [labels.pairs.main.agree=70%] (Cohen's kappa [labels.pairs.main.kappa=0.39]; [labels.pairs.rep.kappa=0.63] and [labels.pairs.coarse.kappa=0.56] for the two other builds), below the 0.7 we had set as the bar. The coder splits finer than he does: he called [labels.pairs.main.hand_same_machine_diff=13] pairs the same that the coder had split, against [labels.pairs.main.hand_diff_machine_same=5] the reverse. He discussed his first five pairs with Claude, which had not seen the codes; without them kappa is [labels.pairs.main.kappa_without_first5=0.36]. On 40 relevance ratings he accepted [labels.useful.judge_yes.hand_yes=17 of 17] of the judge's acceptances, rejected all 6 items planted from other decisions, and accepted [labels.useful.judge_no.hand_yes=12 of 17] of the judge's rejections. Relevance is a low bar that nearly every generated consideration clears, which is why Section 4.2 does not treat "new" as a measure of what matters.

# Appendix E. The repetition findings under three codebooks

How finely to split considerations is a judgment, so the same sentences were coded three times: the main build; a rebuild from a different random sample of sentences; and a coarse build with the instruction for doubtful cases reversed from "keep them separate" to "treat them as one," made after seeing the hand labels.

| | Main | Rebuilt | Coarse |
|:--------------------------------------|---:|---:|---:|
| Considerations per decision type | [codebook.min=31] to [codebook.max=47] | [rep.codebook.min=33] to [rep.codebook.max=51] | [coarse.codebook.min=20] to [coarse.codebook.max=37] |
| Kappa with the hand labels (60 pairs) | [labels.pairs.main.kappa=0.39] | [labels.pairs.rep.kappa=0.63] | [labels.pairs.coarse.kappa=0.56] |
| Shared, same person, Sonnet twice | [collapse.sonnet.same=5.4] | [rep.collapse.sonnet.same=5.4] | [coarse.collapse.sonnet.same=5.8] |
| Shared, same person, GPT-5.5 then Haiku | [cross.gpt_haiku=4.6] | [rep.cross.gpt_haiku=4.6] | [coarse.cross.gpt_haiku=5.0] |
| Shared, two people, Sonnet | [collapse.sonnet.two=1.5] | [rep.collapse.sonnet.two=1.8] | [coarse.collapse.sonnet.two=2.2] |
| New per briefing: plain | [fix.plain.good=2.3] | [rep.fix.plain.good=2.7] | [coarse.fix.plain.good=1.5] |
| New per briefing: property substitution | [fix.properties.good=3.1] | [rep.fix.properties.good=3.1] | [coarse.fix.properties.good=2.1] |
| New per briefing: think first, be diverse | [fix.think_diverse.good=4.0] | [rep.fix.think_diverse.good=4.0] | [coarse.fix.think_diverse.good=2.9] |
| New per briefing: "What else?" turn | [fix.what_else.good=5.2] | [rep.fix.what_else.good=5.3] | [coarse.fix.what_else.good=4.1] |

Table: The same sentences under three codings. The pairs for the hand labels were drawn to stress the main build, so its kappa is not comparable with the other two.

A coarser codebook finds more overlap and fewer distinct considerations. The pattern does not move: a repeat ask returns 5 to 6 of 8, a second model nearly as many, two people 1 to 3, and the prompts keep their order. The slot, stated-detail and 16-item analyses were run on the main build only. The missing-fact study does not use the codebooks.

![Left: considerations shared by two answers to the plain prompt, of 8. Right: distinct considerations accumulated as one person asks repeatedly. Bars and lines are means over 8 decision types; whiskers are 95% bootstrap intervals.](figures/collapse.png){width=62%}

\FloatBarrier

# LLM Usage Statement

This project was done in a weekend by one person working with Claude (Anthropic's Claude Code). The author chose the question, supplied the property practice behind one of the prompts, approved the vignettes and every prompt before they were frozen, decided to add the missing-fact study and approved its plan, edited the probes, labeled the validation samples by hand, and read this report for overclaims. He wrote the property-substitution prompt; Claude drafted the vignettes and the other prompts for his approval, wrote the code, ran the experiments and the analysis, convened simulated reviewers (Claude instances) whose criticism led to the missing-fact study, and wrote this report. GPT-5.5 drafted the probes. Claude Sonnet 5.5 is the judge and coder, and Claude Haiku 5.5, Claude Sonnet 5.5 and GPT-5.5 are the models studied. Every tagged number in the report is checked against the released data by the build. Errors are the author's.
