import nextcord
from nextcord.ext import commands
from utils import FQutils, FQdatabase

def main():
    database = FQdatabase.FQdb('./data', 'foxquotes.db')
    config = FQutils.ConfigReader('config.json')

    supervisors = config.get_supervisors()

    intents = nextcord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True

    client = commands.Bot(intents=intents)


    payload = {
        'client': client,
        'database': database,
        'config': config,
        'supervisors': supervisors
    }

    FQutils.FQLoader(payload)

    client.run(config.get_bot_token())

if __name__ == '__main__':
    main()

###
# to do
# przebudowac generator o tryby serwera, rozbudowe info
# zablokowac użycia per dzień
# usuwanie cytatów CLI
# report cytatów
# daily cytaty - event
