# Few-Shot Examples — Real Before/After from Corpus

These are real flagged → cleared (or improved) passages from the IMU BCP2485 corpus. Use them as ground truth for what the interventions actually look like in practice.

---

## Example 1 — T4 Hyper-specific detail + T2 Burstiness + T3 Scaffold disruption
**Source:** Dwayne · §4.1 Problem Statement · R1 (flagged) → R2 (cleared)

**BEFORE (flagged):**
> Although many personal trainers now hold recognised fitness certifications, they are not trained to conduct clinical assessments, manage pain presentations, or design exercise programmes for individuals with multiple health conditions.

**AFTER (cleared):**
> Personal trainers hold fitness certifications, not clinical qualifications. They are not trained to screen for red flags, interpret imaging, or modify loading for someone with active lumbar pathology or uncontrolled diabetes. For the MSK-chronic disease population this proposal targets, that is a clinical contraindication, not a minor gap in service.

**What changed:**
- T4: "multiple health conditions" → "active lumbar pathology or uncontrolled diabetes" (specific named conditions)
- T2: one 42-word sentence → three sentences of 9, 22, 22 words (burstiness introduced)
- T3: closes on a blunt negative contrast ("not a minor gap in service") instead of synthesis
- T5: "conduct clinical assessments, manage pain presentations, or design exercise programmes" → plainer, more specific

---

## Example 2 — T3 Scaffold disruption
**Source:** Dwayne · §7.3 Competitive Landscape · R1 (flagged) → R2 (cleared)

**BEFORE (flagged):**
> These clinics provide clinical assessment and treatment for neuromusculoskeletal conditions. However, their exercise components are typically delivered in a clinical setting and are limited in scale. Exercise programmes are usually individually prescribed and confined to rehabilitation rooms rather than full gym environments. They generally do not offer group training, structured fitness memberships, or progressive strength and conditioning programmes.

**AFTER (cleared):**
> Assessment and manual treatment are well covered. What these clinics do not offer is what happens next. Exercise is prescribed for a specific complaint, delivered in a clinical room, and stopped at discharge. None of these centres run progressive strength programmes, structured gym memberships, or a defined route from rehabilitation into long-term conditioning.

**What changed:**
- T3: opens with an abrupt fragment "Assessment and manual treatment are well covered" — skips topic sentence entirely
- T3: conversational pivot "What these clinics do not offer is what happens next" disrupts the scaffold
- T5: concrete verb triple "prescribed, delivered, stopped at discharge" replaces abstract-noun phrasing
- T7: the closing triplet uses concrete action verbs, not abstract nouns

---

## Example 3 — T5 Vocabulary substitution (amplified by T2)
**Source:** Dwayne · §3.1 Background · R1 (flagged) → R2 (improved)

**BEFORE (flagged):**
> The relationship between MSK conditions and multimorbidity is bidirectional and self-reinforcing. Chronic pain drives physical inactivity, which precipitates cardiovascular deconditioning, visceral adiposity, and metabolic dysregulation…

**AFTER (improved):**
> The relationship between MSK conditions and multimorbidity goes both ways. Chronic pain cuts activity; inactivity produces cardiovascular deconditioning, visceral fat accumulation, and metabolic dysregulation…

**What changed:**
- T5: "is bidirectional and self-reinforcing" → "goes both ways" (plain English)
- T5: "drives physical inactivity" → "cuts activity" (verb + noun → single verb)
- T5: "visceral adiposity" → "visceral fat accumulation" (jargon → plain)
- T2: semicolon creates rhythm variation within the second sentence

---

## Example 4 — T6 Cut meta-commentary (surgical single deletion)
**Source:** Dataset G · §2.1 Literature Review · AI1 (flagged) → AI2 (cleared)

**BEFORE (flagged):**
> To ensure a comprehensive and focused review of relevant literature, a literature search strategy was crafted, involving databases such as Google Scholar, PubMed, Scopus and the IMU e-Library.

**AFTER (cleared):**
> A literature search strategy was first developed, using databases such as Google Scholar, PubMed, Scopus and the IMU e-Library.

