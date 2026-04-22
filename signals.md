# Signal & Technique Reference — Turnitin AI Detector Playbook

Derived from 8 corpora · 13 reports · ~103,150 words · ~476 flagged segments (BCP2485, IMU). **Model: v0.5** (22 Apr 2026).

---

## Predictive model — read first (v0.5)

**Formula:** `AI_para = S_struct × P_polish × first_person_factor`, word-weighted across all qualifying paragraphs (≥20 words).

**S_struct** is additive (capped at 1.0): S2 +0.15 · S3 +0.175 · S4a +0.10 · S4b-P1 +0.25 · S4b-P2 +0.30 · S4b-P3 +0.35 · S5 +0.10 · S6 +0.175 · S7 +0.10 · S8 +0.10

**P_polish:** 1.0 clean · 0.9 light typos · 0.8 moderate · 0.7 heavy · 0.5 recurring

**first_person_factor:** 0.8 sustained we/our/you/your · 0.9 ≥2 contractions · 0.95 light markers · 1.0 formal

**Display bands:** HIGH ≥0.55 · MEDIUM 0.30–0.54 · LOW 0.10–0.29 · CLEAR <0.10

**Calibration (three v0.5 runs, Apr 2026):**
- Huewrite R3: ~20% predicted vs <20% actual (Δ ~0, PyMuPDF-verified)
- G8 ChiroFlow AI2: ~65% predicted vs 69% actual (Δ −4, 80–85% paragraph-level alignment)
- G7 Moveeeeenow! AI1: ~45% predicted vs 47% actual (Δ ~0, 5/6 heavy-hitter alignment)

**Open issue (v0.6 watch):** Telehealth/mHealth scaffolded prose in market-analysis, target-audience, competition, and risk-mitigation sections flags more in Turnitin than S4b Pattern regex detects. Count 3 — re-weighting due. For now, manually raise ai_para by +0.10 when you read this register even without a full Pattern 1/2/3 hit.

**Retained findings from v0.4:**
- S4b is still the dominant signal and the highest-leverage rewrite target (T5b)
- S2, S3, S6 are no longer gated behind S4b but still carry lower weights on their own
- Grammatical noise suppresses Turnitin flags — now modelled as P_polish multiplier, not a binary step-down
- First-person / conversational voice genuinely clears paragraphs — now modelled as first_person_factor

---

## The 8 Detection Signals (+ S4 sub-split)

### S1 · Qualifying-text membership [Highest weight]
The detector only scores long-form prose. Short bulleted **fragments**, table **row labels**, headings, and reference entries are strongly biased toward non-qualification. However, the filter is **sentence-level, not container-level**: a complete sentence (subject + verb + predicate) inside a bullet or table cell can still flag. Format biases toward clearance, but it is not a guaranteed exemption. The test: does the item read as a complete grammatical sentence? If yes, it can still score.

**Conditional override — S4b-dense list clusters break the protection.** A sequence of 10+ list items each carrying the consulting-register cluster (abstract-noun triplets, nominalised outcomes) *will* flag despite bullet format. Confirmed Shawn BP2 Risk Mitigation list (~15 items flagged). Fragment format is not a shield when the cluster is dense.

### S2 · Uniform sentence length [High weight, **conditional on S4b**]
Tight clustering of sentence lengths in the 15–30 word band across 3+ consecutive sentences is a strong correlate of flagged passages — **but only when S4b consulting-register vocabulary co-occurs**. Low stdev on its own is not predictive. Where sentence length varies aggressively — sentences under 10 words interleaved with sentences over 25 — the same content stops flagging. Low stdev + S4b = strong AI signal. Low stdev without S4b = weak correlate, often clears. Note: removing a short sentence to "tighten" a paragraph can worsen this signal when S4b is also present (Dataset G regression).

### S3 · Scaffolded paragraph shape [Medium weight, **correlate only**]
The canonical AI paragraph: **topic sentence → 1–2 supporting sentences → concluding/transition sentence**. This 4-sentence scaffold appears in ~70% of flagged paragraphs but **does not flag on its own**. Shawn BP2 contained four fully-scaffolded paragraphs (Introduction, Proposed Solution at 468 words, Executive Summary, Conclusion) that cleared entirely — each lacked S4b and contained grammatical noise. Treat scaffold as a *necessary but not sufficient* correlate: it amplifies S4b but does not trigger without it.

