from nextcord.ext import commands
import nextcord
from typing import Iterable

from utils import FQdatabase


class SupervisorsCog(commands.Cog):
    def __init__(self, client, database: FQdatabase.FQdb, supervisors: Iterable[int]):
        self.client = client
        self.database = database
        self.supervisors = supervisors

        self.commands_info = {
            "trust": {
                "description": "Manage trust status of users.",
                "usage": "<fq> trust [--add/-a <user>] [--status/-s] [--help/-h]",
                "options": {
                    "--add": "Add a user to trusted list. Requires a user mention or ID.",
                    "-a": "Alias for --add.",
                    "--status": "Show trust status of a user. Requires a user mention or ID.",
                    "-s": "Alias for --status.",
                    "--help": "Show help for trust command.",
                    "-h": "Alias for --help."
                }
            },
            "clear": {
                "description": "Clear bot CLI messages in the channel (only in guild channels).",
                "usage": "<fq> clear [limit]",
                "options": {
                    "limit": "Optional number of messages to delete (max 100)."
                }
            },
            "help": {
                "description": "Show help message.",
                "usage": "<fq> help [command]",
                "options": {
                    "command": "Optional command to show detailed help for."
                }
            }
        }

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return
        if message.author.id not in self.supervisors:
            return

        content = message.content.strip()
        if not content.lower().startswith("<fq>"):
            return

        args = content[4:].strip().split()
        if not args:
            await message.reply("No command provided.")
            return

        command = args[0].lower()
        subargs = args[1:]

        if command == "trust":
            await self._handle_trust_command(message, subargs)
        elif command == "clear":
            await self._handle_clear_command(message, subargs)
        elif command == "help":
            await self._handle_help_command(message, subargs)
        else:
            await message.reply(f"Unknown command: `{command}`")

    async def _handle_help_command(self, message: nextcord.Message, args):
        if args:
            cmd = args[0].lower()
            info = self.commands_info.get(cmd)
            if not info:
                await message.reply(f"No help found for command `{cmd}`.")
                return

            help_text = f"**Help for `{cmd}` command:**\n" \
                        f"Description: {info['description']}\n" \
                        f"Usage: `{info['usage']}`\n"
            if info.get("options"):
                help_text += "Options:\n"
                for opt, desc in info["options"].items():
                    help_text += f"  `{opt}`: {desc}\n"
            await message.reply(help_text)
        else:
            cmds_list = "\n".join(
                f"`{cmd}` - {info['description']}" for cmd, info in self.commands_info.items()
            )
            await message.reply(f"**Available commands:**\n{cmds_list}\n"
                                f"Use `<fq> help <command>` for details.")

    async def _handle_trust_command(self, message: nextcord.Message, args):
        opts = {}
        i = 0
        while i < len(args):
            arg = args[i].lower()
            if arg in ("--add", "-a"):
                if i + 1 < len(args):
                    opts["add"] = args[i + 1]
                    i += 2
                else:
                    await message.reply("Option --add requires a user mention or ID.")
                    return
            elif arg in ("--status", "-s"):
                if i + 1 < len(args):
                    opts["status"] = args[i + 1]
                    i += 2
                else:
                    await message.reply("Option --status requires a user mention or ID.")
                    return
            elif arg in ("--help", "-h"):
                info = self.commands_info["trust"]
                help_text = f"**Help for `trust` command:**\n" \
                            f"Description: {info['description']}\n" \
                            f"Usage: `{info['usage']}`\nOptions:\n"
                for opt, desc in info["options"].items():
                    help_text += f"  `{opt}`: {desc}\n"
                await message.reply(help_text)
                return
            else:
                await message.reply(f"Unknown option `{arg}`. Use --help for usage.")
                return

        if "add" in opts:
            user = await self._extract_user_from_mention_or_id(opts["add"])
            if not user:
                await message.reply("No valid user found for --add option.")
                return

            self.database.ensureUserExists(user.id)
            self.database.updateUserTrust(user.id, True)
            await message.reply(f"Trusted user: {user.name} (ID: {user.id})")
            return

        if "status" in opts:
            user = await self._extract_user_from_mention_or_id(opts["status"])
            if not user:
                await message.reply("No valid user found for --status option.")
                return

            self.database.ensureUserExists(user.id)
            is_trusted = self.database.isTrusted(user.id)
            await message.reply(
                f"User {user.name} (ID: {user.id}) is currently {'trusted' if is_trusted else 'not trusted'}.")
            return

        info = self.commands_info["trust"]
        help_text = f"**Help for `trust` command:**\n" \
                    f"Description: {info['description']}\n" \
                    f"Usage: `{info['usage']}`\nOptions:\n"
        for opt, desc in info["options"].items():
            help_text += f"  `{opt}`: {desc}\n"
        await message.reply(help_text)

    async def _extract_user_from_mention_or_id(self, arg: str) -> nextcord.User | None:
        try:
            user_id = int(arg.strip("<@!>"))
            user = await self.client.fetch_user(user_id)
            return user
        except Exception:
            return None

    async def _handle_clear_command(self, message: nextcord.Message, args):
        if isinstance(message.channel, nextcord.DMChannel):
            await message.reply("You cannot use the `clear` command in private messages (DMs).")
            return

        channel = message.channel
        limit = 100

        if args:
            try:
                parsed = int(args[0])
                if parsed < 1:
                    await message.reply("Specify a number greater than 0.", delete_after=15)
                    return
                limit = min(parsed, 100)
            except ValueError:
                await message.reply("The limit must be an integer.", delete_after=15)
                return

        fetched = []
        async for msg in channel.history(limit=200):
            fetched.append(msg)

        cli_messages = [
            m for m in fetched
            if m.content.strip().lower().startswith("<fq>")
            and m.author.id in self.supervisors
        ]

        cli_messages.sort(key=lambda m: m.created_at, reverse=True)

        cli_messages = cli_messages[:limit]

        cli_ids = {m.id for m in cli_messages}

        bot_replies = [
            m for m in fetched
            if m.author.id == self.client.user.id
            and m.reference
            and m.reference.message_id in cli_ids
        ]

        to_delete = cli_messages + bot_replies

        deleted = 0
        for msg in to_delete:
            try:
                await msg.delete()
                deleted += 1
            except Exception:
                pass

        try:
            await message.delete()
        except Exception:
            pass

        await channel.send(
            f"Deleted {deleted} CLI messages.",
            delete_after=15
        )