**What changed:**
- T6: the entire "To ensure a comprehensive and focused review of relevant literature," meta-framing clause was deleted — not paraphrased, deleted
- The rest of the sentence is near-identical
- Single surgical deletion cleared the entire block

---

## Example 5 — T2 Burstiness negative proof (what NOT to do)
**Source:** Dataset G · §1.6 Objectives · AI1 (1/3 flagged) → AI2 (3/3 flagged) — REGRESSION

**BEFORE AI2 edit (partially clear):**
> The objectives of this study are as follows: [8-word intro line]
> Objective 1: [~20 words] — flagged
> Objective 2: [~20 words] — cleared
> Objective 3: [~20 words] — cleared

**AFTER AI2 edit (fully flagged):**
> [intro line removed — "tighter" edit]
> Objective 1: [~20 words] — flagged
> Objective 2: [~20 words] — flagged
> Objective 3: [~20 words] — flagged

**What went wrong:**
- Removing the 8-word intro line eliminated the only burstiness in the block
- Three near-identical-length objectives (18–22 words each) now cluster uniformly in the 15–30 word band
- The edit felt editorially correct but was S2-toxic
- **Lesson:** T2 is directional — short sentences must be added, not removed. When "tightening" a paragraph, check whether you are removing the only short sentence in a block.

---

## Example 6 — T6 Meta-opener: paraphrase FAILS (what NOT to do)  ·  P006 anti · ✅ confirmed 3/3
**Source:** Dataset G8 · §7.3 Market Strategy · AI1 (62.6% flagged) → AI2 (**84.3% flagged, flag went UP**)

**BEFORE (AI1, flagged):**
> Chiroflow adopts a tiered subscription pricing model designed to align with the growth stages of chiropractic clinics, thereby ensuring scalability and affordability.

**AFTER (AI2, MORE flagged):**
> Chiroflow has implemented a tiered subscription pricing approach to match the developmental levels of chiropractic clinics, keeping it scalable and affordable.

**What went wrong:**
- Pure thesaurus paraphrase with register upgrade: "adopts" → "has implemented", "growth stages" → "developmental levels", "ensuring scalability" → "keeping it scalable"
- The scaffold (topic sentence → purpose clause → benefit closer) was preserved intact
- Register was made *more* formal and nominalised — exactly the S4b signature
- Flag went from 62.6% to **84.3% (+22pt)** — paraphrase didn't just fail, it actively made it worse
- **Lesson:** meta-framing openers must be **deleted or absorbed**, never rephrased. The second corpus case: Dataset G8 §10.1.1 went 84.0% → 94.6% (+10pt) via "Operating…requires strict adherence to" → "Industry practices…operate under the framework of" (another register-upgrade paraphrase). Any "operate under the framework of" / "implemented…to match developmental levels" type rephrasing is an anti-pattern.

---

## Example 7 — T6 Meta-opener: absorption-deletion (positive companion)  ·  P006 positive
**Source:** Dataset Dwayne · §1.0 Introduction · R1 (flagged, 53.8% section) → R2 (cleared, 0.0%)

**BEFORE (flagged):**
> Guidelines such as NICE and ACP endorse combining spinal manipulative therapy (SMT) with exercise for LBP. This shows that a multimodal approach to musculoskeletal diseases, combining manual treatment, rehabilitation exercises, and lifestyle modification, is increasingly supported by modern healthcare research.

**AFTER (cleared):**
> National Institute for Health and Care Excellence (NICE) and the American College of Physicians (ACP) guidelines prove that a multimodal approach combining spinal manipulative therapy (SMT), rehabilitation exercises and lifestyle modification is highly recommended for treating LBP.

**What changed:**
- T6: the "This shows that…" synthesis meta-clause was *absorbed* into the preceding factual sentence — the meta-scaffold element is gone as a standalone unit
- Two sentences merged into one direct declarative: the framing ("This shows that…is supported by modern research") was deleted by merge, not rephrased
- **Lesson:** when a meta-framing clause can be expressed as a direct fact ("X proves Y" instead of "X supports the idea that Y"), absorb it. Merger counts as deletion. Shawn's Risk Analysis opener showed the same move: "The potential risk that arises from X can come from A, B, C" → "X may provide A, B, C" — absorption-deletion, not paraphrase.

---

