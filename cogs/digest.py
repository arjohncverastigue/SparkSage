import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import config
import db as database

class Digest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if config.DIGEST_ENABLED:
            self.daily_digest.start()

    def cog_unload(self):
        self.daily_digest.cancel()

    @tasks.loop(hours=24)
    async def daily_digest(self):
        if not config.DIGEST_ENABLED:
            return

        print("Daily digest task running!")

        target_channel_id = int(config.DIGEST_CHANNEL_ID)
        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel:
            print(f"Daily digest: Target channel {config.DIGEST_CHANNEL_ID} not found.")
            return

        # Collect messages from the last 24 hours
        now = datetime.datetime.now(datetime.timezone.utc)
        yesterday = now - datetime.timedelta(hours=24)

        history_messages = await database.get_messages_since(
            str(target_channel_id), yesterday
        )

        if not history_messages:
            print("Daily digest: No messages found in the last 24 hours.")
            return

        formatted_messages = []
        for msg in history_messages:
            # Fetch message object to get author's display name if needed
            # This is simplified; in a real scenario, you might need to fetch
            # the actual discord.Message object if `database.get_messages_since`
            # doesn't provide enough detail (e.g., author names).
            # For now, let's assume `msg` contains 'author' and 'content'
            formatted_messages.append(f"{msg['author']}: {msg['content']}")
        
        # Summarize with AI
        full_text = "\n".join(formatted_messages)
        prompt = f"Summarize the following Discord conversation from the last 24 hours:\n\n{full_text}"

        try:
            summary, _ = await self.bot.ask_ai(
                channel_id=target_channel_id,
                user_name="SparkSage", # Bot's own name for context
                message=prompt,
                system_prompt="You are a helpful assistant that summarizes Discord conversations.",
                message_type="digest"
            )
            
            # Post to digest channel
            await target_channel.send(f"**Daily Digest:**\n{summary}")
            print(f"Daily digest posted to {target_channel.name}")

        except Exception as e:
            print(f"Daily digest: Error summarizing or posting: {e}")


    @daily_digest.before_loop
    async def before_daily_digest(self):
        await self.bot.wait_until_ready()
        if not config.DIGEST_ENABLED:
            print("Daily digest: Disabled in config.")
            self.daily_digest.cancel()
            return

        try:
            target_time_str = config.DIGEST_TIME
            hour, minute = map(int, target_time_str.split(':'))
        except ValueError:
            print(f"Daily digest: Invalid DIGEST_TIME format: {config.DIGEST_TIME}. Expected HH:MM.")
            self.daily_digest.cancel()
            return
        
        while True:
            now = datetime.datetime.now(datetime.timezone.utc)
            # Find the next target time
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run < now:
                next_run += datetime.timedelta(days=1)
            
            time_to_wait = (next_run - now).total_seconds()
            print(f"Daily digest: Waiting for {time_to_wait:.0f} seconds until {next_run.isoformat()}...")
            await asyncio.sleep(time_to_wait)
            break # Exit loop once we've waited for the first run

async def setup(bot):
    await bot.add_cog(Digest(bot))
