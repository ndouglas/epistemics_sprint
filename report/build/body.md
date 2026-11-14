---
title: "Does the Briefing Raise What Would Change the Decision? Missing Facts in LLM Decision Advice"
author: |
  Nathan Douglas\
  Independent
abstract: |
  The sprint asks whether an AI briefing for a personal decision surfaces "the considerations that actually matter," and how one would know. For 16 decision vignettes, a model drafted and the author edited 94 questions about facts the vignette leaves out, each with two possible answers. Three models made a forced choice between the person's two options under each answer; a fact is decisive if the answer flips the choice of at least two models and inert if it moves none. We checked whether briefings from the same three models, asked what the person should weigh, raise those facts. On a plain prompt, an automated judge found decisive facts raised in 94% of cases and inert ones in 56%. The gap named in advance is 40 points; it is 26 with filler questions set aside, and it holds for each model. The author's blind labels were stricter than the judge about what counts as mentioning a fact, so the levels are uncertain. The clearer finding is that briefings seldom say what to do about a decisive unknown: 30% told the person to find it out. On one small model, prompts for variety did not reliably raise more decisive facts; a list twice as long asked about more of them. A person who asks twice, or asks another vendor's model, gets most of the same list back. The main limit: decisive means a fact flips these models' recommendation. Inert facts can still matter, and no person's choice or outcome was observed.
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

**Models and samples.** All prompts ran on Claude Haiku 5.5, ten samples per vignette. The plain prompt also ran on Claude Sonnet 5.5 and GPT-5.5. Extended reasoning was off and sampling settings were the API defaults. This gave 1,600 briefings and no refusals. The widening prompts ran on Haiku because, in a pilot on other tasks, Sonnet 5.5 refused prompts that ask it to write out its reasoning; we did not work around that.

**Missing-fact probes.** GPT-5.5 was shown each vignette alone and asked for six things it does not say that an adviser might want to know. Each *probe* is a question with two plausible answers, each a sentence that could be added to the vignette as a fact. The drafter was asked for some probes whose answer would change the choice, some whose answer would not (*fillers*), and some about the shape of the decision (is there a third option, is the deadline fixed). The author edited the list without consulting the briefings and dropped a few, leaving 94. The probes and the analysis plan were committed before any briefing was scored (Appendix C).

**Which probes are decisive.** We did not take the drafter's word. For each probe, each of the three models made a forced choice between the vignette's two options with answer A added to the vignette, and again with answer B, ten times each, with the order of the options randomized (6,120 choices, including the vignette with no fact added). For each model, a probe's *shift* is how far the share of choices for one option moves between answer A and answer B. A probe is *decisive* if the shift is at least 0.5 for at least two of the three models, *inert* if it is at most 0.1 for all three, and otherwise *middle*. This gave 22 decisive, 39 inert and 33 middle probes. The drafter's guesses were weak: of 65 probes it expected to change the choice, 21 were decisive and 25 inert.

**Does a briefing raise the probe?** A judge (Sonnet 5.5) saw the vignette, one briefing and that vignette's probe questions, and marked each question *asks* (an item tells the person to find this out, check it or confirm it), *mentions* (an item raises the same matter without saying to find it out) or *absent*. It was told the item must concern the same specific unknown, not just the same topic. It never saw the prompt, the model, the probe's two answers or its status. A probe is *raised* if the label is asks or mentions. The judge rated 1,760 lists (the 1,600 briefings and the 160 plain first turns that the "What else?" turns followed), 10,340 list-question pairs.

**The contrast, named in advance.** The share of decisive probes raised minus the share of inert probes raised, on the plain prompt, pooled over the three models. The plan also named by-model, by-prompt and 8-against-16 comparisons as exploratory.

**Controls.** (a) *Fact stated:* for each decisive or inert probe we added each of its answers in turn to the vignette and collected plain briefings from each model (732); the judge, shown the original vignette, should find the matter raised. (b) *Foreign probes:* the judge rated briefings against probes written for a different decision type (1,800 pairs); it should find almost nothing. This is an easy negative and does not test near misses on the same topic. (c) *Hand labels:* the author labeled 80 list-question pairs blind to the judge's rating and before he was shown the study's results (Appendix D).

**Coding considerations.** For Section 4.3, Sonnet 5.5 built a codebook of distinct considerations for each decision type (31 to 47 codes) and sorted every sentence under one code without seeing the prompt or model. A consideration is *obvious* for a vignette if it appears in at least half of Haiku's plain briefings for it (leaving out the briefing being scored), and *new* if it is not obvious and a judge rated it relevant. A further judge marked each as resting on a stated detail or brought in from outside. Hand labels agreed only moderately with the coding (Cohen's kappa, a chance-corrected agreement, 0.39 to 0.63 across three codebook builds, below our bar of 0.7); the overlap findings held in all three (Appendix E).

