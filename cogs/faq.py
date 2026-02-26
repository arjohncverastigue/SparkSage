from discord.ext import commands
from discord import app_commands
import discord
import db
import time # For cooldown

# Cooldown for FAQ auto-responses per channel
FAQ_COOLDOWN = commands.CooldownMapping.from_cooldown(
    1, 60.0, commands.BucketType.channel
)

class FAQ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    faq_group = app_commands.Group(name="faq", description="Manage Frequently Asked Questions")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None: # Only process guild messages for FAQs
            return

        bucket = FAQ_COOLDOWN.get_bucket(message)
        if bucket.update_rate_limit(): # Returns non-None if rate limited
            return

        content = message.content.lower()
        faqs = await db.get_faqs(str(message.guild.id))

        best_match_faq = None
        highest_confidence = 0

        # Simple keyword matching for now
        for faq in faqs:
            keywords = [kw.strip().lower() for kw in faq["match_keywords"].split(',') if kw.strip()]
            confidence = sum(1 for kw in keywords if kw in content)
            
            # Simple heuristic: prioritize more matches, or longer matches if match count is equal
            if confidence > highest_confidence:
                highest_confidence = confidence
                best_match_faq = faq
            elif confidence > 0 and confidence == highest_confidence:
                # If same confidence, prefer FAQ with more keywords or specific logic if needed
                if len(faq["match_keywords"]) > len(best_match_faq["match_keywords"]):
                    best_match_faq = faq


        # Respond if confidence is high enough (e.g., at least one keyword matches)
        if best_match_faq and highest_confidence > 0:
            await message.channel.send(best_match_faq["answer"])
            await db.increment_faq_usage(best_match_faq["id"])

        await self.bot.process_commands(message) # Important to process other commands too


    faq_group = app_commands.Group(name="faq", description="Manage Frequently Asked Questions")

    @faq_group.command(name="add", description="Add a new FAQ entry")
    @app_commands.describe(
        question="The question for the FAQ.",
        answer="The answer to the FAQ.",
        keywords="Comma-separated keywords for auto-detection."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def faq_add(self, interaction: discord.Interaction, question: str, answer: str, keywords: str):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await db.add_faq(
            str(interaction.guild.id),
            question,
            answer,
            keywords,
            interaction.user.name # created_by
        )
        await interaction.response.send_message("FAQ added successfully!", ephemeral=True)

    @faq_group.command(name="list", description="List all FAQs for this server")
    async def faq_list(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        faqs = await db.get_faqs(str(interaction.guild.id))
        if not faqs:
            await interaction.response.send_message("No FAQs configured for this server.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"FAQs for {interaction.guild.name}",
            color=discord.Color.blue()
        )
        for faq in faqs:
            embed.add_field(
                name=f"ID: {faq['id']} - Q: {faq['question']}",
                value=f"A: {faq['answer']}\nKeywords: `{faq['match_keywords']}` | Used: {faq['times_used']} | By: {faq['created_by']}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @faq_group.command(name="remove", description="Remove a FAQ entry by its ID")
    @app_commands.describe(
        faq_id="The ID of the FAQ to remove."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def faq_remove(self, interaction: discord.Interaction, faq_id: int):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        faq = await db.get_faq_by_id(faq_id)
        if not faq or str(faq["guild_id"]) != str(interaction.guild.id):
            await interaction.response.send_message("FAQ not found or does not belong to this server.", ephemeral=True)
            return

        await db.delete_faq(faq_id)
        await interaction.response.send_message(f"FAQ with ID `{faq_id}` removed successfully!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(FAQ(bot))