Where the scaffold is broken — paragraphs that open mid-thought, close on a factual fragment, or split at uneven points — flags drop. Reshaping only the topic sentence (declarative → subordinate-clause opener) can flip the whole paragraph **when S4b is also addressed**.

**Sub-sectioned exception — scaffold-broken.** A paragraph that splits into ≥3 bolded or numbered sub-labels (Stage 1, Stage 2, Phase A, Step 1…) each followed by **bullet fragments** counts as scaffold-broken. The sub-labels replace the canonical topic → support → synthesis shape per stage, and fragment content under each carries no S2 rhythm. Confirmed Dataset H §6.1 Patient Journey — rated MEDIUM on prediction, cleared entirely by Turnitin.

**Phased-prose floor — MEDIUM minimum.** The inverse pattern: ≥3 phase/risk/stage enumerators ("Phase 1… Phase 2… Phase 3…", "Risk A… Risk B… Risk C…") each followed by **full prose paragraphs** rather than fragments. Floor severity at MEDIUM regardless of per-paragraph S6 absence. Per-phase prose carries S2 uniform rhythm + S4 vocabulary even when surface openers are clean, and the document-level enumeration scaffold itself is what Turnitin scores. Confirmed G9 AI1 Operational Plan and Risk Analysis — rated LOW on prediction, heavily flagged by Turnitin; under-prediction drove a −13pt gap.

### S4a · Generic LLM vocabulary [Low–Medium weight]
Single words LLMs reach for reflexively: *utilise, leverage, comprehensive, holistic, seamless, robust, facilitate, implement, underscore, pivotal, crucial, stakeholders, ecosystem, streamline, enhance, foster, synergy, framework, paradigm*. Individual substitutions rarely flip a flagged passage alone. Presence raises the severity ceiling but does **not** gate HIGH severity. S4a is a mild amplifier; S4b is the actual fingerprint.

### S4b · Consulting-register cluster [Highest weight — THE flagging fingerprint]
This is the signal that actually discriminates flagged from cleared prose in the corpus. Three co-occurring patterns define it:

**Pattern 1 — Abstract-noun chains.** Noun-of-noun constructions where both nouns are abstract:
- "assimilation of digital technologies"
- "integration of evidence-based modalities"
- "optimisation of healthcare delivery frameworks"
- "transformation of patient engagement paradigms"

**Pattern 2 — Nominalised outcomes.** Verbs converted to abstract nouns in outcome clauses:
- "enables enhanced coordination" (vs "helps providers coordinate")
- "drives the transitional shift to technology-enabled healthcare delivery"
- "fosters strategic alignment across stakeholder ecosystems"
- "facilitates standardisation of care pathways"

**Pattern 3 — Abstract-noun triplets (the high-risk triplet form).** Three nominalised outcomes strung together:
- "aggregate healthcare providers, enhance accessibility, and streamline patient experience"
- "consolidate data, optimise workflows, and elevate care quality"
- "integrate services, empower patients, and advance clinical outcomes"

**Diagnostic test:** Can you strip every concrete noun (device names, anatomical terms, conditions, numbers) from the sentence and still have a grammatical, meaningful sentence? If yes, the cluster is present.

**Gating rule:** HIGH severity requires S4b presence. A paragraph with S2+S3+S6 but no S4b caps at MEDIUM. S4b alone + S3 scaffold almost always flags. S4b alone without structural signals flags roughly half the time.

### S5 · Rule-of-three triplets [Medium weight — context-sensitive]
Phrases of the form "X, Y and Z" appear approximately every second sentence in flagged sections. LLMs produce these reflexively because training data rewards triadic rhythm. **Abstract-noun triplets score as S5+S4b compound** ("physical, psychological and social factors"). **Concrete-verb triplets score weakly** ("prescribed, delivered, stopped at discharge"). When counting triplets for severity, weight abstract triplets 2× and concrete triplets 0.5×.

### S6 · Self-referential / meta-commentary [Medium weight, **moderated by grammatical noise**]
Sentences that describe what the document is doing rather than saying something substantive:
- "This section analyses…"
- "This proposal presents…"
- "The core idea of this business plan is…"
- "The following discussion outlines…"

