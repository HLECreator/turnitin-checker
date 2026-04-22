#!/usr/bin/env python3
"""
Turnitin AI Checker — v0.5
Run: python check.py <document.docx|document.pdf>
Output: <docname>_packet.md — drag into Claude.ai (Opus) for a flagged HTML report.

v0.5 — Continuous per-paragraph scoring (22 Apr 2026, 8 corpora, 13 reports, ~103,150 words):
- Replaces v0.4 four-band categorical output (CLEAR/LOW/MEDIUM/HIGH + S4b hard gate)
- Formula: AI_para = S_struct × P_polish × first_person_factor, bounded [0, 1]
- S_struct: additive per-signal weights (see compute_s_struct()); no S4b gating required for HIGH
- P_polish: multiplicative noise moderator (1.0 clean → 0.5 recurring noise)
- first_person_factor: voice-register moderator (0.8 sustained first/second-person, 0.9 contractions)
- Document score: word-weighted average of AI_para across all qualifying paragraphs (≥20 words)
- Removes v0.3/v0.4 fixed 7-paragraph ceiling — full document coverage
- Calibration: Huewrite R3 ~20% vs <20% actual; G8 AI2 ~65% vs 69%; G7 AI1 ~45% vs 47%
- Open issue (v0.6 target): S4b-gating too strict on telehealth/mHealth scaffolded prose
"""

import sys
import re
import statistics
from pathlib import Path

# ── ruler signal thresholds (conservative v0.1 heuristics) ──────────────────
STDEV_FLAG_BELOW = 8.0    # S2: sentence-length stdev below this = uniform rhythm
TTR_FLAG_BELOW   = 0.55   # S8: type-token ratio below this = low vocab diversity
HEDGE_FLAG_ABOVE = 0.06   # S4: hedge word fraction above this = hedge-heavy
MIN_PARA_WORDS   = 20     # skip paragraphs shorter than this
MIN_SENTENCES    = 3      # minimum sentences needed to run S2 stdev check

HEDGE_SINGLE = {
    "moreover", "furthermore", "additionally", "nevertheless", "therefore",
    "consequently", "subsequently", "accordingly", "hence", "thereby",
    "utilize", "utilise", "leverage", "facilitate", "implement", "optimise",
    "optimize", "streamline", "robust", "comprehensive", "holistic", "seamless",
    "enhance", "foster", "underscore", "pivotal", "crucial", "synergy",
    "stakeholders", "ecosystem", "paradigm",
}

HEDGE_PHRASES = [
    "it is important to note",
    "it is worth noting",
    "it should be noted",
    "in order to",
    "with regards to",
    "in terms of",
    "a wide range of",
    "a variety of",
    "a number of",
    "in today's",
]

# S4b — consulting-register cluster (the true flagging fingerprint).
# Three patterns: abstract-noun chains, nominalised outcomes, abstract-noun triplets.
# A paragraph is S4b-positive when it contains 2+ hits combined.

# Pattern 1 — abstract-noun chain phrases (noun-of-abstract-noun constructions)
S4B_CHAIN_PATTERNS = [
    r"\b(assimilation|integration|optimisation|optimization|transformation|"
    r"implementation|facilitation|realisation|realization|consolidation|"
    r"augmentation|enhancement|alignment|cultivation|orchestration|"
    r"standardisation|standardization|harmonisation|harmonization|"
    r"amplification|elevation|proliferation) of\b",
    r"\bshift to (technology|digital|integrated|holistic|comprehensive|seamless)",
    r"\btransition(al)? (shift|move|progression) to\b",
    r"\b(ecosystem|paradigm|framework|landscape) of (digital|integrated|holistic)",
]

# Pattern 2 — nominalised outcome verbs (AI-favoured active verbs with abstract objects)
S4B_NOMINAL_PATTERNS = [
    r"\b(enables?|drives?|fosters?|facilitates?|empowers?|elevates?|"
    r"streamlines?|optimi[sz]es?|leverages?|cultivates?|orchestrates?|"
    r"catalys(es|ts?)|accelerates?|underpins?|underscores?) "
    r"(enhanced|seamless|holistic|comprehensive|integrated|strategic|"
    r"sustainable|scalable|robust|transformative|innovative)\b",
    r"\b(coordination|alignment|engagement|adoption|delivery|accessibility|"
    r"scalability|interoperability) across\b",
]

# Pattern 3 — abstract-noun triplet construction (three nominalised outcomes)
# Heuristic: three verbs-that-become-abstract in a row, connected by commas + and
S4B_TRIPLET_PATTERN = re.compile(
    r"\b(aggregate|enhance|streamline|optimi[sz]e|facilitate|foster|empower|"
    r"drive|deliver|elevate|consolidate|integrate|leverage|cultivate|"
    r"orchestrate|accelerate)\w*\s+[\w\s\-]{1,40},\s+"
    r"(enhanc|streamlin|optimi[sz]|facilitat|foster|empower|drive|deliver|"
    r"elevat|consolidat|integrat|leverag|cultivat|orchestrat|accelerat)\w*\s+[\w\s\-]{1,40},?\s+and\s+"
    r"(enhanc|streamlin|optimi[sz]|facilitat|foster|empower|drive|deliver|"
    r"elevat|consolidat|integrat|leverag|cultivat|orchestrat|accelerat)\w*\s+[\w\s\-]{1,40}",
    re.IGNORECASE,
)

S4B_CHAIN_RE = [re.compile(p, re.IGNORECASE) for p in S4B_CHAIN_PATTERNS]
S4B_NOMINAL_RE = [re.compile(p, re.IGNORECASE) for p in S4B_NOMINAL_PATTERNS]

# Grammatical-noise moderator heuristic: detect common signs of noisy prose.
# This is deliberately conservative — false negatives are safer than false positives.
NOISE_PATTERNS = [
    r"\s{2,}\w",                        # double-spaces mid-sentence (typo artefact)
    r"\b[a-z]+[A-Z][a-z]+\b",           # camelCase mid-word (OCR/paste artefact)
    r"\bis are\b|\bare is\b|\bhas have\b|\bhave has\b",  # agreement errors
    r"\b(a|an)\s+[aeiouAEIOU]",         # "a apple" type errors (rough)
    r"\b(the the|and and|of of|to to|in in)\b",  # accidental doubling
    r"[\.\,\;\:\?\!]{2,}",              # double punctuation
    r"\w\s+[\.\,\;\:]\s*\w",            # space before punctuation
]
NOISE_RE = [re.compile(p) for p in NOISE_PATTERNS]

