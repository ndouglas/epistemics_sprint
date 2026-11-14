---
title: "Ask Again, Get the Same List: What LLM Decision Briefings Repeat, and What Widening Them Costs"
author: |
  Nathan Douglas\
  Independent
abstract: |
  When someone asks a language model what to weigh in a personal decision, do they get the considerations that matter, or the ones the model always gives? We wrote 16 vignettes (8 kinds of decision, each faced by two different people), asked three models for exactly 8 considerations ten times each, and sorted the sentences under a codebook of distinct considerations per decision type. A person who asks the same model twice gets about 5 of the same 8 considerations. Asking a different model changes little: answers from two models share nearly as many as two answers from one. The models do tailor to the person, since two people facing the same kind of decision share only 1 or 2 of 8. We then tested six prompts for widening the list on one model, two of them based on naming a situation's properties and varying them. Every method raised the number of useful, non-obvious considerations per answer, and every method paid for them by dropping obvious ones, roughly one for one. The simplest methods moved furthest. A second-turn "What else?" added the most new material and kept the least of the core, and the property-based methods landed in the middle. Hand labels agreed only moderately with the automated coding, which splits considerations more finely than the labeler; the findings held under three separate codings, including a coarser one. With a fixed-length briefing, the question is less how to get variety than how many slots to spend on it.
---

# 1. Introduction

People now ask language models what to think about before accepting a job, signing a lease or lending money to a relative. The sprint's prompt for epistemic products asks whether such a briefing "surface[s] the considerations that actually matter." A briefing can fail that test in a quiet way: every consideration in it is sensible, and it is the same list everyone else got. Language models are known to return similar outputs across samples and across models on open-ended tasks (Jiang et al., 2025; Zhang et al., 2025). If decision advice behaves the same way, then the considerations outside the usual list are ones that a person will not hear by asking again, and that nobody else who asks will hear either.

We measure this for personal decisions and then test ways to widen the list. Our contributions:

- **A measurement of the repetition.** On a plain prompt, a person who asks twice gets back about 5 of the 8 considerations from their earlier answer, on each of three models. Switching models helps little. The repetition is about the situation, not the kind of decision: a different person with the same kind of decision gets a mostly different list.
- **A comparison of six ways to widen the list, with their cost.** All six surface more useful considerations from outside the obvious set, and all six do it by displacing obvious ones. We report both sides for each method, because a method that swaps the whole list for a fresh one would look best on novelty alone.

The author uses a practice drawn from ideonomy (Gunkel; Kind) for exploring ideas: name the properties of a thing that matter in its present situation, and vary them one at a time. Two of the six methods are that practice written as a prompt. They were the methods the author expected to do best. They did not.

# 2. Related Work

**Homogeneous outputs.** Jiang et al. (2025) document that language models give similar answers to open-ended questions, within a model and across models. Doshi and Hauser (2024) and Anderson et al. (2024) find that people who write or brainstorm with a model produce work that is more alike across people. These concern creative text and ideas. We found no study that measures the considerations in decision advice or compares two askers with the same kind of decision.

**Prompting for diversity.** Zhang et al. (2025) ask the model to verbalize a distribution over responses and sample from it. Meincke et al. (2024) compare prompting strategies for idea diversity and find chain-of-thought prompting the most effective. Troshin et al. (2025) find that asking for further responses given those already listed gives more diverse sets than independent samples. Misaki and Akiba (2025) inject randomness through a generated random string. Carichon et al. (2026) compare 25 prompts drawn from structured ideation methods such as TRIZ and SCAMPER and from simple divergence cues, and report that no single method wins on all of their measures; their measures do not include a rating of quality. Our arms are modeled on these, and we add a judgment of whether each consideration could bear on the person's choice.

# 3. Methods