These reliably flag **when embedded in clean, consulting-register prose**. They can clear when the surrounding paragraph contains grammatical noise (broken syntax, typos, awkward phrasing, incomplete sentences). Confirmed Shawn BP2: meta-openers in paragraphs with typo-laden grammar cleared; meta-openers in polished paragraphs with S4b vocabulary flagged.

**Critical rule: when the cluster IS present, meta-commentary must be cut, not paraphrased.** Rephrasing a meta-sentence in clean prose keeps it flagged (confirmed G8, G7). If the heading already signals the section's content, the meta-sentence is redundant.

**Attribution note — opener does not absorb body risk.** When a meta-opener sits at the top of a paragraph that continues into a substantive S4b-heavy body, score the opener and the body as **independent** flag risks. Turnitin frequently flags the substantive paragraph on its own S2/S4b pattern regardless of what came before; do not assume the meta-sentence absorbs all the weight. Confirmed Dataset H ¶3 T&CM regulatory: the meta-opener "This business plan details…" was blamed as the trigger, but Turnitin actually highlighted the substantive T&CM regulatory body that followed.

### S7 · Document-wide phrase recurrence [Low weight, cumulative]
Each individual repetition is benign. Document-wide consistency of recurring phrases compounds across scoring — the detector weights whole-document signature as well as per-segment. Single-author documents are more vulnerable than multi-author documents, where natural voice variation dilutes the signature. S7 amplifies S4b; on its own it does not gate severity.

### S8 · Abstract-descriptor density [Low weight, aggregate]
Heavy reliance on abstract descriptors ("multiple health conditions", "complex comorbidities", "various stakeholders", "modern lifestyle changes") raises perplexity scores. Named specifics — actual conditions, named parties, real numbers — score as human because they are less predictable. S8 overlaps heavily with S4b Pattern 1 (abstract-noun chains) — treat them as reinforcing.

---

## Moderators (not signals — adjust severity after signal assessment)

### Grammatical-noise moderator [passive clearance mechanism]
If a paragraph contains visible grammatical noise — broken syntax, obvious typos, awkward agreement errors, incomplete sentences, or run-on fragments — reduce classified severity by **one step** (HIGH → MEDIUM, MEDIUM → LOW). This is a calibration factor, not a prescribable technique (do not advise writers to introduce typos). Confirmed Shawn BP2: multiple scaffolded paragraphs with meta-openers and S2 uniformity cleared because grammatical noise was present throughout.

The mechanism appears to be that Turnitin's perplexity model reads grammatical noise as human authorship evidence strong enough to outweigh structural signals. When the prose is clean *and* carries S4b, the cluster wins. When prose is noisy, noise wins.

### S4b-gating rule [v0.5 update — soft gate, not hard cap]
**S4b still carries the highest weight, but is no longer a hard gate for HIGH.** In v0.5, a paragraph with S2+S3+S6+S5 but no S4b can reach a raw S_struct of ~0.60, which × P_polish × fp_factor often lands in the MEDIUM band. The old v0.4 hard cap caused systematic under-prediction on Huewrite R2 (−21pp) and Dwayne R2 (−34pp). When S4b IS present, it remains the primary rewrite target (T5b) — removing it drops S_struct by 0.25–0.90 depending on which patterns fire.

---

## The 8 Techniques (ranked by effort-adjusted impact)

### T1 · Prose-to-table conversion [Highest impact] — targets S1
Convert any content expressible as rows × columns: service categories, role/responsibility breakdowns, timeline/objective mappings, risk/mitigation pairs, segment comparisons. Fragment-style cells clear reliably. **Caveat:** cell content must be genuine fragments — a full sentence in a table cell still flags. Test: "3+ month cash reserve" is safe; "Maintain a cash reserve covering at least three months of operating expenses" will still flag. **Additional caveat:** S4b-dense list clusters (10+ items each carrying nominalised outcomes) flag despite bullet format — rewrite the cluster, don't rely on list shape alone.

### T2 · Burstiness engineering [Highest impact] — targets S2
Within any paragraph of 3+ sentences: include at least one sentence **under 10 words** and one **over 25 words**. Never run three consecutive sentences within 3 words of each other. Simplest method: split one long sentence into two short fragments, then join two short sentences into one medium one. **Direction matters:** short sentences must be added, not removed. **Note:** T2 alone is insufficient when S4b is heavy — pair with T5b.

