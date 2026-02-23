import discord
from discord.ext import commands
from discord import app_commands # Import app_commands
import config
from utils.rate_limiter import rate_limiter # Import rate_limiter

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="translate", description="Translate text to a target language.")
    @app_commands.describe(text="The text to translate", target_language="The language to translate to (e.g., 'French', 'es', 'Japanese')")
    async def translate_command(self, interaction: discord.Interaction, text: str, target_language: str):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        
        await interaction.response.defer()

        # Use the existing AI provider for translation
        translation_prompt = f"""Translate the following text to {target_language}. Respond only with the translated text, without any additional conversational filler.

Text to translate: "{text}"
"""

        try:
            translated_text, provider_name, tokens_used, latency_ms, input_tokens, output_tokens, estimated_cost = await self.bot.ask_ai(
                channel_id=interaction.channel_id,
                user_name=interaction.user.display_name,
                message=translation_prompt,
                system_prompt="You are a helpful translation assistant. Provide only the translation.",
                message_type="translation"
            )
            # Record analytics for the 'translate' command
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
            await interaction.followup.send(f"""**Original ({text}) translated to {target_language}:**
{translated_text}""")
        except Exception as e:
            await interaction.followup.send(f"An error occurred during translation: {e}")

async def setup(bot):
    await bot.add_cog(Translate(bot))