FORMULAIC_OPENERS = [
    r"^in today['\u2019]s",
    r"^in (an? )?(increasingly|ever[-\s])",
    r"^this (section|proposal|report|document|paper|plan|chapter|study|business)",
    r"^the (core|primary|main|key|fundamental) (idea|purpose|goal|aim|objective)",
    r"^it is (important|essential|crucial|critical|necessary|worth)",
    r"^as (mentioned|discussed|outlined|noted|stated|described)",
    r"^in (conclusion|summary|closing)",
    r"^overall[,\s]",
    r"^to (ensure|achieve|facilitate|implement|address|support|enhance|provide)",
    r"^by (leveraging|utilizing|utilising|implementing|integrating|combining)",
    r"^the following (section|discussion|analysis|overview)",
]

# S3 partial — synthesis closer: last sentence wraps up with a meta-conclusion
SYNTHESIS_CLOSER = re.compile(
    r"\b(in conclusion|in summary|overall|therefore|thus|as a result|"
    r"this (shows|demonstrates|highlights|suggests|indicates|underscores|"
    r"reveals|allows|ensures|means|reflects|reinforces)|"
    r"this is (why|evident|crucial|important|essential)|"
    r"these (results|findings|factors|aspects|elements) (show|suggest|highlight|demonstrate))"
    r"[,\s]",
    re.IGNORECASE,
)

# S5 — rule-of-three triplet: "X, Y and Z" or "X, Y, and Z"
TRIPLET = re.compile(
    r"\b[\w][\w\s\-]{1,30},\s+[\w][\w\s\-]{1,30},?\s+and\s+[\w][\w\s\-]{1,30}\b",
    re.IGNORECASE,
)


# ── file readers ─────────────────────────────────────────────────────────────

def read_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        sys.exit("Missing: pip install python-docx")
    doc = Document(path)
    return "\n\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def normalise_whitespace(text: str) -> str:
    # PDFs often extract with inter-character spaces; collapse them
    text = re.sub(r'[ \t]{2,}', ' ', text)
    # Preserve paragraph breaks (2+ newlines) but normalise single newlines within a paragraph
    paragraphs = re.split(r'\n{2,}', text)
    cleaned = []
    for para in paragraphs:
        # Join lines that don't end with punctuation (mid-word line breaks from PDF)
        lines = para.splitlines()
        joined = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if joined and not joined[-1] in ".!?,:;-":
                joined += " " + line
            else:
                joined += ("\n" if joined else "") + line
        cleaned.append(joined.strip())
    return "\n\n".join(p for p in cleaned if p)


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            sys.exit("Missing: pip install pypdf")
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    raw = "\n\n".join(p.strip() for p in pages if p.strip())
    return normalise_whitespace(raw)


# ── ruler metrics ─────────────────────────────────────────────────────────────

def split_sentences(text: str) -> list:
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in raw if len(s.split()) >= 3]


def sentence_length_stdev(sentences: list) -> float:
    lengths = [len(s.split()) for s in sentences]
    return statistics.stdev(lengths) if len(lengths) > 1 else 0.0


def type_token_ratio(text: str) -> float:
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if len(words) < 5:
        return 1.0
    return len(set(words)) / len(words)


def hedge_density(text: str) -> float:
    words = text.lower().split()
    if not words:
        return 0.0
    hits = sum(1 for w in words if w.rstrip(".,;:!?") in HEDGE_SINGLE)
    lower = text.lower()
    for phrase in HEDGE_PHRASES:
        if phrase in lower:
            hits += 1
    return hits / len(words)


def has_formulaic_opener(text: str) -> bool:
    sentences = split_sentences(text)
    first = sentences[0].strip().lower() if sentences else text.strip().lower()
    return any(re.search(pat, first, re.IGNORECASE) for pat in FORMULAIC_OPENERS)


def s4b_hits(text: str) -> dict:
    """
    Count consulting-register cluster hits — the true flagging fingerprint.
    Returns {chain, nominal, triplet, total}. S4b-positive when total >= 2.
    """
    chain = sum(len(r.findall(text)) for r in S4B_CHAIN_RE)
    nominal = sum(len(r.findall(text)) for r in S4B_NOMINAL_RE)
    triplet = len(S4B_TRIPLET_PATTERN.findall(text))
    return {
        "chain": chain,
        "nominal": nominal,
        "triplet": triplet,
        "total": chain + nominal + (triplet * 2),  # triplets weighted double
    }


def noise_hits(text: str) -> int:
    """Rough grammatical-noise heuristic — count matches across all patterns."""
    return sum(len(r.findall(text)) for r in NOISE_RE)


def compute_s_struct(flags: list, metrics: dict) -> float:
    """
    v0.5: Additive S_struct from detected signals, capped at 1.0.
    Each signal contributes independently — no S4b hard gate.
    S4b still carries the highest weight (up to 0.90 if all three patterns fire).
    """
    s = 0.0
    if metrics.get("s2_correlate"):         s += 0.15   # S2 uniform burstiness
    if metrics.get("synthesis_closer"):     s += 0.175  # S3 scaffold shape (closer proxy)
    if "S4a" in flags:                      s += 0.10   # S4a generic LLM vocab
    if metrics.get("s4b_chain", 0) > 0:    s += 0.25   # S4b Pattern 1 — abstract-noun chains
    if metrics.get("s4b_nominal", 0) > 0:  s += 0.30   # S4b Pattern 2 — nominalised outcomes
    if metrics.get("s4b_triplet", 0) > 0:  s += 0.35   # S4b Pattern 3 — abstract-noun triplets
    if metrics.get("triplets", 0) >= 2:    s += 0.10   # S5 rule-of-three / smooth connectives
    if metrics.get("formulaic_opener"):     s += 0.175  # S6 meta-opener / meta-closer
    if "S8" in flags:                       s += 0.10   # S8 register uniformity / low vocab diversity
    # S7 (citation-anchored triplets) — cannot reliably detect with ruler; Claude applies it
    return min(s, 1.0)


def compute_p_polish(noise_hits: int) -> float:
    """
    v0.5 grammatical-noise moderator as multiplicative factor.
    Replaces the step-down "noisy" boolean from v0.4.
    """
    if noise_hits == 0:    return 1.0   # clean prose
    elif noise_hits <= 2:  return 0.9   # light typos / one agreement slip
    elif noise_hits <= 4:  return 0.8   # moderate — two or three slips
    elif noise_hits <= 7:  return 0.7   # heavy — multiple typos + broken clause
    else:                  return 0.5   # recurring — typo-dense throughout


