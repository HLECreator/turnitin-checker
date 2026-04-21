import re
import tempfile
import streamlit as st
from pathlib import Path

from check import (
    read_docx, read_pdf, ruler_pass, build_packet, build_rewrite_packet,
    match_flagged_passages, load_file, severity, MIN_PARA_WORDS,
)

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Turnitin AI Checker",
    page_icon="🔍",
    layout="centered",
)

# ── header ────────────────────────────────────────────────────────────────────
st.title("Turnitin AI Checker")
st.caption(
    "Upload a `.docx` or `.pdf` → download an analysis packet → "
    "drag it into Claude.ai (Opus) to get a flagged HTML report."
)

# ── mode selector ─────────────────────────────────────────────────────────────
mode = st.radio(
    "Mode",
    ["Prediction mode (before Turnitin)", "Rewrite mode (after Turnitin)"],
    horizontal=True,
    captions=[
        "Upload draft → predict AI score + rewrite suggestions",
        "Upload draft + paste flagged passages → targeted rewrites",
    ],
)

if mode.startswith("Prediction"):
    st.info(
        "**How it works:** The tool runs a quick ruler pass on your document "
        "(sentence length, hedge words, formulaic openers, vocabulary diversity), "
        "then bundles everything — including the full signal reference and real "
        "before/after examples — into a single file for Claude to analyse.",
        icon="ℹ️",
    )
else:
    st.info(
        "**How it works:** You already have a Turnitin AI report. Upload your draft, "
        "paste the cyan-highlighted passages (one per blank-line-separated block), "
        "and the tool matches each passage to a paragraph. The packet tells Claude "
        "exactly which paragraphs to rewrite — no prediction, no guessing.",
        icon="ℹ️",
    )

st.divider()

# ── upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Choose your document", type=["docx", "pdf"])

if not uploaded:
    st.stop()

# ── process ───────────────────────────────────────────────────────────────────
suffix = Path(uploaded.name).suffix.lower()

