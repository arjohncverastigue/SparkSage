from discord.ext import commands
import discord
import config

class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not config.WELCOME_ENABLED:
            return

        if not config.WELCOME_CHANNEL_ID:
            print(f"Warning: WELCOME_ENABLED is True but WELCOME_CHANNEL_ID is not set in config.")
            return

        welcome_channel = member.guild.get_channel(int(config.WELCOME_CHANNEL_ID))

        if not welcome_channel:
            print(f"Warning: Welcome channel with ID {config.WELCOME_CHANNEL_ID} not found in guild {member.guild.name}.")
            return

        if not isinstance(welcome_channel, discord.TextChannel):
            print(f"Warning: Welcome channel {welcome_channel.name} is not a text channel.")
            return

        welcome_message = config.WELCOME_MESSAGE.format(
            user=member.mention,
            server=member.guild.name
        )

        try:
            await welcome_channel.send(welcome_message)
            print(f"Sent welcome message to {member.name} in #{welcome_channel.name}")
        except discord.Forbidden:
            print(f"Error: Missing permissions to send welcome message in #{welcome_channel.name}.")
        except Exception as e:
            print(f"Error sending welcome message to {member.name}: {e}")

async def setup(bot):
    await bot.add_cog(Onboarding(bot))
