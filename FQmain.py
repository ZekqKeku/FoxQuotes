try:
    from nextcord.ext import commands
    from utils import FQutils, FQdatabase
    import nextcord

except:
    raise RuntimeError('\n > Failed to load libraries!\n')

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
# przebudowac genertor o tryby serwera, debudowe info
# zblkowac użycia per dzień
# usuwanie cyatatów CLI
# report cytatów
# daily cytaty - event
