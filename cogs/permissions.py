from discord.ext import commands
from discord import app_commands
import discord
import db
from utils.checks import has_permissions, MissingRolePermission # Import the check and custom exception

class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    permissions_group = app_commands.Group(
        name="permissions",
        description="Manage command role permissions."
    )

    @permissions_group.command(name="set", description="Require a role to use a command.")
    @app_commands.describe(
        command_name="The name of the command to restrict (e.g., 'ask', 'faq add').",
        role="The role to require for this command."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def perm_set(self, interaction: discord.Interaction, command_name: str, role: discord.Role):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # Check if the command actually exists (this is a basic check)
        # More robust checking would involve iterating bot.tree.walk_commands()
        if not self.bot.tree.get_command(command_name):
            await interaction.response.send_message(f"Command '{command_name}' not found. Make sure to use the top-level command name or full subcommand path.", ephemeral=True)
            return

        await db.add_command_permission(command_name, str(interaction.guild.id), str(role.id))
        await interaction.response.send_message(f"Command `{command_name}` now requires the role `{role.name}`.", ephemeral=True)

    @permissions_group.command(name="remove", description="Remove a role restriction from a command.")
    @app_commands.describe(
        command_name="The name of the command (e.g., 'ask', 'faq add').",
        role="The role to no longer require for this command."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def perm_remove(self, interaction: discord.Interaction, command_name: str, role: discord.Role):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        # Check if the command actually exists (this is a basic check)
        if not self.bot.tree.get_command(command_name):
            await interaction.response.send_message(f"Command '{command_name}' not found. Make sure to use the top-level command name or full subcommand path.", ephemeral=True)
            return

        await db.remove_command_permission(command_name, str(interaction.guild.id), str(role.id))
        await interaction.response.send_message(f"Role `{role.name}` no longer required for command `{command_name}`.", ephemeral=True)

    @permissions_group.command(name="list", description="List all command role restrictions for this server.")
    @app_commands.default_permissions(manage_guild=True)
    async def perm_list(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        permissions = await db.get_all_command_permissions(str(interaction.guild.id))

        if not permissions:
            await interaction.response.send_message("No command role restrictions are set for this server.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Command Permissions for {interaction.guild.name}",
            color=discord.Color.dark_green()
        )

        # Group by command name
        grouped_perms = {}
        for perm in permissions:
            if perm["command_name"] not in grouped_perms:
                grouped_perms[perm["command_name"]] = []
            grouped_perms[perm["command_name"]].append(perm["role_id"])

        for cmd_name, role_ids in grouped_perms.items():
            role_mentions = []
            for role_id in role_ids:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    role_mentions.append(role.mention)
                else:
                    role_mentions.append(f"Unknown Role ({role_id})")
            
            embed.add_field(
                name=f"`/{cmd_name}`",
                value=f"Requires: {', '.join(role_mentions)}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Global error handler for app commands
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, MissingRolePermission):
            await interaction.response.send_message(
                f"You do not have the required role(s) to use this command: {error.message}", ephemeral=True
            )
        else:
            # Fallback to default error handling
            self.bot.dispatch("app_command_error", interaction, error)


async def setup(bot):
    await bot.add_cog(Permissions(bot))
    # Add the error handler to the bot's tree
    bot.tree.on_error = Permissions(bot).on_app_command_error # This will overwrite any previous on_error
