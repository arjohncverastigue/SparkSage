# cogs/general.py
from discord.ext import commands
from discord import app_commands
import discord
import config
import providers
import db as database
from utils.checks import has_permissions
from utils.rate_limiter import rate_limiter # Import rate_limiter

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask SparkSage a question")
    @app_commands.describe(question="Your question for SparkSage")
    @has_permissions()
    async def ask(self, interaction: discord.Interaction, question: str):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        
        await interaction.response.defer()
        response, provider_name, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost = await self.bot.ask_ai(
            interaction.channel_id, interaction.user.display_name, question
        )
        provider_label = config.PROVIDERS.get(provider_name, {}).get("name", provider_name)
        footer = f"-# Powered by {provider_label}"

        # Record analytics for the 'ask' command
        if interaction.guild:
            await database.add_analytics_event(
                event_type="command",
                guild_id=str(interaction.guild.id),
                channel_id=str(interaction.channel_id),
                user_id=str(interaction.user.id),
                provider=provider_name,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=estimated_cost
            )

        for i in range(0, len(response), 1900):
            chunk = response[i : i + 1900]
            if i + 1900 >= len(response):
                chunk += footer
            await interaction.followup.send(chunk)

    @app_commands.command(name="clear", description="Clear SparkSage's conversation memory for this channel")
    @has_permissions()
    async def clear(self, interaction: discord.Interaction):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        await database.clear_messages(str(interaction.channel_id))
        # Record analytics for the 'clear' command
        if interaction.guild:
            await database.add_analytics_event(
                event_type="command",
                guild_id=str(interaction.guild.id),
                channel_id=str(interaction.channel_id),
                user_id=str(interaction.user.id),
                provider=None, # No AI provider involved
                tokens_used=None,
                latency_ms=None
            )
        await interaction.response.send_message("Conversation history cleared!")

    @app_commands.command(name="provider", description="Show which AI provider SparkSage is currently using")
    @has_permissions()
    async def provider(self, interaction: discord.Interaction):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
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