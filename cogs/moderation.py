import discord
from discord.ext import commands
import json
import config
import db as database
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_message_for_moderation(self, message: discord.Message):
        if not config.MODERATION_ENABLED:
            return

        if message.author.bot:
            return

        # Prepare the moderation prompt
        moderation_prompt = (
            "Rate the following message for toxicity, spam, and rule violations. "
            "Respond with JSON: {\"flagged\": bool, \"reason\": \"str\", \"severity\": \"low\"|\"medium\"|\"high\"}\n\n"
            f"Message: \"{message.content}\""
        )

        try:
            # Call AI for moderation review
            # We use a placeholder channel ID and bot's own name for logging purposes,
            # as this isn't directly tied to a user conversation history.
            ai_response, _ = await self.bot.ask_ai(
                channel_id=0,  # A dummy channel ID for moderation logs
                user_name="ModerationSystem",
                message=moderation_prompt,
                system_prompt="You are a moderation AI. Analyze messages for problematic content and respond only with JSON.",
                message_type="moderation_check"
            )
            
            # Preprocess AI response to remove markdown code blocks if present
            if ai_response.startswith("```json") and ai_response.endswith("```"):
                clean_response = ai_response[7:-3].strip() # Remove ```json\n and \n```
            else:
                clean_response = ai_response.strip()

            # Attempt to parse the JSON response
            moderation_result = json.loads(clean_response)
            flagged = moderation_result.get("flagged", False)
            reason = moderation_result.get("reason", "No reason provided.")
            severity = moderation_result.get("severity", "low")

            if flagged:
                await self.flag_message_for_review(message, reason, severity)
                # Increment moderation stats
                await database.add_moderation_log(
                    guild_id=str(message.guild.id),
                    channel_id=str(message.channel.id),
                    message_id=str(message.id),
                    author_id=str(message.author.id),
                    reason=reason,
                    severity=severity
                )

        except json.JSONDecodeError:
            print(f"Moderation AI returned invalid JSON: {ai_response}")
        except Exception as e:
            print(f"Error during moderation check: {e}")

    async def flag_message_for_review(self, message: discord.Message, reason: str, severity: str):
        mod_log_channel_id = config.MOD_LOG_CHANNEL_ID
        if not mod_log_channel_id:
            return

        mod_log_channel = self.bot.get_channel(int(mod_log_channel_id))
        if not mod_log_channel:
            return

        embed = discord.Embed(
            title=f"Message Flagged: {severity.upper()}",
            description=f"""**Author:** {message.author.mention} (`{message.author}`)
**Channel:** {message.channel.mention}
**Reason:** {reason}
**Original Message:**
```
{message.content}
```
[Jump to Message]({message.jump_url})""",
            color=discord.Color.red() if severity == "high" else discord.Color.orange()
        )

        # Add action buttons (placeholders for now)
        # This part would require discord.ui.View and persistent views,
        # which is more complex and out of scope for initial setup.
        # For now, we'll just send the embed.
        
        await mod_log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))