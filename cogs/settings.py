import nextcord
from nextcord.ext import commands, application_checks
from nextcord import Interaction, SlashOption, File
from typing import Iterable
from datetime import datetime
from PIL import Image
from io import BytesIO
import re

from utils import FQutils, FQdatabase, checs
from lang import lang
from utils.FQutils import DateTools


class SettingsCog(commands.Cog):
    def __init__(self, client, database: FQdatabase.FQdb, supervisors:Iterable[int]):
        self.client = client
        self.database = database
        self.supervisors = supervisors
        self.image_tool = FQutils.FQimage()

    @nextcord.slash_command(
        name=lang("cmd_settings", "name", "en-US"),
        description=lang("cmd_settings", "description", "en-US"),
        name_localizations=lang.localizations("cmd_settings", "name"),
        description_localizations=lang.localizations("cmd_settings", "description"),
        default_member_permissions=nextcord.Permissions(manage_guild=True)
    )
    @application_checks.guild_only()
    async def settings(self, interaction: Interaction):
        await interaction.response.send_message("", ephemeral=True, delete_after=0)

    @settings.subcommand(
        name=lang("cmd_settings_help", "name", "en-US"),
        description=lang("cmd_settings_help", "description", "en-US"),
        name_localizations=lang.localizations("cmd_settings_help", "name"),
        description_localizations=lang.localizations("cmd_settings_help", "description")
    )
    @application_checks.guild_only()
    async def help(self, interaction: Interaction):
        await interaction.response.send_message("Lorem ipsum", ephemeral=True)

    @settings.subcommand(
        name=lang("cmd_set_channel", "name", "en-US"),
        description=lang("cmd_set_channel", "description", "en-US"),
        name_localizations=lang.localizations("cmd_set_channel", "name"),
        description_localizations=lang.localizations("cmd_set_channel", "description")
    )
    @application_checks.guild_only()
    async def set_channel(
        self,
        interaction: Interaction,
        channel: nextcord.TextChannel = SlashOption(
            name=lang("cmd_set_channel", "p1_name", "en-US"),
            description=lang("cmd_set_channel", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_channel", "p1_name"),
            description_localizations=lang.localizations("cmd_set_channel", "p1_description"),
            required=False
        )
    ):
        await interaction.response.defer()

        member = interaction.user
        guild = interaction.guild
        guild_lang = self.database.getGuildLang(interaction.guild.id)

        if channel:
            self.database.setGuildChannel(guild.id, channel.id)
            await interaction.followup.send(
                lang("quotes", "other_channel", guild_lang, channel=f"<#{channel.id}>"),
                ephemeral=True
            )
        else:
            self.database.clearGuildChannel(guild.id)
            await interaction.followup.send(
                lang("quotes", "channel_cleared", guild_lang),
                ephemeral=True
            )

    @settings.subcommand(
        name=lang("cmd_set_lang", "name", "en-US"),
        description=lang("cmd_set_lang", "description", "en-US"),
        name_localizations=lang.localizations("cmd_set_lang", "name"),
        description_localizations=lang.localizations("cmd_set_lang", "description")
    )
    @application_checks.guild_only()
    async def set_lang(self, interaction: Interaction,
        lang_: str = SlashOption(
            name=lang("cmd_set_lang", "p1_name", "en-US"),
            description=lang("cmd_set_lang", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_lang", "p1_name"),
            description_localizations=lang.localizations("cmd_set_lang", "p1_description"),
            choices={name: code for code, name in lang.language_display_names().items()}
        )
    ):
        self.database.setGuildLang(interaction.guild.id, lang_)
        guild_lang = self.database.getGuildLang(interaction.guild.id)
        display_name = lang.language_display_names().get(lang_, lang_)
        await interaction.response.send_message(
            lang("set_lang", "message", guild_lang, lang=display_name),
            ephemeral=True
        )

    @settings.subcommand(
        name=lang("cmd_dummy_image", "name", "en-US"),
        description=lang("cmd_dummy_image", "description", "en-US"),
        name_localizations=lang.localizations("cmd_dummy_image", "name"),
        description_localizations=lang.localizations("cmd_dummy_image", "description")
    )
    @application_checks.guild_only()
    async def dummy_image(self, interaction: Interaction,
        dummy: str = SlashOption(
            name=lang("cmd_dummy_image", "p1_name", "en-US"),
            description=lang("cmd_dummy_image", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_dummy_image", "p1_name"),
            description_localizations=lang.localizations("cmd_dummy_image", "p1_description"),
            required=False,
            min_length=3,
            max_length=380
        )
    ):
        await interaction.response.defer()
        guild_lang = self.database.getGuildLang(interaction.guild.id)

        if not dummy:
            dummy = f"Lorem ipsum dolor sit amet, <@{self.client.user.id}> consectetur adipiscing elit. "

        ping_list = self.image_tool.list_username_id_from_text(dummy)
        ping_map = []
        if ping_list:
            for id in ping_list:
                map_user = await self.client.fetch_user(id)
                ping_map.append({
                    "id": id,
                    "name": map_user.display_name
                })

        avatar_asset = self.client.user.display_avatar
        avatar_bytes = await avatar_asset.read()
        avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA")

        guild_name = interaction.guild.name
        creator = str(self.client.user.display_name)
        footer_text = lang("quotes", "footer", guild_lang, creator = creator, guild = guild_name)

        if len(footer_text) >= 78:
            if len(creator) >= 10:
                creator = creator[:15] + "..."
                if len(guild_name) >= 35:
                    guild_name = guild_name[:35] + "..."
            else:
                if len(guild_name) >= 50:
                    guild_name = guild_name[:50] + "..."
            footer_text = lang("quotes", "footer", guild_lang, creator = creator, guild = guild_name)

        image_data = {
            "avatar": avatar_img,
            "username": str(self.client.user.display_name).upper(),
            "content": dummy,
            "creator": creator,
            "guild_name": guild_name,
            "date": datetime.now(),
            "footer": footer_text,
            "ping_map": ping_map,
            "ping_color": self.database.getGuildColor(interaction.guild.id),
            "background_mode": self.database.getBackgroundMode(interaction.guild.id),
            "background_url": self.database.getGuildBgUrl(interaction.guild.id),
            "bg_postproces": self.database.getGuildBgPost(interaction.guild.id)
        }
        result_img = self.image_tool.generate_image(image_data)

        buffer = BytesIO()
        result_img.save(buffer, format="PNG")
        buffer.seek(0)

        file = File(buffer, filename="quote.png")

        await interaction.followup.send(
            lang("dummy_image", "message", guild_lang),
            file=file,
            ephemeral=True
        )

    @settings.subcommand(
        name=lang("cmd_set_color", "name", "en-US"),
        description=lang("cmd_set_color", "description", "en-US"),
        name_localizations=lang.localizations("cmd_set_color", "name"),
        description_localizations=lang.localizations("cmd_set_color", "description")
    )
    @application_checks.guild_only()
    async def set_color(self, interaction: Interaction,
        color: str = SlashOption(
            name=lang("cmd_set_color", "p1_name", "en-US"),
            description=lang("cmd_set_color", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_color", "p1_name"),
            description_localizations=lang.localizations("cmd_set_color", "p1_description"),
            required=False,
            min_length=6,
            max_length=7
        )
    ):
        guild_lang = self.database.getGuildLang(interaction.guild.id)

        if color:
            color = color.lstrip('#')
            if re.match(r'^[0-9a-fA-F]{6}$', color, re.IGNORECASE):
                color = "#" + color
                await interaction.response.send_message(
                    lang("set_color", "hex_correct", guild_lang, color=color),
                    ephemeral=True
                )
                self.database.setGuildColor(interaction.guild.id, color)
            else:
                await interaction.response.send_message(
                    lang("set_color", "hex_error", guild_lang),
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                lang("set_color", "set_default", guild_lang),
                ephemeral=True
            )
            self.database.clearGuildColor(interaction.guild.id)

    @settings.subcommand(
        name=lang("cmd_set_background", "name", "en-US"),
        description=lang("cmd_set_background", "description", "en-US"),
        name_localizations=lang.localizations("cmd_set_background", "name"),
        description_localizations=lang.localizations("cmd_set_background", "description")
    )
    @application_checks.guild_only()
    async def set_background(self, interaction: Interaction,
        url: str = SlashOption(
            name=lang("cmd_set_background", "p1_name", "en-US"),
            description=lang("cmd_set_background", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_background", "p1_name"),
            description_localizations=lang.localizations("cmd_set_background", "p1_description"),
            required=False,
            min_length=10
        )
    ):
        guild_lang = self.database.getGuildLang(interaction.guild.id)
        url_pattern = r"^https://.*\.(png|jpeg|jpg)$"

        if url:
            if re.match(url_pattern, url, re.IGNORECASE):
                await interaction.response.send_message(
                    lang("set_background", "changed", guild_lang),
                    ephemeral=True
                )
                self.database.setGuildBgUrl(interaction.guild.id, url)
            else:
                await interaction.response.send_message(
                    lang("set_background", "error", guild_lang),
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                lang("set_background", "clear", guild_lang),
                ephemeral=True
            )
            self.database.clearGuildBgUrl(interaction.guild.id)

            await interaction.followup.send(
            lang("set_bg_mode", "message", guild_lang,
                 mode=
                 lang("set_bg_mode", "mode0", guild_lang)
                ),
            ephemeral=True
        )
            self.database.setBackgroundMode(interaction.guild.id, 0)

    @settings.subcommand(
        name=lang("cmd_set_bg_mode", "name", "en-US"),
        description=lang("cmd_set_bg_mode", "description", "en-US"),
        name_localizations=lang.localizations("cmd_set_bg_mode", "name"),
        description_localizations=lang.localizations("cmd_set_bg_mode", "description")
    )
    @application_checks.guild_only()
    async def set_background_mode(self, interaction: Interaction,
        mode: int = SlashOption(
            name=lang("cmd_set_bg_mode", "p1_name", "en-US"),
            description=lang("cmd_set_bg_mode", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_bg_mode", "p1_name"),
            description_localizations=lang.localizations("cmd_set_bg_mode", "p1_description"),
            required=True,
            choices={
                lang("cmd_set_bg_mode", "c1_name0", "en-US"): 0,
                lang("cmd_set_bg_mode", "c1_name1", "en-US"): 1,
                lang("cmd_set_bg_mode", "c1_name2", "en-US"): 2
            },
            choice_localizations={
                lang("cmd_set_bg_mode", "c1_name0", "en-US"):
                    lang.localizations("cmd_set_bg_mode", "c1_name0"),
                lang("cmd_set_bg_mode", "c1_name1", "en-US"):
                    lang.localizations("cmd_set_bg_mode", "c1_name1"),
                lang("cmd_set_bg_mode", "c1_name2", "en-US"):
                    lang.localizations("cmd_set_bg_mode", "c1_name2")
            }
        )
    ):
        guild_lang = self.database.getGuildLang(interaction.guild.id)

        if self.database.getGuildBgUrl(interaction.guild.id) is None: mode=0

        await interaction.response.send_message(
            lang("set_bg_mode", "message", guild_lang,
                 mode=
                 lang("set_bg_mode", f"mode{mode}", guild_lang)
                ),
            ephemeral=True
        )
        self.database.setBackgroundMode(interaction.guild.id, mode)

    @settings.subcommand(
        name=lang("cmd_set_background_postprocess", "name", "en-US"),
        description=lang("cmd_set_background_postprocess", "description", "en-US"),
        name_localizations=lang.localizations("cmd_set_background_postprocess", "name"),
        description_localizations=lang.localizations("cmd_set_background_postprocess", "description")
    )
    @application_checks.guild_only()
    async def set_background_postprocess(self, interaction: Interaction,
        post_proces: int = SlashOption(
            name=lang("cmd_set_background_postprocess", "p1_name", "en-US"),
            description=lang("cmd_set_background_postprocess", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_background_postprocess", "p1_name"),
            description_localizations=lang.localizations("cmd_set_background_postprocess", "p1_description"),
            required=True,
            choices={
                lang("cmd_set_background_postprocess", "c1_name1", "en-US"): 1,
                lang("cmd_set_background_postprocess", "c1_name0", "en-US"): 0
            },
            choice_localizations={
                lang("cmd_set_background_postprocess", "c1_name1", "en-US"):
                    lang.localizations("cmd_set_background_postprocess", "c1_name1"),
                lang("cmd_set_background_postprocess", "c1_name0", "en-US"):
                    lang.localizations("cmd_set_background_postprocess", "c1_name0")
            }
        )
    ):
        guild_lang = self.database.getGuildLang(interaction.guild.id)

        await interaction.response.send_message(
            lang("set_background_postprocess", f"message{post_proces}", guild_lang),
            ephemeral=True
        )
        self.database.setGuildBgPost(interaction.guild.id, post_proces)

    @settings.subcommand(
        name=lang("cmd_set_daily_quote", "name", "en-US"),
        description=lang("cmd_set_daily_quote", "description", "en-US"),
        name_localizations=lang.localizations("cmd_set_daily_quote", "name"),
        description_localizations=lang.localizations("cmd_set_daily_quote", "description")
    )
    @application_checks.guild_only()
    async def set_daily_quote(self, interaction: Interaction,
        channel: nextcord.TextChannel = SlashOption(
            name=lang("cmd_set_daily_quote", "p1_name", "en-US"),
            description=lang("cmd_set_daily_quote", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_daily_quote", "p1_name"),
            description_localizations=lang.localizations("cmd_set_daily_quote", "p1_description"),
            required=True
        ),
        hour: int = SlashOption(
            name=lang("cmd_set_daily_quote", "p2_name", "en-US"),
            description=lang("cmd_set_daily_quote", "p2_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_daily_quote", "p2_name"),
            description_localizations=lang.localizations("cmd_set_daily_quote", "p2_description"),
            required=True,
            min_value = 0,
            max_value = 23
        ),
        minute: int = SlashOption(
            name=lang("cmd_set_daily_quote", "p3_name", "en-US"),
            description=lang("cmd_set_daily_quote", "p3_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_daily_quote", "p3_name"),
            description_localizations=lang.localizations("cmd_set_daily_quote", "p3_description"),
            required=True,
            min_value = 0,
            max_value = 59
        ),
        timezone: int = SlashOption(
            name=lang("cmd_set_daily_quote", "p4_name", "en-US"),
            description=lang("cmd_set_daily_quote", "p4_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_daily_quote", "p4_name"),
            description_localizations=lang.localizations("cmd_set_daily_quote", "p4_description"),
            min_value = -12,
            max_value = 12,
            required=True
        ),
        mode: int = SlashOption(
            name=lang("cmd_set_daily_quote", "p5_name", "en-US"),
            description=lang("cmd_set_daily_quote", "p5_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_daily_quote", "p5_name"),
            description_localizations=lang.localizations("cmd_set_daily_quote", "p5_description"),
            choices={
                lang("cmd_set_daily_quote", "c1_name0", "en-US"): 0,
                lang("cmd_set_daily_quote", "c1_name1", "en-US"): 1,
                lang("cmd_set_daily_quote", "c1_name2", "en-US"): 2,
                lang("cmd_set_daily_quote", "c1_name3", "en-US"): 3,
                lang("cmd_set_daily_quote", "c1_name4", "en-US"): 4,
                lang("cmd_set_daily_quote", "c1_name5", "en-US"): 5,
                lang("cmd_set_daily_quote", "c1_name6", "en-US"): 6,
                lang("cmd_set_daily_quote", "c1_name7", "en-US"): 7,
            },
            choice_localizations= {
                lang("cmd_set_daily_quote", "c1_name0", "en-US"):
                    lang.localizations("cmd_set_daily_quote", "c1_name0"),
                lang("cmd_set_daily_quote", "c1_name1", "en-US"):
                    lang.localizations("cmd_set_daily_quote", "c1_name1"),
                lang("cmd_set_daily_quote", "c1_name2", "en-US"):
                    lang.localizations("cmd_set_daily_quote", "c1_name2"),
                lang("cmd_set_daily_quote", "c1_name3", "en-US"):
                    lang.localizations("cmd_set_daily_quote", "c1_name3"),
                lang("cmd_set_daily_quote", "c1_name4", "en-US"):
                    lang.localizations("cmd_set_daily_quote", "c1_name4"),
                lang("cmd_set_daily_quote", "c1_name5", "en-US"):
                    lang.localizations("cmd_set_daily_quote", "c1_name5"),
                lang("cmd_set_daily_quote", "c1_name6", "en-US"):
                    lang.localizations("cmd_set_daily_quote", "c1_name6"),
                lang("cmd_set_daily_quote", "c1_name7", "en-US"):
                    lang.localizations("cmd_set_daily_quote", "c1_name7"),
            }
        ),
        ping: nextcord.Role = SlashOption(
            name=lang("cmd_set_daily_quote", "p6_name", "en-US"),
            description=lang("cmd_set_daily_quote", "p6_description", "en-US"),
            name_localizations=lang.localizations("cmd_set_daily_quote", "p6_name"),
            description_localizations=lang.localizations("cmd_set_daily_quote", "p6_description"),
            required=False
        )
    ):
        guild_lang = self.database.getGuildLang(interaction.guild.id)

        self.database.setGuildDailyChannel(interaction.guild.id, channel.id)
        self.database.setDailyTime(interaction.guild.id, hour, minute, timezone)
        self.database.setDailyMode(interaction.guild.id, mode)
        if ping: self.database.setDailyPing(interaction.guild.id, ping.id)
        else: self.database.clearDailyPing(interaction.guild.id)

        if ping: ping_setting = f"<@&{ping.id}>"
        else: ping_setting = lang("set_daily_quote", "empty_ping", guild_lang)

        await interaction.response.send_message(
            lang("set_daily_quote", "message", guild_lang,
                 channel = f"<#{channel.id}>",
                 hour = DateTools.short_number(hour),
                 minute = DateTools.short_number(minute),
                 timezone = timezone,
                 mode =
                    lang("cmd_set_daily_quote", f"c1_name{mode}", guild_lang),
                 ping = ping_setting
             ),
            ephemeral=True
        )
