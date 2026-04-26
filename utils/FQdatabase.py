import sqlite3
import os
from datetime import date

class FQdb:
    def __init__(self, directory, filename):
        os.makedirs(directory, exist_ok=True)
        self.db_path = os.path.join(directory, filename)

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes (
                id integer NOT NULL CONSTRAINT quotes_pk PRIMARY KEY,
                quote text NOT NULL,
                user_id integer NOT NULL,
                creator_id integer NOT NULL,
                guild_id integer NOT NULL,
                date date NOT NULL
            )
        ''')

        self.cursor.execute('''                
            CREATE TABLE IF NOT EXISTS users (
                id integer NOT NULL CONSTRAINT users_pk PRIMARY KEY,
                trusted boolean NOT NULL DEFAULT false,
                create_count integer NOT NULL DEFAULT 0,
                last_use datetime
            )
        ''')

        self.cursor.execute('''                
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id integer NOT NULL PRIMARY KEY,
                lang text NOT NULL DEFAULT 'en-US',
                channel_id integer,
                daily_channel_id integer,
                daily_hour integer,
                daily_minute integer,
                timezone integer DEFAULT 0,
                daily_mode integer DEFAULT 0,
                daily_ping integer,
                color text DEFAULT '#55a8b5',
                background_mode text DEFAULT 'avatar',
                bg_url text,
                bg_post bool DEFAULT true
            )
        ''')
        self.conn.commit()

    def add_quote(self, user_id, creator_id, guild_id, quote, created_date=None):
        if created_date is None:
            created_date = date.today()
        self.cursor.execute('''
                INSERT INTO quotes (quote, user_id, creator_id, guild_id, date)
                VALUES (?, ?, ?, ?, ?)
                ''', (quote, user_id, creator_id, guild_id, created_date))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_quote(self, id):
        self.cursor.execute('SELECT * FROM quotes WHERE id = ?', (id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'quote': row[1],
                'user_id': row[2],
                'creator_id': row[3],
                'guild_id': row[4],
                'date': row[5]
            }
        return None

    def get_quotes_by_user(self, user_id):
        self.cursor.execute('SELECT * FROM quotes WHERE user_id = ?', (user_id,))
        rows = self.cursor.fetchall()
        return [
            {
                'id': row[0],
                'quote': row[1],
                'user_id': row[2],
                'creator_id': row[3],
                'guild_id': row[4],
                'date': row[5]
            }
            for row in rows
        ]

    def get_quotes_by_creator(self, creator_id):
        self.cursor.execute('SELECT * FROM quotes WHERE creator_id = ?', (creator_id,))
        rows = self.cursor.fetchall()
        return [
            {
                'id': row[0],
                'quote': row[1],
                'user_id': row[2],
                'creator_id': row[3],
                'guild_id': row[4],
                'date': row[5]
            }
            for row in rows
        ]

    def count_by_user(self, user_id):
        self.cursor.execute('SELECT COUNT(*) FROM quotes WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()[0]

    def count_by_creator(self, creator_id):
        self.cursor.execute('SELECT COUNT(*) FROM quotes WHERE creator_id = ?', (creator_id,))
        return self.cursor.fetchone()[0]

    def delete_quote_by_id(self, id):
        self.cursor.execute('DELETE FROM quotes WHERE id = ?', (id,))
        self.conn.commit()
        return self.cursor.rowcount  # zwraca liczbe usunietych wierszy (0 lub 1)

    def delete_quotes_by_user(self, user_id):
        self.cursor.execute('DELETE FROM quotes WHERE user_id = ?', (user_id,))
        self.conn.commit()
        return self.cursor.rowcount  # liczba usunietych cytatów

    def delete_quotes_by_creator(self, creator_id):
        self.cursor.execute('DELETE FROM quotes WHERE creator_id = ?', (creator_id,))
        self.conn.commit()
        return self.cursor.rowcount

    def delete_quotes_by_guild(self, guild_id):
        self.cursor.execute('DELETE FROM quotes WHERE guild_id = ?', (guild_id,))
        self.conn.commit()
        return self.cursor.rowcount

    def ensureUserExists(self, user_id):
        self.cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if self.cursor.fetchone() is None:
            self.cursor.execute('''
                INSERT INTO users (id, trusted, create_count, last_use)
                VALUES (?, 0, 0, NULL)
                ''', (user_id,))
            self.conn.commit()

    def hasReachedDailyLimit(self, user_id, limit=5):
        today = date.today()
        self.cursor.execute('''
            SELECT COUNT(*)
            FROM quotes
            WHERE creator_id = ? AND date = ?
            ''', (user_id, today))
        count = self.cursor.fetchone()[0]
        return count >= limit

    def updateUserTrust(self, user_id, trust):
        self.cursor.execute('''
                UPDATE users SET trusted = ?
                WHERE id = ?
                ''', (trust, user_id))
        self.conn.commit()

    def isTrusted(self, user_id):
        self.cursor.execute('SELECT trusted FROM users WHERE id = ?', (user_id,))
        row = self.cursor.fetchone()
        if row is None:
            return False
        return bool(row[0])

    def getTrustedUsers(self):
        self.cursor.execute('SELECT * FROM users WHERE trusted = 1')
        rows = self.cursor.fetchall()
        return [
            {
                'id': row[0],
                'trusted': bool(row[1]),
                'create_count': row[2],
                'last_use': row[3]
            }
            for row in rows
        ]

    def getNumberOfQuotes(self, id=None, by_user=False, by_guild=False):
        if id:
            if by_user:
                self.cursor.execute('SELECT count(*) FROM quotes WHERE user_id = ?', (id,))
            elif by_guild:
                self.cursor.execute('SELECT count(*) FROM quotes WHERE guild_id = ?', (id,))
            else:
                self.cursor.execute('SELECT count(*) FROM quotes WHERE guild_id = ?', (id,))
        else:
            self.cursor.execute('SELECT count(*) FROM quotes')

        result = self.cursor.fetchone()
        return result[0] if result else 0

    def addGuild(self, guild_id):
        self.cursor.execute('''
            INSERT INTO guilds (guild_id)
            VALUES (?)
            ''', (guild_id,))
        self.conn.commit()
        return self.cursor.lastrowid

    def setGuildLang(self, guild_id, lang):
        self.cursor.execute('''
            UPDATE guilds
            SET lang = ?
            WHERE guild_id = ?
        ''', (lang, guild_id))
        self.conn.commit()

    def getGuildLang(self, guild_id):
        self.cursor.execute('''
            SELECT lang
            FROM guilds
            WHERE guild_id = ?
        ''', (guild_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def removeGuild(self, guild_id):
        self.cursor.execute('''
            DELETE
            FROM guilds
            WHERE guild_id = ?
            ''', (guild_id,))
        self.conn.commit()

    def setGuildChannel(self, guild_id, channel_id):
        self.cursor.execute('''
            UPDATE guilds
            SET channel_id = ?
            WHERE guild_id = ?
        ''', (channel_id, guild_id))
        self.conn.commit()

    def clearGuildChannel(self, guild_id):
        self.cursor.execute('''
            UPDATE guilds
            SET channel_id = null
            WHERE guild_id = ?
        ''', (guild_id,))
        self.conn.commit()

    def getGuildChannel(self, guild_id):
        self.cursor.execute('''
            SELECT channel_id
            FROM guilds
            WHERE guild_id = ?
        ''', (guild_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def setGuildDailyChannel(self, guild_id, channel_id):
        self.cursor.execute('''
            UPDATE guilds
            SET daily_channel_id = ?
            WHERE guild_id = ?
        ''', (channel_id, guild_id))
        self.conn.commit()

    def clearGuildDailyChannel(self, guild_id):
        self.cursor.execute('''
            UPDATE guilds
            SET daily_channel_id = null
            WHERE guild_id = ?
        ''', (guild_id,))
        self.conn.commit()

    def setGuildColor(self, guild_id, color):
        self.cursor.execute('''
            UPDATE guilds
            SET color = ?
            WHERE guild_id = ?
            ''', (color, guild_id))
        self.conn.commit()

    def clearGuildColor(self, guild_id):
        self.cursor.execute("PRAGMA table_info(guilds)")
        columns = self.cursor.fetchall()
        default_color = None
        for col in columns:
            if col[1] == "color":
                raw_default = col[4]
                if raw_default and raw_default.startswith("'") and raw_default.endswith("'"):
                    default_color = raw_default[1:-1]
                else:
                    default_color = raw_default
                break

        if default_color is None:
            raise ValueError("No default value defined for 'color' column.")

        self.cursor.execute('''
            UPDATE guilds
            SET color = ?
            WHERE guild_id = ?
        ''', (default_color, guild_id))
        self.conn.commit()

    def setBackgroundMode(self, guild_id, mode: int):
        if mode == 0:
            background_mode = 'avatar'
        elif mode == 1:
            background_mode = 'file'
        elif mode == 2:
            background_mode = 'url'
        else:
            raise ValueError(" > Invalid mode value. It must be 0 - 2.")

        self.cursor.execute('''
            UPDATE guilds
            SET background_mode = ?
            WHERE guild_id = ?
        ''', (background_mode, guild_id))
        self.conn.commit()

    def getBackgroundMode(self, guild_id):
        self.cursor.execute('''
            SELECT background_mode
            FROM guilds
            WHERE guild_id = ?
        ''', (guild_id,))
        result = self.cursor.fetchone()
        return result[0]

    def setGuildBgUrl(self, guild_id, bg_url):
        self.cursor.execute('''
            UPDATE guilds
            SET bg_url = ?
            WHERE guild_id = ?
            ''', (bg_url, guild_id))
        self.conn.commit()

    def setGuildBgPost(self, guild_id, bg_post):
        self.cursor.execute('''
            UPDATE guilds
            SET bg_post = ?
            WHERE guild_id = ?
            ''', (bg_post, guild_id))
        self.conn.commit()

    def clearGuildBgUrl(self, guild_id):
        self.cursor.execute('''
            UPDATE guilds
            SET bg_url = NULL
            WHERE guild_id = ?
            ''', (guild_id,))
        self.conn.commit()

    def clearGuildBgPost(self, guild_id):
        self.cursor.execute('''
            UPDATE guilds
            SET bg_post = NULL
            WHERE guild_id = ?
            ''', (guild_id,))
        self.conn.commit()

    def getGuildColor(self, guild_id):
        self.cursor.execute('''
            SELECT color
            FROM guilds
            WHERE guild_id = ?
            ''', (guild_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def getGuildBgUrl(self, guild_id):
        self.cursor.execute('''
            SELECT bg_url
            FROM guilds
            WHERE guild_id = ?
            ''', (guild_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def getGuildBgPost(self, guild_id):
        self.cursor.execute('''
            SELECT bg_post
            FROM guilds
            WHERE guild_id = ?
            ''', (guild_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def getGuildDailyChannel(self, guild_id):
        self.cursor.execute('''
            SELECT daily_channel_id
            FROM guilds
            WHERE guild_id = ?
        ''', (guild_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def getTopByUser(self, limit=10):
        self.cursor.execute('''
            SELECT user_id, COUNT(*) as user
            FROM quotes
            GROUP BY user_id
            ORDER BY user DESC
            LIMIT ?;
        ''', (limit,))
        rows = self.cursor.fetchall()
        return [
            {
                'user_id': row[0],
                'count': row[1],
            }
            for row in rows
        ]

    def getTopByCreator(self, limit=10):
        self.cursor.execute('''
            SELECT creator_id, COUNT(*) as creator
            FROM quotes
            GROUP BY creator_id
            ORDER BY creator DESC
            LIMIT ?;
        ''', (limit,))
        rows = self.cursor.fetchall()
        return [
            {
                'user_id': row[0],
                'count': row[1],
            }
            for row in rows
        ]

    def setDailyTime(self, guild_id, hour, minute, timezone):
        self.cursor.execute('''
            UPDATE guilds
            SET daily_hour   = ?,
                daily_minute = ?,
                timezone     = ?
            WHERE guild_id = ?
            ''', (hour, minute, timezone, guild_id))
        self.conn.commit()

    def getDailyTime(self, guild_id):
        self.cursor.execute('''
            SELECT daily_hour, daily_minute, timezone
            FROM guilds
            WHERE guild_id = ?
            ''', (guild_id,))
        result = self.cursor.fetchone()
        if result:
            return {
                "hour": result[0],
                "minute": result[1],
                "timezone": result[2]
            }
        return None

    def setDailyMode(self, guild_id, mode):
        self.cursor.execute('''
            UPDATE guilds
            SET daily_mode = ?
            WHERE guild_id = ?
            ''', (mode, guild_id))
        self.conn.commit()

    def getDailyMode(self, guild_id):
        self.cursor.execute('''
            SELECT daily_mode
            FROM guilds
            WHERE guild_id = ?
            ''', (guild_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def clearGuildDaily(self, guild_id):
        self.cursor.execute('''
            UPDATE guilds
            SET daily_channel_id = NULL,
                daily_hour = NULL,
                daily_minute = NULL,
                daily_ping = NULL,
                timezone = 0,
                daily_mode = 0
            WHERE guild_id = ?
            ''', (guild_id,))
        self.conn.commit()

    def setDailyPing(self, guild_id, ping):
        self.cursor.execute('''
            UPDATE guilds
            SET daily_ping = ?
            WHERE guild_id = ?
            ''', (ping, guild_id))
        self.conn.commit()

    def getDailyPing(self, guild_id):
        self.cursor.execute('''
            SELECT daily_ping
            FROM guilds
            WHERE guild_id = ?
            ''', (guild_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def clearDailyPing(self, guild_id):
        self.cursor.execute('''
            UPDATE guilds
            SET daily_ping = NULL
            WHERE guild_id = ?
            ''', (guild_id,))
        self.conn.commit()