**Decisions.** We wrote 16 vignettes of three or four sentences: 8 decision types (job offer, lease, first home, part-time graduate school, lending money to family, care for an aging parent, leaving a job to work independently, moving for a partner's job), each with two people who differ in age, money and dependents. Every prompt asks, "What should this person weigh in making this decision?" and requires exactly 8 considerations of one sentence each, returned as structured output. The vignettes and all prompts were committed before any treatment prompt was run (Appendix B).

**Arms.** (1) *Plain*: the vignette and the question. (2) *Think first, be diverse*: ask for non-obvious considerations from different angles, after working it through in a notes field. (3) *Verbalized sampling*, in the wording of Zhang et al. (4) *"What else?"*: a plain answer, then a second turn asking for 8 more; the second turn is the answer we score. (5) *Random word*: arm 2 plus a randomly drawn noun for inspiration. (6a) *Properties*: say what the situation is to this person at this time, name a few properties that vary independently, change each and see what moves, then answer. (6b) *Properties + dice*: 6a plus three dimension names drawn at random from a list of 29 (such as scale, reversibility, rate) to steer which properties are chosen. Arms 2, 5, 6a and 6b form a two-by-two: free notes or property structure, with or without a random draw. Arms 2 and 5 tell the model to avoid the obvious; 6a and 6b do not, so a gap between those pairs cannot be assigned to structure alone.

**Models and samples.** All seven arms ran on Claude Haiku 5.5, ten samples per vignette. The plain arm also ran on Claude Sonnet 5.5 and GPT-5.5. Extended reasoning was off for all three and sampling settings were the API defaults. This gave 1,440 answers and 11,520 sentences; none was refused, and 11 answers needed a retry to return exactly 8 items. We had planned to run the arms on Sonnet 5.5, but it declined every prompt in arms 2 and 5 under a policy against requests to write out reasoning, so the arms moved to Haiku before the freeze (Section 5).

**Coding.** For each decision type we pooled every sentence from every arm and model, shuffled them, and had Sonnet 5.5 (a) draft a codebook of distinct considerations from a sample of 500 sentences and (b) sort every sentence under one code, extending the codebook for sentences that fit none. The coder saw only sentence text, never the arm or model. The rule for "same" was that two sentences tell the person to weigh the same thing, even in different words; they differ if someone who had heard one would learn something new from the other. Codes are stated without naming either person, so that the two people's answers can be compared. The codebooks have 31 to 47 considerations each, and 15 of 11,520 sentences fit no code. Each answer then becomes a set of codes.

**Useful, obvious, good.** For each vignette, Sonnet 5.5 judged each consideration that appeared: could weighing it plausibly change what this person chooses, or how they go about choosing? A consideration is *obvious* for a vignette if it appears in at least half of that vignette's plain answers from Haiku (on average 7.6 considerations per vignette). We call a consideration *good* if it is useful and not obvious.

**Validation.** The author labeled two blind samples by hand (Appendix D). On 60 pairs of sentences, a third of them chosen to be the coder's hardest cases, he agreed with the coder's same-or-different call on 70% (Cohen's kappa 0.39, below the 0.7 we had set as the bar). The coder splits finer than he does: he called 13 pairs the same that the coder had split, against 5 the reverse. By his standard the overlaps in Section 4.1 are therefore understated, and Section 4.3 repeats the analysis under two other codebooks. On 40 usefulness ratings he accepted everything the judge accepted, rejected all 6 items planted from other decisions, and accepted 12 of 17 of the judge's rejections. Nearly everything the models generate is useful by either standard, so in practice *good* means *not obvious*.

**Statistics.** The unit is the decision type. Each measure is computed per vignette, averaged over a type's two vignettes, then averaged over the 8 types; brackets give 95% bootstrap intervals over types. Differences between arms are paired by type.

# 4. Results

## 4.1 Asking again returns most of the same list

![Left: considerations shared by two answers to the plain prompt, of 8. Right: distinct considerations accumulated as one person asks repeatedly. Bars and lines are means over 8 decision types; whiskers are 95% bootstrap intervals.](figures/collapse.png){width=100%}

Two plain answers to the same vignette from the same model share 5.3 of 8 considerations on Haiku [4.9 to 5.6], 5.4 on Sonnet [5.0 to 5.8] and 5.2 on GPT-5.5 [5.0 to 5.5] (Figure 1). Answers from two different models share between 4.6 and 4.8. A person who takes their question to a second vendor's model gets almost as much repetition as one who asks the first model again.

The repetition is not a generic list for the decision type. Two different people facing the same kind of decision share 1.5 of 8 on Sonnet [1.1 to 2.0], with the other models alike. The models read the vignette and answer for that person; what they repeat is their reading of it.

Repeated asking does reach further. After ten plain answers a person has seen 16.1 distinct considerations on Sonnet, and the tenth ask still adds 0.4 new ones on average. Roughly twice as many considerations are within reach of the plain prompt as one answer holds, and which of them a person sees beyond the common core is left to chance. Appendix C shows a typical pair of answers.

## 4.2 Every fix trades the obvious for the new

| Arm | Good | Useful | Obvious kept | Shared | Good in 10 | Tokens |
|:------------------------|---:|---:|---:|---:|---:|---:|
| Plain | 1.8 | 7.7 | 80% | 5.3 | 8.2 | 462 |
| Verbalized sampling | 2.5 | 7.7 | 69% | 5.2 | 9.0 | 494 |
| Properties (6a) | 2.9 | 7.5 | 61% | 4.5 | 9.9 | 990 |
| Properties + dice (6b) | 2.9 | 7.5 | 63% | 4.6 | 10.6 | 973 |
| Random word | 3.6 | 7.3 | 49% | 4.0 | 11.2 | 876 |
| Think first, be diverse | 3.8 | 7.4 | 48% | 4.2 | 11.8 | 840 |
| "What else?" (2nd turn) | 5.0 | 6.5 | 19% | 3.5 | 13.6 | 896 |

Table: The seven arms on Haiku 5.5, means over 8 decision types. *Good*: considerations per answer that are useful and not obvious (of 8). *Useful*: useful considerations per answer. *Obvious kept*: share of the vignette's obvious considerations that an answer includes. *Shared*: considerations two answers to the same vignette have in common. *Good in 10*: distinct good considerations across ten answers. *Tokens*: output tokens per answer; for "What else?" both turns are counted.

![Each arm's position: good considerations per answer against the share of obvious considerations kept. Whiskers are 95% bootstrap intervals over decision types.](figures/fixes.png){width=55%}

Every arm beats plain on good considerations per answer, from verbalized sampling (+0.7 [0.6 to 1.0]) to "What else?" (+3.2 [2.9 to 3.5]). Every arm also keeps fewer of the obvious considerations, and the two move together (Figure 2): an answer has 8 slots, nearly all of them are filled with something useful in every arm, and a good consideration takes the slot of an obvious one. The arms differ mainly in how far along that line they go.

"What else?" goes furthest. Its answers hold 5.0 good considerations and only 19% of the obvious ones, as expected of a second turn told not to repeat the first; it also has the fewest useful considerations per answer (6.5 of 8). Read on its own, such a list omits most of what the person most needs. Read after the first answer, it is the best supplement we tested. The comparison we named in advance, properties + dice against "What else?", went against the property method: its difference from "What else?" was -2.1 good considerations per answer [-2.5 to -1.8].

**The property methods are a middling fix.** Arms 6a and 6b add about one good consideration per answer over plain (+1.1 [0.8 to 1.4] and +1.1 [0.7 to 1.4]) and keep about 61% of the obvious set. Free-form notes with an instruction to be non-obvious do more: think-first exceeds 6a by 0.9 [0.5 to 1.3]. As noted, that pair differs in two ways, so this does not show that property structure hurts. It does show that a one-line instruction to avoid the obvious moved the list further than the structured practice did, with fewer output tokens.

**The random draws did little.** Dimension names did not change good considerations per answer (6b minus 6a: 0.0 [-0.3 to 0.3]), and the random word did not help think-first (-0.2 [-0.5 to 0.1]).

**The repetition moves up a level.** We predicted that in 6a the model would name the same properties each time, so that the sameness would shift from the considerations to the properties behind them. The property logs agree: an answer in 6a names 6.4 properties, and two answers to the same vignette share 4.8 of them (74%). With dice the share is 70%. Telling a model to choose where to look gives the same choice each time, and three random words do not move it much.

**Two people stay different.** No arm made two different people's lists more alike: shared considerations between the two people of a decision type stayed between 1.1 and 1.6 of 8 in every arm.

## 4.3 The same answers under three codebooks

How finely to split considerations is a judgment, and the hand labels say our coder splits finer than the labeler would. We therefore coded the same answers twice more: once from a different random sample of sentences with the same instructions (*rebuilt*), and once with the instruction for doubtful cases reversed from "keep them separate" to "treat them as one" (*coarse*). The coarse build was made after seeing the hand labels. Each build has its own codebooks, obvious sets and usefulness ratings.

| | Main | Rebuilt | Coarse |
|:--------------------------------------|---:|---:|---:|
| Considerations per decision type | 31 to 47 | 33 to 51 | 20 to 37 |
| Kappa with the hand labels (60 pairs) | 0.39 | 0.63 | 0.56 |
| Shared, same person, Sonnet twice | 5.4 | 5.4 | 5.8 |
| Shared, same person, GPT-5.5 then Haiku | 4.6 | 4.6 | 5.0 |
| Shared, two people, Sonnet | 1.5 | 1.8 | 2.2 |
| Good per answer: plain | 1.8 | 1.8 | 1.2 |
| Good per answer: properties (6a) | 2.9 | 2.7 | 1.9 |
| Good per answer: think first, be diverse | 3.8 | 3.6 | 2.8 |
| Good per answer: "What else?" | 5.0 | 5.0 | 4.0 |
| Obvious kept: "What else?" | 19% | 20% | 29% |
| 6b minus "What else?", good per answer | -2.1 | -2.2 | -2.0 |

Table: Headline numbers under three codings of the same 11,520 sentences. The pairs for the hand labels were drawn to stress the main build, so its kappa is not comparable with the other two.

The levels move as expected: a coarser codebook finds more overlap and fewer distinct considerations. The findings do not move. In all three builds a repeat ask returns between 5 and 6 of 8, a second model returns nearly as many, two people share between 1 and 3, the arms fall in the same order (6a and 6b are tied and change places), and each arm's gain in good considerations comes with a loss of obvious ones. No build reaches the agreement bar, so we rest the conclusions on what all three share and treat single values as approximate. Dropping the usefulness filter also leaves the order unchanged: non-obvious considerations per answer run from 1.9 for plain to 5.9 for "What else?" in the main build.

# 5. Discussion and Limitations

**A fixed-length briefing has a budget.** We expected the arms to differ in how much variety they found. They differed mostly in how many of the 8 slots they gave to it. This suggests treating the split as a design choice instead of a side effect of prompt wording: keep most slots for the considerations nearly everyone in the situation should hear, and give a stated few to useful considerations from outside that set, varied from one ask to the next. The second-turn result suggests a simple version: a plain answer, then "What else?", shown as a core list and a supplement. We did not test whether people decide better with such a briefing.

**Asking a second model is not a second opinion.** Three models from two vendors gave lists that overlap almost as much across models as within one.

**What we did not show.** (1) *Whether the considerations matter.* "Useful" is one model's yes-or-no judgment, and it said yes to nearly everything; "obvious" is defined by frequency in plain answers, which stands in for importance without measuring it. We did not compare the lists with what advisers or people who have faced these decisions would say. (2) *One model for the arms.* The fixes were tested on Haiku 5.5 only. Sonnet 5.5 refused the two arms that ask for written-out reasoning, which we did not work around; the ranking of arms may differ on larger models. (3) *Vignettes, not people.* Sixteen short invented situations and ten samples each; intervals are over 8 types. Real questions carry more context, which might reduce or increase repetition. (4) *Coding by a model, imperfectly validated.* One model built the codebooks and sorted the sentences. Agreement with one person's hand labels was moderate and below the bar we set, the labeler knew the hypotheses, and all three codebook builds share the same coder. The values in this report are approximate; the ordering and the trade-off are what held across builds. (5) *A confounded pair.* Arms 2 and 5 ask for non-obvious considerations and 6a and 6b do not. (6) *One prompt per method.* Each method is a single wording, and a different rendering of the property practice might do better. (7) *Exactly 8.* Fixing the list length builds in part of the trade-off; a longer list would relax it at the cost of the reader's attention.

# 6. Conclusion

Three current models tailor their considerations to the person and then repeat themselves: ask again, or ask another model, and about 5 of the 8 come back. Simple prompts widen the list, each by giving up some of the obvious core. The property-variation practice we set out to test helps, but less than a one-line request to be non-obvious. Builders of decision briefings should decide on purpose how many slots go to the considerations everyone gets and how many to the ones only some askers see.

<!-- appendices -->

# Code and Data

Code, prompts, vignettes, every generated answer, the codebooks, the judge's ratings, the hand labels and the claims register are at `REPO-URL`. `uv run python -m sprint.build_report` checks every number in this report against the data before rendering it.

# References

- Anderson, B. R., Shah, J. H., & Kreminski, M. (2024). Homogenization effects of large language models on human creative ideation. arXiv:2402.01536.
- Carichon, F., et al. (2026). IDEAFix. arXiv:2606.00875.
- Doshi, A. R., & Hauser, O. P. (2024). Generative AI enhances individual creativity but reduces the collective diversity of novel content. *Science Advances*, 10(28).
- Gunkel, P. *Ideonomy: The Science of Ideas.* Unpublished manuscripts.
- Jiang, L., et al. (2025). Artificial Hivemind: The open-ended homogeneity of language models (and beyond). arXiv:2510.22954.
- Kind, G. Ideonomy. https://gracekind.net/writing/ideonomy/intro
- Meincke, L., Mollick, E. R., & Terwiesch, C. (2024). Prompting diverse ideas: Increasing AI idea variance. arXiv:2402.01727.
- Misaki, K., & Akiba, T. (2025). String seed of thought. arXiv:2510.21150.
- Troshin, S., et al. (2025). Asking a language model for diverse responses. arXiv:2509.17570.
- Zhang, J., et al. (2025). Verbalized sampling: How to mitigate mode collapse and unlock LLM diversity. arXiv:2510.01171.

# Appendix A. Limitations and Dual-Use / Ethical Considerations

Limitations are listed in Section 5. Three further points concern use.

**Variety has a cost to the people advised.** A briefing that varies across askers gives two people with the same question different advice. A shared list is common ground: people can compare notes on it and outsiders can audit it. A varied supplement weakens both, which is one reason to keep a stated core and to label the supplement as such.

**Who chooses the supplement matters.** If the extra slots are filled at random, nobody can aim them. If they are filled by a system that tracks what has been shown to whom, that system decides which considerations reach which people, and it could steer decisions without any single briefing looking wrong. The methods in this report are prompts and random draws; we would want any targeted allocator to be logged and open to audit.

**The measures can be gamed.** A prompt can raise "non-obvious considerations per answer" by leaving out what matters most, as the second-turn arm shows when read alone. Anyone adopting such a metric should report what was displaced, as we do.

No human participants were involved; the vignettes are invented and describe no real person.

# Appendix B. Prompts and vignettes

The plain prompt is the vignette, the question, and "Give exactly 8 considerations, one sentence each." The other prompts add the text below to the same opening. All prompts, the 16 vignettes, the 29 dimension names and the 110 random words are in the repository as run.

**Think first, be diverse.** "Aim for considerations that are non-obvious and unconventional, beyond what most people would list first. Be diverse: each one should come from a different angle than the others. Before you answer, think it through in the `notes` field. Take your time there and work out what you want to say and why."

**Random word.** As above, with "Here is a random word to draw on for inspiration: (word)."

**"What else?"** Second turn: "What else? Give exactly 8 more considerations that you haven't mentioned yet, one sentence each."

**Properties (6a).** "Before you answer, work through it this way, recording what you do in the `properties` field. First ask what this situation is, to this person, at this time. Not the kind of situation in general: this one, for them, now. Then name a few properties of the situation that matter from where they stand. Pick properties that can vary independently of each other. For each property, change its value to something else and see what happens to the rest of the situation: what else has to move, and what the change shows. Record each property's `name` and the `alternative` value you tried. Then give exactly 8 considerations, one sentence each, drawing on what the variations showed."

**Properties + dice (6b).** 6a, then "As you choose which properties to look at, let these dimensions steer you: (three names)."

**Verbalized sampling** uses the standard wording from the authors' repository, with 8 responses.

# Appendix C. A typical pair of plain answers

Two plain answers from Sonnet 5.5 to the same vignette, chosen as the first pair whose overlap equals the median over all pairs of that vignette's ten answers (6 of 8 shared). The italic label is the code each sentence was sorted under.

> Maya is 27 and works as a data analyst at a hospital system, earning $68,000. A 40-person logistics startup has offered her $82,000 plus stock options, fully remote. She has $31,000 in student loans, no dependents, and her current manager has hinted at a promotion next year. The startup wants an answer by Friday.

**Ask 1:**

- [only here] *Student loan repayment situation.* The $14,000 salary increase (about 21%) would meaningfully accelerate paying down her $31,000 in student loans, but she should compare it to what the hinted promotion at her current job might actually pay.
- **[shared]** *Equity option value.* Stock options at a 40-person startup are speculative, so she should ask about the strike price, vesting schedule, current valuation, and dilution risk and treat them as a lottery ticket rather than guaranteed compensation.
- [only here] *Employer financial runway.* A small startup carries real risk of layoffs or shutdown, so she should ask about runway, funding stage, and profitability and make sure she has an emergency fund to cover a job search.
- **[shared]** *Verifying the promotion hint.* A manager's hint of a promotion is not a commitment, so she could ask for specifics on timing and salary or use the competing offer as leverage to see what her current employer will put in writing.
- **[shared]** *Total compensation beyond base pay.* She should weigh the stability, benefits, and retirement matching of a hospital system against the startup's benefits package, including health insurance quality, 401(k) match, and paid time off.
- **[shared]** *Career growth and skill development.* Consider which role will build more valuable skills and career capital, such as broader responsibilities and faster growth at a startup versus domain expertise in healthcare data that may be harder to replicate elsewhere.
- **[shared]** *Remote work trade-offs.* Fully remote work can improve flexibility and save commuting costs, but she should honestly assess whether she thrives with less in-person mentorship, structure, and social connection, especially early in her career.
- **[shared]** *Deadline as pressure and information.* The Friday deadline is a pressure tactic she can push on, so she should ask for a short extension, negotiate the offer, and make sure her decision reflects her own priorities and risk tolerance rather than the clock.

**Ask 2:**

- **[shared]** *Total compensation beyond base pay.* The $14,000 salary increase (about 20%) could meaningfully accelerate paying down her $31,000 in student loans, but she should compare take-home pay after benefits like health insurance and retirement matching at each employer.
- **[shared]** *Equity option value.* Stock options in a 40-person startup are speculative, so she should ask about the strike price, vesting schedule, current valuation, and dilution risk, and treat them as potentially worth zero rather than as guaranteed compensation.
- [only here] *Job security comparison.* A hospital system offers far more job stability than a small startup, so she should consider the company's funding runway, revenue, and layoff risk, especially given her student debt obligations.
- **[shared]** *Verifying the promotion hint.* Her manager's hint of a promotion is unconfirmed, so she should weigh how likely and how large that raise would be against a certain offer in hand, and consider asking her manager for clarity before Friday.
- **[shared]** *Career growth and skill development.* The roles may differ in career growth, since a startup could offer broader responsibility and faster skill development while a hospital system offers structured advancement and deep healthcare-domain expertise.
- **[shared]** *Remote work trade-offs.* Fully remote work changes daily life through flexibility and saved commuting costs, but she should consider whether she thrives without in-person mentorship, team culture, and social connection.
- [only here] *Personal financial cushion.* Her financial cushion matters, so she should assess whether she has enough savings to absorb a sudden job loss, since her low risk exposure (no dependents) at 27 makes this a relatively good time to take a calculated risk.
- **[shared]** *Deadline as pressure and information.* The Friday deadline is short, so she should try to negotiate more time, ask for the offer details in writing, and use the interim to research the startup's finances, leadership, and employee reviews.

# Appendix D. Hand labels

The author labeled two blind samples by hand in a terminal tool that showed only text: no codes, arms, models or judge ratings. (a) *Same or different:* 60 pairs of sentences, 20 that the coder put under the same code, 20 under different codes chosen at random, and 20 under different codes but with the most similar wording (the top 2% by word overlap), a stratum built to find the coder's worst cases. He agreed with the coder on 15/20 of the same-code pairs, 19/20 of the random pairs and 8/20 of the similar-wording pairs: 70% overall, Cohen's kappa 0.39, below the 0.7 we had set as the bar. The disagreements lean one way: he called 13 pairs the same that the coder had split, against 5 the reverse. The coder splits finer than he does, so by his standard the overlaps in Section 4.1 are understated. (He discussed his first five pairs with Claude, which had not seen the codes; without those five, kappa is 0.36.) (b) *Useful:* 40 vignette-consideration pairs, 17 the judge had accepted, 17 it had rejected, and 6 planted from a different decision type. He accepted 17 of 17 of the judge's acceptances, rejected all 6 planted items, and accepted 12 of 17 of the judge's rejections. The judge is stricter than the labeler, and by either standard nearly everything the models generate is useful; in practice, *good* means *not obvious*.

# LLM Usage Statement

This project was done in a weekend by one person working with Claude (Anthropic's Claude Code). The author chose the question, supplied the method under test (his own practice of naming and varying properties), approved the design, the vignettes and every prompt before they were frozen, and labeled the validation samples by hand. Claude wrote the vignettes and prompts for his approval, wrote the code, ran the experiments and the analysis, and wrote this report, which the author reviewed and edited. Claude Sonnet 5.5 is also the coder and judge, and Claude Haiku 5.5 and Sonnet 5.5 are among the models studied. Every number in the report is checked against the released data by the build. Errors are the author's.
