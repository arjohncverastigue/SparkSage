from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands
import config
import providers
import db as database

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents)

MAX_HISTORY = 20


async def get_history(channel_id: int) -> list[dict]:
    """Get conversation history for a channel from the database."""
    messages = await database.get_messages(str(channel_id), limit=MAX_HISTORY)
    return [{"role": m["role"], "content": m["content"]} for m in messages]


async def ask_ai(channel_id: int, user_name: str, message: str) -> tuple[str, str]:
    """Send a message to AI and return (response, provider_name)."""
    # Store user message in DB
    await database.add_message(str(channel_id), "user", f"{user_name}: {message}")

    history = await get_history(channel_id)

    try:
        response, provider_name = providers.chat(history, config.SYSTEM_PROMPT)
        # Store assistant response in DB
        await database.add_message(str(channel_id), "assistant", response, provider=provider_name)
        return response, provider_name
    except RuntimeError as e:
        return f"Sorry, all AI providers failed:\n{e}", "none"


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
            response, provider_name = await ask_ai(
                message.channel.id, message.author.display_name, clean_content
            )

        # Split long responses (Discord 2000 char limit)
        for i in range(0, len(response), 2000):
            await message.reply(response[i : i + 2000])

    await bot.process_commands(message)


# --- Slash Commands ---


@bot.tree.command(name="ask", description="Ask SparkSage a question")
@app_commands.describe(question="Your question for SparkSage")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    response, provider_name = await ask_ai(
        interaction.channel_id, interaction.user.display_name, question
    )
    provider_label = config.PROVIDERS.get(provider_name, {}).get("name", provider_name)
    footer = f"\n-# Powered by {provider_label}"

    for i in range(0, len(response), 1900):
        chunk = response[i : i + 1900]
        if i + 1900 >= len(response):
            chunk += footer
        await interaction.followup.send(chunk)


@bot.tree.command(name="clear", description="Clear SparkSage's conversation memory for this channel")
async def clear(interaction: discord.Interaction):
    await database.clear_messages(str(interaction.channel_id))
    await interaction.response.send_message("Conversation history cleared!")


@bot.tree.command(name="summarize", description="Summarize the recent conversation in this channel")
async def summarize(interaction: discord.Interaction):
    await interaction.response.defer()
    history = await get_history(interaction.channel_id)
    if not history:
        await interaction.followup.send("No conversation history to summarize.")
        return

    summary_prompt = "Please summarize the key points from this conversation so far in a concise bullet-point format."
    response, provider_name = await ask_ai(
        interaction.channel_id, interaction.user.display_name, summary_prompt
    )
    await interaction.followup.send(f"**Conversation Summary:**\n{response}")


@bot.tree.command(name="provider", description="Show which AI provider SparkSage is currently using")
async def provider(interaction: discord.Interaction):
    primary = config.AI_PROVIDER
    provider_info = config.PROVIDERS.get(primary, {})
    available = providers.get_available_providers()

    msg = f"**Current Provider:** {provider_info.get('name', primary)}\n"
    msg += f"**Model:** `{provider_info.get('model', '?')}`\n"
    msg += f"**Free:** {'Yes' if provider_info.get('free') else 'No (paid)'}\n"
    msg += f"**Fallback Chain:** {' -> '.join(available)}"
    await interaction.response.send_message(msg)


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
