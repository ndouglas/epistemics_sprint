---
title: "Does the Briefing Raise What Would Change the Decision? Missing Facts in LLM Decision Advice"
author: |
  Nathan Douglas\
  Independent
abstract: |
  The sprint asks whether an AI briefing for a personal decision surfaces "the considerations that actually matter," and how one would know. For 16 short decision vignettes we wrote 94 questions about facts the vignette leaves out, each with two possible answers, and measured which facts matter: three models made a forced choice between the person's two options under each answer, and a fact counts as decisive if the answer flips the choice and inert if it leaves the choice alone. We then checked whether briefings from the same three models, asked what the person should weigh, raise those facts. On a plain prompt, briefings raised decisive missing facts in 94% of cases and inert ones in 56%. The gap held for each model, under a second definition of decisive, and, smaller, with deliberately trivial questions set aside. The author's blind labels show the automated judge is lenient about what counts as mentioning a fact; by his standard both rates are about a third lower and the gap remains. Briefings less often say what to do: about 30% told the person to find the decisive fact out. On one small model, prompts written to make the list less obvious did not reliably raise more decisive facts, and asking for a longer list did. A person who asks twice, or asks another vendor's model, gets most of the same list back. The main limit is that "decisive" means the fact flips these models' recommendation, not that it changes the person's outcome.
---

# 1. Introduction

People now ask language models what to think about before accepting a job, signing a lease or lending money to a relative. The sprint's prompt for epistemic products asks whether such a briefing "surface[s] the considerations that actually matter," and adds: how would you know? The second question is the hard one. Nearly everything a current model writes about a decision is relevant, so relevance does not separate a good briefing from a poor one, and a list can be made more varied by leaving out what matters most.

This project began as a study of variety (do all askers get the same list, and can a prompt widen it?) and ran into that problem: we could count new considerations but not say whether they mattered. So we added a measurement with a ground truth. A short description of a decision leaves facts out, and some of them would change the answer. If the roof needs replacing this year for $28,000, do not make the offer; if it has five years left, do. A briefing that surfaces what matters should raise the missing facts that would change the decision, more often than it raises missing facts that would not. People are poor at noticing what a list leaves out (Fischhoff et al., 1978), so they are unlikely to supply these themselves.

Our contributions are a way to score a briefing against what matters (missing-fact probes whose status is measured by forced choice, and one contrast named in advance); a result on three current models (Section 4.1); a check on six prompts for variety (4.2); and a description of how much the lists repeat (4.3).

# 2. Related Work

**Shared models, shared outcomes.** Kleinberg and Raghavan (2021) show that when many decision-makers rely on one algorithm, overall decision quality can fall even if it is more accurate for each of them, and Bommasani et al. (2022) that systems sharing components can fail the same individuals repeatedly. Goel et al. (2025) find that language models' mistakes grow more alike with capability, and Jiang et al. (2025) that models give similar answers to open-ended questions, within and across models. Section 4.3 measures this sameness in decision advice.

**Prompting for diversity.** Methods such as verbalized sampling (Zhang et al., 2025) and chain-of-thought prompting (Meincke et al., 2024) are scored on diversity. Section 4.2 scores six such prompts on whether they raise what matters.

**Asking for what is missing.** QuestBench (Li et al., 2025) finds that models often cannot identify the one question needed to solve an underspecified reasoning problem, even when they can solve the fully specified version. ClarifyMT-Bench (Luo et al., 2025) reports that models in dialogue tend to answer before clarifying. Those tasks have a known missing variable and a correct answer. Ours has neither, so we measure which missing facts matter and ask whether an unprompted list reaches them.

# 3. Methods

