from discord.ext import commands
from discord import app_commands
import db
import discord # Import discord to use discord.Interaction and discord.Role

class MissingRolePermission(app_commands.CheckFailure):
    def __init__(self, message="You do not have the required role(s) to use this command."):
        self.message = message
        super().__init__(self.message)

def has_permissions():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            # For DMs, no role-based permissions apply.
            # You might want a different default behavior here (e.g., always allow or always deny).
            # For now, let's allow in DMs if no specific guild context.
            return True

        command_name = interaction.command.name # Or full_command_name if it's a subcommand

        # Get required role_ids for this command and guild
        required_role_ids = await db.get_command_permissions(command_name, str(interaction.guild.id))

        # If no specific roles are required, anyone can use it
        if not required_role_ids:
            return True

        # Check if the user has any of the required roles
        # interaction.user.roles is a list of discord.Role objects
        user_role_ids = {str(role.id) for role in interaction.user.roles}

        if any(role_id in user_role_ids for role_id in required_role_ids):
            return True
        
        raise MissingRolePermission()

    return app_commands.check(predicate)
