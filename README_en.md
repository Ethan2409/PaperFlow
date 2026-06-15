# PaperFlow

> Semi-automated literature screening & deep reading pipeline — from Scopus weekly CSV to structured reading notes.

## What is this?

PaperFlow is a set of [WorkBuddy](https://workbuddy.ai) / [Claude Code](https://claude.ai/claude-code) Skills that turn "reading papers" into a two-step pipeline:

1. **scopus-subscription**: Feed it Scopus weekly CSV literature lists → auto-score (0–10), rank, generate Obsidian Markdown recommendations
2. **paper-reader**: Feed it downloaded PDFs → deep analysis across 9 modules → self-contained HTML with images, formulas, SVG, and Q&A

Reading papers is not about making summaries — it's about hunting for ideas you can use.

## Why semi-automated?

By design, not by limitation:

- PDF downloading requires campus network access that AI agents can't handle
- Full automation (search + download + analyze) burns tokens unnecessarily
- Manual PDF download is the optimal human-machine boundary in terms of cost-effectiveness

## Quick Start

```bash
# 1. Copy skills to WorkBuddy
cp -r scopus-subscription/ ~/.workbuddy/skills/
cp -r paper-reader/ ~/.workbuddy/skills/

# 2. Create your config
cp config.example.yaml config.yaml
# Edit config.yaml with your local paths

# 3. Install Python dependencies
pip install PyMuPDF pandas pyyaml

# 4. Restart WorkBuddy and say "处理本周文献"
```

## Key Features

- **3D scoring engine**: Relevance (50%) + Impact (30%) + Quality (20%), local Python, zero API calls
- **9-module deep reading framework**: From "Quick Overview" to "Interviewer's Soul Q&A"
- **Self-contained HTML output**: KaTeX math rendering + embedded figures + SVG visualization
- **Obsidian integration**: ISO week organization, WikiLink bidirectional links
- **Domain-agnostic core**: Change keywords = change research field, no code changes needed

## Domain Adaptation

The scoring engine (`score.py`) is essentially:
- Regex keyword matching → relevance score
- Journal tier lookup → impact score
- Methodology keyword detection → quality score

Swap the keyword lists in `config.yaml` and it adapts to any research field.

## Acknowledgments

This project draws design inspiration from:

- [PaperReading-skills](https://github.com/Linchunhui/PaperReading-skills) by Linchunhui: the "hunting for ideas" philosophy, structured analysis framework, quality checklines, self-contained HTML approach
- [evil-read-arxiv](https://github.com/juliye2025/evil-read-arxiv) by juliye2025: multi-dimensional scoring, Obsidian integration, config-driven design, batch processing

See [README.md](./README.md) (Chinese) for a detailed itemized acknowledgment.

## License

MIT
