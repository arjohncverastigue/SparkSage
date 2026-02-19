# SparkSage — Product Design Document

## Product Vision

SparkSage is an AI-powered Discord bot with a web admin dashboard that brings world-class AI intelligence into any Discord server — for free. Using a multi-provider architecture with automatic fallback, it serves as an always-available, wise, and versatile assistant that enhances community engagement, streamlines support, and boosts team productivity without any API costs.

**Tagline:** *The AI spark that makes your community wiser.*

---

## Target Users

| Segment | Description |
|---------|-------------|
| Community Managers | Run public or private Discord servers and need help managing FAQs, onboarding, and moderation |
| Developer Teams | Use Discord for internal comms and want code review, docs lookup, and deployment support |
| Educators & Study Groups | Run learning communities and need tutoring, quizzes, and study assistance |
| Gaming Communities | Need game guides, lore lookups, and LFG (Looking for Group) matching |
| Small-to-Mid Teams | Use Discord as their primary workspace and want a productivity assistant |

---

## Use Cases

### 1. Community & Support

| Feature | Description | Priority |
|---------|-------------|----------|
| **Auto-Answer FAQs** | Automatically respond to frequently asked questions in designated help channels, reducing moderator workload | P0 |
| **Ticket Triage** | Summarize and categorize support threads, tag the appropriate team member based on issue type | P1 |
| **Onboarding Assistant** | Greet new members, walk them through server rules, answer setup questions, and guide them to the right channels | P0 |

**User Story:** *As a community moderator, I want SparkSage to handle common questions in #help so I can focus on complex issues instead of repeating the same answers daily.*

---

### 2. Developer Teams

| Feature | Description | Priority |
|---------|-------------|----------|
| **Code Review Bot** | Paste a code snippet in chat, SparkSage reviews it for bugs, style issues, and suggests improvements | P0 |
| **Bug Analysis** | Describe a bug and get debugging suggestions, root cause hypotheses, and potential fixes | P0 |
| **Documentation Lookup** | Ask SparkSage about project APIs, libraries, or internal docs without leaving Discord | P1 |
| **Deployment Summaries** | Pipe CI/CD webhook payloads through SparkSage to get plain-English summaries of what changed | P2 |

**User Story:** *As a developer, I want to paste a code snippet and get instant feedback so I can catch issues before opening a pull request.*

---

### 3. Content & Moderation

| Feature | Description | Priority |
|---------|-------------|----------|
| **Content Moderation** | Flag or summarize potentially problematic messages for human moderator review | P1 |
| **Meeting/Call Notes** | Paste raw notes from a voice channel session, SparkSage formats them into structured action items | P1 |
| **Thread Summarization** | Use `/summarize` to condense long discussion threads into key takeaways and decisions | P0 |

**User Story:** *As a team lead, I want to summarize a 200-message thread into 5 bullet points so stakeholders can quickly catch up.*

---

### 4. Education & Learning

| Feature | Description | Priority |
|---------|-------------|----------|
| **Study Group Assistant** | Members ask questions, SparkSage explains concepts, generates practice problems, and quizzes users | P1 |
| **Language Practice** | SparkSage acts as a conversation partner in a target language, correcting grammar and suggesting improvements | P2 |
| **Code Tutoring** | Step-by-step explanations for beginners, with follow-up questions to test understanding | P1 |

**User Story:** *As a student in a coding bootcamp Discord, I want SparkSage to explain recursion step by step and then quiz me to make sure I understand.*

---

### 5. Productivity & Workflow

| Feature | Description | Priority |
|---------|-------------|----------|
| **Brainstorming Partner** | Teams bounce ideas off SparkSage in a dedicated channel, getting structured feedback and suggestions | P0 |
| **Writing Assistant** | Draft announcements, patch notes, blog posts, changelogs, or social media copy on demand | P1 |
| **Translation** | Instantly translate messages for multilingual communities | P2 |
| **Scheduling Helper** | Parse availability from messages and suggest optimal meeting times | P2 |

**User Story:** *As a product manager, I want to brainstorm feature ideas with SparkSage and get a structured summary I can share with the team.*

---

### 6. Gaming Communities

| Feature | Description | Priority |
|---------|-------------|----------|
| **Game Guide Assistant** | Answer questions about game mechanics, optimal builds, strategies, and tips | P1 |
| **Lore Lookup** | Pull from game wikis and documentation to answer lore and story questions | P2 |
| **LFG Matching** | Help match players based on preferences, skill level, timezone, and availability | P2 |