## Example 8 — P008 anti: word-level rewrite that preserves scaffold FAILS  ·  ✅ confirmed
**Source:** Dataset H · §7.0 Market Analysis opener · BP4 (flagged) → Huewrite (still flagged)

**BEFORE (flagged):**
> This section analyses the market landscape relevant to Spinability's establishment in Klang Valley.

**AFTER (still flagged — paraphrase failed):**
> This section analyzes the market relevant to the establishment of Spinability in Klang Valley.

**What went wrong:**
- Word-level edits only: "analyses" → "analyzes" (s→z), "market landscape relevant to Spinability's establishment" → "market relevant to the establishment of Spinability" (reorder), "Klang Valley" unchanged
- The "This section…" meta-opener scaffold is intact
- No T1/T3/T6 applied — just T5 surface polish
- **Lesson:** scaffold-preserving edits do not clear prose flags. If S4b or a meta-opener is present, a word swap is wasted effort. Scope caveat: this is confirmed for *prose* scaffolds. Bullet-list scaffolds are more ambiguous (see Shawn Risk Analysis: −37pt on bullet items, partially attributable to P016 context-bleed).

---

## Example 9 — P001: sentence-leading `Our / We / You` rescues meta-openers  ·  🔍 2 datasets, 5 internal instances
**Source:** Dataset Dwayne · §12.0 Conclusion · R1 (80.3% flagged) → R2 (5.9% flagged, −74pt)

**BEFORE (flagged):**
> The ChiroRehab Performance Centre presents as a comprehensive and integrated approach to musculoskeletal care in the Klang Valley.

**AFTER (cleared):**
> Our proposed business provides a fresh and innovative perspective on how patient care goes beyond just typical clinical diagnosis and treatment. To summarise, our proposed centre can contribute to the chiropractic profession by combining chiropractic treatment with supervised strength training.

**What changed:**
- Opening frame shifted from third-person institutional ("The ChiroRehab Performance Centre presents as…") to sentence-leading first-person possessive ("Our proposed business provides…", "our proposed centre can contribute…")
- Sentence-leading position is load-bearing — mid-sentence "our" (as an object pronoun buried after a comma) does NOT produce the same rescue (P003 anti-evidence)
- Also see Dwayne §11.1 Potential Risks: R1 94.5% → R2 34.9% via "The main threat to **our proposed business** will be…" + "…businesses that **our target clientele** are already familiar with" + "This can hinder **our initial growth**"
- And Dataset H §9.0 timeline opener: "Our clinic will be developed over three phases…" cleared despite being a classic meta-opener
- **Lesson:** when faced with a meta-scaffold opener you can't delete (because it carries real information), try rewriting it to *lead* with `Our [noun]` / `We` / `You`. The first-person possessive at sentence-start is a register flip that downgrades the whole sentence's S6/S8 load. Tried-and-failed alternative: burying "our" mid-sentence doesn't work — it must be the first or second word.

---

## Example 10 — T1 Prose→table (structural rupture, no grammatical surgery needed)  ·  P015 🔍 1 dataset, 2 clean instances
**Source:** Dataset Dwayne · §8.4 Strategic Partnerships · R1 (90.9% flagged, single paragraph of prose) → R2 (0.0%, 4-row table)

**BEFORE (flagged):**
> The centre will establish formal referral agreements with general practitioners, orthopaedic surgeons, and rheumatologists in and around the Klang Valley. Sports teams and organisations will be offered packages for performance enhancement. Wellness corporations will be targeted with packages covering MSK screening, ergonomic assessments, and membership discounts for staff. Universities and colleges will be engaged via partnerships providing student discounts for clinical care and gym memberships.

**AFTER (cleared):**

| Channel | Description |
|---|---|
| GP and Specialists | Establish formal referral agreements with general practitioners, orthopaedic surgeons, and even rheumatologists located in and around the Klang Valley |
| Sports teams and organisations | Provide packages for improving and enhancing performance… |
| Wellness corporations | Packages that would cover MSK screening, ergonomic assessments, and membership discounts for staff |
| Universities and Colleges | Partnerships with universities and educational institutions providing student discounts for clinical care and gym memberships |

