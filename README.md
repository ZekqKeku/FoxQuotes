# FoxQuotes

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

FoxQuotes is an advanced Discord bot designed to generate stylish quote graphics based on user messages. It allows you to immortalize funny or important moments from your server in the form of aesthetic images.

## Features
- **Graphic Generation**: Create high-quality images featuring the quote, user avatar, and a personalized background.
- **Full Customization**: Change accent colors, backgrounds (avatar, URL, or local file), and image post-processing settings.
- **Localization**: Full support for English and Polish. New languages can be added easily by creating a JSON file in the `lang/` directory. If you'd like to contribute a new translation, I'm interested!
- **Statistics**: Track the most quoted individuals and the most active quote creators.
- **Daily Quotes**: Automatically send a random quote at a specific time to a designated channel.

## Running the Bot (Native)

Currently, the project supports direct execution via the Python interpreter. Support for **Docker** is planned for the future.

### Requirements
- Python 3.8 or newer
- Libraries listed in `requirements.txt`

### Installation Steps
1. Clone the repository.
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the `config.json` file (description below).
4. Start the bot:
   ```bash
   python main.py
   ```

## Configuration (`config.json`)

Before starting, you must complete the `config.json` file located in the root directory:

```json
{
  "bot": {
    "token": "YOUR_BOT_TOKEN"
  },
  "discord": {
    "supervisors": [
      "BOT_ADMINISTRATOR_ID"
    ]
  }
}
```
- `token`: The bot token obtained from the Discord Developer Portal.
- `supervisors`: A list of user IDs who have administrative permissions within the bot (optional).

## Commands

The bot exclusively uses **Slash Commands (/)**.

### General Commands
- `/make_quote [user] [text]` - Generates a new quote graphic.
- `/random_quote [user]` - Retrieves a random quote from the database (filtering by user is optional).
- `/stats [user]` - Displays quote statistics for a specific person.
- `/stats_top [mode]` - Shows a list of the top 10 most quoted people or the most active creators.

### Settings Commands (`/settings`)
- `/settings set_channel [channel]` - Changes the text channel where the bot sends generated quotes.
- `/settings set_lang [language]` - Changes the bot's language on the server.
- `/settings dummy_image [text]` - Generates a sample image to check current visual settings.
- `/settings set_color [hex]` - Changes the accent color on the graphics.
- `/settings set_background [url]` - Sets a custom background from an image URL.
- `/settings set_bg_mode [mode]` - Selects the background source (User Avatar, Default File, or URL).
- `/settings set_background_postprocess [on/off]` - Toggles blur and desaturation for the URL background.
- `/settings set_daily_quote` - Configures automatic daily quotes (channel, time, timezone, repeat mode, role ping).

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** license.

- **Non-Commercial Use**: Commercial use of this software is strictly reserved for the original author.
- **Attribution**: Any forks or redistributions of this code must include a prominent link back to the original repository and provide proper attribution to the author.

For more details, see the [LICENSE](LICENSE) file.

---
*FoxQuotes Project - Immortalize words with style.*
