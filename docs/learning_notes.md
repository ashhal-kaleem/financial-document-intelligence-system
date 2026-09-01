# Learning Notes

Personal notes captured during each phase of building this project.
These exist to reinforce learning and to demonstrate depth of understanding
in technical interviews.

---

## Phase 0 — Project Setup

**Date:** 2026-05-04

### What I learned

- `pyproject.toml` is the modern standard for Python project metadata.
  It replaces `setup.py`, `setup.cfg`, and `requirements.txt` in a single file.
- Optional dependency groups (`[dev]`, `[eval]`, `[openai]`) let you install
  only what you need. In CI you might skip `[openai]` to avoid needing an API key.
- A `src/` layout forces you to install the package before importing it,
  which catches packaging bugs early and mirrors how the code runs in production.
- Makefile targets are self-documenting when combined with `## comments` and
  the `grep + awk` pattern for `make help`.

### Architecture decisions made

- **Local-first**: All core dependencies work without an API key or GPU.
- **Pluggable LLM backend**: The `LLM_BACKEND` env var selects Groq or Mock
  without changing code.
- **Separate API and UI**: FastAPI serves engineers and downstream tools;
  Streamlit serves human users and demos.

### Questions I had

- _Why FAISS over Chroma?_ FAISS is lower level and more widely used in
  production. Chroma adds a nice API but introduces more abstraction.
  We start with FAISS to understand the primitives.

---

<!-- Add a new section after each phase -->