**What changed:**
- T1: four prose sentences of near-identical length and parallel structure → 4-row table with short label column ("Channel") + detail column ("Description")
- Detail cells remain **full-sentence declarative prose** with no subject-drop or verb-drop (unlike P005 bullets which require grammatical surgery)
- The table's structural rupture is sufficient on its own; no T5 vocab work needed
- Section flag: **90.9% → 0.0%**
- Also see Dwayne §5.0 Objectives: 4 parallel "To establish… / To deliver… / To promote… / To develop…" infinitive-phrase objectives (81.8% flagged) → 5-row "**No. | Objective | Timeline**" table with numeric targets in cells ("at least 10 chiropractic patients a day and 100 members in the gym within the first 6 months"). Cleared to 18.3% (-63pt)
- **Lesson:** prose→table clears at higher flag levels than prose→bullets, and tables don't require per-row grammatical surgery. For any section you can reasonably express as `Label | Detail` rows (partnerships, tiers, risks, objectives, timelines, features), convert.

---

## Example 11 — P005 + P009 paired: prose→bullets REQUIRES grammatical surgery  ·  🔍 1 dataset paired rule
**Source:** Dataset H · §5.x Service offerings · BP4 (prose, flagged) → Huewrite (bullets, cleared — with grammatical surgery)

**BEFORE (flagged, prose):**
> The clinic will offer chiropractic assessment and adjustment services, supervised rehabilitation programmes tailored to each patient's condition, and strength-and-conditioning training delivered in a fully-equipped gym environment.

**AFTER (cleared, bullets WITH grammatical surgery — subject-drop + verb-drop):**
> - Chiropractic assessment and adjustment
> - Supervised rehabilitation programmes (tailored per condition)
> - Strength-and-conditioning training in a fully-equipped gym

**What worked:**
- T1: prose → bullets (structural rupture)
- **Crucial:** every bullet dropped the subject ("The clinic will offer…") and the verb ("offer / provide / deliver"). Bullets are **noun-phrase fragments**, not full sentences
- Parallel syntax is fine when the syntax itself is fragmentary

**COUNTER-EXAMPLE — prose→bullets WITHOUT grammatical surgery FAILS (P009):**

> - The clinic will offer chiropractic assessment and adjustment services.
> - The clinic will provide supervised rehabilitation programmes tailored to each patient.
> - The clinic will deliver strength-and-conditioning training in a fully-equipped gym.

Three bullets, but each is a **full sentence** with intact subject + verb ("The clinic will offer…", "The clinic will provide…", "The clinic will deliver…"). The bullet format is cosmetic; the sentences still carry S2 (uniform length) and S3/S5 (parallel scaffold). In Dataset H this converted structure **stayed flagged**.

- **Lesson:** when converting prose to bullets, the conversion is not what clears — the **fragmentation is**. Bullets must be noun phrases or clause fragments, not full sentences with a shared subject/verb. If you can read your bullets aloud as three complete grammatical sentences, P009 applies: the flag will not clear. Rewrite as fragments.

---

## Calibration note — P016 Context-bleed (not a rewrite, a measurement correction)
🔍 2 datasets, 3 positive cases + 3 negative controls

**What to know:** paragraphs adjacent to rewritten-and-cleared neighbours sometimes flip flagged→cleared **despite being byte-identical** to the earlier version. Confirmed in Shawn Background (para 1 identical R1=R2, 77%→0%, adjacent to rewritten ExecSum para 4) and Dwayne §8.2 opener + §8.3 (identical text, cleared after §8.1/§8.4 were rewritten).

**Negative controls:** in the same document, identical paragraphs *not* adjacent to rewrites kept bit-identical flag offsets — the effect is boundary-driven, not stochastic.

**Implications when diagnosing a rewrite:**
- A cleared paragraph near a heavily-rewritten neighbour may have cleared because of the neighbour, not because of anything done to it. Do not attribute the clearance to the paragraph's own surface features when this is possible.
- When ranking rewrite targets in a high-flag document, prefer paragraphs that *border* other high-flag paragraphs — one rewrite can cascade into its neighbours for free.
- For pre-submission scoring: treat adjacent high-flag paragraphs as correlated, not independent. Scoring them as independent overstates the total flag risk.
