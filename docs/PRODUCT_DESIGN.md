# SparkSage — Product Design Document

## Product Vision

SparkSage is an AI-powered Discord bot that brings world-class AI intelligence into any Discord server — for free. Using a multi-provider architecture with automatic fallback, it serves as an always-available, wise, and versatile assistant that enhances community engagement, streamlines support, and boosts team productivity without any API costs.

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

### Multi-Provider Fallback System

SparkSage uses a unified OpenAI-compatible SDK to connect to multiple AI providers. If the primary provider hits a rate limit or fails, it automatically falls back to the next available free provider.

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│                  │     │                      │     │   FREE FALLBACK CHAIN   │
│  Discord Server  │◄───►│  SparkSage Bot       │────►│                         │
│  (Users)         │     │  (Python)            │     │  1. Google Gemini 2.5   │
│                  │     │                      │     │  2. Groq (Llama 3.3)    │
└─────────────────┘     └──────┬───────────────┘     │  3. OpenRouter (31 free)│
                               │                      │                         │
                        ┌──────┴───────┐              └─────────────────────────┘
                        │              │
                   ┌────▼────┐   ┌─────▼──────────────┐
                   │ Config  │   │ OPTIONAL PAID       │
                   │ (.env)  │   │                     │
                   └─────────┘   │  - Anthropic Claude │
                                 │  - OpenAI GPT       │
                                 └─────────────────────┘
```

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

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.11+ |
| Discord Library | discord.py 2.3+ |
| AI SDK | openai (OpenAI-compatible — works with all providers) |
| Config | python-dotenv |
| Async HTTP | aiohttp |

### Project Structure

```
sparksage/
├── bot.py              # Main bot entry point, Discord events and commands
├── config.py           # Environment config + provider definitions
├── providers.py        # Multi-provider client with automatic fallback
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template (all providers)
├── .gitignore
├── cogs/               # Modular command groups (future)
│   ├── __init__.py
│   ├── support.py      # FAQ and support commands
│   ├── developer.py    # Code review and dev tools
│   ├── moderation.py   # Content moderation
│   └── productivity.py # Writing, translation, brainstorming
├── utils/              # Shared utilities (future)
│   └── __init__.py
├── docs/
│   └── PRODUCT_DESIGN.md
└── tests/
    └── __init__.py
```

---

## Roadmap

### Phase 1 — MVP (Current)
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

### Phase 2 — Core Features
- [ ] Cog-based modular command system
- [ ] Code review with syntax highlighting
- [ ] FAQ auto-detection and response
- [ ] New member onboarding flow
- [ ] Role-based access control for commands

### Phase 3 — Advanced Features
- [ ] Daily digest scheduler
- [ ] Content moderation pipeline
- [ ] Multi-language translation
- [ ] Persistent conversation storage (database)
- [ ] Custom system prompts per channel
- [ ] Per-channel provider override

### Phase 4 — Scale & Polish
- [ ] Dashboard for server admins
- [ ] Analytics and usage tracking
- [ ] Rate limiting and quota management
- [ ] Plugin system for community extensions
- [ ] Provider usage analytics and cost tracking
