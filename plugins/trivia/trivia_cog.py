import discord
from discord.ext import commands
from discord import app_commands

class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="trivia", description="Starts a trivia game or answers a trivia question.")
    async def trivia_command(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Starting a trivia game for {interaction.user.display_name}!")

    def cog_unload(self):
        print("Trivia cog unloaded!")

async def setup(bot):
    await bot.add_cog(Trivia(bot))
