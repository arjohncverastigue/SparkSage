from __future__ import annotations

import discord
from discord.ext import commands

import config
import providers
import db as database

intents = discord.Intents.default()
intents.message_content = True

class SparkSageBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.MAX_HISTORY = 20

    async def get_history(self, channel_id: int) -> list[dict]:
        """Get conversation history for a channel from the database."""
        messages = await database.get_messages(str(channel_id), limit=self.MAX_HISTORY)
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    async def ask_ai(self, channel_id: int, user_name: str, message: str, system_prompt: str = None, message_type: str = None) -> tuple[str, str]:
        """Send a message to AI and return (response, provider_name)."""
        # Store user message in DB
        await database.add_message(str(channel_id), "user", f"{user_name}: {message}", type=message_type)

        history = await self.get_history(channel_id)

        try:
            response, provider_name = providers.chat(history, system_prompt or config.SYSTEM_PROMPT)
            # Store assistant response in DB
            await database.add_message(str(channel_id), "assistant", response, provider=provider_name, type=message_type)
            return response, provider_name
        except RuntimeError as e:
            return f"Sorry, all AI providers failed:\n{e}", "none"

    async def setup_hook(self):
        # Load cogs here
        await self.load_extension("cogs.general")
        await self.load_extension("cogs.summarize")
        await self.load_extension("cogs.code_review")
        await self.load_extension("cogs.faq")
        await self.load_extension("cogs.onboarding")


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

    available = providers.get_available_providers()
    primary = config.AI_PROVIDER
    provider_info = config.PROVIDERS.get(primary, {})

    print(f"SparkSage is online as {bot.user}")
    print(f"Primary provider: {provider_info.get('name', primary)} ({provider_info.get('model', '?')})")
    print(f"Fallback chain: {' -> '.join(available)}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # Respond when mentioned
    if bot.user in message.mentions:
        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_content:
            clean_content = "Hello!"

        async with message.channel.typing():
            response, provider_name = await bot.ask_ai( # Use bot.ask_ai
                message.channel.id, message.author.display_name, clean_content
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