### T3 · Scaffold disruption [Medium impact — pair with T5b] — targets S3
- Open at least one paragraph per section **mid-thought** — skip the topic sentence
- Close at least one paragraph per section **on a factual fragment** — skip the synthesis
- Split long paragraphs at uneven points (after sentence 1, not the middle)
- Use one-sentence paragraphs sparingly for emphasis
- Reshaping only the topic sentence from declarative to subordinate-clause opener ("Even as…", "Where…", "Despite…") can flip the whole paragraph **when S4b is also removed**

**Important:** T3 alone does not clear a flagged paragraph if S4b is present. Scaffold disruption buys perhaps 30–40% of the fix; the remainder is S4b removal (T5b).

### T4 · Hyper-specific detail substitution [High impact, limited scope] — targets S8 + S4a
Replace abstract descriptors with named, specific technical detail. "Multiple health conditions" → "active lumbar pathology or uncontrolled diabetes". "Various stakeholders" → specific named parties. "A range of treatments" → the actual list. Scope is limited by how many abstract placeholders the document contains, but where they exist it is free impact.

### T5a · Generic vocabulary substitution [Low–Medium impact] — targets S4a
Replace LLM-favoured single words at ~70–80% rate (leave some untouched so the rewrite doesn't look mechanical).

| Replace | With |
|---|---|
| utilise | use |
| leverage | use, draw on |
| facilitate | help, run, make possible |
| implement | set up, put in place, run |
| optimise | improve, refine |
| streamline | simplify, speed up |
| robust | strong, reliable |
| comprehensive | full, complete, detailed |
| holistic | whole-person, integrated |
| seamless | smooth, uninterrupted |
| enhance | improve, strengthen |
| foster | build, grow, support |
| underscore | show, point to |
| demonstrate | show |
| ensure | make sure |
| align with | match, fit with |
| synergy | working together |
| framework | system, approach |
| paradigm | model, approach |
| pivotal / crucial | important, central |
| drive (figurative) | lead to, push |
| deliver (figurative) | provide, give |

**Warning:** T5a alone does not clear flags — confirmed independently in Spinability, G8, G7, Dataset G. Must pair with T2/T3 **and** T5b for compound effect.

### T5b · Consulting-register cluster removal [Highest impact] — targets S4b
This is the most load-bearing rewrite technique in the playbook. Three targets:

**Break abstract-noun chains.** "Assimilation of digital technologies" → "clinics are starting to use digital tools". "Integration of evidence-based modalities" → "bringing research-backed treatments into the clinic". Replace noun-of-noun constructions with subject–verb–object prose.

**De-nominalise outcomes.** "Enables enhanced coordination" → "helps providers coordinate". "Drives the transitional shift to technology-enabled healthcare delivery" → "pushes clinics toward tech-supported care". Convert nominalised verbs back to active verbs with concrete subjects.

**Break abstract-noun triplets.** "Aggregate healthcare providers, enhance accessibility, and streamline patient experience" → "bring providers onto one platform so patients can find and book care faster". Keep at most one abstract triplet per page; replace the rest with one concrete action phrase.

**Diagnostic:** After rewriting, re-run the S4b diagnostic — strip concrete nouns and check whether the sentence still parses. If it does, more nominalisations need breaking.

### T6 · Cut meta-commentary [Medium impact, easy] — targets S6
Any sentence describing what the document is doing is a free cut **when the paragraph is clean-prose and S4b-heavy**. "This section analyses…" → delete and rely on the heading. **Meta-commentary survives paraphrasing — it must be cut entirely.** Confirmed G8: "This business proposal outlines…" → "This business proposal consists of the plan to…" — still flagged.

**Exception:** If the paragraph already contains grammatical noise and S4b is absent, meta-openers may self-clear. Do not waste effort cutting them when the moderator already suppresses the signal.

### T7 · Break rule-of-three triplets [Medium impact for abstract triplets] — targets S5
Break roughly half of all triplets into pairs or single items. Keep triplets only where all three items are genuinely distinct and necessary. Prioritise **abstract-noun triplets** (these are S4b Pattern 3 and carry the heaviest weight) over concrete-verb triplets. "Timely, coordinated and multi-modal management" → "coordinated multi-modal management".

### T8 · Force variation in recurring phrases [Low impact, polish] — targets S7
Phrasings that recur across sections should be said differently each time. "Working adults aged 25–55" in §2 → "professionals in their late 20s to mid-50s" in §7 → "office-based workers" in §8. Softens the whole-document signature.
