from __future__ import annotations

import discord
from discord.ext import commands
import os # For path manipulation
import json # For reading plugin manifests
import asyncio # For async operations

import config
import providers
import db as database
from utils.rate_limiter import rate_limiter

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class SparkSageBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.MAX_HISTORY = 20

    async def _load_plugin(self, plugin_name: str, cog_path: str):
        """Helper to load a single plugin cog."""
        try:
            await self.load_extension(cog_path)
            print(f"Successfully loaded plugin: {plugin_name} from {cog_path}")
        except Exception as e:
            print(f"Failed to load plugin {plugin_name} from {cog_path}: {e}")

    async def _unload_plugin(self, plugin_name: str, cog_path: str):
        """Helper to unload a single plugin cog."""
        try:
            await self.unload_extension(cog_path)
            print(f"Successfully unloaded plugin: {plugin_name} from {cog_path}")
        except Exception as e:
            print(f"Failed to unload plugin {plugin_name} from {cog_path}: {e}")

    async def _reload_plugin(self, plugin_name: str, cog_path: str):
        """Helper to reload a single plugin cog."""
        try:
            await self.reload_extension(cog_path)
            print(f"Successfully reloaded plugin: {plugin_name} from {cog_path}")
        except Exception as e:
            print(f"Failed to reload plugin {plugin_name} from {cog_path}: {e}")

    async def get_history(self, channel_id: int) -> list[dict]:
        """Get conversation history for a channel from the database."""
        messages = await database.get_messages(str(channel_id), limit=self.MAX_HISTORY)
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    async def ask_ai(self, channel_id: int, user_name: str, message: str, system_prompt: str = None, message_type: str = None) -> tuple[str, str, int | None, int | None, int | None, int | None, float | None]:
        """Send a message to AI and return (response, provider_name, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost)."""
        # Store user message in DB
        await database.add_message(str(channel_id), "user", user_name, message, type=message_type)

        history = await self.get_history(channel_id)

        # Get channel-specific system prompt if available
        channel_system_prompt = await database.get_channel_prompt(str(channel_id))
        final_system_prompt = system_prompt or channel_system_prompt or config.SYSTEM_PROMPT

        # Get channel-specific provider if available
        channel_provider_override = await database.get_channel_provider(str(channel_id))

        tokens_used = None
        latency_ms = None
        input_tokens = None
        output_tokens = None
        estimated_cost = None
        try:
            response, provider_name, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost = providers.chat(history, final_system_prompt, primary_provider=channel_provider_override)
            # Store assistant response in DB
            await database.add_message(str(channel_id), "assistant", self.user.display_name, response, provider=provider_name, type=message_type)
            
            # Record analytics
            if message_type != "moderation_check": # Don't log moderation checks as user interactions
                await database.add_analytics_event(
                    event_type="mention" if message_type == None else message_type, # Default to mention if type is not set
                    guild_id=str(self.get_channel(channel_id).guild.id) if self.get_channel(channel_id) and self.get_channel(channel_id).guild else None,
                    channel_id=str(channel_id),
                    user_id=None, # For mentions, user_id is often the bot itself responding to an interaction
                    provider=provider_name,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=estimated_cost,
                )
            
            return response, provider_name, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost
        except RuntimeError as e:
            return f"Sorry, all AI providers failed:\n{e}", "none", None, None, None, None, None

    async def setup_hook(self):
        # Load core cogs
        await self.load_extension("cogs.general")
        await self.load_extension("cogs.summarize")
        await self.load_extension("cogs.code_review")
        await self.load_extension("cogs.faq")
        await self.load_extension("cogs.onboarding")
        await self.load_extension("cogs.permissions")
        await self.load_extension("cogs.digest")
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.translate")
        await self.load_extension("cogs.channel_prompts")
        await self.load_extension("cogs.channel_providers")
        await self.load_extension("cogs.plugins") # Load plugin management cog


bot = SparkSageBot(command_prefix=config.BOT_PREFIX, intents=intents)


def get_bot_status() -> dict:
    """Return bot status info for the dashboard API."""
    if bot.is_ready():
        return {
            "online": True,
            "username": str(bot.user),
            "latency_ms": round(bot.latency * 1000, 1),
            "guild_count": len(bot.guilds),
            "guilds": [{"id": str(g.id), "name": g.name, "member_count": g.member_count} for g in bot.guilds],
        }
    return {"online": False, "username": None, "latency_ms": None, "guild_count": 0, "guilds": []}


# --- Events ---


@bot.event
async def on_ready():
    # Initialize database when bot is ready
    await database.init_db()
    await database.sync_env_to_db()

    # Configure the global rate limiter instance
    rate_limiter.configure(
        user_limit=config.RATE_LIMIT_USER,
        guild_limit=config.RATE_LIMIT_GUILD,
        enabled=config.RATE_LIMIT_ENABLED
    )

    available = providers.get_available_providers()
    primary = config.AI_PROVIDER
    provider_info = config.PROVIDERS.get(primary, {})

    print(f"SparkSage is online as {bot.user}")
    print(f"Primary provider: {provider_info.get('name', primary)} ({provider_info.get('model', '?')})")
    print(f"Fallback chain: {' -> '.join(available)}")

    # Load enabled plugins from the database
    enabled_plugins = [p for p in await database.get_all_plugins() if p["enabled"]]
    for plugin in enabled_plugins:
        await bot._load_plugin(plugin["name"], plugin["cog_path"])
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    moderation_cog = bot.get_cog("Moderation")
    if moderation_cog:
        await moderation_cog.check_message_for_moderation(message)
    
    # Respond when mentioned
    if bot.user in message.mentions:
        # Rate limit check
        if message.guild:
            allowed, reason = rate_limiter.check_and_consume(str(message.author.id), str(message.guild.id))
            if not allowed:
                await message.reply(reason, ephemeral=True)
                return
        
        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_content:
            clean_content = "Hello!"

        async with message.channel.typing():
            response, provider_name, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost = await bot.ask_ai( # Use bot.ask_ai
                message.channel.id, message.author.display_name, clean_content, message_type="mention"
            )
        
        # Record analytics for mentions
        if message.guild: # Ensure it's a guild channel
            await database.add_analytics_event(
                event_type="mention",
                guild_id=str(message.guild.id),
                channel_id=str(message.channel.id),
                user_id=str(message.author.id),
                provider=provider_name,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=estimated_cost,
            )

        # Split long responses (Discord 2000 char limit)
        for i in range(0, len(response), 2000):
            await message.reply(response[i : i + 2000])

    await bot.process_commands(message)


# --- Run ---


def main():
    if not config.DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not set. Copy .env.example to .env and fill in your tokens.")
        return

    available = providers.get_available_providers()
    if not available:
        print("Error: No AI providers configured. Add at least one API key to .env")
        print("Free options: GEMINI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY")
        return

    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
