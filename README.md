# Turnitin AI Checker — v0.1

Analyses a `.docx` or `.pdf` and produces a packet file you drag into Claude.ai to get a flagged HTML report.

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
