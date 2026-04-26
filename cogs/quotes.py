import nextcord
from nextcord.ext import commands, application_checks
from nextcord import Interaction, SlashOption, SelectOption, SelectMenu, File, SlashCommandOption
from PIL import Image
from io import BytesIO
from random import randint
import datetime

from utils import FQutils, FQdatabase, Checks
from lang import lang

class QuotesCog(commands.Cog):
    def __init__(self, client, database: FQdatabase.FQdb):
        self.client = client
        self.database = database
        self.image_tool = FQutils.FQimage()

    @nextcord.slash_command(
        name=lang("cmd_make_quote", "name", "en-US"),
        description=lang("cmd_make_quote", "description", "en-US"),
        name_localizations=lang.localizations("cmd_make_quote", "name"),
        description_localizations=lang.localizations("cmd_make_quote", "description"),
    )
    @Checks.onlyGuild()
    async def make_quote(self, interaction: Interaction,
        user: nextcord.User = SlashOption(
            name=lang("cmd_make_quote", "p1_name", "en-US"),
            description=lang("cmd_make_quote", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_make_quote", "p1_name"),
            description_localizations=lang.localizations("cmd_make_quote", "p1_description"),
            required=True
        ),
        quote: str = SlashOption(
            name=lang("cmd_make_quote", "p2_name", "en-US"),
            description=lang("cmd_make_quote", "p2_description", "en-US"),
            name_localizations=lang.localizations("cmd_make_quote", "p2_name"),
            description_localizations=lang.localizations("cmd_make_quote", "p2_description"),
            required=True,
            min_length=3,
            max_length=380
        )
    ):
        await interaction.response.defer()
        self.database.add_quote(user.id, interaction.user.id, interaction.guild.id, quote)
        guild_lang = self.database.getGuildLang(interaction.guild.id)

        avatar_asset = user.display_avatar
        avatar_bytes = await avatar_asset.read()
        avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA")

        ping_list = self.image_tool.list_username_id_from_text(quote)
        ping_map = []
        if ping_list:
            for id in ping_list:
                map_user = await self.client.fetch_user(id)
                ping_map.append({
                    "id": id,
                    "name": map_user.display_name
                })

        guild_name = interaction.guild.name if interaction.guild else "DM"
        creator = str(interaction.user.display_name)
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
            "username": str(user.display_name).upper(),
            "content": quote,
            "creator": creator,
            "guild_name": guild_name,
            "date": datetime.datetime.now(),
            "footer": footer_text,
            "ping_map": ping_map,
            "ping_color": self.database.getGuildColor(interaction.guild.id),
            "background_mode": self.database.getBackgroundMode(interaction.guild.id),
            "background_url": self.database.getGuildBgUrl(interaction.guild.id),
            "bg_postproces": self.database.getGuildBgPost(interaction.guild.id)
        }
        result_img = await self.image_tool.generate_image(image_data)

        buffer = BytesIO()
        result_img.save(buffer, format="PNG")
        buffer.seek(0)

        file = File(buffer, filename="quote.png")

        guildS = interaction.guild.id
        channelS = self.database.getGuildChannel(guildS)
        if channelS is not None:
            try:
                channel = self.client.get_channel(channelS)
                await channel.send(
                    lang("quotes", "generated", guild_lang),
                    file=file
                )
                await interaction.followup.send(
                    lang("quotes", "generated_on", guild_lang, channel=f"<#{channelS}>"),
                    ephemeral=True,
                    delete_after=10
                )
            except Exception:
                await interaction.followup.send(
                    lang("quotes", "channel_error", guild_lang, channel=f"<#{channelS}>"),
                    file=file
                )
        else:
            await interaction.followup.send(
                lang("quotes", "generated", guild_lang),
                file=file
            )

    @nextcord.slash_command(
        name=lang("cmd_random_quote", "name", "en-US"),
        description=lang("cmd_random_quote", "description", "en-US"),
        name_localizations=lang.localizations("cmd_random_quote", "name"),
        description_localizations=lang.localizations("cmd_random_quote", "description")
    )
    @Checks.onlyGuild()
    async def random_quote(
        self,
        interaction: Interaction,
        random_user: nextcord.User = SlashOption(
            name=lang("cmd_random_quote", "p1_name", "en-US"),
            description=lang("cmd_random_quote", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_random_quote", "p1_name"),
            description_localizations=lang.localizations("cmd_random_quote", "p1_description"),
            required=False
        )
    ):
        await interaction.response.defer()
        guild_lang = self.database.getGuildLang(interaction.guild.id)

        if random_user:
            quotes_num = self.database.getNumberOfQuotes(id=random_user.id, by_user=True)
        else:
            quotes_num = self.database.getNumberOfQuotes()

        if quotes_num == 0:
            await interaction.followup.send(
                lang("quotes", "empty_database", guild_lang)
            )
            return

        if random_user:
            quoteD = self.database.get_quotes_by_user(random_user.id)
            if not quoteD:
                await interaction.followup.send(
                    lang("quotes", "empty_database_user", guild_lang)
                )
                return
            rdm_val = randint(0, len(quoteD) - 1)
            quoteD = quoteD[rdm_val]
        else:
            rdm_val = randint(1, quotes_num)
            quoteD = self.database.get_quote(rdm_val)

        if not quoteD:
            await interaction.followup.send(
                lang("quotes", "get_database_failed", guild_lang)
            )
            return

        user = await self.client.fetch_user(quoteD['user_id'])
        creator_user = await self.client.fetch_user(quoteD['creator_id'])
        guild = await self.client.fetch_guild(quoteD['guild_id'])
        date = quoteD['date']
        quote = quoteD['quote']

        avatar_asset = user.display_avatar
        avatar_bytes = await avatar_asset.read()
        avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA")

        ping_list = self.image_tool.list_username_id_from_text(quote)
        ping_map = []
        if ping_list:
            for id in ping_list:
                map_user = await self.client.fetch_user(id)
                ping_map.append({
                    "id": id,
                    "name": map_user.display_name
                })

        guild_name = guild.name if guild else "DM"
        creator = str(creator_user.display_name)
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
            "username": str(user.display_name).upper(),
            "content": quote,
            "creator": creator,
            "guild_name": guild_name,
            "date": date[:4],
            "footer": footer_text,
            "ping_map": ping_map,
            "ping_color": self.database.getGuildColor(interaction.guild.id),
            "background_mode": self.database.getBackgroundMode(interaction.guild.id),
            "background_url": self.database.getGuildBgUrl(interaction.guild.id),
            "bg_postproces": self.database.getGuildBgPost(interaction.guild.id)
        }
        result_img = await self.image_tool.generate_image(image_data)

        buffer = BytesIO()
        result_img.save(buffer, format="PNG")
        buffer.seek(0)

        file = File(buffer, filename="quote.png")

        guildS = interaction.guild.id
        channelS = self.database.getGuildChannel(guildS)
        if channelS is not None:
            try:
                channel = self.client.get_channel(channelS)
                await channel.send(
                    lang("quotes", "generated", guild_lang),
                    file=file
                )
                await interaction.followup.send(
                    lang("quotes", "generated_on", guild_lang, channel=f"<#{channelS}>"),
                    ephemeral=True,
                    delete_after=10
                )
            except Exception:
                await interaction.followup.send(
                    lang("quotes", "channel_error", guild_lang, channel=f"<#{channelS}>"),
                    file=file
                )
        else:
            await interaction.followup.send(
                lang("quotes", "generated", guild_lang),
                file=file
            )

    @nextcord.slash_command(
        name=lang("cmd_stats", "name", "en-US"),
        description=lang("cmd_stats", "description", "en-US"),
        name_localizations=lang.localizations("cmd_stats", "name"),
        description_localizations=lang.localizations("cmd_stats", "description")
    )
    @Checks.onlyGuild()
    async def stats(self, interaction: Interaction,
        user: nextcord.User = SlashOption(
            name=lang("cmd_stats", "p1_name", "en-US"),
            description=lang("cmd_stats", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_stats", "p1_name"),
            description_localizations=lang.localizations("cmd_stats", "p1_description"),
            required=True
        )
    ):
        await interaction.response.defer()

        guild_lang = self.database.getGuildLang(interaction.guild.id)
        guild_color = self.database.getGuildColor(interaction.guild.id)
        quote_count = self.database.count_by_user(user.id)
        created_count = self.database.count_by_creator(user.id)

        embed = nextcord.Embed(
            title= lang("stats", "title", guild_lang, user=user.name),
            description=lang("stats", "description",
               guild_lang,
               quotes=quote_count,
               created=created_count),
                color = nextcord.Color(int(guild_color.lstrip("#"), 16)),
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    @nextcord.slash_command(
        name=lang("cmd_stats_top", "name", "en-US"),
        description=lang("cmd_stats_top", "description", "en-US"),
        name_localizations=lang.localizations("cmd_stats_top", "name"),
        description_localizations=lang.localizations("cmd_stats_top", "description")
    )
    @Checks.onlyGuild()
    async def stats_top(self, interaction: Interaction,
        mode: int = SlashOption(
            name=lang("cmd_stats_top", "p1_name", "en-US"),
            description=lang("cmd_stats_top", "p1_description", "en-US"),
            name_localizations=lang.localizations("cmd_stats_top", "p1_name"),
            description_localizations=lang.localizations("cmd_stats_top", "p1_description"),
            required=True,
            choices={
                lang("cmd_stats_top", "c1_name0", "en-US"): 0,
                lang("cmd_stats_top", "c1_name1", "en-US"): 1
            },
            choice_localizations={
                lang("cmd_stats_top", "c1_name0", "en-US"):
                    lang.localizations("cmd_stats_top", "c1_name0"),
                lang("cmd_stats_top", "c1_name1", "en-US"):
                    lang.localizations("cmd_stats_top", "c1_name1")
            }
        )
    ):
        await interaction.response.defer()
        guild_lang = self.database.getGuildLang(interaction.guild.id)
        guild_color = self.database.getGuildColor(interaction.guild.id)

        if  mode: stats = self.database.getTopByCreator()
        else: stats = self.database.getTopByUser()

        embed = nextcord.Embed(
            title=lang("stats_top", f"title{mode}", guild_lang),
            description=lang("stats_top", f"description{mode}", guild_lang),
            color = nextcord.Color(int(guild_color.lstrip("#"), 16)),
            timestamp=datetime.datetime.now()
        )

        num = 1
        for stat in stats:
            user = await self.client.fetch_user(stat['user_id'])
            embed.add_field(
                name=f"{num}. {user.display_name}",
                value=lang("stats_top", f"crotch{mode}", guild_lang, count=stat['count']),
                inline=False
            )
            num += 1

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )

