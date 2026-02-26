# SparkSage — Developer Continuation Guide

> **Goal:** Complete all remaining features (Phases 3–5) and produce a Loom video demo showcasing the finished product, its use cases, and how it works.

> **Work Mode:** This project is to be developed **locally and individually**. Each developer should clone the repo, run everything on their own machine, and work independently. There is no shared staging server or team deployment at this stage — all development, testing, and demoing happens on your local environment.

---

## Table of Contents

1. [Project Status](#project-status)
2. [Getting Started](#getting-started)
3. [Architecture Quick Reference](#architecture-quick-reference)
4. [Phase 3 — Core Features](#phase-3--core-features)
5. [Phase 4 — Advanced Features](#phase-4--advanced-features)
6. [Phase 5 — Scale & Polish](#phase-5--scale--polish)
7. [Testing Strategy](#testing-strategy)
8. [Loom Video Demo Plan](#loom-video-demo-plan)

---

## Project Status

### Completed (Phases 1 & 2)

| Component | Status |
|-----------|--------|
| Discord bot with `/ask`, `/clear`, `/summarize`, `/provider` | Done |
| Multi-provider fallback (Gemini → Groq → OpenRouter) | Done |
| Optional paid providers (Anthropic, OpenAI) | Done |
| Per-channel conversation history (SQLite) | Done |
| FastAPI backend with 14 REST API endpoints | Done |
| JWT authentication (password + Discord OAuth2) | Done |
| Next.js + shadcn/ui admin dashboard | Done |
| 4-step setup wizard | Done |
| Overview, Providers, Settings, Conversations pages | Done |
| Unified launcher (`run.py`) | Done |

### Remaining (Phases 3–5)

All tasks below are unchecked in the roadmap and need to be built.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- At least one free AI provider API key (Gemini, Groq, or OpenRouter)

### Local Setup

```bash
# 1. Clone and install Python dependencies
cd sparksage
cp .env.example .env
# Edit .env — fill in DISCORD_TOKEN and at least one AI provider API key
pip install -r requirements.txt

# 2. Start the bot + API server
python run.py
# Bot connects to Discord, API starts on http://localhost:8000

# 3. In a separate terminal, start the dashboard
cd dashboard
npm install
npm run dev
# Dashboard starts on http://localhost:3000
```

### Key Files to Know

| File | Purpose | When to Modify |
|------|---------|----------------|
| `bot.py` | Discord event handlers and slash commands | Adding new commands, changing bot behavior |
| `config.py` | All configuration variables, provider definitions | Adding new config keys |
| `providers.py` | AI provider clients, fallback logic, `chat()` function | Changing AI call behavior |
| `db.py` | SQLite database layer (aiosqlite) | Adding new tables or queries |
| `run.py` | Unified launcher (bot + FastAPI in one process) | Changing startup behavior |
| `api/routes/*.py` | REST API endpoints | Adding new dashboard API endpoints |
| `dashboard/src/app/` | Next.js pages (App Router) | Adding new dashboard pages |
| `dashboard/src/components/` | React components (23 shadcn/ui + custom) | Adding new UI components |
| `dashboard/src/lib/api.ts` | API client for backend calls | Adding new API client methods |

---

## Architecture Quick Reference

```
Discord Users ──► bot.py ──────────────┐
                                        ├── providers.py → AI APIs (Gemini/Groq/OpenRouter/...)
Admin Dashboard ──► FastAPI (api/) ────┘
                        │
                    SQLite DB
               (config, conversations,
                sessions, wizard_state)
```

**Pattern for adding a new feature:**
1. Add any new DB tables/columns in `db.py`
2. Add new bot commands in `bot.py` (or create a new cog in `cogs/`)
3. Add new API endpoints in `api/routes/`
4. Add new dashboard pages/components in `dashboard/src/`
5. Update `config.py` if new settings are needed

---

## Phase 3 — Core Features

### 3.1 Cog-Based Modular Command System

**Goal:** Refactor commands out of `bot.py` into separate cog files for better organization.

**What to do:**
1. Create `cogs/` directory with `__init__.py`
2. Create individual cog files:
   - `cogs/general.py` — `/ask`, `/clear`, `/provider` (move from `bot.py`)
   - `cogs/summarize.py` — `/summarize` (move from `bot.py`)
   - `cogs/code_review.py` — new `/review` command (see 3.2)
   - `cogs/faq.py` — new FAQ auto-detection (see 3.3)
   - `cogs/onboarding.py` — new member welcome flow (see 3.4)
3. Each cog is a class extending `commands.Cog` with `@app_commands.command()` decorators
4. Load cogs in `bot.py` using `await bot.load_extension("cogs.general")`

**Example cog structure:**
```python
# cogs/general.py
from discord.ext import commands
from discord import app_commands
import discord

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask SparkSage a question")
    @app_commands.describe(question="Your question")
    async def ask(self, interaction: discord.Interaction, question: str):
        # ... existing logic from bot.py ...
        pass

async def setup(bot):
    await bot.add_cog(General(bot))
```

**Acceptance criteria:**
- All existing commands work identically after refactoring
- New cogs can be added by creating a file in `cogs/` and loading it
- `bot.py` is simplified to just event handlers and cog loading

---

### 3.2 Code Review with Syntax Highlighting

**Goal:** `/review` command that analyzes pasted code for bugs, style issues, and improvements.

**What to do:**
1. Create `cogs/code_review.py`
2. Add `/review` slash command with parameters:
   - `code` (str, required) — the code snippet
   - `language` (str, optional) — programming language hint
3. Use a specialized system prompt for code review:
   ```
   You are a senior code reviewer. Analyze the code for:
   1. Bugs and potential errors
   2. Style and best practices
   3. Performance improvements
   4. Security concerns
   Respond with markdown formatting using code blocks.
   ```
4. Format the response with Discord markdown (` ```lang ` blocks)
5. Add a dashboard view under Conversations that tags code review interactions with a "Code Review" badge

**Acceptance criteria:**
- Users can paste code and get structured feedback
- Response uses proper syntax highlighting via Discord markdown
- Language auto-detection works when language param is omitted

---

### 3.3 FAQ Auto-Detection and Response

**Goal:** Automatically detect and answer frequently asked questions without requiring a command.

**What to do:**
1. Add a new DB table `faqs`:
   ```sql
   CREATE TABLE faqs (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       guild_id TEXT NOT NULL,
       question TEXT NOT NULL,
       answer TEXT NOT NULL,
       match_keywords TEXT NOT NULL,  -- comma-separated keywords
       times_used INTEGER DEFAULT 0,
       created_by TEXT,
       created_at TEXT DEFAULT (datetime('now'))
   );
   ```
2. Create `cogs/faq.py` with:
   - `/faq add <question> <answer>` — admin adds FAQ entries
   - `/faq list` — list all FAQs for the server
   - `/faq remove <id>` — delete a FAQ entry
   - Auto-detection in `on_message`: check incoming messages against FAQ keywords, respond if confidence is high
3. Add API endpoints:
   - `GET /api/faqs` — list FAQs
   - `POST /api/faqs` — create FAQ
   - `DELETE /api/faqs/{id}` — delete FAQ
4. Add a dashboard FAQ management page

**Acceptance criteria:**
- Admins can CRUD FAQ entries via Discord commands and dashboard
- Bot auto-responds to messages matching FAQ keywords in designated channels
- FAQ usage is tracked (times_used counter)

---

### 3.4 New Member Onboarding Flow

**Goal:** Greet new members and guide them through server setup.

**What to do:**
1. Create `cogs/onboarding.py`
2. Listen to `on_member_join` event
3. Send a DM or channel message with:
   - Welcome message (configurable via dashboard)
   - Server rules summary
   - Links to key channels
   - Option to ask SparkSage any setup questions
4. Add config keys:
   - `WELCOME_CHANNEL_ID` — channel to post welcome messages
   - `WELCOME_MESSAGE` — customizable template with `{user}`, `{server}` placeholders
   - `WELCOME_ENABLED` — on/off toggle
5. Add dashboard settings for onboarding configuration

**Acceptance criteria:**
- New members receive a welcome message automatically
- Message template is customizable from the dashboard
- Onboarding can be enabled/disabled without restart

---

### 3.5 Role-Based Access Control for Commands

**Goal:** Restrict certain commands to specific Discord roles.

**What to do:**
1. Add a `command_permissions` DB table:
   ```sql
   CREATE TABLE command_permissions (
       command_name TEXT NOT NULL,
       guild_id TEXT NOT NULL,
       role_id TEXT NOT NULL,
       PRIMARY KEY (command_name, guild_id, role_id)
   );
   ```
2. Create a decorator/check function that validates permissions before command execution
3. Add `/permissions` command group:
   - `/permissions set <command> <role>` — require role for command
   - `/permissions remove <command> <role>` — remove restriction
   - `/permissions list` — show all restrictions
4. Add API endpoints and a dashboard Permissions page

**Acceptance criteria:**
- Server admins can restrict any command to specific roles
- Unrestricted commands remain available to everyone
- Permission changes take effect immediately

---

## Phase 4 — Advanced Features

### 4.1 Daily Digest Scheduler

**Goal:** Automatically summarize daily activity and post to a designated channel.

**What to do:**
1. Create `cogs/digest.py`
2. Use `discord.ext.tasks` for scheduling:
   ```python
   from discord.ext import tasks

   @tasks.loop(hours=24)
   async def daily_digest(self):
       # Collect messages from past 24h
       # Summarize with AI
       # Post to digest channel
   ```
3. Add config keys: `DIGEST_CHANNEL_ID`, `DIGEST_TIME` (e.g., "09:00"), `DIGEST_ENABLED`
4. Add dashboard controls for digest settings

---

### 4.2 Content Moderation Pipeline

**Goal:** Flag potentially problematic messages for moderator review.

**What to do:**
1. Create `cogs/moderation.py`
2. In `on_message`, check messages against a moderation prompt:
   ```
   Rate the following message for toxicity, spam, and rule violations.
   Respond with JSON: {"flagged": bool, "reason": str, "severity": "low"|"medium"|"high"}
   ```
3. If flagged, post to a `#mod-log` channel with the original message, reason, and action buttons
4. Add config: `MODERATION_ENABLED`, `MOD_LOG_CHANNEL_ID`, `MODERATION_SENSITIVITY`
5. Track moderation stats in DB

**Important:** Be careful with AI moderation — always flag for human review, never auto-delete.

---

### 4.3 Multi-Language Translation

**Goal:** `/translate` command and auto-translation for multilingual servers.

**What to do:**
1. Create `cogs/translate.py`
2. Add `/translate <text> <target_language>` command
3. Optional: auto-detect language and translate messages in designated channels
4. Use the existing AI provider with a translation-specific prompt

---

### 4.4 Custom System Prompts Per Channel

**Goal:** Allow different AI personalities per channel.

**What to do:**
1. Add `channel_prompts` DB table:
   ```sql
   CREATE TABLE channel_prompts (
       channel_id TEXT PRIMARY KEY,
       guild_id TEXT NOT NULL,
       system_prompt TEXT NOT NULL
   );
   ```
2. Modify `ask_ai()` in `bot.py` to check for channel-specific prompts before falling back to the global system prompt
3. Add `/prompt set <text>` and `/prompt reset` commands
4. Add API endpoints and dashboard UI for per-channel prompt management

---

### 4.5 Per-Channel Provider Override

**Goal:** Allow specific channels to use specific AI providers.

**What to do:**
1. Add `channel_providers` DB table
2. Modify `ask_ai()` to check for channel-specific provider before using the global primary
3. Add `/channel-provider set <provider>` command
4. Add dashboard UI for channel-provider mapping

---

## Phase 5 — Scale & Polish

### 5.1 Analytics and Usage Tracking

**Goal:** Track and visualize bot usage across servers.

**What to do:**
1. Add `analytics` DB table:
   ```sql
   CREATE TABLE analytics (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       event_type TEXT NOT NULL,     -- 'command', 'mention', 'faq', 'moderation'
       guild_id TEXT,
       channel_id TEXT,
       user_id TEXT,
       provider TEXT,
       tokens_used INTEGER,
       latency_ms INTEGER,
       created_at TEXT DEFAULT (datetime('now'))
   );
   ```
2. Instrument all AI calls to record usage metrics
3. Add API endpoints: `GET /api/analytics/summary`, `GET /api/analytics/history`
4. Add a dashboard Analytics page with charts (use recharts or similar):
   - Messages per day (line chart)
   - Provider usage distribution (pie chart)
   - Top channels by activity (bar chart)
   - Average response latency (line chart)

---

### 5.2 Rate Limiting and Quota Management

**Goal:** Prevent abuse and manage provider quotas.

**What to do:**
1. Create `utils/rate_limiter.py` with a token-bucket or sliding-window implementation
2. Track per-user and per-guild usage
3. Add config: `RATE_LIMIT_USER` (requests/min), `RATE_LIMIT_GUILD` (requests/min)
4. Return friendly messages when rate limited
5. Add dashboard quota monitoring

---

### 5.3 Plugin System for Community Extensions

**Goal:** Allow community-contributed cog plugins.

**What to do:**
1. Create a `plugins/` directory with a loader
2. Define a plugin manifest format (JSON):
   ```json
   {
     "name": "trivia",
     "version": "1.0.0",
     "author": "community",
     "description": "Trivia game commands",
     "cog": "trivia.py"
   }
   ```
3. Add `/plugin list`, `/plugin enable`, `/plugin disable` commands
4. Add dashboard plugin management page
5. Plugins are loaded/unloaded at runtime without restart

---

### 5.4 Provider Usage Analytics and Cost Tracking

**Goal:** Track API costs for paid providers and show usage trends.

**What to do:**
1. Extend the `analytics` table with `input_tokens`, `output_tokens`, `estimated_cost`
2. Calculate cost based on provider pricing (store pricing in `config.py`)
3. Add dashboard cost tracking page with:
   - Cost per provider per day
   - Projected monthly cost
   - Cost alerts when approaching thresholds

---

### 5.5 Dashboard Responsive Design + Dark Mode

**Goal:** Make the dashboard mobile-friendly and add dark/light mode toggle.

**What to do:**
1. Audit all dashboard pages for mobile breakpoints (Tailwind `sm:`, `md:`, `lg:`)
2. Add dark mode using Tailwind's `dark:` variant and `next-themes`:
   ```bash
   cd dashboard && npm install next-themes
   ```
3. Add a theme toggle button in the sidebar header
4. Ensure all shadcn/ui components respect the theme
5. Test on mobile viewports (375px, 768px, 1024px)

---

## Testing Strategy

### Unit Tests

Create `tests/` with:
```
tests/
├── test_config.py       — config loading, reload_from_db
├── test_providers.py    — fallback logic, test_provider
├── test_db.py           — all DB operations
├── test_api/
│   ├── test_auth.py     — login, JWT validation
│   ├── test_config.py   — config CRUD
│   ├── test_providers.py — provider endpoints
│   └── test_wizard.py   — wizard flow
└── conftest.py          — fixtures (test DB, mock providers)
```

**Recommended tools:**
- `pytest` + `pytest-asyncio` for Python tests
- `vitest` for dashboard component tests
- `httpx` for API integration tests

### Manual Testing Checklist

Before recording the Loom demo, verify:

- [ ] Fresh setup: `python run.py` starts cleanly with no .env
- [ ] Setup wizard completes successfully in browser
- [ ] Bot comes online in Discord after wizard completion
- [ ] `/ask` returns AI responses with provider footer
- [ ] `/summarize` condenses conversation history
- [ ] `/clear` resets channel memory
- [ ] `/provider` shows current provider info
- [ ] Provider fallback works (disable primary, verify fallback triggers)
- [ ] Dashboard Overview shows live bot status
- [ ] Dashboard Providers page: test keys, switch primary
- [ ] Dashboard Settings page: change system prompt, verify bot uses new prompt
- [ ] Dashboard Conversations page: view chat history with provider badges
- [ ] All Phase 3–5 features work as specified

---

## Loom Video Demo Plan

Record a **5–8 minute Loom video** covering the following sections. Share the Loom link as the final deliverable.

### Part 1 — Introduction (30 seconds)
- "This is SparkSage — an AI-powered Discord bot with a web admin dashboard"
- Show the project tagline and high-level architecture diagram
- Mention it's free to run using free AI providers

### Part 2 — First-Time Setup (1–2 minutes)
1. Show `python run.py` starting in the terminal
2. Open the dashboard at `localhost:3000`
3. Walk through the 4-step setup wizard:
   - Enter Discord token
   - Configure AI providers (show testing a Gemini key)
   - Adjust bot settings (system prompt, max tokens)
   - Review and complete setup
4. Show the bot coming online in Discord

### Part 3 — Discord Bot Demo (2–3 minutes)
Show each use case in action:

1. **General Q&A** — @mention the bot with a question, show the response with provider footer
2. **Code Review** — Use `/review` to analyze a code snippet, show syntax-highlighted feedback
3. **Summarization** — After a few messages, use `/summarize` to condense the conversation
4. **FAQ System** — Add a FAQ entry with `/faq add`, then ask the question naturally and show auto-response
5. **Translation** — Use `/translate` to translate a message
6. **Provider Fallback** — Show `/provider` output, explain the fallback chain

### Part 4 — Admin Dashboard Demo (1–2 minutes)
1. **Overview Page** — Show bot status, latency, guild count, active provider
2. **Provider Management** — Test a provider key, switch primary provider, show fallback chain
3. **Settings** — Change the system prompt live, show the bot using the new prompt in Discord
4. **Conversations** — Browse conversation history per channel, show provider badges
5. **Analytics** (if Phase 5 complete) — Show usage charts and cost tracking

### Part 5 — Use Cases Summary (30 seconds)
Recap the 7 use case categories:
1. Community & Support — auto-FAQ, onboarding, ticket triage
2. Developer Teams — code review, bug analysis, docs lookup
3. Content & Moderation — content flagging, thread summarization
4. Education — tutoring, quizzes, language practice
5. Productivity — brainstorming, writing, translation
6. Gaming — game guides, lore, LFG matching
7. Data & Reporting — daily digests, sentiment analysis

### Part 6 — Closing (15 seconds)
- "SparkSage is free, self-hosted, and extensible"
- Point to the GitHub repo and docs
- "Thanks for watching"

### Loom Recording Tips
- Use 1920x1080 resolution
- Record both screen and camera (picture-in-picture)
- Have Discord and the dashboard side by side
- Pre-populate some conversation history so the demo looks active
- Test all commands before recording to avoid errors
- Use Loom's drawing tools to highlight key UI elements

---

## Development Workflow

### Working Locally & Individually

This project is meant to be worked on **locally on your own machine**. There is no shared deployment, CI/CD pipeline, or team server at this stage.

**What this means for you:**
- Clone the repo to your machine and work on your own copy
- Run the bot, API, and dashboard all on `localhost`
- **Temporarily use your own Discord server** for development and testing (do not use a production server — create a throwaway test server)
- **Use only free AI providers during development and testing** (Gemini, Groq, OpenRouter) — do not use paid providers (Anthropic, OpenAI) until production. Get your own free API keys and do not share them.
- Commit your work to your own branch and push when ready
- Record your own Loom demo from your local environment
- Do not depend on anyone else's environment or deploy to any shared infrastructure

**Setting up a temporary test Discord server:**

You will need your own Discord server to develop and test against. This is a temporary dev server — it will not be used in production. Once we consolidate to a shared server later, you can delete it.

1. Create a new Discord server (click "+" in Discord sidebar) — name it something like "SparkSage Dev - [YourName]"
2. Go to [Discord Developer Portal](https://discord.com/developers/applications) → New Application
3. Go to Bot → Reset Token → copy the token to your `.env`
4. Go to OAuth2 → URL Generator → select `bot` + `applications.commands` scopes
5. Select permissions: Send Messages, Read Message History, Use Slash Commands
6. Copy the generated URL, open it, and add the bot to your test server
7. Create a few test channels (e.g., `#general`, `#help`, `#code-review`) to test different features

**Using free AI models only during development:**

While in development and testing, **only use the free-tier AI providers**. Do not configure or spend money on paid providers (Anthropic, OpenAI) — save those for production.

| Provider | Free API Key Link | Free Limits |
|----------|-------------------|-------------|
| **Google Gemini** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | 10 RPM, 250 req/day |
| **Groq** | [console.groq.com/keys](https://console.groq.com/keys) | 30 RPM, 1,000 req/day |
| **OpenRouter** | [openrouter.ai/keys](https://openrouter.ai/keys) | 20 RPM, 200+ req/day |

Sign up for at least one (ideally all three so you can test the fallback chain). Leave `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` blank in your `.env`.

### Branch Strategy
```
main ← feature/phase-3-cogs
     ← feature/phase-3-code-review
     ← feature/phase-3-faq
     ← feature/phase-4-digest
     ← ...
```

One branch per feature. PR into `main` with a short description. Update `CHANGELOG.md` with each merge.

### Commit Convention
```
feat: add /review command for code review
fix: handle empty code blocks in review
refactor: extract cog loading into separate function
docs: update roadmap with Phase 3 completion
```

### Running the Project During Development
```bash
# Terminal 1 — Bot + API (auto-restarts are not built in; restart manually after changes)
python run.py

# Terminal 2 — Dashboard (hot-reload built in)
cd dashboard && npm run dev
```

### Adding a New Slash Command (Quick Reference)
1. Create a cog file in `cogs/`
2. Define the command with `@app_commands.command()`
3. Load the cog in `bot.py`
4. Restart the bot (commands sync on startup via `bot.tree.sync()`)

### Adding a New API Endpoint (Quick Reference)
1. Create or edit a route file in `api/routes/`
2. Register the router in `api/main.py`
3. Add the corresponding API client method in `dashboard/src/lib/api.ts`
4. Build the dashboard UI

---

## Final Deliverable

> **A Loom video link** demonstrating:
> 1. The complete SparkSage system running (bot + dashboard)
> 2. First-time setup wizard walkthrough
> 3. All major Discord bot commands in action
> 4. Admin dashboard features
> 5. Key use cases (code review, FAQ, summarization, translation)
>
> Upload the Loom link to the project README or share it in the team channel.