**Decisions.** Sixteen vignettes of three or four sentences: 8 decision types (job offer, lease, first home, part-time graduate school, lending money to family, care for an aging parent, going freelance, moving for a partner's job), each with two people who differ in age, money and dependents, and each posing a choice between two courses of action. Every prompt asks, "What should this person weigh in making this decision?" and requires a fixed number of one-sentence considerations.

**Prompts.** *Plain*: the vignette and the question, 8 items. Six prompts meant to widen the list, also 8 items: *think first, be diverse* (non-obvious considerations from different angles, after working it through in a notes field); *verbalized sampling* (Zhang et al.); *"What else?"*, a second turn after a plain answer asking for 8 more; *random word*, think-first plus a random noun; a *property-substitution* prompt (name a few properties of the situation, change each, see what moves, then answer); and the same with three randomly drawn dimension names. Property substitution is one step of a practice the author uses, taken from ideonomy (Gunkel; Kind); this is not a test of that practice. We later added *plain, 16 items*. Appendix B gives the wording.

**Models and samples.** All prompts ran on Claude Haiku 5.5, ten samples per vignette. The plain prompt also ran on Claude Sonnet 5.5 and GPT-5.5. Extended reasoning was off and sampling settings were the API defaults. This gave 1,600 answers and no refusals. The widening prompts ran on Haiku because, in a pilot, Sonnet 5.5 refused the prompts that ask it to write out its reasoning, which we did not work around.

**Missing-fact probes.** GPT-5.5 was shown each vignette alone and asked for six things it does not say that an adviser might want to know: a question and two plausible answers, each a sentence that could be added to the vignette as a fact. It was asked for some facts that would change the choice and some that would not, and for some about the shape of the decision (is there a third option, is the deadline fixed). The author edited the list without looking at any generated answer and dropped a few, leaving 94. The probes and the analysis plan were committed before any answer was scored (Appendix C).

**Which facts are decisive.** We did not take the drafter's word. For each probe, each of the three models made a forced choice between the vignette's two options with answer A added to the vignette, and again with answer B, ten times each, with the order of the options randomized (6,120 choices, including the vignette with no fact added). A probe's shift for a model is the absolute difference, between the two answers, in the share choosing a given option. A probe is *decisive* if the shift is at least 0.5 for at least two of the three models, *inert* if it is at most 0.1 for all three, and otherwise *middle*. This gave 22 decisive, 39 inert and 33 middle probes. The drafter's own guesses were weak: of 65 facts it expected to change the choice, 21 were decisive and 25 were inert.

**Does a briefing raise the fact?** A judge (Sonnet 5.5) saw the vignette, one answer's list and that vignette's probe questions, and marked each question *asks* (an item tells the person to find this out), *mentions* (an item raises the same matter without saying to find it out) or *absent*. It was told the item must concern the same specific unknown, not just the same topic. It never saw the prompt, the model, the probe's two answers or its status. A probe is *raised* if the label is asks or mentions. All 1,760 lists were judged (10,340 list-question pairs).

**The contrast, named in advance.** The share of decisive probes raised minus the share of inert probes raised, on the plain prompt, pooled over the three models. Everything else in Section 4 is exploratory.

**Controls.** (a) *Fact stated:* for each decisive or inert probe we added each of its answers in turn to the vignette and collected plain answers from each model (732 answers); the judge, shown the original vignette, should find the matter raised. (b) *Foreign probes:* the judge rated lists against probes written for a different decision type (1,800 pairs); it should find almost nothing. This is an easy negative and does not test near misses on the same topic. (c) *Hand labels:* the author labeled 80 list-question pairs blind to the judge and before seeing any result (Appendix D).

**Coding considerations.** For Section 4.3, Sonnet 5.5 built a codebook of distinct considerations for each decision type (31 to 47 codes) and sorted every sentence under one code without seeing the prompt or model. A consideration is *obvious* for a vignette if it appears in at least half of Haiku's plain answers to it (leaving out the answer being scored), and *new* if it is not obvious and a judge rated it relevant. A further judge marked each as resting on a detail the vignette states or brought in from outside. Hand labels agreed only moderately with the coding (kappa 0.39 to 0.63 across three codebook builds, below our bar of 0.7); the overlap findings held in all three (Appendix E).

**Statistics.** The unit is the decision type. Rates are computed per type and averaged over types; brackets are 95% bootstrap intervals over types. One type (parent care) has no decisive probe, so the contrast is paired over 7 types. With so few units the intervals are rough.

# 4. Results

## 4.1 Briefings raise the missing facts that would change the choice

![Left: share of plain answers that raise a missing fact; the dark part of each bar is answers that tell the person to find it out. Right: the same for decisive facts under each prompt on Haiku 5.5. Whiskers are 95% bootstrap intervals over decision types for the full bar. Labels are the automated judge's.](figures/probes.png){width=95%}

On the plain prompt, a briefing raised a decisive missing fact 94% of the time [87% to 99%] and an inert one 56% of the time [46% to 67%]. The difference named in advance is 40 points [31 to 49]. It holds for each model (Figure 1): Haiku 88% against 47%, Sonnet 96% against 59%, GPT-5.5 97% against 63%.

Probes in the middle group were raised 57% of the time, the same as inert ones. Of the 22 decisive probes, 16 were raised by all 30 plain answers to their vignette, and only 1 was raised by fewer than half. That one was raised by none of the 30: whether Maya, weighing a startup offer against her current job, has any other prospect in hand. (Told she has a final interview next week for a better-paid role, two of the three models switched from "accept" to "stay.") It was the only decisive probe about an option outside the two on the table.

**Controls.** With the fact stated in the vignette, briefings raised the matter 99% (decisive) and 95% (inert) of the time, so the judge finds a matter when it is there. Against probes from a different decision type it marked 63 of 1,800 as raised (3.5%), so it is not marking everything.

**Hand labels.** On 80 list-question pairs labeled blind, the author agreed with the judge on whether a fact was raised in 79% (kappa 0.57). The disagreement is one-sided. He accepted 24 of 27 of the judge's "asks" and 25 of 27 of its "absent," but only 14 of 26 of its "mentions": the judge counts as a mention what he counts as the same topic. Restated by his standard, plain briefings raise about 62% of decisive facts and 38% of inert ones, a gap of about 24 points. That assumes the judge is equally lenient on both kinds; in the sample it over-called 2 of 12 decisive and 8 of 20 inert pairs, which would widen the gap, but the counts are small. The levels in this section are upper bounds; the direction of the contrast is the finding.

**Checks on the contrast.** (1) *Trivial probes.* The drafter was asked for some facts it expected not to matter, and inert probes of that kind were raised only 32% of the time. Among probes the drafter expected to matter, the gap is 26 points [17 to 37] (94% against 70%). That is the fairer estimate; about a third of the headline gap comes from easy fillers. (2) *Circularity.* If two models define decisive and inert and the third model's briefings are scored, the gap is 44 points for Haiku, 41 for Sonnet and 36 for GPT-5.5, so a model raises facts that move the other models' choices. (3) *Types and thresholds.* The gap is positive in 7 of 7 decision types (smallest 19 points) and stays between 33 and 45 points across other cutoffs for decisive (0.3 to 0.8) and inert (0 to 0.2). (4) *A third option.* With "something else" offered in the forced choice, which the models chose 59% of the time, many probes change group and the gap is 37 points [10 to 62]. The plan named the two-option version as primary. Checks 1 to 3 were added after a review of the first draft.

**Mentioning is not asking.** A briefing can raise a missing fact by weighing it ("the roof may be a major cost") or by telling the person to find it out ("get a roofer's estimate before Sunday"). Only the second gives the person something to do. Plain briefings told the person to find out a decisive fact 30% of the time [22% to 38%], against 11% for inert facts. The models differ here more than anywhere else: Sonnet 44%, Haiku 26%, GPT-5.5 20%.

## 4.2 Prompts that make the list less obvious do not raise more of what matters

| Prompt (Haiku 5.5) | New per answer | Decisive raised | Told to find out | Inert raised |
|:------------------------|---:|---:|---:|---:|
| Plain, 8 items | 2.3 | 88% | 26% | 47% |
| Verbalized sampling | 2.8 | 87% | 15% | 40% |
| Property substitution | 3.1 | 89% | 35% | 44% |
| Same, + random dimensions | 3.1 | 87% | 27% | 46% |
| Random word | 3.9 | 87% | 19% | 40% |
| Think first, be diverse | 4.0 | 79% | 21% | 41% |
| "What else?" turn, read alone | 5.2 | 45% | 8% | 31% |
| Plain, then "What else?" (16) | | 96% | 33% | 61% |
| Plain, 16 items | | 96% | 45% | 57% |

Table: Each prompt on Haiku 5.5, means over decision types. *New per answer*: relevant considerations outside the vignette's obvious ones (of 8). *Decisive raised*, *Inert raised*: share of such probes an answer raises. *Told to find out*: share of decisive probes it tells the person to find out.

Before the probes existed we had scored the six widening prompts by new considerations per answer, and on that score all beat plain, from verbalized sampling (+0.5) to the "What else?" turn (+2.8). The probes give a different picture (Table 1). No widening prompt raised reliably more decisive facts than plain. Think-first raised somewhat fewer (-9 points [-20 to 0]), and a "What else?" turn read without the answer before it raised about half as many (45%). A count of new considerations rewards the list that leaves out the most of what matters.

What did help was length. A plain list of 16 raised 96% of decisive facts (8 points over the 8-item list [1 to 19]) and told the person to find them out 45% of the time (19 points more [12 to 26]). It also raised more inert facts, so it is longer, not better aimed: the gap between decisive and inert, paired by type, stayed between 36 and 49 points for every prompt except the "What else?" turn alone.

The property-substitution prompt, which the author expected to do best on variety, was middling on it, though it told the person to find out decisive facts somewhat more often than plain (9 points [5 to 15]). Its property lists were themselves repetitive: two answers to a vignette named 74% of the same properties.

## 4.3 Asking again returns the same list

**Across asks and across vendors.** Two plain answers to the same vignette from the same model share 5.3 of 8 considerations on Haiku, 5.4 on Sonnet and 5.2 on GPT-5.5 (Appendix E, Figure 2). Answers from two different models share 4.6 to 4.8. Taking the question to another vendor's model is close to asking the first one again, so their agreement is weak evidence that the list is complete. The lists are fitted to the person: two people facing the same kind of decision share only 1.5 of 8 (Sonnet; the others are alike). Ten asks of one model reach about 16.1 distinct considerations, twice what one answer holds.

**The list is ranked.** On Haiku, 93% of first items are among the vignette's common considerations, falling to 48% of eighth items (Sonnet and GPT-5.5 are similar). Considerations that two answers share keep their relative order 87% of the time, and 85% of Haiku's answers to a vignette open with the same one. Variation between asks lives in the last few slots.

**Most of it restates the vignette.** About 6.2 of Haiku's 8 considerations rest on a detail the vignette states, and those reappear on a second ask 72% of the time. The 1.6 brought in from outside reappear 41% of the time. Many decisive probes read to us as unknowns attached to a stated detail (the roof's cost, the startup's runway), which may be why they are raised so reliably; we did not measure this.

**"What else?" is a longer list.** A plain answer followed by "What else?" holds 14.3 distinct considerations; one plain answer asked for 16 items holds 14.0, and two such answers share 10.2.

# 5. Discussion and Limitations

On these vignettes plain briefings are aimed: they raise the missing facts that flip the choice of at least two of the three models more often than those that flip none, by the judge's standard and by the author's stricter one. We expected to find decisive facts going unraised and mostly did not. The weak point is that briefings usually note a decisive unknown without telling the person to resolve it.

**Limits.**

1. *Decisive means "flips the models' recommendation."* The models that write the briefings also define what is decisive. Leaving one model out (Section 4.1) shows a model raises what moves the others, but the three may share blind spots, and facts that matter to a person but move no model are invisible here. The fix is the choices of people who have faced the decision, or outcomes.
2. *The probes come from a model,* so facts no model would think of are not in the set. The author edited them but did not write them.
3. *A two-option forced choice cannot see everything.* Facts about the shape of the decision (a third option, a soft deadline) rarely shift a choice between two fixed options: only 2 of the 30 such probes were decisive. They may matter most in practice.
4. *Raised is a loose bar.* A briefing that walks through each stated detail will mention the unknowns attached to it. If decisive probes tend to extend stated details, part of the headline rate reflects that habit and not judgment about what matters. The hand labels confirm the judge's "mentions" is lenient. Telling the person to find out is the stricter and better-validated measure, though "asks" includes "confirm.""
5. *Small and invented.* Sixteen vignettes written by a model, ten samples each, 22 decisive probes over 7 decision types. The judges are models, checked by one person who knew the hypotheses (Appendix D).
6. *The prompt comparison is exploratory:* one small model, one wording per prompt, not named in advance. The missing-fact study itself was designed partway through, after a review of the first analysis, and committed before it ran (Appendix C).

# 6. Conclusion

Whether a briefing surfaces what matters can be scored by asking what the description leaves out, measuring which of those facts flip the choice, and checking whether the briefing raises them. On that test, plain briefings from three current models raise the decisive facts and under-ask about them; on one small model, in an exploratory comparison, prompts for variety did not help and a longer list did. The lists barely vary from one ask or vendor to the next. The step that would make the method trustworthy is replacing the models' forced choice with people's.

