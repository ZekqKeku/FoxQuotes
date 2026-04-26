from nextcord.ext import application_checks
import nextcord
from typing import Iterable
import nextcord.ext.application_checks.errors as error

def onlyGuild():
    async def predicate(interaction: nextcord.Interaction) -> bool:
        if interaction.guild is None:
            raise error.ApplicationNoPrivateMessage("This command cannot be used in private messages.")
        return True
    return application_checks.check(predicate)

def onlyDM():
    async def predicate(interaction: nextcord.Interaction) -> bool:
        return isinstance(interaction.channel, nextcord.DMChannel)
    return application_checks.check(predicate)

def onlyAdmin():
    async def predicate(interaction: nextcord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return application_checks.check(predicate)

def hasRole(role):
    async def predicate(interaction: nextcord.Interaction) -> bool:
        if not interaction.guild:
            return False
        roles = [r.name if isinstance(role, str) else r.id for r in interaction.user.roles]
        return role in roles
    return application_checks.check(predicate)

def onlyGuildOwner():
    async def predicate(interaction: nextcord.Interaction) -> bool:
        return interaction.guild is not None and interaction.user.id == interaction.guild.owner_id
    return application_checks.check(predicate)

def onlyChannel(channel_id: int):
    async def predicate(interaction: nextcord.Interaction) -> bool:
        return interaction.channel.id == channel_id
    return application_checks.check(predicate)

def hasPermissions(**perms):
    async def predicate(interaction: nextcord.Interaction) -> bool:
        user_perms = interaction.user.guild_permissions
        return all(getattr(user_perms, perm, False) == value for perm, value in perms.items())
    return application_checks.check(predicate)

def userOnList(user_ids: Iterable[int]):
    async def predicate(interaction: nextcord.Interaction) -> bool:
        return interaction.user.id in user_ids
    return application_checks.check(predicate)