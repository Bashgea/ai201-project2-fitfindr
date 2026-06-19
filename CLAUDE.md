# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FitFindr is an AI agent project (AI201, Module 1, Week 2) that recommends secondhand fashion finds. The agent uses the Groq API (LLM) to power a planning loop that calls three tools: search listings, suggest outfits, and create a formatted fit card.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create a `.env` file with:
```
GROQ_API_KEY=your_key_here
```

## Common Commands

```bash
# Verify data loads correctly
python utils/data_loader.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_tools.py

# Run a single test
pytest tests/test_tools.py::test_search_listings_returns_results
```

## Architecture

The agent follows a **ReAct-style planning loop**:

```
User query
    ↓
Planning Loop (Groq LLM)
    ↓ decides which tool to call
    ├── search_listings(description, size, max_price) → filtered listing dicts
    ├── suggest_outfit(new_item, wardrobe) → outfit suggestion string
    └── create_fit_card(outfit, new_item) → formatted card string
    ↓
Final output to user
```

**Data layer** (`utils/data_loader.py`): Provides `load_listings()` and `get_example_wardrobe()` / `get_empty_wardrobe()` — call these inside tool implementations rather than re-reading files directly.

**Listings** (`data/listings.json`): 40 items with fields `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. Categories: tops, bottoms, outerwear, shoes, accessories.

**Wardrobe schema** (`data/wardrobe_schema.json`): Items have `id`, `name`, `category`, `colors`, `style_tags`, `notes`. The `suggest_outfit` tool receives a wardrobe in this format. Use `get_example_wardrobe()` for testing.

## Required Tool Signatures

Your `tools.py` must implement exactly these signatures (the README validates them):

```python
def search_listings(description: str, size: str, max_price: float) -> list[dict]: ...
def suggest_outfit(new_item: dict, wardrobe: dict) -> str: ...
def create_fit_card(outfit: str, new_item: dict) -> str: ...
```

Parameter names and types must match what's documented in `README.md` — the grader cross-checks them.

## Key Constraints

- LLM calls go through Groq (`groq` Python SDK), not OpenAI. Use the `GROQ_API_KEY` env var.
- `planning.md` must be filled out before implementation — it is reviewed as part of the submission.
- The `README.md` Interaction Walkthrough and Error Handling table must be completed with real examples (not template placeholders).
- Gradio is included in dependencies — the UI (if built) should use it.