with st.spinner("Reading document…"):
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = Path(tmp.name)

    try:
        text = read_docx(tmp_path) if suffix == ".docx" else read_pdf(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    raw_paras = re.split(r'\n{2,}', text)
    all_paras = [p.strip() for p in raw_paras if p.strip()]

    # Drop everything from the references/bibliography section onward.
    # Handles three cases:
    #   1. Standalone heading:  "References" or "References:" alone on a line
    #   2. Merged heading+text: paragraph that *starts* with "References:" or "References\n"
    #   3. Numbered citation block: paragraph that starts with "1." or "[1]" citation format
    HEADING_ALONE = re.compile(
        r'^(\d+[.):]?\s+)?(references|bibliography|works cited|reference list):?\s*$',
        re.IGNORECASE,
    )
    HEADING_MERGED = re.compile(
        r'^(\d+[.):]?\s+)?(references|bibliography|works cited|reference list)[:\s]',
        re.IGNORECASE,
    )
    # Bracket format only — "1." also matches section headings like "2. Executive Summary"
    CITATION_BLOCK = re.compile(
        r'^\[\d+\]\s+\w',
    )
    cutoff = len(all_paras)
    for idx, p in enumerate(all_paras):
        first_line = p.split('\n')[0].strip()
        if (
            HEADING_ALONE.match(p.strip())
            or HEADING_MERGED.match(p.strip())
            or CITATION_BLOCK.match(first_line)
        ):
            cutoff = idx
            break

    paragraphs = [
        p for p in all_paras[:cutoff]
        if len(p.split()) >= MIN_PARA_WORDS
    ]

if not paragraphs:
    st.error(
        "No paragraphs found. If this is a PDF, try opening it in Word and saving as .docx first."
    )
    st.stop()

# ── mode branch ───────────────────────────────────────────────────────────────
if mode.startswith("Rewrite"):
    st.divider()
    st.subheader("Paste Turnitin-flagged passages")
    st.caption(
        "Copy the cyan-highlighted text from your Turnitin AI report. "
        "Separate distinct passages with a blank line. Fragments under 10 characters are skipped."
    )
    flagged_raw = st.text_area(
        "Flagged passages",
        height=240,
        placeholder=(
            "This section analyses the market relevant to the establishment of…\n\n"
            "Despite the prevalent burden of musculoskeletal conditions…\n\n"
            "In conclusion, this proposal offers a strategic response…"
        ),
        label_visibility="collapsed",
    )

    if not flagged_raw.strip():
        st.info("Paste at least one flagged passage above to continue.")
        st.stop()

    flagged_passages = [p.strip() for p in re.split(r"\n{2,}", flagged_raw) if p.strip()]
    flagged_map = match_flagged_passages(paragraphs, flagged_passages)

    matched_para_idxs = {idx for idx in flagged_map if idx != -1}
    unmatched = flagged_map.get(-1, [])

    st.divider()
    st.subheader("Match summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Paragraphs",       len(paragraphs))
    c2.metric("🔴 Flagged",       len(matched_para_idxs))
    c3.metric("🟢 Clear",         len(paragraphs) - len(matched_para_idxs))
    c4.metric("⚠️ Unmatched",     len(unmatched))

    st.caption(
        f"{len(flagged_passages)} passage(s) submitted · "
        f"{len(flagged_passages) - len(unmatched)} matched to a paragraph · "
        f"{len(unmatched)} unmatched (included in packet as context)."
    )

    if unmatched:
        with st.expander(f"⚠️ Review {len(unmatched)} unmatched passage(s)"):
            for p in unmatched:
                st.text(p[:400] + ("…" if len(p) > 400 else ""))
            st.caption(
                "Most common causes: text from tables/figures/captions (extracted differently "
                "than prose), highlights split across page breaks, or OCR whitespace artefacts. "
                "These still appear in the packet under 'Unmatched passages' — Claude uses them as context."
            )

    st.divider()
    st.subheader("Paragraph breakdown")

    for i, para in enumerate(paragraphs, 1):
        passages = flagged_map.get(i - 1, [])
        if passages:
            label = f"🔴 ¶{i} · **FLAGGED** · {len(passages)} passage(s)"
            expanded = True
        else:
            label = f"🟢 ¶{i} · Clear"
            expanded = False
        with st.expander(label, expanded=expanded):
            if passages:
                st.markdown("**Turnitin-highlighted:**")
                for p in passages:
                    st.info(p[:500] + ("…" if len(p) > 500 else ""), icon="🔴")
                st.markdown("**Full paragraph:**")
            preview = para[:600] + ("…" if len(para) > 600 else "")
            st.text(preview)

    # ── rewrite packet download ──────────────────────────────────────────────
    st.divider()
    st.subheader("Get your rewrites")

    script_dir   = Path(__file__).parent
    signals_ref  = load_file("signals.md",  script_dir)
    fewshots_ref = load_file("fewshots.md", script_dir)
    packet       = build_rewrite_packet(
        paragraphs, flagged_map, signals_ref, fewshots_ref, uploaded.name
    )

    packet_name = f"{Path(uploaded.name).stem}_rewrite_packet.md"

    st.download_button(
        label="⬇️  Download rewrite packet",
        data=packet.encode("utf-8"),
        file_name=packet_name,
        mime="text/markdown",
        type="primary",
        use_container_width=True,
    )

    st.markdown(
        """
**Next steps:**
1. Open [claude.ai](https://claude.ai) → start a new chat → switch the model to **Opus**
2. Drag the downloaded packet file into the chat
3. Send: *Rewrite the flagged paragraphs and return an HTML report as an artifact.*
4. Download the HTML report from the artifact panel
"""
    )

    st.stop()

# ── prediction mode continues ─────────────────────────────────────────────────
with st.spinner("Running ruler pass…"):
    results = [ruler_pass(p) for p in paragraphs]

# ── summary metrics ───────────────────────────────────────────────────────────
sevs = [severity(r["flags"]) for r in results]
n_high   = sevs.count("HIGH")
n_medium = sevs.count("MEDIUM")
n_low    = sevs.count("LOW")
n_flagged = sum(1 for r in results if r["flags"])

st.subheader("Ruler-pass summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Paragraphs", len(paragraphs))
c2.metric("🔴 HIGH",    n_high)
c3.metric("🟡 MEDIUM",  n_medium)
c4.metric("⚪ LOW",     n_low)

st.caption(
    f"{n_flagged} of {len(paragraphs)} paragraphs tripped at least one measurable signal. "
    "An estimated AI% is included in the HTML report Claude generates — "
    "it uses all 8 signals and is much closer to Turnitin's actual score."
)

# ── paragraph breakdown ───────────────────────────────────────────────────────
st.divider()
st.subheader("Paragraph breakdown")

SEV_ICON = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "⚪", "CLEAR": "🟢"}