def compute_fp_factor(text: str) -> float:
    """
    v0.5 first-person / voice-register factor.
    Sustained first/second-person address or contraction use reduces AI_para.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    total = len(words) or 1
    fp_words = sum(1 for w in words if w in {"we", "our", "you", "your"})
    contractions = len(re.findall(
        r"\b(it's|don't|can't|won't|we're|we've|they're|you're|isn't|"
        r"wasn't|weren't|haven't|hasn't|hadn't|doesn't|didn't|i'm|i've|i'd|i'll)\b",
        text, re.IGNORECASE,
    ))
    fp_density = fp_words / total
    if fp_density >= 0.04:          return 0.8   # sustained first/second-person
    elif contractions >= 2:         return 0.9   # conversational register
    elif fp_words > 0 or contractions > 0: return 0.95  # light voice markers
    return 1.0                                   # third-person formal — no modifier


def ruler_pass(paragraph: str) -> dict:
    sentences = split_sentences(paragraph)
    flags = []
    metrics = {}

    # S2 — sentence length uniformity (correlate only — does not flag alone)
    if len(sentences) >= MIN_SENTENCES:
        stdev = sentence_length_stdev(sentences)
        metrics["sent_stdev"] = round(stdev, 1)
        s2_hit = stdev < STDEV_FLAG_BELOW
    else:
        metrics["sent_stdev"] = "n/a"
        s2_hit = False
    metrics["s2_correlate"] = s2_hit

    # S4a — generic LLM vocabulary density (hedge-based heuristic)
    hd = hedge_density(paragraph)
    metrics["hedge_pct"] = f"{hd:.0%}"
    if hd > HEDGE_FLAG_ABOVE:
        flags.append("S4a")

    # S4b — consulting-register cluster (the true fingerprint)
    s4b = s4b_hits(paragraph)
    metrics["s4b_chain"] = s4b["chain"]
    metrics["s4b_nominal"] = s4b["nominal"]
    metrics["s4b_triplet"] = s4b["triplet"]
    metrics["s4b_total"] = s4b["total"]
    if s4b["total"] >= 2:
        flags.append("S4b")

    # S6 — formulaic opener (correlate only — moderated by grammatical noise)
    opener = has_formulaic_opener(paragraph)
    metrics["formulaic_opener"] = opener
    if opener:
        flags.append("S6")

    # S8 — vocabulary diversity
    ttr = type_token_ratio(paragraph)
    metrics["ttr"] = round(ttr, 2)
    if ttr < TTR_FLAG_BELOW:
        flags.append("S8")

    # S3 partial — synthesis closer in last sentence (correlate only)
    last_sentence = sentences[-1] if sentences else paragraph
    if SYNTHESIS_CLOSER.search(last_sentence):
        flags.append("S3")
        metrics["synthesis_closer"] = True
    else:
        metrics["synthesis_closer"] = False

    # S5 — rule-of-three triplet density (flag if 2+ triplets in paragraph)
    triplet_count = len(TRIPLET.findall(paragraph))
    metrics["triplets"] = triplet_count
    if triplet_count >= 2:
        flags.append("S5")

    # Promote S2 to a flag only when S4b co-occurs (per calibration rule)
    if s2_hit and "S4b" in flags:
        flags.append("S2")

    # Grammatical-noise moderator count
    noise = noise_hits(paragraph)
    metrics["noise_hits"] = noise
    metrics["noisy"] = noise >= 3  # kept for legacy display; p_polish is the v0.5 factor

    # ── v0.5 continuous score ────────────────────────────────────────────────
    s_struct  = compute_s_struct(flags, metrics)
    p_polish  = compute_p_polish(noise)
    fp_factor = compute_fp_factor(paragraph)
    ai_para   = round(s_struct * p_polish * fp_factor, 3)
    metrics["s_struct"]  = round(s_struct, 3)
    metrics["p_polish"]  = p_polish
    metrics["fp_factor"] = fp_factor
    metrics["ai_para"]   = ai_para

    return {"flags": flags, "metrics": metrics}


# ── packet assembly ───────────────────────────────────────────────────────────

def load_file(name: str, script_dir: Path) -> str:
    path = script_dir / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"[{name} not found — place it alongside check.py]\n"


def severity(flags: list, metrics: dict = None) -> str:
    """
    v0.5: Convert continuous ai_para score to display band for the packet.
    Thresholds: HIGH ≥0.55 · MEDIUM ≥0.30 · LOW ≥0.10 · CLEAR <0.10

    Falls back to flag-count heuristic if ai_para is not yet computed
    (e.g. when called before ruler_pass has populated metrics).
    """
    if metrics and "ai_para" in metrics:
        ai = metrics["ai_para"]
        if ai >= 0.55:    return "HIGH"
        elif ai >= 0.30:  return "MEDIUM"
        elif ai >= 0.10:  return "LOW"
        else:             return "CLEAR"

    # ── legacy fallback (pre-v0.5 call sites) ───────────────────────────────
    if not flags:
        return "CLEAR"
    has_s4b = "S4b" in flags
    correlate_flags = [f for f in flags if f in {"S2", "S3", "S6", "S5", "S7", "S8"}]
    strong_flags    = [f for f in flags if f in {"S1", "S4a", "S4b"}]
    if has_s4b:
        n = len(flags)
        base = "HIGH" if n >= 4 else "MEDIUM" if n >= 2 else "LOW"
    else:
        effective = len(strong_flags) + len(correlate_flags) / 2
        base = "MEDIUM" if effective >= 2.5 else "LOW" if effective >= 1.0 else "CLEAR"
    if metrics and metrics.get("noisy"):
        base = {"HIGH": "MEDIUM", "MEDIUM": "LOW", "LOW": "CLEAR", "CLEAR": "CLEAR"}[base]
    return base


def estimate_ai_score(paragraphs: list, results: list) -> int:
    """
    v0.5 word-weighted continuous score.
    Score = Σ(ai_para × word_count) / Σ(word_count) across all qualifying paragraphs.
    Qualifying threshold: ≥20 words (matches MIN_PARA_WORDS — full document coverage,
    no fixed-paragraph ceiling).

    Calibration (v0.5 ruler-only — Claude's full 8-signal pass is more accurate):
        Huewrite R3   ~20% ruler  vs  <20% actual  (Δ ~0)
        G8 AI2        ~65% ruler  vs   69% actual  (Δ −4)
        G7 AI1       ~45% ruler  vs   47% actual  (Δ ~0)
    """
    MIN_SCORE_WDS = 20  # matches MIN_PARA_WORDS — include all qualifying paragraphs
    total_words   = 0
    flagged_words = 0.0
    for para, result in zip(paragraphs, results):
        wc = len(para.split())
        if wc < MIN_SCORE_WDS:
            continue
        ai_para = result["metrics"].get("ai_para", 0.0)
        total_words   += wc
        flagged_words += wc * ai_para
    if total_words == 0:
        return 0
    return round(flagged_words / total_words * 100)


def build_packet(paragraphs: list, results: list, signals_ref: str, fewshots_ref: str, doc_name: str) -> str:
    lines = []

    lines.append(f"# Turnitin AI Analysis Packet — {doc_name}\n\n")

    lines.append("## Instructions for Claude\n\n")
    lines.append(
        "You are a Turnitin AI-detection expert trained on a live research playbook "
        "covering 8 corpora, 13 reports, and ~103,150 words from IMU BCP2485 proposals.\n\n"
        "This packet contains:\n"
        "1. **Signal reference (S1–S8, with S4 split into S4a/S4b)** and **Technique reference (T1–T9)**\n"
        "2. **Before/after examples** from the real corpus\n"
        "3. **The document under review**, split into numbered paragraphs with a ruler-pass "
        "fingerprint. Each paragraph shows its v0.5 continuous score: "
        "`ai_para = s_struct × p_polish × fp_factor`\n\n"
        "### Your task\n\n"
        "For each paragraph:\n"
        "- Review the ruler fingerprint AND the paragraph text\n"
        "- Identify ALL applicable signals (including S1, S3(full), S7 which the ruler cannot fully measure)\n"
        "- **Specifically assess S4b (consulting-register cluster) by reading** — the ruler's "
        "pattern-matching catches obvious forms but will miss paraphrased variants. Look for the "
        "three S4b patterns: abstract-noun chains, nominalised outcomes, abstract-noun triplets. "
        "Diagnostic: strip every concrete noun from a candidate sentence — if it still parses meaningfully, "
        "the cluster is present.\n"
        "- Compute your own ai_para estimate (see v0.5 rules below) and compare to the ruler's.\n"
        "- For every paragraph with ai_para ≥ 0.30 (MEDIUM or above), write a **concrete rewrite suggestion** "
        "naming the specific T-technique(s) applied. Prioritise T5b when S4b is present.\n\n"
        "### Scoring rules (v0.5 — mandatory)\n\n"
        "**Formula:** `AI_para = S_struct × P_polish × first_person_factor`\n\n"
        "**S_struct (additive, capped at 1.0):**\n"
        "- S2 uniform burstiness: +0.15\n"
        "- S3 scaffold shape (synthesis closer / full topic→support→synthesis): +0.15 to +0.20\n"
        "- S4a generic LLM vocab: +0.10\n"
        "- S4b Pattern 1 abstract-noun chains: +0.25\n"
        "- S4b Pattern 2 nominalised outcomes: +0.30\n"
        "- S4b Pattern 3 abstract-noun triplets: +0.35\n"
        "- S5 rule-of-three / smooth connectives (≥2 triplets): +0.10\n"
        "- S6 formulaic meta-opener / closer: +0.15 to +0.20\n"
        "- S7 citation-anchored triplets: +0.10\n"
        "- S8 abstract-descriptor density: +0.10\n\n"
        "**P_polish (multiplicative):** clean=1.0 · light typos=0.9 · moderate=0.8 · heavy=0.7 · recurring=0.5\n\n"
        "**first_person_factor:** sustained we/our/you/your ≥4% of words=0.8 · "
        "≥2 contractions=0.9 · light markers=0.95 · formal third-person=1.0\n\n"
        "**Display bands:** HIGH ≥0.55 · MEDIUM 0.30–0.54 · LOW 0.10–0.29 · CLEAR <0.10\n\n"
        "**Key calibration notes (v0.5):**\n"
        "- S4b still dominates but is no longer a hard gate — a paragraph with S2+S3+S6+S5 "
        "but no S4b can reach MEDIUM on its own (~0.60 uncapped, ~0.50–0.60 × p_polish). "
        "This closes the Huewrite/Dwayne R2 under-prediction gaps from v0.4.\n"
        "- First-person / conversational prose genuinely suppresses Turnitin — confirmed "
        "in Huewrite R3 where conversational paragraphs carrying structural signals still cleared.\n"
        "- Open calibration issue: telehealth/mHealth scaffolded prose in market-analysis / "
        "risk sections may be under-scored by S4b Pattern weighting — Turnitin flags these "
        "more aggressively than S4b regex detects. Flag them manually if you see the pattern.\n\n"
        "### Calibration patterns to watch for\n\n"
        "Four patterns have been validated against Turnitin post-hoc and require special handling "
        "— they are the most common sources of severity miscalibration:\n\n"
        "- **S4b-gating (the big one).** The consulting-register cluster is THE flagging "
        "fingerprint. A paragraph with clean topic-sentence shape, uniform sentence length, and "
        "a meta-opener that nevertheless lacks abstract-noun chains / nominalised outcomes / "
        "abstract triplets will usually clear. A noisy, informal paragraph that carries the cluster "
        "will usually flag. Always check for S4b before assigning HIGH. "
        "(Shawn BP2: four fully-scaffolded paragraphs — Introduction, Proposed Solution at 468w, "
        "Executive Summary, Conclusion — all cleared because S4b was absent and grammatical noise "
        "was present. Pre-submission prediction had them all HIGH; Turnitin cleared all four.)\n"
        "- **Sub-sectioned paragraph → lower severity.** If a paragraph splits into ≥3 bolded or "
        "numbered sub-labels (Stage 1, Stage 2, Phase A…) each followed by **bullet fragments**, "
        "treat the scaffold as broken — fragments under labels carry no S2/S3 load. "
        "(Dataset H §6.1 Patient Journey: predicted MEDIUM, Turnitin cleared it.)\n"
        "- **Phased-prose section → MEDIUM floor.** The inverse: ≥3 phase/risk/stage enumerators each "
        "followed by **full prose paragraphs** (not fragments). Floor severity at MEDIUM regardless "
        "of per-paragraph S6 absence — per-phase prose carries S2 rhythm and S4b vocab even when "
        "surface openers look clean, and Turnitin scores the document-level enumeration scaffold. "
        "(G9 AI1 Operational Plan and Risk Analysis: predicted LOW, Turnitin flagged heavily, "
        "−13pt overall gap.)\n"
        "- **Meta-opener does not absorb body risk.** When a meta-opener sits at the top of a "
        "paragraph that continues into a substantive S4b-heavy body, score the **opener and the "
        "body as independent risks**. Turnitin often flags the substantive body regardless of what "
        "came before. (Dataset H ¶3 T&CM regulatory: the meta-opener was blamed; Turnitin actually "
        "flagged the substantive body that followed.)\n\n"
        "- **S4b-dense list override for S1.** Bulleted fragments normally clear (S1 protection). "
        "But a list of 10+ items each carrying nominalised outcomes or abstract triplets will flag "
        "despite bullet format. (Shawn BP2 Risk Mitigation list: ~15 items flagged.)\n\n"
        "### Writing style for analysis text\n\n"
        "Write all analysis in plain, direct English. Avoid jargon. Follow these rules:\n"
        "- Say **what the problem is** in one plain sentence, then **why it matters** in one sentence.\n"
        "- Name the specific word or phrase from the text that triggers the signal — quote it.\n"
        "- Keep each analysis note under 3 sentences total.\n"
        "- Bad example: 'Classic LLM scaffold: thesis sentence → supporting claims → concluding sentence. "
        "Heavy S4 vocabulary (comprehensive, standardized). S6 meta-commentary: three separate meta-sentences.'\n"
        "- Good example: 'This paragraph opens with a topic sentence, explains, then wraps up with a summary "
        "closer — the classic AI shape. Cut the opener or closer. The words \"comprehensive\" and "
        "\"standardized\" are AI favourites; swap them for plainer alternatives.'\n\n"
        "For rewrite suggestions: show a short concrete example of what the improved text would look like. "
        "Don't just say 'apply T2 burstiness' — show one sentence split into two shorter ones.\n\n"
        "### Punctuation rules for rewrites (strictly enforced)\n\n"
        "- **Never use em dashes (— or –)** in rewritten text. Em dashes are a strong AI "
        "signal and will re-flag the passage. Use a period, comma, or restructure the sentence instead.\n"
        "- Avoid ellipses (…) in prose unless quoting source text.\n"
        "- Prefer short sentences over parenthetical asides.\n\n"
        "### Output format\n\n"
        "Return a **single self-contained HTML artifact**. Use this exact CSS in a `<style>` block:\n\n"
        "```css\n"
        "body { font-family: system-ui, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 24px; color: #222; }\n"
        "h1 { font-size: 20px; margin-bottom: 4px; }\n"
        ".subtitle { color: #666; font-size: 13px; margin-bottom: 32px; }\n"
        ".summary-table { width: 100%; border-collapse: collapse; margin-bottom: 32px; font-size: 13px; }\n"
        ".summary-table th { background: #f5f5f5; text-align: left; padding: 8px 12px; border-bottom: 2px solid #ddd; }\n"
        ".summary-table td { padding: 7px 12px; border-bottom: 1px solid #eee; vertical-align: top; }\n"
        ".para-block { border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px 18px; margin: 16px 0; }\n"
        ".para-block.high { border-left: 4px solid #c0392b; }\n"
        ".para-block.medium { border-left: 4px solid #b7950b; }\n"
        ".para-block.low { border-left: 4px solid #aaa; }\n"
        ".para-block.clear { border-left: 4px solid #1e8449; opacity: 0.7; }\n"
        ".para-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }\n"
        ".para-num { font-weight: 700; font-size: 13px; color: #555; min-width: 28px; }\n"
        ".sev-badge { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }\n"
        ".sev-badge.high { background: #fde; color: #c0392b; }\n"
        ".sev-badge.medium { background: #fef9e7; color: #b7950b; }\n"
        ".sev-badge.low { background: #f5f5f5; color: #666; }\n"
        ".sev-badge.clear { background: #eafaf1; color: #1e8449; }\n"
        ".signal-chips { display: flex; flex-wrap: wrap; gap: 4px; }\n"
        ".chip { font-size: 11px; padding: 2px 7px; border-radius: 4px; border: 1px solid #c0392b; "
        "background: #fef0f0; color: #c0392b; white-space: nowrap; }\n"
        ".para-text { font-size: 13px; line-height: 1.6; color: #333; margin: 10px 0; }\n"
        ".analysis { font-size: 13px; color: #444; background: #fafafa; border-left: 3px solid #ddd; "
        "padding: 8px 12px; margin: 8px 0; border-radius: 0 4px 4px 0; }\n"
        ".rewrite-box { font-size: 13px; background: #f0f8f0; border-left: 3px solid #1e8449; "
        "padding: 10px 14px; margin: 8px 0; border-radius: 0 4px 4px 0; }\n"
        ".rewrite-box strong { display: block; margin-bottom: 4px; color: #1e8449; }\n"
        ".legend { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 12px; color: #555; "
        "background: #f9f9f9; border: 1px solid #eee; border-radius: 6px; padding: 10px 14px; margin-bottom: 24px; }\n"
        ".legend strong { margin-right: 4px; }\n"
        ".legend .chip { font-size: 11px; }\n"
        ".top-actions { background: #fffbf0; border: 1px solid #f0d080; border-radius: 8px; "
        "padding: 16px 18px; margin-top: 32px; }\n"
        ".top-actions h2 { font-size: 15px; margin: 0 0 10px; }\n"
        ".top-actions ol { margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8; }\n"
        ".print-btn { display: inline-block; margin: 16px 0 24px; padding: 8px 18px; "
        "background: #2c3e50; color: #fff; border: none; border-radius: 6px; "
        "font-size: 13px; cursor: pointer; }\n"
        ".print-btn:hover { background: #1a252f; }\n"
        "@media print {\n"
        "  @page { margin: 15mm; size: A4 portrait; }\n"
        "  html, body { width: 100%; max-width: 100%; margin: 0; padding: 0; "
        "font-size: 10.5pt; color: #000; background: #fff; "
        "-webkit-print-color-adjust: exact; print-color-adjust: exact; }\n"
        "  .print-btn { display: none; }\n"
        "  .para-block { break-inside: avoid; page-break-inside: avoid; "
        "border: 1px solid #ccc !important; margin: 8px 0; padding: 8px 10px; "
        "border-radius: 0 !important; box-shadow: none !important; }\n"
        "  .para-block.clear { display: none; }\n"
        "  .rewrite-box, .analysis { break-inside: avoid; page-break-inside: avoid; }\n"
        "  .summary-table tr { break-inside: avoid; page-break-inside: avoid; }\n"
        "  .top-actions, .legend { break-inside: avoid; page-break-inside: avoid; }\n"
        "  h1, h2 { break-after: avoid; page-break-after: avoid; }\n"
        "}\n"
        "```\n\n"
        "**Important:** include this print button just below the `<h1>` title, before the score block:\n"
        "```html\n"
        "<button class=\"print-btn\" onclick=\"window.print()\">🖨️ Save as PDF</button>\n"
        "```\n"
        "This is the only reliable way to get proper A4 pagination — "
        "right-click Save and the artifact download button both capture the screen layout. "
        "Instruct the user in a short note next to the button: "
        "\"Click to open the print dialog, then choose Save as PDF.\"\n\n"
        "The HTML structure should be:\n"
        "1. `<h1>` title + print button + `.subtitle` with document name and counts\n"
        "2. **Estimated AI score block** — calculate a word-weighted score using your full signal "
        "assessment (all 8 signals, v0.5 continuous model). "
        "Formula: Σ(ai_para × word_count) / Σ(word_count) across all qualifying paragraphs (≥20 words). "
        "Use your own per-paragraph ai_para estimates, not just the ruler's — the ruler misses "
        "paraphrased S4b forms and can't assess S1/S3(full)/S7. "
        "**Exclude from the denominator:** cover page, Turnitin boilerplate/disclaimer text, "
        "headings-only lines, and reference list entries. "
        "Show the result as a large percentage with a coloured border "
        "(red ≥50%, amber 25–49%, green <25%) and a subtitle: "
        "'v0.5 continuous model · ±10 pts vs Turnitin'. "
        "Below it show a thin progress bar in the same colour at that percentage width.\n"
        "3. Signal legend using `.legend` class — one `.chip` per signal with its short label\n"
        "3. Summary table (`.summary-table`) with columns: ¶ · Severity · Signals · One-line note\n"
        "4. Each paragraph as a `.para-block` with appropriate severity class. Inside: `.para-header` "
        "(containing `.para-num`, `.sev-badge`, `.signal-chips`), `.para-text`, `.analysis` note, "
        "and `.rewrite-box` for HIGH/MEDIUM paragraphs only\n"
        "5. `.top-actions` section with a numbered list of the 3 highest-priority edits for this document\n\n"
        "---\n\n"
    )

    lines.append("## Signal & Technique Reference\n\n")
    lines.append(signals_ref)
    lines.append("\n\n---\n\n")

    lines.append("## Before/After Examples\n\n")
    lines.append(fewshots_ref)
    lines.append("\n\n---\n\n")

    lines.append("## Document Under Review\n\n")

    flagged_count = 0
    high_count = 0
    for i, (para, result) in enumerate(zip(paragraphs, results), 1):
        flags = result["flags"]
        metrics = result["metrics"]
        sev = severity(flags, metrics)

        if flags:
            flagged_count += 1
        if sev == "HIGH":
            high_count += 1

        flag_str = " · ".join(flags) if flags else "—"
        stdev_str = str(metrics.get("sent_stdev", "n/a"))
        metric_str = (
            f"ai_para:{metrics.get('ai_para','?')} "
            f"[s_struct:{metrics.get('s_struct','?')} × "
            f"p_polish:{metrics.get('p_polish','?')} × "
            f"fp:{metrics.get('fp_factor','?')}] · "
            f"sent_stdev:{stdev_str} · "
            f"hedges:{metrics['hedge_pct']} · "
            f"ttr:{metrics['ttr']} · "
            f"s4b[chain:{metrics['s4b_chain']} nom:{metrics['s4b_nominal']} "
            f"trip:{metrics['s4b_triplet']} total:{metrics['s4b_total']}] · "
            f"noise:{metrics['noise_hits']}"
        )
        if metrics.get("formulaic_opener"):
            metric_str += " · FORMULAIC_OPENER"
        if metrics.get("noisy"):
            metric_str += " · GRAMMATICAL_NOISE"
        if metrics.get("s4b_total", 0) >= 2:
            metric_str += " · S4B_POSITIVE"

        lines.append(f"### ¶{i} · Severity: {sev} · Ruler flags: [{flag_str}]\n")
        lines.append(f"*Ruler metrics: {metric_str}*\n\n")
        lines.append(f"{para}\n\n")

    lines.append("---\n\n")
    lines.append(
        f"*Ruler-pass summary: **{flagged_count}/{len(paragraphs)}** paragraphs tripped "
        f"at least one measurable signal ({high_count} HIGH). "
        f"Signals S1, S3, S5, and S7 require LLM judgment — look for them in the text above.*\n"
    )

    return "".join(lines)


# ── rewrite mode support ─────────────────────────────────────────────────────

def normalise_for_match(text: str) -> str:
    """Collapse whitespace and lowercase for substring/token matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def match_flagged_passages(paragraphs: list, flagged_passages: list) -> dict:
    """
    Map each Turnitin-flagged passage to the index of the paragraph that contains it.
    Returns {paragraph_idx: [passages…]}; unmatched passages live under key -1.

    Strategy:
      1. Exact substring match on normalised (lowercased, whitespace-collapsed) text.
      2. Fallback: token-overlap ≥ 70% of passage tokens present in paragraph.

    Designed for Turnitin cyan highlights, which preserve the exact source text but
    may contain OCR whitespace artefacts or cross paragraph boundaries.
    """
    match_map = {}
    norm_paras = [normalise_for_match(p) for p in paragraphs]

    for passage in flagged_passages:
        norm_passage = normalise_for_match(passage)
        if len(norm_passage) < 10:
            continue  # trivial fragment — not worth matching

        hit = None

        # Pass 1: exact substring
        for idx, norm_para in enumerate(norm_paras):
            if norm_passage in norm_para:
                hit = idx
                break

        # Pass 2: token-overlap fallback
        if hit is None:
            passage_tokens = set(re.findall(r"\b\w+\b", norm_passage))
            if len(passage_tokens) >= 4:
                best_idx, best_overlap = None, 0.0
                for idx, norm_para in enumerate(norm_paras):
                    para_tokens = set(re.findall(r"\b\w+\b", norm_para))
                    overlap = len(passage_tokens & para_tokens) / len(passage_tokens)
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_idx = idx
                if best_overlap >= 0.70:
                    hit = best_idx

        key = hit if hit is not None else -1
        match_map.setdefault(key, []).append(passage)

    return match_map


def build_rewrite_packet(
    paragraphs: list,
    flagged_map: dict,
    signals_ref: str,
    fewshots_ref: str,
    doc_name: str,
) -> str:
    """
    Build a rewrite-mode packet for Claude.

    Each paragraph is labelled [FLAGGED] or [CLEAR] based on whether the user-supplied
    Turnitin-highlighted passages matched it. Claude's task is targeted rewriting —
    no severity prediction, no AI score calculation — because the ground truth is known.
    """
    lines = []
    lines.append(f"# Turnitin AI Rewrite Packet — {doc_name}\n\n")

    lines.append("## Instructions for Claude\n\n")
    lines.append(
        "You are a Turnitin AI-detection expert trained on a live research playbook "
        "covering 8 corpora, 13 reports, and ~103,150 words from IMU BCP2485 proposals.\n\n"
        "This packet contains a document that has **already been scored by Turnitin**. "
        "Each paragraph is labelled [FLAGGED] or [CLEAR] based on whether Turnitin's AI "
        "detector cyan-highlighted any of its text. Your task is **targeted rewriting** — "
        "no prediction, no severity classification, no AI score calculation. The ground "
        "truth is known; produce the fixes.\n\n"
        "### Your task\n\n"
        "For each [FLAGGED] paragraph:\n"
        "1. Identify which of the 8 signals (S1–S8, with S4 split into S4a/S4b) are active, "
        "quoting the exact words or phrases that trigger each signal\n"
        "2. **Diagnose S4b first.** The consulting-register cluster (abstract-noun chains, "
        "nominalised outcomes, abstract-noun triplets) is the load-bearing signal. If it is "
        "present, T5b (cluster removal) is mandatory and highest-priority.\n"
        "3. Produce a concrete **before/after rewrite** applying the appropriate T1–T8 techniques\n"
        "4. Explain in one sentence what the rewrite changes and why it removes the signal\n\n"
        "For [CLEAR] paragraphs: do NOT rewrite. Include them as a single row in the summary "
        "table only — no detail block.\n\n"
        "### Calibration patterns to watch for\n\n"
        "Four patterns have been validated against Turnitin post-hoc — apply them when "
        "choosing techniques for flagged paragraphs:\n\n"
        "- **S4b is the fingerprint.** When S4b is present → T5b (strip the cluster) is the "
        "highest-leverage fix; T2/T3/T6 are amplifiers. When S4b is absent but the paragraph "
        "is still flagged → the flag comes from document-wide signature (S7), list-density "
        "overflow (S1 override with 10+ cluster-carrying bullets), or residual S4a/S5 vocab. "
        "Do not reach for T5b in that case; it has nothing to strip.\n"
        "- **Sub-sectioned paragraph** (≥3 bolded or numbered sub-labels, each with bullet "
        "fragments under it): scaffold is already broken — don't apply T3. Look for S4a/S4b/S5 instead.\n"
        "- **Phased-prose section** (≥3 phase/risk/stage enumerators, each followed by full "
        "prose paragraphs): apply T1 (convert each phase to a table row) + T5b (strip the "
        "cluster). Under-weighted by surface inspection — Turnitin scores the document-level "
        "enumeration even when per-paragraph openers look clean.\n"
        "- **Meta-opener + substantive body**: rewrite BOTH independently. The opener is not "
        "the whole risk — Turnitin often flags the substantive body on its own S2/S4b "
        "pattern regardless of what came before it.\n\n"
        "### Writing style for rewrites and analysis text\n\n"
        "Plain, direct English. Avoid jargon. Follow these rules:\n"
        "- Quote the exact word or phrase that triggers each signal\n"
        "- Keep each analysis note under 3 sentences\n"
        "- Show concrete rewrite examples, not just technique names\n"
        "- Good: 'The opener \"This section analyses…\" is meta-commentary (S6). Cut it — "
        "the heading already signposts.'\n"
        "- Bad: 'S6 meta-commentary present; apply T6.'\n\n"
        "### Punctuation rules for rewrites (strictly enforced)\n\n"
        "- **Never use em dashes (— or –)** in rewritten text. Em dashes are a strong AI "
        "signal and will re-flag the passage. Use a period, comma, or restructure the sentence instead.\n"
        "- Avoid ellipses (…) in prose unless quoting source text.\n"
        "- Prefer short sentences over parenthetical asides.\n\n"
        "### Output format\n\n"
        "Return a **single self-contained HTML artifact**. Use this exact CSS in a `<style>` block:\n\n"
        "```css\n"
        "body { font-family: system-ui, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 24px; color: #222; }\n"
        "h1 { font-size: 20px; margin-bottom: 4px; }\n"
        ".subtitle { color: #666; font-size: 13px; margin-bottom: 32px; }\n"
        ".summary-table { width: 100%; border-collapse: collapse; margin-bottom: 32px; font-size: 13px; }\n"
        ".summary-table th { background: #f5f5f5; text-align: left; padding: 8px 12px; border-bottom: 2px solid #ddd; }\n"
        ".summary-table td { padding: 7px 12px; border-bottom: 1px solid #eee; vertical-align: top; }\n"
        ".para-block { border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px 18px; margin: 16px 0; }\n"
        ".para-block.flagged { border-left: 4px solid #c0392b; }\n"
        ".para-block.clear { border-left: 4px solid #1e8449; opacity: 0.6; }\n"
        ".para-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }\n"
        ".para-num { font-weight: 700; font-size: 13px; color: #555; min-width: 28px; }\n"
        ".sev-badge { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }\n"
        ".sev-badge.flagged { background: #fde; color: #c0392b; }\n"
        ".sev-badge.clear { background: #eafaf1; color: #1e8449; }\n"
        ".signal-chips { display: flex; flex-wrap: wrap; gap: 4px; }\n"
        ".chip { font-size: 11px; padding: 2px 7px; border-radius: 4px; border: 1px solid #c0392b; "
        "background: #fef0f0; color: #c0392b; white-space: nowrap; }\n"
        ".para-text { font-size: 13px; line-height: 1.6; color: #333; margin: 10px 0; white-space: pre-wrap; }\n"
        ".analysis { font-size: 13px; color: #444; background: #fafafa; border-left: 3px solid #ddd; "
        "padding: 8px 12px; margin: 8px 0; border-radius: 0 4px 4px 0; }\n"
        ".rewrite-box { font-size: 13px; background: #f0f8f0; border-left: 3px solid #1e8449; "
        "padding: 10px 14px; margin: 8px 0; border-radius: 0 4px 4px 0; }\n"
        ".rewrite-box strong { display: block; margin-bottom: 4px; color: #1e8449; }\n"
        ".legend { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 12px; color: #555; "
        "background: #f9f9f9; border: 1px solid #eee; border-radius: 6px; padding: 10px 14px; margin-bottom: 24px; }\n"
        ".top-actions { background: #fffbf0; border: 1px solid #f0d080; border-radius: 8px; "
        "padding: 16px 18px; margin-top: 32px; }\n"
        ".top-actions h2 { font-size: 15px; margin: 0 0 10px; }\n"
        ".top-actions ol { margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8; }\n"
        ".print-btn { display: inline-block; margin: 16px 0 24px; padding: 8px 18px; "
        "background: #2c3e50; color: #fff; border: none; border-radius: 6px; "
        "font-size: 13px; cursor: pointer; }\n"
        ".print-btn:hover { background: #1a252f; }\n"
        "@media print {\n"
        "  @page { margin: 15mm; size: A4 portrait; }\n"
        "  html, body { width: 100%; max-width: 100%; margin: 0; padding: 0; "
        "font-size: 10.5pt; color: #000; background: #fff; "
        "-webkit-print-color-adjust: exact; print-color-adjust: exact; }\n"
        "  .print-btn { display: none; }\n"
        "  .para-block { break-inside: avoid; page-break-inside: avoid; "
        "border: 1px solid #ccc !important; margin: 8px 0; padding: 8px 10px; "
        "border-radius: 0 !important; box-shadow: none !important; }\n"
        "  .para-block.clear { display: none; }\n"
        "  .rewrite-box, .analysis { break-inside: avoid; page-break-inside: avoid; }\n"
        "  .summary-table tr { break-inside: avoid; page-break-inside: avoid; }\n"
        "  .top-actions, .legend { break-inside: avoid; page-break-inside: avoid; }\n"
        "  h1, h2 { break-after: avoid; page-break-after: avoid; }\n"
        "}\n"
        "```\n\n"
        "**Include this print button just below the `<h1>` title:**\n"
        "```html\n"
        "<button class=\"print-btn\" onclick=\"window.print()\">🖨️ Save as PDF</button>\n"
        "```\n\n"
        "The HTML structure:\n"
        "1. `<h1>` title + print button + `.subtitle` showing the document name and "
        "'X of Y paragraphs flagged by Turnitin'\n"
        "2. Signal legend (`.legend`) listing which S1–S8 signals appear in this document, "
        "with one `.chip` per signal\n"
        "3. Summary table (`.summary-table`) with columns: ¶ · Status · Signals active · Techniques applied\n"
        "4. For each [FLAGGED] paragraph, a `.para-block.flagged` containing:\n"
        "   - `.para-header` with `.para-num`, `.sev-badge.flagged`, and `.signal-chips`\n"
        "   - `.para-text` — the original paragraph\n"
        "   - `.analysis` — bullet list of triggering signals with the exact quoted phrase from the text\n"
        "   - `.rewrite-box` — the rewritten paragraph, preceded by a `<strong>` 'Rewrite:' label, "
        "     followed by a one-sentence rationale\n"
        "5. For [CLEAR] paragraphs: one row in the summary table, no detail block\n"
        "6. `.top-actions` with a numbered list of the 3 highest-leverage edits for this document "
        "(e.g. 'Cut all N meta-openers — accounts for Z% of flagged paragraphs')\n\n"
        "**Do NOT compute an AI score** — Turnitin has already provided it. Focus exclusively on fixes.\n\n"
        "---\n\n"
    )

    lines.append("## Signal & Technique Reference\n\n")
    lines.append(signals_ref)
    lines.append("\n\n---\n\n")

    lines.append("## Before/After Examples\n\n")
    lines.append(fewshots_ref)
    lines.append("\n\n---\n\n")

    lines.append("## Document Under Review — Turnitin-Scored\n\n")

    matched_para_idxs = {idx for idx in flagged_map if idx != -1}
    unmatched = flagged_map.get(-1, [])

    for i, para in enumerate(paragraphs):
        passages = flagged_map.get(i, [])
        status = "FLAGGED" if passages else "CLEAR"
        lines.append(f"### ¶{i+1} · Status: {status}\n")
        if passages:
            lines.append(f"*Turnitin flagged {len(passages)} passage(s) in this paragraph:*\n\n")
            for p in passages:
                quoted = p.strip().replace("\n", " ")
                if len(quoted) > 400:
                    quoted = quoted[:400] + "…"
                lines.append(f"> {quoted}\n\n")
        lines.append(f"{para}\n\n")

    lines.append("---\n\n")
    lines.append(
        f"*Turnitin summary: **{len(matched_para_idxs)}/{len(paragraphs)}** paragraphs contain "
        f"at least one cyan-highlighted passage. Rewrite those; leave CLEAR paragraphs alone.*\n"
    )

    if unmatched:
        lines.append("\n## Unmatched passages\n\n")
        lines.append(
            f"*{len(unmatched)} flagged passage(s) could not be matched to any paragraph in the "
            f"source document. Likely origins: tables, figures, captions, headings, or text that "
            f"crosses paragraph boundaries. Use them as additional rewrite context:*\n\n"
        )
        for p in unmatched:
            quoted = p.strip().replace("\n", " ")
            if len(quoted) > 400:
                quoted = quoted[:400] + "…"
            lines.append(f"> {quoted}\n\n")

    return "".join(lines)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python check.py <document.docx|document.pdf>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        sys.exit(f"File not found: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".docx":
        text = read_docx(input_path)
    elif suffix == ".pdf":
        text = read_pdf(input_path)
    else:
        sys.exit("Unsupported format. Use .docx or .pdf")

    raw_paras = re.split(r'\n{2,}', text)
    paragraphs = [p.strip() for p in raw_paras if len(p.strip().split()) >= MIN_PARA_WORDS]

    if not paragraphs:
        sys.exit("No paragraphs found. Check the file format.")

    print(f"Analysing {len(paragraphs)} paragraphs from '{input_path.name}'...")

    results = [ruler_pass(p) for p in paragraphs]

    script_dir = Path(__file__).parent
    signals_ref  = load_file("signals.md",  script_dir)
    fewshots_ref = load_file("fewshots.md", script_dir)

    packet = build_packet(paragraphs, results, signals_ref, fewshots_ref, input_path.name)

    output_path = input_path.parent / f"{input_path.stem}_packet.md"
    output_path.write_text(packet, encoding="utf-8")

    flagged = sum(1 for r in results if r["flags"])
    high    = sum(1 for r in results if severity(r["flags"], r["metrics"]) == "HIGH")

    print(f"\nResults:")
    print(f"  Total paragraphs : {len(paragraphs)}")
    print(f"  Ruler-flagged    : {flagged}  ({flagged/len(paragraphs):.0%})")
    print(f"  HIGH severity    : {high}")
    print(f"\nPacket written to : {output_path}")
    print(f"\nNext: open Claude.ai, start a new chat (use Opus), drag in '{output_path.name}'")
    print("      and send: 'Analyse this document and return an HTML report as an artifact.'")


if __name__ == "__main__":
    main()
