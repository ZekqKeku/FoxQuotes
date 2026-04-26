import traceback
from nextcord.ext import commands, application_checks
import nextcord

from lang import lang

class ErrorHandlerCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: nextcord.Interaction, error):
        try:
            if interaction.response.is_done():
                send = interaction.followup.send
            else:
                send = interaction.response.send_message

            user_locale = getattr(interaction, "locale", None)
            if user_locale not in lang.available_languages():
                user_locale = "en-US"

            if isinstance(error, application_checks.ApplicationCheckAnyFailure):
                await send(lang("errors", "no_guild", user_locale), ephemeral=True)

            elif isinstance(error, nextcord.ext.application_checks.errors.ApplicationNoPrivateMessage):
                await send(lang("errors", "no_dm", user_locale), ephemeral=True)

            elif isinstance(error, nextcord.errors.ApplicationCheckFailure):
                await send(lang("errors", "no_perm", user_locale), ephemeral=True)

            elif isinstance(error, commands.MissingPermissions):
                await send(lang("errors", "no_perm", user_locale), ephemeral=True)

            elif isinstance(error, commands.BotMissingPermissions):
                await send(lang("errors", "bot_no_perm", user_locale), ephemeral=True)

            elif isinstance(error, commands.MissingRole):
                await send(lang("errors", "missing_role", user_locale, role=error.missing_role), ephemeral=True)

            elif isinstance(error, commands.BotMissingRole):
                await send(lang("errors", "bot_missing_role", user_locale, role=error.missing_role), ephemeral=True)

            elif isinstance(error, commands.CommandNotFound):
                await send(lang("errors", "command_not_found", user_locale), ephemeral=True)

            elif isinstance(error, commands.UserInputError):
                await send(lang("errors", "user_input", user_locale), ephemeral=True)

            elif isinstance(error, commands.BadArgument):
                await send(lang("errors", "bad_argument", user_locale), ephemeral=True)

            elif isinstance(error, commands.BadUnionArgument):
                await send(lang("errors", "bad_union_argument", user_locale), ephemeral=True)

            elif isinstance(error, commands.MissingRequiredArgument):
                await send(lang("errors", "missing_required_argument", user_locale), ephemeral=True)

            elif isinstance(error, commands.TooManyArguments):
                await send(lang("errors", "too_many_arguments", user_locale), ephemeral=True)

            elif isinstance(error, commands.CommandOnCooldown):
                await send(lang("errors", "cooldown", user_locale, seconds=round(error.retry_after, 1)), ephemeral=True)

            elif isinstance(error, commands.DisabledCommand):
                await send(lang("errors", "disabled", user_locale), ephemeral=True)

            elif isinstance(error, commands.NoPrivateMessage):
                await send(lang("errors", "no_dm", user_locale), ephemeral=True)

            elif isinstance(error, commands.PrivateMessageOnly):
                await send(lang("errors", "dm_only", user_locale), ephemeral=True)

            elif isinstance(error, commands.CheckFailure):
                await send(lang("errors", "check_failure", user_locale), ephemeral=True)

            elif isinstance(error, commands.CommandInvokeError):
                await send(lang("errors", "invoke_error", user_locale), ephemeral=True)

            elif isinstance(error, nextcord.errors.Forbidden):
                await send(lang("errors", "forbidden", user_locale), ephemeral=True)

            elif isinstance(error, nextcord.errors.HTTPException):
                await send(lang("errors", "http", user_locale), ephemeral=True)

            elif isinstance(error, nextcord.errors.NotFound):
                await send(lang("errors", "not_found", user_locale), ephemeral=True)

            elif isinstance(error, nextcord.errors.InvalidArgument):
                await send(lang("errors", "invalid_argument", user_locale), ephemeral=True)

            elif isinstance(error, nextcord.errors.LoginFailure):
                await send(lang("errors", "login_failure", user_locale), ephemeral=True)

            elif isinstance(error, nextcord.errors.ConnectionClosed):
                await send(lang("errors", "connection_closed", user_locale), ephemeral=True)

            else:
                await send(lang("errors", "unknown", user_locale), ephemeral=True)

        except Exception as e:
            print(" > E.H. module error: ")
            traceback.print_exception(type(e), e, e.__traceback__)
        finally:
            print(" > Command Error: ", repr(error))