for i, (para, result) in enumerate(zip(paragraphs, results), 1):
    sev   = severity(result["flags"])
    flags = result["flags"]
    icon  = SEV_ICON[sev]
    chips = "  ".join(f"`{f}`" for f in flags) if flags else "—"
    label = f"{icon} ¶{i} · **{sev}**" + (f" — {chips}" if flags else "")

    with st.expander(label, expanded=(sev in ("HIGH", "MEDIUM"))):
        m = result["metrics"]
        stdev_str = str(m.get("sent_stdev", "n/a"))
        cols = st.columns([1, 1, 1, 1])
        cols[0].metric("Sent stdev", stdev_str, help="< 8 triggers S2 (uniform rhythm)")
        cols[1].metric("Hedges",     m["hedge_pct"], help="> 6% triggers S4")
        cols[2].metric("Vocab TTR",  str(m["ttr"]),  help="< 0.55 triggers S8")
        cols[3].metric("Form. opener", "Yes" if m.get("formulaic_opener") else "No",
                       help="Triggers S6")

        st.markdown("**Text preview:**")
        preview = para[:500] + ("…" if len(para) > 500 else "")
        st.text(preview)

# ── packet download ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Get your analysis")

script_dir   = Path(__file__).parent
signals_ref  = load_file("signals.md",  script_dir)
fewshots_ref = load_file("fewshots.md", script_dir)
packet       = build_packet(paragraphs, results, signals_ref, fewshots_ref, uploaded.name)

packet_name = f"{Path(uploaded.name).stem}_packet.md"

st.download_button(
    label="⬇️  Download analysis packet",
    data=packet.encode("utf-8"),
    file_name=packet_name,
    mime="text/markdown",
    type="primary",
    use_container_width=True,
)

st.markdown(
    """
**Next steps:**
1. Open [claude.ai](https://claude.ai) → start a new chat → switch the model to **Opus**
2. Drag the downloaded packet file into the chat
3. Send: *Analyse this document and return an HTML report as an artifact.*
4. Download the HTML report from the artifact panel
"""
)

st.divider()
st.subheader("What do these metrics mean?")

with st.expander("Sent stdev — Sentence length variation"):
    st.markdown(
        "**What it measures:** How much the word count varies between sentences in a paragraph.\n\n"
        "**Why it matters:** Human writers naturally mix short punchy sentences with longer ones. "
        "AI-generated text tends to cluster every sentence in the 15–30 word range, producing a "
        "flat, uniform rhythm. A low stdev (below 8) means most sentences are nearly the same "
        "length — a strong AI signal.\n\n"
        "**How to fix it:** Add at least one sentence under 10 words and one over 25 words per paragraph. "
        "The simplest method: split one long sentence into two short fragments."
    )

with st.expander("Hedges — Hedge word density"):
    st.markdown(
        "**What it measures:** The fraction of words in a paragraph that are AI-favoured "
        "connectives and filler vocabulary — words like *moreover, furthermore, utilise, "
        "leverage, comprehensive, holistic, seamless, robust, facilitate, implement*.\n\n"
        "**Why it matters:** These words appear reflexively in AI output because they are "
        "common in formal training data. A density above 6% signals a paragraph saturated "
        "with low-surprise vocabulary.\n\n"
        "**How to fix it:** Swap AI-favoured words for plainer alternatives — "
        "\"utilise\" → \"use\", \"facilitate\" → \"help\", \"comprehensive\" → \"full\"."
    )

with st.expander("Vocab TTR — Vocabulary type-token ratio"):
    st.markdown(
        "**What it measures:** The proportion of *unique* words out of all words in a paragraph. "
        "A TTR of 0.60 means 60% of words are distinct; the other 40% are repeats.\n\n"
        "**Why it matters:** AI text often repeats the same nouns, verbs, and phrases within a "
        "short passage, reducing vocabulary diversity. A TTR below 0.55 suggests the paragraph "
        "is leaning on a narrow word set — a low-perplexity signature that detectors pick up.\n\n"
        "**How to fix it:** Vary the nouns and verbs across sentences rather than restating "
        "the same concept in the same words."
    )

with st.expander("Form. opener — Formulaic opener"):
    st.markdown(
        "**What it measures:** Whether the paragraph's first sentence matches a known AI-style "
        "opening pattern — phrases like *\"In today's world…\"*, *\"This section analyses…\"*, "
        "*\"It is important to note…\"*, *\"By leveraging…\"*, *\"To ensure…\"*.\n\n"
        "**Why it matters:** These openers are meta-commentary — they describe what the document "
        "is doing rather than saying something substantive. Turnitin's detector consistently "
        "flags paragraphs that open this way. Paraphrasing does not help; the sentence must be "
        "cut entirely or replaced with a concrete claim.\n\n"
        "**How to fix it:** Delete the opener and let the heading carry the signposting. "
        "Start the paragraph mid-argument instead."
    )

st.divider()
st.caption(
    "Ruler pass covers S2, S3 (partial), S4, S5, S6, S8. "
    "Claude identifies all 8 signals and writes the rewrite suggestions. "
    "Corpus: 8 datasets · 12 reports · ~450 flagged segments (IMU BCP2485)."
)
