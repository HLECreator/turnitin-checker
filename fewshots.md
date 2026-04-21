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
