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

### 🛡️ Mandatory Exa Search Protocol (Zero Waste Standards)
1. **Query Precision**: No conversational filler (`"how to"`, `"can you"`). Use statement-style vectors or dense technical keywords.
2. **Strict Result Cap**: Always pass `numResults: 3` (maximum 5). Never request 10–25 results.
3. **Recency & Version Guard**: For modern web frameworks, specify explicit version or `startPublishedDate: "2025-01-01"`.
4. **Domain Filtering**: Target official docs and repositories with `includeDomains` to eliminate SEO spam.
5. **Code Search First**: Use `get_code_context_exa` when code snippets are needed instead of crawling blog pages.
6. **2-Stage Lookup**: Stage 1 = Highlights; Stage 2 = Fetch single targeted URL via Jina Reader only when deep content is required.
