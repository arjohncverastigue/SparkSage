import discord
from discord.ext import commands
from discord import app_commands
import db as database
import config
from utils.rate_limiter import rate_limiter # Import rate_limiter
import os
import json

class Plugins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    plugin_group = app_commands.Group(name="plugin", description="Manage bot plugins and extensions.")

    async def plugin_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        plugins = await database.get_all_plugins()
        choices = []
        for plugin in plugins:
            if current.lower() in plugin["name"].lower():
                choices.append(app_commands.Choice(name=plugin["name"], value=plugin["name"]))
        return choices

    @plugin_group.command(name="list", description="List all installed plugins and their status.")
    @app_commands.default_permissions(manage_guild=True)
    async def plugin_list(self, interaction: discord.Interaction):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        
        await interaction.response.defer(ephemeral=True)

        plugins = await database.get_all_plugins()
        if not plugins:
            await interaction.followup.send("No plugins installed.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Installed Plugins",
            color=discord.Color.blue()
        )
        for plugin in plugins:
            status = "🟢 Enabled" if plugin["enabled"] else "🔴 Disabled"
            embed.add_field(
                name=f"{plugin['name']} (v{plugin['version']}) {status}",
                value=f"""Author: {plugin['author']}
Description: {plugin['description']}""",
                inline=False
            )
        await interaction.followup.send(embed=embed)
        
        # Record analytics
        if interaction.guild:
            await database.add_analytics_event(
                event_type="command",
                guild_id=str(interaction.guild.id),
                channel_id=str(interaction.channel_id),
                user_id=str(interaction.user.id),
                provider=None,
                tokens_used=None,
                latency_ms=None
            )

    @plugin_group.command(name="enable", description="Enable an installed plugin.")
    @app_commands.describe(plugin_name="The name of the plugin to enable.")
    @app_commands.autocomplete(plugin_name=plugin_autocomplete)
    @app_commands.default_permissions(manage_guild=True)
    async def plugin_enable(self, interaction: discord.Interaction, plugin_name: str):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)

        plugin = await database.get_plugin(plugin_name)
        if not plugin:
            await interaction.followup.send(f"Plugin '{plugin_name}' not found.", ephemeral=True)
            return

        if plugin["enabled"]:
            await interaction.followup.send(f"Plugin '{plugin_name}' is already enabled.", ephemeral=True)
            return

        try:
            await self.bot._load_plugin(plugin["name"], plugin["cog_path"])
            await database.set_plugin_enabled(plugin["name"], True)
            await interaction.followup.send(f"Plugin '{plugin_name}' enabled successfully!")
            # Record analytics
            if interaction.guild:
                await database.add_analytics_event(
                    event_type="command",
                    guild_id=str(interaction.guild.id),
                    channel_id=str(interaction.channel_id),
                    user_id=str(interaction.user.id),
                    provider=None,
                    tokens_used=None,
                    latency_ms=None
                )
        except Exception as e:
            await interaction.followup.send(f"Failed to enable plugin '{plugin_name}': {e}", ephemeral=True)

    @plugin_group.command(name="disable", description="Disable an installed plugin.")
    @app_commands.describe(plugin_name="The name of the plugin to disable.")
    @app_commands.autocomplete(plugin_name=plugin_autocomplete)
    @app_commands.default_permissions(manage_guild=True)
    async def plugin_disable(self, interaction: discord.Interaction, plugin_name: str):
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)

        plugin = await database.get_plugin(plugin_name)
        if not plugin:
            await interaction.followup.send(f"Plugin '{plugin_name}' not found.", ephemeral=True)
            return

        if not plugin["enabled"]:
            await interaction.followup.send(f"Plugin '{plugin_name}' is already disabled.", ephemeral=True)
            return

        try:
            await self.bot._unload_plugin(plugin["name"], plugin["cog_path"])
            await database.set_plugin_enabled(plugin["name"], False)
            await interaction.followup.send(f"Plugin '{plugin_name}' disabled successfully!")
            # Record analytics
            if interaction.guild:
                await database.add_analytics_event(
                    event_type="command",
                    guild_id=str(interaction.guild.id),
                    channel_id=str(interaction.channel_id),
                    user_id=str(interaction.user.id),
                    provider=None,
                    tokens_used=None,
                    latency_ms=None
                )
        except Exception as e:
            await interaction.followup.send(f"Failed to disable plugin '{plugin_name}': {e}", ephemeral=True)

    def cog_load(self):
        pass # The command group is automatically registered

    def cog_unload(self):
        self.bot.tree.remove_command(self.plugin_group)

async def setup(bot):
    await bot.add_cog(Plugins(bot))