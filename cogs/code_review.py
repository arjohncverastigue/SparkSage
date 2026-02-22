# cogs/code_review.py
from discord.ext import commands
from discord import app_commands
import discord
import config
import providers # This import is not strictly needed here as ask_ai uses providers internally, but good for clarity

class CodeReview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="review", description="Analyze code for bugs, style, performance, and security.")
    @app_commands.describe(
        code="The code snippet to review.",
        language="Optional: Programming language hint (e.g., python, javascript)."
    )
    async def review(self, interaction: discord.Interaction, code: str, language: str = None):
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

        response, provider_name = await self.bot.ask_ai(
            interaction.channel_id,
            interaction.user.display_name,
            user_message,
            system_prompt=system_prompt, # Pass specialized system prompt
            message_type="code_review" # Tag this as a code review
        )
        await interaction.followup.send(response)

async def setup(bot):
    await bot.add_cog(CodeReview(bot))