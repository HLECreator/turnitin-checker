# Signal & Technique Reference — Turnitin AI Detector Playbook

Derived from 7 corpora · 11 reports · ~79,400 words · 445 flagged segments (BCP2485, IMU).

---

## The 8 Detection Signals

### S1 · Qualifying-text membership [Highest weight]
The detector only scores long-form prose. Short bulleted **fragments**, table **row labels**, headings, and reference entries are strongly biased toward non-qualification. However, the filter is **sentence-level, not container-level**: a complete sentence (subject + verb + predicate) inside a bullet or table cell can still flag. Format biases toward clearance, but it is not a guaranteed exemption. The test: does the item read as a complete grammatical sentence? If yes, it can still score.

### S2 · Uniform sentence length [Highest weight]
Tight clustering of sentence lengths in the 15–30 word band across 3+ consecutive sentences is the dominant measurable feature of flagged passages. Where sentence length varies aggressively — sentences under 10 words interleaved with sentences over 25 — the same content stops flagging. Low stdev = AI signal. Note: removing a short sentence to "tighten" a paragraph can worsen this signal (Dataset G regression).

### S3 · Scaffolded paragraph shape [High weight]
The canonical AI paragraph: **topic sentence → 1–2 supporting sentences → concluding/transition sentence**. This 4-sentence scaffold appears in ~70% of flagged paragraphs. Where the scaffold is broken — paragraphs that open mid-thought, close on a factual fragment, or split at uneven points — flags drop. Reshaping only the topic sentence (declarative → subordinate-clause opener) can flip the whole paragraph.

### S4 · Low-perplexity vocabulary clusters [Medium weight]
Words and phrases LLMs reach for reflexively: *utilise, leverage, comprehensive, holistic, seamless, robust, facilitate, implement, underscore, pivotal, stakeholders, ecosystem, streamline, enhance, foster, synergy, framework, paradigm*. Individual substitutions rarely flip a flagged passage alone, but consistent replacement compounds with structural changes.

### S5 · Rule-of-three triplets [Medium weight]
Phrases of the form "X, Y and Z" appear approximately every second sentence in flagged sections. LLMs produce these reflexively because training data rewards triadic rhythm. Abstract-noun triplets ("physical, psychological and social factors") score worse than concrete-verb triplets ("prescribed, delivered, stopped at discharge").

### S6 · Self-referential / meta-commentary [Medium weight]
Sentences that describe what the document is doing rather than saying something substantive:
- "This section analyses…"
- "This proposal presents…"
- "The core idea of this business plan is…"
- "The following discussion outlines…"

These reliably flag. **Critical rule: meta-commentary must be cut, not paraphrased.** Rephrasing a meta-sentence keeps it flagged (confirmed G8, G7 datasets). If the heading already signals the section's content, the meta-sentence is redundant.

### S7 · Document-wide phrase recurrence [Low weight, cumulative]
Each individual repetition is benign. Document-wide consistency of recurring phrases compounds across scoring — the detector weights whole-document signature as well as per-segment. Single-author documents are more vulnerable than multi-author documents, where natural voice variation dilutes the signature.

### S8 · Abstract-descriptor density [Low weight, aggregate]
Heavy reliance on abstract descriptors ("multiple health conditions", "complex comorbidities", "various stakeholders", "modern lifestyle changes") raises perplexity scores. Named specifics — actual conditions, named parties, real numbers — score as human because they are less predictable.

---

## The 8 Techniques (ranked by effort-adjusted impact)

### T1 · Prose-to-table conversion [Highest impact] — targets S1
Convert any content expressible as rows × columns: service categories, role/responsibility breakdowns, timeline/objective mappings, risk/mitigation pairs, segment comparisons. Fragment-style cells clear reliably. **Caveat:** cell content must be genuine fragments — a full sentence in a table cell still flags. Test: "3+ month cash reserve" is safe; "Maintain a cash reserve covering at least three months of operating expenses" will still flag.

### T2 · Burstiness engineering [Highest impact] — targets S2
Within any paragraph of 3+ sentences: include at least one sentence **under 10 words** and one **over 25 words**. Never run three consecutive sentences within 3 words of each other. Simplest method: split one long sentence into two short fragments, then join two short sentences into one medium one. **Direction matters:** short sentences must be added, not removed.

### T3 · Scaffold disruption [High impact] — targets S3
- Open at least one paragraph per section **mid-thought** — skip the topic sentence
- Close at least one paragraph per section **on a factual fragment** — skip the synthesis
- Split long paragraphs at uneven points (after sentence 1, not the middle)
- Use one-sentence paragraphs sparingly for emphasis
- Reshaping only the topic sentence from declarative to subordinate-clause opener ("Even as…", "Where…", "Despite…") can flip the whole paragraph without changing anything else

### T4 · Hyper-specific detail substitution [High impact, limited scope] — targets S8 + S4
Replace abstract descriptors with named, specific technical detail. "Multiple health conditions" → "active lumbar pathology or uncontrolled diabetes". "Various stakeholders" → specific named parties. "A range of treatments" → the actual list. Scope is limited by how many abstract placeholders the document contains, but where they exist it is free impact.

### T5 · Vocabulary substitution [Medium impact, amplifies T2/T3] — targets S4
Replace LLM-favoured vocabulary at ~70–80% rate (leave some untouched so the rewrite doesn't look mechanical).

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

**Warning:** vocabulary substitution without structural change (T2/T3) does not clear flags — confirmed independently in Spinability, G8, G7, and Dataset G.

### T6 · Cut meta-commentary [Medium impact, easy] — targets S6
Any sentence describing what the document is doing is a free cut. "This section analyses…" → delete and rely on the heading. **Meta-commentary survives paraphrasing — it must be cut entirely.** Confirmed G8: "This business proposal outlines…" → "This business proposal consists of the plan to…" — still flagged.

### T7 · Break rule-of-three triplets [Low impact, high volume] — targets S5
Break roughly half of all triplets into pairs or single items. Keep triplets only where all three items are genuinely distinct and necessary. "Timely, coordinated and multi-modal management" → "coordinated multi-modal management".

### T8 · Force variation in recurring phrases [Low impact, polish] — targets S7
Phrasings that recur across sections should be said differently each time. "Working adults aged 25–55" in §2 → "professionals in their late 20s to mid-50s" in §7 → "office-based workers" in §8. Softens the whole-document signature.
