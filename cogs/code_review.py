# cogs/code_review.py
from discord.ext import commands
from discord import app_commands
import discord
import db as database # Import database module
import config
import providers # This import is not strictly needed here as ask_ai uses providers internally, but good for clarity
from utils.checks import has_permissions
from utils.rate_limiter import rate_limiter # Import rate_limiter

class CodeReview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="review", description="Analyze code for bugs, style, performance, and security.")
    @app_commands.describe(
        code="The code snippet to review.",
        language="Optional: Programming language hint (e.g., python, javascript)."
    )
    @has_permissions()
    async def review(self, interaction: discord.Interaction, code: str, language: str = None):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        
        await interaction.response.defer()

        # Specialized system prompt for code review
        system_prompt = """You are a senior code reviewer. Analyze the code for:
        1. Bugs and potential errors
        2. Style and best practices
        3. Performance improvements
        4. Security concerns
        Respond with markdown formatting using code blocks."""

        user_message = f"""Please review the following code snippet. The language is {language or 'auto-detected'}:
```{"\n" + language if language else ""}{code}
```"""

        try:
            print(f"DEBUG: Calling ask_ai for review command. Channel: {interaction.channel_id}, User: {interaction.user.display_name}")
            response, provider_name, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost = await self.bot.ask_ai(
                interaction.channel_id,
                interaction.user.display_name,
                user_message,
                system_prompt=system_prompt, # Pass specialized system prompt
                message_type="code_review" # Tag this as a code review
            )
            print(f"DEBUG: ask_ai returned. Response starts with: {response[:50]}..., Provider: {provider_name}")

            if response.startswith("Sorry, all AI providers failed:"):
                await interaction.followup.send(response, ephemeral=True)
                return

            # Record analytics for the 'review' command
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
            
            # Split long responses (Discord 2000 char limit)
            for i in range(0, len(response), 2000):
                await interaction.followup.send(response[i : i + 2000])

        except Exception as e:
            print(f"ERROR: Exception during /review command: {e}")
            await interaction.followup.send(f"An unexpected error occurred during code review: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CodeReview(bot))