**Statistics.** The unit is the decision type. Rates are computed per type and averaged over types; brackets are 95% percentile bootstrap intervals over types, which run narrow with so few units. One type (parent care) has no decisive probe, so differences involving decisive probes are paired over 7 types and can differ by a point or two from the difference of the rates shown.

# 4. Results

## 4.1 Plain briefings raise decisive probes more often than inert ones

![Left: share of plain briefings that raise a probe; the dark part of each bar is briefings that tell the person to find it out. Right: the same for decisive probes under each prompt on Haiku 5.5. Whiskers are 95% bootstrap intervals over decision types for the full bar. Ratings are the automated judge's.](figures/probes.png){width=84%}

On the plain prompt, by the judge's ratings, a briefing raised a decisive probe 94% of the time [87% to 99%] and an inert one 56% of the time [46% to 67%] (54% in the seven paired types). The difference named in advance is 40 points [31 to 49]. It holds for each model (Figure 1): Haiku 88% against 47%, Sonnet 96% against 59%, GPT-5.5 97% against 63%.

There is a step and no slope: middle probes were raised 57% of the time, the same as inert ones. Of the 22 decisive probes, 16 were raised by all 30 plain briefings for their vignette, and only 1 by fewer than half. That one was raised by none of the 30: whether Maya, weighing a startup offer against her current job, has any other prospect in hand. (Told she has a final interview next week, two of the three models switched from "accept" to "stay.") It was the only decisive probe about an option outside the two on the table.

**Controls.** With the fact stated in the vignette, briefings raised the matter 99% (decisive) and 95% (inert) of the time, so the judge finds a matter when it is there. Against probes from a different decision type it marked 63 of 1,800 as raised (3.5%).

**The gap survives four checks, at 26 to 44 points.** Checks 1 to 3 were added after an AI review of the first draft. (1) *Fillers.* Inert probes that the drafter meant as fillers were raised only 32% of the time. Among probes the drafter expected to matter, the gap is 26 points [17 to 37] (94% against 70%); about a third of the planned gap comes from fillers. (2) *Circularity.* If two models define decisive and inert and the third model's briefings are scored, the gap is 44 points for Haiku, 41 for Sonnet and 36 for GPT-5.5 (on 18, 9 and 7 decisive probes), so a model raises what moves the other models' choices. (3) *Types and thresholds.* The gap is positive in 7 of 7 decision types (smallest 19 points) and stays between 33 and 45 points across other cutoffs for decisive (0.3 to 0.8) and inert (0 to 0.2). (4) *A third option.* With "something else" offered in the forced choice, which the models chose 59% of the time, many probes change group and the gap is 37 points [10 to 62]. The plan named the two-option version as primary.

**Hand labels: the levels are uncertain.** On 80 list-question pairs labeled blind, the author agreed with the judge on raised against absent in 79% (kappa 0.57). He called raised 24 of 27 of the judge's "asks" and 2 of 27 of its "absent," but only 14 of 26 of its "mentions": where the judge saw the same unknown, he often saw only the same topic. Applying those shares to the judge's ratings puts plain briefings near 62% for decisive probes and 38% for inert ones. This restatement cannot test the gap, since it assumes the judge is equally lenient on both kinds; the only direct evidence is that he rejected 2 of 12 of the judge's "raised" calls on decisive probes and 8 of 20 on inert ones. One human rater cannot settle which reading of "mentions" is right. Neither reading contradicts the direction of the contrast; the rates themselves are uncertain.

**Mentioning is not asking.** A briefing can raise a missing fact by weighing it ("the roof may be a major cost") or by telling the person to find it out ("get a roofer's estimate before Sunday"). Plain briefings told the person to find out a decisive probe's fact 30% of the time [22% to 38%], against 11% for inert ones. The models differ here more than anywhere else: Sonnet 44%, Haiku 26%, GPT-5.5 20%. This is the rating on which the judge and the author agreed best.

## 4.2 Prompts that make the list less obvious do not raise more decisive probes

| Prompt (Haiku 5.5) | New per briefing | Decisive raised | Inert raised | Decisive: told to find out |
|:------------------------|---:|---:|---:|---:|
| Plain, 8 items | 2.3 | 88% | 47% | 26% |
| Verbalized sampling | 2.8 | 87% | 40% | 15% |
| Property substitution | 3.1 | 89% | 44% | 35% |
| Same, + random dimensions | 3.1 | 87% | 46% | 27% |
| Random word | 3.9 | 87% | 40% | 19% |
| Think first, be diverse | 4.0 | 79% | 41% | 21% |
| "What else?" turn, read alone | 5.2 | 45% | 31% | 8% |
| Plain, then "What else?" (16 items) | n/a | 96% | 61% | 33% |
| Plain, 16 items | n/a | 96% | 57% | 45% |

Table: Each prompt on Haiku 5.5, means over decision types, by the judge's ratings. *New per briefing*: relevant considerations outside the vignette's obvious ones (of 8; not scored for 16-item lists). *Decisive raised*, *Inert raised*: share of such probes a briefing raises. *Told to find out*: share of decisive probes it tells the person to find out.

Before the probes existed we had scored the six widening prompts by new considerations per briefing. On that score all beat plain, from verbalized sampling (+0.5) to the "What else?" turn (+2.8), though "obvious" is defined from plain briefings, so part of that is built in. The probes give a different picture (Table 1). No widening prompt raised reliably more decisive probes than plain. The prompt that scored highest on new considerations, the "What else?" turn read without the briefing before it, raised about half as many (45%); it had been told not to repeat the first list. Think-first did not reliably differ from plain (-9 points, lower in 3 of 7 types).

What length changed was asking. A plain 16-item list told the person to find out decisive facts 45% of the time, 19 points more than the 8-item list and higher in 7 of 7 types. It raised 96% against 88%, but that difference is higher in only 4 of 7 types and mostly comes from one. It also raised more inert probes, so it is longer, not more selective: the gap between decisive and inert, paired by type, stayed between 36 and 49 points for every prompt except the "What else?" turn alone.

These are about 16 unadjusted comparisons on seven units, so none is firm. Two others were consistent across types: property substitution, the author's own prompt, told the person to find out decisive facts more often than plain (+9 points, higher in 7 of 7 types), and verbalized sampling less often (-11, lower in 7 of 7).

## 4.3 Asking again returns most of the same list

**Across asks and across vendors.** Two plain briefings for the same vignette from the same model share 5.3 of 8 considerations on Haiku, 5.4 on Sonnet and 5.2 on GPT-5.5 (Appendix E, Figure 2). Briefings from two different models share 4.6 to 4.8. Taking the question to another vendor's model is close to asking the first one again, so their agreement is weak evidence that the list is complete. The lists are fitted to the person: two people facing the same kind of decision share only 1.5 of 8 (Sonnet; the others are alike). Ten asks of one model reach 16.1 distinct considerations, twice what one briefing holds.

**Most of it rests on what the vignette states.** About 6.2 of the roughly 8 considerations in a Haiku briefing rest on a detail the vignette states, and those reappear on a second ask 72% of the time. The 1.6 brought in from outside reappear 41% of the time.

# 5. Discussion and Limitations

On these vignettes plain briefings are selective toward facts that move the models' choice. By the judge's reading few decisive facts go unraised, which we did not expect; by the author's stricter reading, more than a third may. Briefings tell the person to find a decisive fact out about a third of the time. We cannot say whether that is too few: some decisive facts the person already knows (their other prospects, their savings), and for those a mention is enough.

**Limits.**

1. *Decisive means "flips the models' recommendation," and inert does not mean unimportant.* The models that write the briefings also define what is decisive. Leaving one model out shows a model raises what moves the others, but the three may share blind spots, and facts that matter to a person but move no model are invisible here. Several inert probes plainly matter (how much care a parent needs, whether a third option exists), and briefings were arguably right to raise them. A larger gap is therefore not a better briefing. The fix is the choices of people who have faced the decision, or outcomes.
2. *The probes come from a model,* so facts no model would think of are not in the set. The author edited them but did not write them. Each probe's two answers were chosen to be far apart, with no estimate of how likely each is.
3. *A two-option forced choice cannot see everything.* Facts about the shape of the decision (a third option, a soft deadline) rarely shift a choice between two fixed options: only 2 of the 30 such probes were decisive.
4. *Raised is a loose bar.* A briefing that walks through each stated detail will mention the unknowns attached to it, which may be habit and not judgment about what matters. Telling the person to find out is the stricter measure and the one the author's labels supported, though the judge also counts "confirm" or "check" as asking.
5. *Small and invented.* Sixteen vignettes written by a model, ten samples each, 22 decisive probes over 7 decision types. The judges are models, checked by one person who knew the hypotheses (Appendix D).
6. *The prompt comparison is exploratory:* one small model, one wording per prompt. The missing-fact study itself was designed partway through, after an AI review of the first analysis, and committed before it ran (Appendix C).

# 6. Conclusion

Whether a briefing surfaces what matters can be approximated by asking what the description leaves out, measuring which of those facts flip a model's choice, and checking whether the briefing raises them. On that test, plain briefings from three current models raise decisive facts more often than inert ones and tell the person to find them out about a third of the time; on one small model, in an exploratory comparison, prompts for variety did not help and a longer list asked about more of them. Most of the list repeats from one ask or vendor to the next. The step that would make the method trustworthy is replacing the models' forced choice with people's.

