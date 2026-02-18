# Changelog

## [0.2.0] - 2026-02-18

### Added
- **Multi-provider fallback system** (`providers.py`) — automatic failover across free AI providers
- **Free fallback chain:** Google Gemini 2.5 Flash → Groq (Llama 3.3 70B) → OpenRouter (DeepSeek R1)
- **Paid provider support** (optional): Anthropic Claude and OpenAI as configurable primary providers
- **`/provider` slash command** — shows active provider, model, and fallback chain status
- **Response footer** — each reply shows which AI provider generated the answer
- **Provider health check on startup** — logs active provider and full fallback chain

### Changed
- **`requirements.txt`** — replaced `anthropic` SDK with `openai` SDK (OpenAI-compatible, works with all providers)
- **`config.py`** — expanded from single-provider to multi-provider config with `PROVIDERS` dict and `FREE_FALLBACK_CHAIN`
- **`.env.example`** — now includes all 5 providers (3 free + 2 paid) with setup links and rate limit notes
- **`bot.py`** — refactored `ask_claude()` → `ask_ai()`, removed Anthropic-specific code, integrated `providers.py`
- **`docs/PRODUCT_DESIGN.md`** — updated architecture diagram, added provider comparison tables, updated roadmap

### Architecture

```
Before (v0.1):
  Discord → bot.py → Anthropic SDK → Claude API (paid only)

After (v0.2):
  Discord → bot.py → providers.py → OpenAI-compatible SDK
                                       ├── Gemini (free)
                                       ├── Groq (free)
                                       ├── OpenRouter (free)
                                       ├── Anthropic (paid, optional)
                                       └── OpenAI (paid, optional)
```

### Files Changed

| File | Action | Description |
|------|--------|-------------|
| `providers.py` | **Created** | Multi-provider client with automatic fallback logic |
| `bot.py` | Modified | Refactored to use `providers.py`, added `/provider` command, response footer |
| `config.py` | Modified | Multi-provider config, provider definitions, fallback chain |
| `requirements.txt` | Modified | `anthropic` → `openai` SDK |
| `.env.example` | Modified | All 5 providers with API key placeholders and docs links |
| `.env` | **Created** | Dummy keys for local development |
| `CHANGELOG.md` | **Created** | This file |
| `docs/PRODUCT_DESIGN.md` | Modified | Updated architecture, provider comparison, roadmap |

---

## [0.1.0] - 2026-02-18

### Added
- Initial project setup
- Discord bot with `discord.py`
- Anthropic Claude API integration
- `/ask` slash command
- `/clear` command to reset conversation memory
- `/summarize` command for thread summarization
- Per-channel conversation history (in-memory)
- Configurable model, tokens, and system prompt via `.env`
- Responds to @mentions
- Auto-splits long responses for Discord's 2000 char limit
- Project structure with `cogs/`, `utils/`, `docs/`, `tests/` directories
- Product design document with 7 use case categories and phased roadmap
