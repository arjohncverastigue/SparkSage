import discord
from discord.ext import commands
from discord import app_commands # Import app_commands
import config

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="translate", description="Translate text to a target language.")
    @app_commands.describe(text="The text to translate", target_language="The language to translate to (e.g., 'French', 'es', 'Japanese')")
    async def translate_command(self, interaction: discord.Interaction, text: str, target_language: str):
        await interaction.response.defer()

        # Use the existing AI provider for translation
        translation_prompt = f"""Translate the following text to {target_language}. Respond only with the translated text, without any additional conversational filler.

Text to translate: "{text}"
"""

        try:
            translated_text, _ = await self.bot.ask_ai(
                channel_id=interaction.channel_id,
                user_name=interaction.user.display_name,
                message=translation_prompt,
                system_prompt="You are a helpful translation assistant. Provide only the translation.",
                message_type="translation"
            )
            await interaction.followup.send(f"""**Original ({text}) translated to {target_language}:**
{translated_text}""")
        except Exception as e:
            await interaction.followup.send(f"An error occurred during translation: {e}")

async def setup(bot):
    await bot.add_cog(Translate(bot))