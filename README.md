# Turnitin AI Checker — v0.2

Analyses a `.docx` or `.pdf` and produces a packet file you drag into Claude.ai to get a flagged HTML report.

Two modes:
- **Prediction mode** — before you submit to Turnitin. Get a predicted AI score and rewrite suggestions.
- **Rewrite mode** — after you have a Turnitin report. Paste the flagged passages; get targeted rewrites for those specific paragraphs (no prediction, no guessing).

---

## First-time setup (do this once)

### 1. Install Python
Download from https://www.python.org/downloads/ and run the installer.
**Important:** tick "Add Python to PATH" on the first screen.

### 2. Install dependencies
Open Command Prompt (search "cmd" in the Start menu) and run:

```
pip install python-docx pypdf
```

---

## Running the tool

Open Command Prompt in the `turnitin-check` folder:
- Navigate to the folder in File Explorer
- Click the address bar, type `cmd`, press Enter

Then run:

```
python check.py "C:\path\to\your\document.docx"
```

Or if your document is in the same folder:

```
python check.py mydocument.docx
```

The tool prints a summary and writes a file called `mydocument_packet.md` next to your document.

---

## Getting the HTML report

1. Open [claude.ai](https://claude.ai) in your browser
2. Start a new chat — switch the model to **Claude Opus** (top-left dropdown)
3. Drag `mydocument_packet.md` into the chat, or click the paperclip and attach it
4. Send this message:

> Analyse this document and return an HTML report as an artifact.

Claude will produce a styled HTML report in the side panel. Click **Download** to save it.

---

## Rewrite mode — when you already have a Turnitin report

Use this mode after you've submitted to Turnitin and received the AI detection report. Instead of predicting what might flag, the tool generates targeted rewrites for the paragraphs Turnitin actually highlighted.

**How to use it:**

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```
   *(CLI `check.py` only supports prediction mode; rewrite mode is Streamlit-only.)*

2. At the top of the app, switch to **Rewrite mode (after Turnitin)**.

3. Upload your original `.docx` or `.pdf` (the version you submitted to Turnitin).

4. Open your Turnitin AI report PDF. **Copy each cyan-highlighted passage** and paste it into the text area. Separate distinct passages with a blank line:

   ```
   This section analyses the market relevant to...

   Despite the prevalent burden of musculoskeletal conditions...

   In conclusion, this proposal offers a strategic response...
   ```

5. The app matches each passage to a paragraph (exact substring first, then token-overlap fallback). You'll see a match summary and any unmatched passages flagged for review.

6. Download the rewrite packet → drag into Claude.ai (Opus) → send:

   > Rewrite the flagged paragraphs and return an HTML report as an artifact.

**What you get:** an HTML report with before/after rewrites for every flagged paragraph, each showing the triggering signal (S1–S8) with the exact quoted phrase, the technique applied (T1–T9), and a one-sentence rationale. Clear paragraphs are listed in the summary table only — no wasted effort.

**Unmatched passages** (from tables, figures, page-break splits, etc.) still appear in the packet under a dedicated section so Claude can use them as context.

---

## Files in this folder

| File | Purpose |
|---|---|
| `check.py` | Main script |
| `signals.md` | S1–S8 signal and T1–T8 technique reference (loaded into every packet) |
| `fewshots.md` | Before/after examples from the real corpus (loaded into every packet) |
| `README.md` | This file |

---

## What the ruler pass measures

The script automatically checks four things per paragraph:

| Metric | Signal | Flag condition |
|---|---|---|
| Sentence-length stdev | S2 | Stdev < 8 words (uniform rhythm) |
| Hedge/connective density | S4 | >6% of words are AI-favoured hedges |
| Formulaic opener | S6 | Paragraph starts with a known AI-style opener |
| Type-token ratio | S8 | <55% unique words (low vocabulary diversity) |

Four other signals (S1, S3, S5, S7) require reading judgment — Claude handles those in the analysis step.

---

## Troubleshooting

**"python is not recognized"** — Python is not in PATH. Re-run the installer and tick "Add Python to PATH".

**"No module named docx"** — Run `pip install python-docx` again.

**"No paragraphs found"** — The PDF may use a format that doesn't extract cleanly. Try saving as .docx from Word first.

**Packet file is very large** — The script skips paragraphs under 20 words. If your document has many short lines (e.g. headers), these are already excluded.
