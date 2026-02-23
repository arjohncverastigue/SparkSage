from __future__ import annotations

import os
import json
import aiosqlite

DATABASE_PATH = os.getenv("DATABASE_PATH", "sparksage.db")

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Return the shared database connection, creating it if needed."""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DATABASE_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def init_db():
    """Create tables if they don't exist."""
    db = await get_db()
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT    NOT NULL,
            role       TEXT    NOT NULL,
            author_name TEXT,
            content    TEXT    NOT NULL,
            provider   TEXT,
            type       TEXT,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_conv_channel ON conversations(channel_id);
        
        -- Add 'author_name' column if it doesn't exist (for existing databases)
        PRAGMA table_info(conversations); -- Get table info to check for column existence

        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS wizard_state (
            id           INTEGER PRIMARY KEY CHECK (id = 1),
            completed    INTEGER NOT NULL DEFAULT 0,
            current_step INTEGER NOT NULL DEFAULT 0,
            data         TEXT    NOT NULL DEFAULT '{}'
        );

        INSERT OR IGNORE INTO wizard_state (id) VALUES (1);

        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            match_keywords TEXT NOT NULL,  -- comma-separated keywords
            times_used INTEGER DEFAULT 0,
            created_by TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS command_permissions (
            command_name TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            PRIMARY KEY (command_name, guild_id, role_id)
        );

        CREATE TABLE IF NOT EXISTS moderation_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id   TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            author_id  TEXT NOT NULL,
            reason     TEXT NOT NULL,
            severity   TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS channel_prompts (
            channel_id TEXT PRIMARY KEY,
            guild_id TEXT NOT NULL,
            system_prompt TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS channel_providers (
            channel_id TEXT PRIMARY KEY,
            guild_id TEXT NOT NULL,
            provider_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,     -- 'command', 'mention', 'faq', 'moderation', 'translate'
            guild_id TEXT,
            channel_id TEXT,
            user_id TEXT,
            provider TEXT,
            tokens_used INTEGER,
            latency_ms INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            estimated_cost REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS plugins (
            name TEXT PRIMARY KEY,
            version TEXT NOT NULL,
            author TEXT,
            description TEXT,
            cog_path TEXT NOT NULL, -- Path to the cog file (e.g., "plugins.my_plugin.main")
            manifest_path TEXT NOT NULL, -- Path to the manifest file
            enabled BOOLEAN NOT NULL DEFAULT FALSE,
            installed_at TEXT DEFAULT (datetime('now'))
        );
        """
    )
    cursor = await db.execute("PRAGMA table_info(conversations)")
    columns = [row[1] for row in await cursor.fetchall()]
    if "type" not in columns:
        await db.execute("ALTER TABLE conversations ADD COLUMN type TEXT")
    if "author_name" not in columns:
        await db.execute("ALTER TABLE conversations ADD COLUMN author_name TEXT")

    await db.commit()


# --- Config helpers ---


async def get_config(key: str, default: str | None = None) -> str | None:
    """Get a config value from the database."""
    db = await get_db()
    cursor = await db.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = await cursor.fetchone()
    return row["value"] if row else default


async def get_all_config() -> dict[str, str]:
    """Return all config key-value pairs."""
    db = await get_db()
    cursor = await db.execute("SELECT key, value FROM config")
    rows = await cursor.fetchall()
    return {row["key"]: row["value"] for row in rows}


async def set_config(key: str, value: str):
    """Set a config value in the database."""
    db = await get_db()
    await db.execute(
        "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    await db.commit()


async def set_config_bulk(data: dict[str, str]):
    """Set multiple config values at once."""
    db = await get_db()
    await db.executemany(
        "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        list(data.items()),
    )
    await db.commit()


async def sync_env_to_db():
    """Seed the DB config table from current environment / .env values."""
    import config as cfg

    env_keys = {
        "DISCORD_TOKEN": cfg.DISCORD_TOKEN or "",
        "AI_PROVIDER": cfg.AI_PROVIDER,
        "GEMINI_API_KEY": cfg.GEMINI_API_KEY or "",
        "GEMINI_MODEL": cfg.GEMINI_MODEL,
        "GROQ_API_KEY": cfg.GROQ_API_KEY or "",
        "GROQ_MODEL": cfg.GROQ_MODEL,
        "OPENROUTER_API_KEY": cfg.OPENROUTER_API_KEY or "",
        "OPENROUTER_MODEL": cfg.OPENROUTER_MODEL,
        "ANTHROPIC_API_KEY": cfg.ANTHROPIC_API_KEY or "",
        "ANTHROPIC_MODEL": cfg.ANTHROPIC_MODEL,
        "OPENAI_API_KEY": cfg.OPENAI_API_KEY or "",
        "OPENAI_MODEL": cfg.OPENAI_MODEL,
        "BOT_PREFIX": cfg.BOT_PREFIX,
        "MAX_TOKENS": str(cfg.MAX_TOKENS),
        "SYSTEM_PROMPT": cfg.SYSTEM_PROMPT,
    }
    # Only insert keys that don't already exist in DB (don't overwrite user edits)
    db = await get_db()
    for key, value in env_keys.items():
        await db.execute(
            "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
    await db.commit()


async def sync_db_to_env():
    """Write DB config back to the .env file."""
    from dotenv import dotenv_values, set_key

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    all_config = await get_all_config()

    for key, value in all_config.items():
        set_key(env_path, key, value)


# --- Conversation helpers ---


async def add_message(channel_id: str, role: str, author_name: str | None, content: str, provider: str | None = None, type: str | None = None):
    """Add a message to conversation history."""
    db = await get_db()
    await db.execute(
        "INSERT INTO conversations (channel_id, role, author_name, content, provider, type) VALUES (?, ?, ?, ?, ?, ?)",
        (channel_id, role, author_name, content, provider, type),
    )
    await db.commit()


async def get_messages(channel_id: str, limit: int = 20) -> list[dict]:
    """Get recent messages for a channel."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT role, content, provider, created_at FROM conversations WHERE channel_id = ? ORDER BY id DESC LIMIT ?",
        (channel_id, limit),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in reversed(rows)]


async def get_messages_since(channel_id: str, since_datetime: datetime.datetime) -> list[dict]:
    """Get messages for a channel since a specific datetime."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT role, author_name, content, provider, created_at FROM conversations WHERE channel_id = ? AND created_at >= ? ORDER BY created_at ASC",
        (channel_id, since_datetime.isoformat()),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]



async def clear_messages(channel_id: str):
    """Delete all messages for a channel."""
    db = await get_db()
    await db.execute("DELETE FROM conversations WHERE channel_id = ?", (channel_id,))
    await db.commit()


async def list_channels() -> list[dict]:
    """List all channels with message counts."""
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT channel_id, COUNT(*) as message_count, MAX(created_at) as last_active
        FROM conversations
        GROUP BY channel_id
        ORDER BY last_active DESC
        """
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- Wizard helpers ---


async def get_wizard_state() -> dict:
    """Get the wizard state."""
    db = await get_db()
    cursor = await db.execute("SELECT completed, current_step, data FROM wizard_state WHERE id = 1")
    row = await cursor.fetchone()
    return {
        "completed": bool(row["completed"]),
        "current_step": row["current_step"],
        "data": json.loads(row["data"]),
    }


async def set_wizard_state(completed: bool | None = None, current_step: int | None = None, data: dict | None = None):
    """Update wizard state fields."""
    db = await get_db()
    updates = []
    params = []
    if completed is not None:
        updates.append("completed = ?")
        params.append(int(completed))
    if current_step is not None:
        updates.append("current_step = ?")
        params.append(current_step)
    if data is not None:
        updates.append("data = ?")
        params.append(json.dumps(data))
    if updates:
        await db.execute(f"UPDATE wizard_state SET {', '.join(updates)} WHERE id = 1", params)
        await db.commit()


# --- Session helpers ---


async def create_session(token: str, user_id: str, expires_at: str):
    """Store a session token."""
    db = await get_db()
    await db.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at),
    )
    await db.commit()


