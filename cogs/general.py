# cogs/general.py
from discord.ext import commands
from discord import app_commands
import discord
import config
import providers
import db as database

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask SparkSage a question")
    @app_commands.describe(question="Your question for SparkSage")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        response, provider_name = await self.bot.ask_ai(
            interaction.channel_id, interaction.user.display_name, question
        )
        provider_label = config.PROVIDERS.get(provider_name, {}).get("name", provider_name)
        footer = f"-# Powered by {provider_label}"

        for i in range(0, len(response), 1900):
            chunk = response[i : i + 1900]
            if i + 1900 >= len(response):
                chunk += footer
            await interaction.followup.send(chunk)

    @app_commands.command(name="clear", description="Clear SparkSage's conversation memory for this channel")
    async def clear(self, interaction: discord.Interaction):
        await database.clear_messages(str(interaction.channel_id))
        await interaction.response.send_message("Conversation history cleared!")

    @app_commands.command(name="provider", description="Show which AI provider SparkSage is currently using")
    async def provider(self, interaction: discord.Interaction):
        primary = config.AI_PROVIDER
        provider_info = config.PROVIDERS.get(primary, {})
        available = providers.get_available_providers()

        msg = f"""**Current Provider:** {provider_info.get('name', primary)}
**Model:** `{provider_info.get('model', '?')}`
**Free:** {'Yes' if provider_info.get('free') else 'No (paid)'}
**Fallback Chain:** {' -> '.join(available)}"""
        await interaction.response.send_message(msg)

async def setup(bot):
    await bot.add_cog(General(bot))