**User Story:** *As a guild leader, I want members to ask SparkSage about boss strategies instead of pinging officers at 3 AM.*

---

### 7. Data & Reporting

| Feature | Description | Priority |
|---------|-------------|----------|
| **Daily Digest** | Automatically summarize the day's most active channels and key discussions | P1 |
| **Sentiment Check** | Gauge community mood from recent messages and flag potential issues | P2 |
| **Poll Analysis** | Summarize and interpret poll/survey results with context and recommendations | P2 |

**User Story:** *As a community manager, I want a morning digest of what happened overnight so I can start my day informed without reading every channel.*

---

## Architecture Overview

### System Architecture

SparkSage consists of three layers: a Discord bot, a FastAPI backend, and a Next.js admin dashboard.

```
┌──────────────────┐     ┌──────────────────────────────────────────────────┐
│                   │     │              SparkSage Server                    │
│  Discord Server   │     │                                                 │
│  (Users)          │◄───►│  ┌─────────────┐     ┌──────────────────────┐  │
│                   │     │  │  Discord Bot │     │   FastAPI Backend    │  │
└──────────────────┘     │  │  (bot.py)    │     │   (localhost:8000)   │  │
                          │  │              │     │                      │  │
                          │  │  - Mentions  │     │  - /api/auth         │  │
                          │  │  - /ask      │     │  - /api/config       │  │
                          │  │  - /clear    │     │  - /api/providers    │  │
                          │  │  - /summarize│     │  - /api/bot          │  │
                          │  │  - /provider │     │  - /api/conversations│  │
                          │  └──────┬───────┘     │  - /api/wizard       │  │
                          │         │              └──────────┬───────────┘  │
                          │         │                         │              │
                          │         ▼                         ▼              │
                          │  ┌─────────────────────────────────────────┐    │
                          │  │         Shared Python Core               │    │
                          │  │  config.py / providers.py / db.py        │    │
                          │  │  SQLite (config, conversations, sessions)│    │
                          │  └─────────────────────────────────────────┘    │
                          └──────────────────────────────────────────────────┘
                                              ▲
                                              │ REST API
                                              ▼
                          ┌──────────────────────────────────────────────────┐
                          │          Next.js Admin Dashboard                 │
                          │          (localhost:3000)                        │
                          │                                                 │
                          │  ┌─────────────┐  ┌──────────────────────────┐  │
                          │  │ Setup Wizard │  │    Dashboard Pages       │  │
                          │  │             │  │                          │  │
                          │  │ 1. Discord  │  │  - Overview (bot status) │  │
                          │  │ 2. Providers│  │  - Provider management   │  │
                          │  │ 3. Settings │  │  - Bot settings editor   │  │
                          │  │ 4. Review   │  │  - Conversation viewer   │  │
                          │  └─────────────┘  └──────────────────────────┘  │
                          │                                                 │
                          │  Auth: Discord OAuth2 + Password fallback       │
                          └──────────────────────────────────────────────────┘
```

### Multi-Provider Fallback System

SparkSage uses a unified OpenAI-compatible SDK to connect to multiple AI providers. If the primary provider hits a rate limit or fails, it automatically falls back to the next available free provider.

```
Request → Primary Provider → [fail] → Gemini → [fail] → Groq → [fail] → OpenRouter
```

Providers can be tested, switched, and monitored in real-time through the admin dashboard.

### Provider Comparison

#### Free Providers (Fallback Chain)

| Provider | Model | Free Limits | Strengths |
|----------|-------|-------------|-----------|
| **Google Gemini** | Gemini 2.5 Flash | 10 RPM, 250 req/day | Best quality free model, 1M context, beats Sonnet on MMLU (94.8%) |
| **Groq** | Llama 3.3 70B | 30 RPM, 1,000 req/day | Ultra-fast (300+ tokens/sec), highest free throughput |
| **OpenRouter** | DeepSeek R1 :free | 20 RPM, 200+ req/day | 31 free models, DeepSeek R1 scores 96.1% HumanEval |

#### Paid Providers (Optional)

| Provider | Model | Pricing (per 1M tokens) | Free Tier? |
|----------|-------|------------------------|------------|
| **Anthropic** | Claude Sonnet 4.6 | $3.00 in / $15.00 out | No free API tier |
| **OpenAI** | GPT-4o-mini | $0.15 in / $0.60 out | Very limited: 3 RPM, 200 req/day |
| **OpenAI** | GPT-5 Nano | $0.05 in / $0.40 out | Not on free tier |
| **OpenAI** | GPT-4.1 | $2.00 in / $8.00 out | 3 RPM, 200 req/day (free) |