async def validate_session(token: str) -> dict | None:
    """Validate a session token, return session data or None."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT user_id, expires_at FROM sessions WHERE token = ? AND expires_at > datetime('now')",
        (token,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def delete_session(token: str):
    """Delete a session."""
    db = await get_db()
    await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    await db.commit()


# --- FAQ helpers ---

async def add_faq(guild_id: str, question: str, answer: str, match_keywords: str, created_by: str | None = None) -> int:
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO faqs (guild_id, question, answer, match_keywords, created_by) VALUES (?, ?, ?, ?, ?)",
        (guild_id, question, answer, match_keywords, created_by),
    )
    await db.commit()
    return cursor.lastrowid

async def get_faqs(guild_id: str | None = None) -> list[dict]:
    db = await get_db()
    if guild_id:
        cursor = await db.execute(
            "SELECT id, guild_id, question, answer, match_keywords, times_used, created_by, created_at FROM faqs WHERE guild_id = ?",
            (guild_id,),
        )
    else:
        cursor = await db.execute(
            "SELECT id, guild_id, question, answer, match_keywords, times_used, created_by, created_at FROM faqs",
        )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]

async def get_faq_by_id(faq_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, guild_id, question, answer, match_keywords, times_used, created_by, created_at FROM faqs WHERE id = ?",
        (faq_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None

async def delete_faq(faq_id: int):
    db = await get_db()
    await db.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    await db.commit()

async def increment_faq_usage(faq_id: int):
    db = await get_db()
    await db.execute("UPDATE faqs SET times_used = times_used + 1 WHERE id = ?", (faq_id,))
    await db.commit()


# --- Command Permissions helpers ---

async def add_command_permission(command_name: str, guild_id: str, role_id: str):
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO command_permissions (command_name, guild_id, role_id) VALUES (?, ?, ?)",
        (command_name, guild_id, role_id),
    )
    await db.commit()

async def remove_command_permission(command_name: str, guild_id: str, role_id: str):
    db = await get_db()
    await db.execute(
        "DELETE FROM command_permissions WHERE command_name = ? AND guild_id = ? AND role_id = ?",
        (command_name, guild_id, role_id),
    )
    await db.commit()

async def get_command_permissions(command_name: str, guild_id: str) -> list[str]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT role_id FROM command_permissions WHERE command_name = ? AND guild_id = ?",
        (command_name, guild_id),
    )
    rows = await cursor.fetchall()
    return [row["role_id"] for row in rows]

async def get_all_command_permissions(guild_id: str | None = None) -> list[dict]:
    db = await get_db()
    if guild_id:
        cursor = await db.execute(
            "SELECT command_name, guild_id, role_id FROM command_permissions WHERE guild_id = ?",
            (guild_id,),
        )
    else:
        cursor = await db.execute(
            "SELECT command_name, guild_id, role_id FROM command_permissions",
        )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- Moderation helpers ---

async def add_moderation_log(guild_id: str, channel_id: str, message_id: str, author_id: str, reason: str, severity: str):
    """Add an entry to the moderation log."""
    db = await get_db()
    await db.execute(
        "INSERT INTO moderation_logs (guild_id, channel_id, message_id, author_id, reason, severity) VALUES (?, ?, ?, ?, ?, ?)",
        (guild_id, channel_id, message_id, author_id, reason, severity),
    )
    await db.commit()


# --- Channel Prompt helpers ---

async def set_channel_prompt(channel_id: str, guild_id: str, system_prompt: str):
    """Set a custom system prompt for a channel."""
    db = await get_db()
    await db.execute(
        "INSERT INTO channel_prompts (channel_id, guild_id, system_prompt) VALUES (?, ?, ?) ON CONFLICT(channel_id) DO UPDATE SET system_prompt = excluded.system_prompt",
        (channel_id, guild_id, system_prompt),
    )
    await db.commit()

async def get_channel_prompt(channel_id: str) -> str | None:
    """Get the custom system prompt for a channel."""
    db = await get_db()
    cursor = await db.execute("SELECT system_prompt FROM channel_prompts WHERE channel_id = ?", (channel_id,))
    row = await cursor.fetchone()
    return row["system_prompt"] if row else None

async def delete_channel_prompt(channel_id: str):
    """Delete the custom system prompt for a channel."""
    db = await get_db()
    await db.execute("DELETE FROM channel_prompts WHERE channel_id = ?", (channel_id,))
    await db.commit()

async def get_all_channel_prompts(guild_id: str | None = None) -> list[dict]:
    """Get all custom system prompts for a guild, or all prompts if guild_id is None."""
    db = await get_db()
    if guild_id:
        cursor = await db.execute(
            "SELECT channel_id, guild_id, system_prompt FROM channel_prompts WHERE guild_id = ?",
            (guild_id,),
        )
    else:
        cursor = await db.execute("SELECT channel_id, guild_id, system_prompt FROM channel_prompts")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- Channel Provider helpers ---

async def set_channel_provider(channel_id: str, guild_id: str, provider_name: str):
    """Set a custom AI provider for a channel."""
    db = await get_db()
    await db.execute(
        "INSERT INTO channel_providers (channel_id, guild_id, provider_name) VALUES (?, ?, ?) ON CONFLICT(channel_id) DO UPDATE SET provider_name = excluded.provider_name",
        (channel_id, guild_id, provider_name),
    )
    await db.commit()

async def get_channel_provider(channel_id: str) -> str | None:
    """Get the custom AI provider for a channel."""
    db = await get_db()
    cursor = await db.execute("SELECT provider_name FROM channel_providers WHERE channel_id = ?", (channel_id,))
    row = await cursor.fetchone()
    return row["provider_name"] if row else None

async def delete_channel_provider(channel_id: str):
    """Delete the custom AI provider for a channel."""
    db = await get_db()
    await db.execute("DELETE FROM channel_providers WHERE channel_id = ?", (channel_id,))
    await db.commit()

async def get_all_channel_providers(guild_id: str | None = None) -> list[dict]:
    """Get all custom AI providers for a guild, or all providers if guild_id is None."""
    db = await get_db()
    if guild_id:
        cursor = await db.execute(
            "SELECT channel_id, guild_id, provider_name FROM channel_providers WHERE guild_id = ?",
            (guild_id,),
        )
    else:
        cursor = await db.execute("SELECT channel_id, guild_id, provider_name FROM channel_providers")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


# --- Analytics helpers ---

async def add_analytics_event(
    event_type: str,
    guild_id: str | None = None,
    channel_id: str | None = None,
    user_id: str | None = None,
    provider: str | None = None,
    tokens_used: int | None = None,
    latency_ms: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    estimated_cost: float | None = None,
):
    """Add an analytics event to the database."""
    db = await get_db()
    await db.execute(
        "INSERT INTO analytics (event_type, guild_id, channel_id, user_id, provider, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (event_type, guild_id, channel_id, user_id, provider, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost),
    )
    await db.commit()


# --- Plugin helpers ---

async def add_plugin(
    name: str,
    version: str,
    author: str,
    description: str,
    cog_path: str,
    manifest_path: str,
):
    """Add a new plugin to the database."""
    db = await get_db()
    await db.execute(
        "INSERT INTO plugins (name, version, author, description, cog_path, manifest_path) VALUES (?, ?, ?, ?, ?, ?)",
        (name, version, author, description, cog_path, manifest_path),
    )
    await db.commit()

async def get_plugin(name: str) -> dict | None:
    """Get a plugin's information by name."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM plugins WHERE name = ?", (name,))
    row = await cursor.fetchone()
    return dict(row) if row else None

async def get_all_plugins() -> list[dict]:
    """Get all registered plugins."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM plugins")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]

async def set_plugin_enabled(name: str, enabled: bool):
    """Set the enabled status of a plugin."""
    db = await get_db()
    await db.execute("UPDATE plugins SET enabled = ? WHERE name = ?", (enabled, name))
    await db.commit()

async def delete_plugin(name: str):
    """Delete a plugin from the database."""
    db = await get_db()
    await db.execute("DELETE FROM plugins WHERE name = ?", (name,))
    await db.commit()


async def close_db():
    """Close the database connection."""
    global _db
    if _db:
        await _db.close()
        _db = None
