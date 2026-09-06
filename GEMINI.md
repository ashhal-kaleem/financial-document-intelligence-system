# Tooling & Internet Access Policy (STRICT SYSTEM OVERRIDE)

## 🚫 Prohibited Built-in Tools
- **NEVER** use Antigravity's built-in `search_web` tool.
- **NEVER** use Antigravity's built-in `read_url_content` tool.
- **NEVER** use GUI/direct file tools (`read_file`, `write_file`, `edit_block`).

## 💻 Mandatory Terminal-Native Commands
Instead of built-in file and inspection tools, ALWAYS execute native Linux terminal commands:

| Operation | Mandatory Terminal Command |
|---|---|
| **Read File** | `cat file`, `head -n 50 file`, `tail -n 50 file`, `sed -n '1,50p' file` |
| **Write File (Create/Overwrite)** | `cat << 'EOF' > file ... EOF` |
| **Append to File** | `cat << 'EOF' >> file ... EOF` |
| **Edit File (Search & Replace)** | `sed -i 's/old/new/g' file` or `awk` |
| **List Directory** | `ls -la path/`, `find path/ -maxdepth 2` |
| **Search in Code / Text** | `grep -rn "pattern" path/`, `find . -name "*.ext"` |

## 🌐 Default Internet & Web Research Mechanism
- **ALWAYS** use the `agent-reach` skill as the default and only router for:
  - Web searches and general internet research (Exa via `mcporter`)
  - Fetching and reading URLs / web pages (via Jina Reader: `curl -sL https://r.jina.ai/URL`)
  - YouTube video transcripts and metadata (via `yt-dlp`)
  - GitHub repositories, issues, and PR lookups (via `gh` CLI)
  - Reddit, Twitter/X, and social discussions (via `rdt-cli` / `opencli`)

### 🛡️ Mandatory Cognitive Deep Research & Exa Protocol
1. **Query Decomposition (MindSearch WebPlanner Standard)**:
   - Never fire a single broad query for a complex technical question.
   - Decompose multi-faceted problems into 2 to 4 atomic sub-questions (Mechanics, Constraints, Disconfirmation/Regrets, Implementation).
2. **Deterministic Search Operators**:
   - Use `"exact phrase"` for exact error messages, function names, and quotes.
   - Use `site:trusted.domain` (e.g. `site:arxiv.org`, `site:github.com`) to anchor search in authority sources.
   - Use `OR` for synonym expansions (`"vector store" OR "pgvector"`).
   - Use `-exclusion` (`-course -medium -pricing`) to eliminate low-signal SEO aggregators.
3. **Query Precision & Recency Guard**:
   - No conversational filler (`"how to"`, `"can you"`). Use statement-style vectors or dense technical keywords.
   - For fast-moving frameworks, always supply library version or `startPublishedDate: "2025-01-01"`.
4. **Strict Result Cap**: Keep `numResults: 3` (maximum 5). Quality over quantity.
5. **Mandatory Anti-Snippet Verification (Jina Reader Direct-Read)**:
   - Never finalize an architecture or code solution based solely on 2-line search snippets or highlight cards.
   - Drill into the primary authority URL via Jina Reader (`curl -sL https://r.jina.ai/<URL> | head -n 100`) to verify ground-truth signatures and caveats.
6. **Code Search First**: Use `get_code_context_exa` when code snippets are needed instead of crawling blog pages.
7. **Bounded Reflection & Saturation Rule (EXSEARCH Standard)**:
   - Evaluate what was proven vs what gap remains after each search.
   - Max 3 search iterations per sub-question; stop immediately when 2 consecutive searches return redundant evidence.
8. **Metacognitive Self-Audit & Proposal Gate**:
   - Actively monitor retrieval quality during research. If a systemic limitation or missing search operator pattern is detected, formulate a diagnosis.
   - Never silently mutate master templates. Present a surgical proposal to the user and encode the rule into `instructions.md` and `search.md` only upon explicit confirmation ("update kardo").
