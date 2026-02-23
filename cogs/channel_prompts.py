import discord
from discord.ext import commands
from discord import app_commands
import db as database
import config
from utils.rate_limiter import rate_limiter # Import rate_limiter

class ChannelPrompts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    prompt_group = app_commands.Group(name="prompt", description="Manage channel-specific AI system prompts.")

    @prompt_group.command(name="set", description="Set a custom AI system prompt for this channel.")
    @app_commands.describe(new_prompt="The new system prompt for this channel.")
    @app_commands.default_permissions(manage_channels=True)
    async def prompt_set(self, interaction: discord.Interaction, new_prompt: str):
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server channel.", ephemeral=True)
            return

        # Rate limit check
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        
        await interaction.response.defer(ephemeral=True)

        try:
            await database.set_channel_prompt(
                channel_id=str(interaction.channel_id),
                guild_id=str(interaction.guild_id),
                system_prompt=new_prompt
            )
            # Record analytics for the 'prompt set' command
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
            await interaction.followup.send(f"""Successfully set custom system prompt for this channel:
```
{new_prompt}
```""")
        except Exception as e:
            await interaction.followup.send(f"Failed to set prompt: {e}", ephemeral=True)

    @prompt_group.command(name="reset", description="Reset this channel's custom AI system prompt to the global default.")
    @app_commands.default_permissions(manage_channels=True)
    async def prompt_reset(self, interaction: discord.Interaction):
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server channel.", ephemeral=True)
            return

        # Rate limit check
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        
        await interaction.response.defer(ephemeral=True)

        try:
            await database.delete_channel_prompt(channel_id=str(interaction.channel_id))
            # Record analytics for the 'prompt reset' command
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
            await interaction.followup.send("Successfully reset custom system prompt for this channel. It will now use the global default.")
        except Exception as e:
            await interaction.followup.send(f"Failed to reset prompt: {e}", ephemeral=True)

    @prompt_group.command(name="get", description="Get the current custom AI system prompt for this channel.")
    @app_commands.default_permissions(manage_channels=True)
    async def prompt_get(self, interaction: discord.Interaction):
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server channel.", ephemeral=True)
            return

        # Rate limit check
        if interaction.guild:
            allowed, reason = rate_limiter.check_and_consume(str(interaction.user.id), str(interaction.guild.id))
            if not allowed:
                await interaction.response.send_message(reason, ephemeral=True)
                return
        
        await interaction.response.defer(ephemeral=True)

        try:
            current_prompt = await database.get_channel_prompt(channel_id=str(interaction.channel_id))
            if current_prompt:
                await interaction.followup.send(f"""Current custom system prompt for this channel:
```
{current_prompt}
```""")
            else:
                await interaction.followup.send("This channel does not have a custom system prompt set. It uses the global default.")
            
            # Record analytics for the 'prompt get' command
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
            await interaction.followup.send(f"Failed to retrieve prompt: {e}", ephemeral=True)

    def cog_load(self):
        # self.bot.tree.add_command(self.prompt_group) # Removed explicit add, handled automatically
        pass

    def cog_unload(self):
        self.bot.tree.remove_command(self.prompt_group)

async def setup(bot):
    await bot.add_cog(ChannelPrompts(bot))