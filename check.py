#!/usr/bin/env python3
"""
Turnitin AI Checker — v0.1
Run: python check.py <document.docx|document.pdf>
Output: <docname>_packet.md — drag into Claude.ai (Opus) for a flagged HTML report.
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


def ruler_pass(paragraph: str) -> dict:
    sentences = split_sentences(paragraph)
    flags = []
    metrics = {}

    # S2 — sentence length uniformity
    if len(sentences) >= MIN_SENTENCES:
        stdev = sentence_length_stdev(sentences)
        metrics["sent_stdev"] = round(stdev, 1)
        if stdev < STDEV_FLAG_BELOW:
            flags.append("S2")
    else:
        metrics["sent_stdev"] = "n/a"

    # S4 — hedge/connective density
    hd = hedge_density(paragraph)
    metrics["hedge_pct"] = f"{hd:.0%}"
    if hd > HEDGE_FLAG_ABOVE:
        flags.append("S4")

    # S6 — formulaic opener
    opener = has_formulaic_opener(paragraph)
    metrics["formulaic_opener"] = opener
    if opener:
        flags.append("S6")

    # S8 — vocabulary diversity
    ttr = type_token_ratio(paragraph)
    metrics["ttr"] = round(ttr, 2)
    if ttr < TTR_FLAG_BELOW:
        flags.append("S8")

    # S3 partial — synthesis closer in last sentence
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

    return {"flags": flags, "metrics": metrics}


# ── packet assembly ───────────────────────────────────────────────────────────

def load_file(name: str, script_dir: Path) -> str:
    path = script_dir / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"[{name} not found — place it alongside check.py]\n"


def severity(flags: list) -> str:
    n = len(flags)
    if n == 0:
        return "CLEAR"
    if n == 1:
        return "LOW"
    if n == 2:
        return "MEDIUM"
    return "HIGH"


def estimate_ai_score(paragraphs: list, results: list) -> int:
    """
    Word-weighted AI score estimate. Mirrors Turnitin's logic:
    flagged words / total qualifying words.

    Calibration notes (v0.3):
    - These are RULER-ONLY weights (Streamlit preview). They are intentionally higher than
      the packet weights Claude uses, because the ruler misses S1/S3(full)/S7 and needs
      compensation. Two-point corpus calibration: G9 ruler→54% vs Turnitin 62%.
    - Claude's HTML report uses separate weights (HIGH=0.90, MEDIUM=0.65, LOW=0.20)
      calibrated on a rewritten proposal: Claude→36% vs Turnitin 33% (delta 3 pts).
    - Paragraphs under 50 words excluded from denominator (document furniture).
    """
    SEV_WEIGHT    = {"HIGH": 0.95, "MEDIUM": 0.75, "LOW": 0.25, "CLEAR": 0.0}
    MIN_SCORE_WDS = 50  # below this, paragraph is furniture — skip from denominator
    total_words   = 0
    flagged_words = 0.0
    for para, result in zip(paragraphs, results):
        wc = len(para.split())
        if wc < MIN_SCORE_WDS:
            continue  # exclude furniture from denominator
        total_words   += wc
        flagged_words += wc * SEV_WEIGHT[severity(result["flags"])]
    if total_words == 0:
        return 0
    return round(flagged_words / total_words * 100)


def build_packet(paragraphs: list, results: list, signals_ref: str, fewshots_ref: str, doc_name: str) -> str:
    lines = []

    lines.append(f"# Turnitin AI Analysis Packet — {doc_name}\n\n")

    lines.append("## Instructions for Claude\n\n")
    lines.append(
        "You are a Turnitin AI-detection expert trained on a live research playbook "
        "covering 8 corpora, 12 reports, and ~450 flagged segments from IMU BCP2485 proposals.\n\n"
        "This packet contains:\n"
        "1. **Signal reference (S1–S8)** and **Technique reference (T1–T8)**\n"
        "2. **Before/after examples** from the real corpus\n"
        "3. **The document under review**, split into numbered paragraphs with a ruler-pass "
        "fingerprint showing which measurable signals each paragraph tripped\n\n"
        "### Your task\n\n"
        "For each paragraph:\n"
        "- Review the ruler fingerprint AND the paragraph text\n"
        "- Identify ALL applicable signals (including S1, S3, S5, S7 which the ruler cannot measure)\n"
        "- Assign severity: **HIGH** (≥3 signals) · **MEDIUM** (2) · **LOW** (1) · **CLEAR** (0)\n"
        "- For every HIGH or MEDIUM paragraph, write a **concrete rewrite suggestion** "
        "naming the specific T-technique(s) applied\n\n"
        "### Calibration patterns to watch for\n\n"
        "Three patterns have been validated against Turnitin post-hoc and require special handling "
        "— they are the most common source of severity miscalibration:\n\n"
        "- **Sub-sectioned paragraph → lower severity.** If a paragraph splits into ≥3 bolded or "
        "numbered sub-labels (Stage 1, Stage 2, Phase A…) each followed by **bullet fragments**, "
        "treat the scaffold as broken — fragments under labels carry no S2/S3 load. "
        "(Dataset H §6.1 Patient Journey: predicted MEDIUM, Turnitin cleared it.)\n"
        "- **Phased-prose section → MEDIUM floor.** The inverse: ≥3 phase/risk/stage enumerators each "
        "followed by **full prose paragraphs** (not fragments). Floor severity at MEDIUM regardless "
        "of per-paragraph S6 absence — per-phase prose carries S2 rhythm and S4 vocab even when "
        "surface openers look clean, and Turnitin scores the document-level enumeration scaffold. "
        "(G9 AI1 Operational Plan and Risk Analysis: predicted LOW, Turnitin flagged heavily, "
        "−13pt overall gap.)\n"
        "- **Meta-opener does not absorb body risk.** When a meta-opener sits at the top of a "
        "paragraph that continues into a substantive scaffolded body, score the **opener and the "
        "body as independent risks**. Turnitin often flags the substantive body regardless of what "
        "came before. (Dataset H ¶3 T&CM regulatory: the meta-opener was blamed; Turnitin actually "
        "flagged the substantive body that followed.)\n\n"
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
        "assessment (all 8 signals). "
        "Formula: sum(word_count × severity_weight) / total_qualifying_words × 100, "
        "where HIGH=0.90, MEDIUM=0.65, LOW=0.20, CLEAR=0.0. "
        "**Exclude from the denominator:** cover page, Turnitin boilerplate/disclaimer text, "
        "any paragraph under ~50 words that reads as document furniture rather than substantive prose. "
        "These would be filtered as non-qualifying by Turnitin's own pipeline. "
        "Show the result as a large percentage with a coloured border "
        "(red ≥60%, amber 30–59%, green <30%) and a subtitle: "
        "'Full 8-signal estimate · ±10 pts vs Turnitin'. "
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
        sev = severity(flags)

        if flags:
            flagged_count += 1
        if sev == "HIGH":
            high_count += 1

        flag_str = " · ".join(flags) if flags else "—"
        stdev_str = str(metrics.get("sent_stdev", "n/a"))
        metric_str = (
            f"sent_stdev:{stdev_str} · "
            f"hedges:{metrics['hedge_pct']} · "
            f"ttr:{metrics['ttr']}"
        )
        if metrics.get("formulaic_opener"):
            metric_str += " · FORMULAIC_OPENER"

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
    high    = sum(1 for r in results if severity(r["flags"]) == "HIGH")

    print(f"\nResults:")
    print(f"  Total paragraphs : {len(paragraphs)}")
    print(f"  Ruler-flagged    : {flagged}  ({flagged/len(paragraphs):.0%})")
    print(f"  HIGH severity    : {high}")
    print(f"\nPacket written to : {output_path}")
    print(f"\nNext: open Claude.ai, start a new chat (use Opus), drag in '{output_path.name}'")
    print("      and send: 'Analyse this document and return an HTML report as an artifact.'")


if __name__ == "__main__":
    main()