**Note on OpenAI free tier:** OpenAI offers a free tier but it is severely limited (3 RPM, 200 RPD). New accounts no longer receive free credits by default. OpenAI also released open-weight GPT-OSS models (Apache 2.0) but these require self-hosting — they are not served through the OpenAI API. GPT-OSS is available free through Groq and OpenRouter.

---

## Admin Dashboard

### Setup Wizard

A 4-step guided setup shown on first login. Can be skipped and accessed later from the sidebar navigation.

| Step | Screen | Description |
|------|--------|-------------|
| 1 | **Discord Token** | Bot token input with show/hide toggle, test connection button, link to Discord developer portal |
| 2 | **AI Providers** | Free provider cards (Gemini/Groq/OpenRouter) with API key inputs and test buttons. Collapsible paid section (Anthropic/OpenAI). Primary provider selection. |
| 3 | **Bot Settings** | Prefix, max tokens slider (128-4096), system prompt textarea. All pre-filled with defaults. |
| 4 | **Review** | Summary of all settings with edit links per section. "Complete Setup" button saves to DB and .env. |

Wizard state persists in localStorage (Zustand) and server-side (SQLite) so progress is not lost if the browser is closed.

### Dashboard Pages

| Page | Description |
|------|-------------|
| **Overview** | Bot status (online/offline, latency, guild count), active provider card, fallback chain visualization, recent activity feed |
| **Providers** | Grid of 5 provider cards with status indicators, "Test Key" button, "Set as Primary" button, fallback chain display |
| **Settings** | Form editor for all bot configuration (Discord, bot, API keys) with save and reset buttons. Changes apply live without restart. |
| **Conversations** | Channel list with message counts and last activity. Click to view chat-style conversation with provider badges and timestamps. Clear history per channel. |

### Authentication

| Method | Use Case |
|--------|----------|
| **Discord OAuth2** | Primary auth — verifies Discord account and server admin role |
| **Password** | Fallback for local/dev use — set `ADMIN_PASSWORD` in .env |

Protected by next-auth middleware. Unauthenticated users redirect to login.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Bot Runtime** | Python 3.11+ |
| **Discord Library** | discord.py 2.3+ |
| **AI SDK** | openai (OpenAI-compatible — works with all providers) |
| **Backend API** | FastAPI + Uvicorn |
| **Database** | SQLite via aiosqlite |
| **Auth (API)** | JWT (PyJWT) |
| **Dashboard** | Next.js 16 (App Router) + TypeScript |
| **UI Components** | shadcn/ui (23 components) + Tailwind CSS |
| **Auth (Frontend)** | next-auth v5 (Discord OAuth2 + Credentials) |
| **Forms** | React Hook Form + Zod |
| **State** | Zustand (wizard persistence) |
| **Icons** | Lucide React |

---

## Database Schema

```sql
config          — key/value store for all bot settings (synced to .env)
conversations   — channel_id, role, content, provider, created_at
sessions        — JWT session tracking (id, user_id, username, expires_at)
wizard_state    — singleton: completed, current_step, data (JSON)
```

---

## Project Structure

