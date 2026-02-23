import discord
from discord.ext import commands
from discord import app_commands
import db as database
import config
import providers

class ChannelProviders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    channel_provider_group = app_commands.Group(name="channel-provider", description="Manage channel-specific AI providers.")

    @channel_provider_group.command(name="set", description="Set a custom AI provider for this channel.")
    @app_commands.describe(provider_name="The name of the AI provider to use for this channel.")
    @app_commands.autocomplete(provider_name=providers.provider_autocomplete)
    @app_commands.default_permissions(manage_channels=True)
    async def channel_provider_set(self, interaction: discord.Interaction, provider_name: str):
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if provider_name not in config.PROVIDERS:
            await interaction.followup.send(f"Provider '{provider_name}' not recognized. Available providers: {', '.join(config.PROVIDERS.keys())}", ephemeral=True)
            return
        
        if not config.PROVIDERS[provider_name].get("api_key"):
            await interaction.followup.send(f"Provider '{provider_name}' is not configured (missing API key).", ephemeral=True)
            return

        try:
            await database.set_channel_provider(
                channel_id=str(interaction.channel_id),
                guild_id=str(interaction.guild_id),
                provider_name=provider_name
            )
            await interaction.followup.send(f"Successfully set custom AI provider for this channel to **{provider_name}**.")
        except Exception as e:
            await interaction.followup.send(f"Failed to set channel provider: {e}", ephemeral=True)

    @channel_provider_group.command(name="reset", description="Reset this channel's custom AI provider to the global primary.")
    @app_commands.default_permissions(manage_channels=True)
    async def channel_provider_reset(self, interaction: discord.Interaction):
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            await database.delete_channel_provider(channel_id=str(interaction.channel_id))
            await interaction.followup.send("Successfully reset custom AI provider for this channel. It will now use the global primary provider.")
        except Exception as e:
            await interaction.followup.send(f"Failed to reset channel provider: {e}", ephemeral=True)

    @channel_provider_group.command(name="get", description="Get the current custom AI provider for this channel.")
    @app_commands.default_permissions(manage_channels=True)
    async def channel_provider_get(self, interaction: discord.Interaction):
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            current_provider = await database.get_channel_provider(channel_id=str(interaction.channel_id))
            if current_provider:
                await interaction.followup.send(f"Current custom AI provider for this channel: **{current_provider}**.")
            else:
                await interaction.followup.send("This channel does not have a custom AI provider set. It uses the global primary provider.")
        except Exception as e:
            await interaction.followup.send(f"Failed to retrieve channel provider: {e}", ephemeral=True)

    def cog_load(self):
        # self.bot.tree.add_command(self.channel_provider_group) # Handled automatically
        pass

    def cog_unload(self):
        self.bot.tree.remove_command(self.channel_provider_group)

async def setup(bot):
    await bot.add_cog(ChannelProviders(bot))