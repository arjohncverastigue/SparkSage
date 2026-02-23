# cogs/summarize.py
from discord.ext import commands
from discord import app_commands
import discord
import config
import providers
import db as database
from utils.checks import has_permissions
from utils.rate_limiter import rate_limiter # Import rate_limiter

class Summarize(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="summarize", description="Summarize the recent conversation in this channel")
    @has_permissions()
    async def summarize(self, interaction: discord.Interaction):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        
        await interaction.response.defer()
        history = await self.bot.get_history(interaction.channel_id)
        if not history:
            await interaction.followup.send("No conversation history to summarize.")
            return

        summary_prompt = "Please summarize the key points from this conversation so far in a concise bullet-point format."
        response, provider_name, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost = await self.bot.ask_ai(
            interaction.channel_id, interaction.user.display_name, summary_prompt, message_type="summarize"
        )
        
        # Record analytics for the 'summarize' command
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
        await interaction.followup.send(f"""**Conversation Summary:**
{response}""")

async def setup(bot):
    await bot.add_cog(Summarize(bot))