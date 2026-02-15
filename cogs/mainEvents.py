from nextcord.ext import commands
import nextcord

from utils import FQutils, FQdatabase

class MainEventsCog(commands.Cog):
    def __init__(self, client, database: FQdatabase.FQdb, config: FQutils.ConfigReader):
        self.client = client
        self.database = database
        self.config = config

    @commands.Cog.listener()
    async def on_ready(self):
        print("Client is ready.")
        print(f"Bot name: {self.client.user.name}")
        print(f"Bot id: {self.client.user.id}")
        print(f"App id: {self.config.get_bot_id()} - (config file)")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.database.addGuild(guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.database.removeGuild(guild.id)