```
sparksage/
├── bot.py                  # Discord bot (DB-backed conversations, bot status)
├── config.py               # Multi-provider config with reload_from_db()
├── providers.py            # Fallback chain, test_provider(), reload_clients()
├── db.py                   # SQLite layer (config, conversations, sessions, wizard)
├── run.py                  # Unified launcher (bot + FastAPI in one process)
├── requirements.txt        # Python dependencies
├── .env.example            # Full environment template
├── .gitignore
├── CHANGELOG.md
├── api/                    # FastAPI backend (19 endpoints)
│   ├── main.py             # App factory with CORS
│   ├── auth.py             # JWT + password utilities
│   ├── deps.py             # Dependency injection
│   └── routes/
│       ├── auth.py         # POST /login, GET /me
│       ├── config.py       # GET/PUT /config
│       ├── providers.py    # GET /providers, POST /test, PUT /primary
│       ├── bot.py          # GET /bot/status
│       ├── conversations.py # GET/DELETE /conversations
│       └── wizard.py       # GET /wizard/status, POST /wizard/complete
├── dashboard/              # Next.js admin dashboard
│   └── src/
│       ├── app/
│       │   ├── (auth)/login/         # Login page
│       │   ├── wizard/               # 4-step setup wizard
│       │   └── dashboard/            # Admin pages
│       │       ├── page.tsx              # Overview
│       │       ├── providers/page.tsx    # Provider management
│       │       ├── settings/page.tsx     # Bot settings
│       │       └── conversations/        # Conversation viewer
│       ├── components/
│       │   ├── ui/                   # 23 shadcn components
│       │   ├── sidebar/              # Dashboard navigation
│       │   ├── wizard/               # Step components
│       │   ├── providers/            # Provider cards, fallback chain
│       │   └── conversations/        # Message list, channel list
│       ├── lib/                      # API client, auth config, utils
│       ├── stores/                   # Zustand wizard store
│       └── types/                    # TypeScript interfaces
├── cogs/                   # Modular command groups (future)
├── utils/                  # Shared utilities (future)
├── docs/
│   └── PRODUCT_DESIGN.md
└── tests/
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | No | Password login, returns JWT |
| GET | `/api/auth/me` | Yes | Current user info |
| GET | `/api/config` | Yes | All config (API keys masked) |
| PUT | `/api/config` | Yes | Update config, reload providers live |
| GET | `/api/providers` | Yes | Provider list with status + fallback chain |
| POST | `/api/providers/test` | Yes | Test a provider's API key |
| PUT | `/api/providers/primary` | Yes | Switch primary provider |
| GET | `/api/bot/status` | Yes | Bot online status, latency, guilds |
| GET | `/api/conversations` | Yes | Channel list with message counts |
| GET | `/api/conversations/{id}` | Yes | Messages for a channel |
| DELETE | `/api/conversations/{id}` | Yes | Clear channel history |
| GET | `/api/wizard/status` | No | Wizard completion status |
| PUT | `/api/wizard/step` | Yes | Save wizard progress |
| POST | `/api/wizard/complete` | Yes | Finalize wizard, save all config |

---

## Running SparkSage

```bash
# Terminal 1 — Bot + API
cd sparksage
pip install -r requirements.txt
python run.py
# Bot connects to Discord, API starts on http://localhost:8000

# Terminal 2 — Dashboard
cd sparksage/dashboard
npm install
npm run dev
# Dashboard starts on http://localhost:3000
```

First visit redirects to the setup wizard. After setup, the admin dashboard is available.

---

## Roadmap

### Phase 1 — MVP
- [x] Bot connects to Discord and responds to mentions
- [x] `/ask` slash command for direct questions
- [x] `/clear` to reset conversation memory
- [x] `/summarize` for thread summarization
- [x] `/provider` to check current AI provider status
- [x] Per-channel conversation history
- [x] Multi-provider fallback (Gemini → Groq → OpenRouter)
- [x] Optional paid provider support (Anthropic, OpenAI)
- [x] Configurable model, tokens, and system prompt
- [x] Response footer showing which provider answered

### Phase 2 — Admin Dashboard (Current)
- [x] SQLite database for persistent config + conversations
- [x] FastAPI backend with 19 REST API endpoints
- [x] JWT authentication (password + Discord OAuth2)
- [x] Next.js + shadcn/ui admin dashboard
- [x] 4-step setup wizard (Discord token, providers, settings, review)
- [x] Setup wizard accessible from sidebar nav if skipped
- [x] Overview page (bot status, providers, activity)
- [x] Provider management (test keys, switch primary, view fallback chain)
- [x] Bot settings editor (live config updates, no restart needed)
- [x] Conversation viewer (per-channel, chat-style, provider badges)
- [x] Unified launcher (`run.py` — bot + API in one process)

### Phase 3 — Core Features
- [ ] Cog-based modular command system
- [ ] Code review with syntax highlighting
- [ ] FAQ auto-detection and response
- [ ] New member onboarding flow
- [ ] Role-based access control for commands

### Phase 4 — Advanced Features
- [ ] Daily digest scheduler
- [ ] Content moderation pipeline
- [ ] Multi-language translation
- [ ] Custom system prompts per channel
- [ ] Per-channel provider override

### Phase 5 — Scale & Polish
- [ ] Analytics and usage tracking
- [ ] Rate limiting and quota management
- [ ] Plugin system for community extensions
- [ ] Provider usage analytics and cost tracking
- [ ] Dashboard responsive design + dark mode
