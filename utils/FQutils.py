import os
import json
import datetime
import calendar
import importlib
import inspect
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageStat
from pathlib import Path
import math
import re

class ConfigReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.config_data = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Config file not found: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_bot_token(self):
        return self.config_data.get("bot", {}).get("token", "")

    def get_supervisors(self):
        return self.config_data.get("discord", {}).get("supervisors", [])


class FQimage:
    # === Configuration / Konfiguracja ===
    def __init__ (self):
        self.width = 1280
        self.height = 720
        self.bg_color = (0, 0, 0)
        self.margin = 70

        # Font sizes / Rozmiary fontów
        self.username_font_size = 72
        self.quote_base_font_size = 36
        self.footer_font_size = 30
        self.footer_small_font_size = 28
        self.date_font_size = 80

        # Quote layout / Układ cytatu
        self.wrap_max_width = 780
        self.quote_font_scale = (1.0, 3.0)
        self.quote_scaling_strength = 0.75
        self.quote_center_x_ratio = 1 / 3
        self.quote_offset_x = 80
        self.quote_offset_y = 30
        self.line_spacing = 10

        # Avatar / Awatar
        self.avatar_foreground_size = (275, 275)
        self.avatar_background_blur_radius = 20
        self.avatar_background_opacity = 0.75
        self.avatar_position = (self.width * 2 // 3 + 110, 40)

        # Drop shadow / Cień
        self.shadow_angle = 136
        self.shadow_distance = 5
        self.shadow_blur_radius = 15
        self.shadow_opacity = 0.25
        self.shadow_color = (0, 0, 0)

        # Footer / Stopka
        self.footer_offset_y = 10
        self.footer_gradient_height = 100

        # Load fonts / Wczytaj fonty
        self.text_font_base = self.load_font(["FuzzyBubbles-Regular.ttf", "arial.ttf", "DejaVuSans.ttf"], self.quote_base_font_size)
        self.title_font = self.load_font(["AkayaKanadaka-Regular.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"], self.username_font_size)
        self.quote_font_list = ["FuzzyBubbles-Regular.ttf", "arial.ttf", "DejaVuSans.ttf"]
        self.date_font = self.load_font(["FuzzyBubbles-Bold.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"], self.date_font_size)
        self.footer_small_font = self.load_font(["arial.ttf", "DejaVuSans.ttf"], self.footer_small_font_size)


    # === Font Loading / Ładowanie fontów ===
    def load_font(self, font_names, size):
        static_path = Path(__file__).resolve().parent.parent / "static"
        for name in font_names:
            font_path = static_path / name
            if font_path.exists():
                return ImageFont.truetype(str(font_path), size)
        for name in font_names:
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue
        raise RuntimeError(f"Nie znaleziono żadnego z fontów: {font_names}")


    # === Drop Shadow Drawing / Rysowanie z cieniem ===
    def draw_text_with_shadow(self, base_image, position, text, font, fill="white", anchor="lt", apply_shadow=True):
        if apply_shadow:
            angle_rad = math.radians(self.shadow_angle)
            offset_x = int(self.shadow_distance * math.cos(angle_rad))
            offset_y = int(self.shadow_distance * math.sin(angle_rad))

            text_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_layer)
            shadow_pos = (position[0] + offset_x, position[1] + offset_y)
            text_draw.text(shadow_pos, text, font=font, fill=self.shadow_color + (int(255 * self.shadow_opacity),),anchor=anchor)
            blurred = text_layer.filter(ImageFilter.GaussianBlur(self.shadow_blur_radius))
            base_image.alpha_composite(blurred)

        draw = ImageDraw.Draw(base_image)
        draw.text(position, text, font=font, fill=fill, anchor=anchor)

    def draw_multicolor_text(self, draw, img, pos, text, font, nick_color, anchor="lt"):
        segments = re.split(r"(\[\[\[.*?\]\]\])", text)
        x, y = pos
        for segment in segments:
            if not segment:
                continue
            if segment.startswith("[[[") and segment.endswith("]]]"):
                content = segment[3:-3]
                fill = nick_color
            else:
                content = segment
                fill = "white"
            size = draw.textlength(content, font=font)
            self.draw_text_with_shadow(img, (x, y), content, font=font, fill=fill, anchor=anchor, apply_shadow=True)
            x += size


    # === Text Wrapping / Zawijanie tekstu ===
    def list_username_id_from_text(self, text: str):
        pattern = r"<@(\d+)>"
        list = re.findall(pattern, text)
        return list

    def replace_pings(self, text, ping_map, color):
        pattern = r"<@(\d+)>"
        color = self.hex_to_rgb(color) if color else (255, 255, 255)

        def repl(match):
            user_id = match.group(1)
            name = next((entry['name'] for entry in ping_map if str(entry.get('id')) == user_id), None)
            if name:
                return f" [[[@{name}]]] "
            else:
                return match.group(0)

        return re.sub(pattern, repl, text), color

    def split_into_syllables(self, word):
        vowels = "aeiouyąęóAEIOUYĄĘÓ"
        forbidden_clusters = ["ch", "cz", "dz", "dź", "dż", "rz", "sz",
                              "qu", "ph", "th", "tion", "sion", "stion",
                              "ght", "ck", "sh", "wh", "ng", "poke"]

        # Zasada 4: nie dzielimy skrótów, liczb i nazw własnych
        if word.isupper() or word.istitle() or word.isdigit() or '.' in word:
            # Dzielenie krytyczne co 5 znaków
            return [word[i:i + 5] for i in range(0, len(word), 5)]

        # Zasada 3: nie dzielimy jednosylabowych, ale zastosuj dzielenie awaryjne
        syllable_count = sum(1 for c in word if c in vowels)
        if syllable_count <= 1:
            return [word[i:i + 5] for i in range(0, len(word), 5)]

        chars = list(word)
        length = len(chars)
        result = []
        current = ""
        i = 0

        while i < length:
            current += chars[i]
            next_vowel = i + 1 < length and chars[i + 1] in vowels

            # Sprawdź zbitki zakazane (czy nie zaczynają się od obecnej pozycji)
            fragment = ''.join(chars[i:i + 4]).lower()
            if any(fragment.startswith(cluster) for cluster in forbidden_clusters):
                i += 1
                continue

            # Jeśli obecny znak to samogłoska i następny nie jest samogłoską → potencjalna sylaba
            if chars[i] in vowels and (i + 1 >= length or chars[i + 1] not in vowels):
                # Nie zostawiamy/przenosimy pojedynczej litery
                if len(current) == 1 and result:
                    result[-1] += current
                    current = ""
                else:
                    result.append(current)
                    current = ""

            i += 1

        if current:
            if result:
                result[-1] += current
            else:
                result = [current]

        # Scal jeśli jakaś sylaba ma długość 1 (np. końcowa litera)
        for i in range(1, len(result)):
            if len(result[i]) == 1:
                result[i - 1] += result[i]
                result[i] = ""
        result = [s for s in result if s]

        # Jeśli nadal tylko jedna część — zastosuj dzielenie krytyczne
        return result if len(result) > 1 else [word[i:i + 5] for i in range(0, len(word), 5)]

    def wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
        import re

        tokens = re.split(r'(\[\[\[.*?\]\]\])', text)
        lines = []
        current_line = ''

        for token in tokens:
            if not token:
                continue

            # === Jeśli to [[[nick]]] ===
            if token.startswith('[[[') and token.endswith(']]]'):
                nick = token[3:-3]  # bez [[[ i ]]]
                test_line = current_line + token
                if draw.textlength(test_line.replace("[[[", "").replace("]]]", ""), font=font) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = ''
                    syllables = self.split_into_syllables(nick)
                    temp_line = ''
                    for i, syll in enumerate(syllables):
                        test = temp_line + syll
                        if draw.textlength(test, font=font) <= max_width:
                            temp_line = test
                        else:
                            if temp_line:
                                lines.append(f'[[[{temp_line}-]]]')
                            temp_line = f'-{syll}'
                    if temp_line:
                        lines.append(f'[[[{temp_line}]]]')

            else:
                # === Inny tekst – rozbij na słowa i białe znaki ===
                for word in re.split(r'(\s+)', token):
                    test_line = current_line + word
                    if draw.textlength(test_line.replace("[[[", "").replace("]]]", ""), font=font) <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        if draw.textlength(word.replace("[[[", "").replace("]]]", ""), font=font) <= max_width:
                            current_line = word
                        else:
                            syllables = self.split_into_syllables(word)
                            for i, syl in enumerate(syllables):
                                if i == 0 and not current_line:
                                    current_line = syl
                                else:
                                    if draw.textlength(current_line + syl, font=font) <= max_width:
                                        current_line += syl
                                    else:
                                        lines.append(current_line + '-')
                                        current_line = '-' + syl
        if current_line:
            lines.append(current_line)
        return lines

    def hyphenate_long_word(self, word: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> \
    list[str]:
        parts = []
        current = ''
        for char in word:
            test = current + char
            if draw.textlength(test.replace("[[[", "").replace("]]]", ""), font=font) <= max_width:
                current = test
            else:
                if current:
                    parts.append(current + '-')
                current = '-' + char
        if current:
            parts.append(current)
        return parts


    # === Quote Scaling / Skalowanie cytatu ===
    def calculate_quote_scale(self, text_length):
        min_scale, max_scale = self.quote_font_scale
        min_len, max_len = 10, 400
        clamped = max(min_len, min(max_len, text_length))
        t = 1 - ((clamped - min_len) / (max_len - min_len))
        s = self.quote_scaling_strength
        t = t ** (1 + 4 * s) if s > 0 else t ** (1 / (1 - 4 * s))
        return min_scale + (max_scale - min_scale) * t


    # === Avatar Background Processing / Tło avatara ===
    def create_bottom_gradient(self, height):
        gradient = Image.new("L", (1, height), color=0xFF)
        for y in range(height):
            alpha = int(255 * (y / height) * 0.75)
            gradient.putpixel((0, y), alpha)
        alpha_gradient = gradient.resize((self.width, height))
        black_img = Image.new("RGBA", (self.width, height), color=(0, 0, 0, 255))
        black_img.putalpha(alpha_gradient)
        return black_img

    def normalize_brightness(self, img):
        grayscale = img.convert("L")
        stat = ImageStat.Stat(grayscale)
        avg = stat.mean[0]
        ideal = 127.5
        factor = ideal / avg if avg > 0 else 1.0
        img = ImageEnhance.Brightness(grayscale.convert("RGB")).enhance(factor)
        return Image.merge("RGBA", (*img.split(), Image.new("L", img.size, 255)))

    # === HEX to RGB / Konwersja koloru ===
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        raise ValueError(f" > [Utils] Invalid hex color, HEX: {hex_color}")


    # === Main Image Rendering / Główna metoda generująca obraz ===
    async def fetch_image(self, url: str) -> Image.Image:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.read()
                        return Image.open(BytesIO(data))
        except Exception as e:
            print(f" > [FQimage] Error fetching image from {url}: {e}")
        return None

    async def generate_image(self, data: dict) -> Image.Image:
        avatar = data["avatar"].convert("RGBA")
        username = data["username"]
        content = data["content"]
        creator = data["creator"]
        guild_name = data["guild_name"]
        date = data["date"]
        footer_text = data["footer"]
        ping_map = data["ping_map"]
        ping_color = data["ping_color"]

        bg_mode = data.get("background_mode", "avatar")
        bg_url = data.get("background_url")
        bg_postprocess = data.get("bg_postproces", True)

        if isinstance(date, datetime.datetime):
            date = date.strftime("%Y")
        date = f"~{date[:1]}k{date[2:]}"

        img = Image.new("RGBA", (self.width, self.height), self.bg_color)

        # --- Background Logic ---
        background_img = None
        if bg_mode == "url" and bg_url:
            background_img = await self.fetch_image(bg_url)

        # Default to avatar background if mode is 'avatar' or if URL fetch failed
        if background_img is None:
            background_img = avatar.copy()

        # Process Background
        background_img = background_img.convert("RGBA")

        # Aspect fill resize
        bg_w, bg_h = background_img.size
        aspect_ratio = bg_w / bg_h
        target_ratio = self.width / self.height

        if aspect_ratio > target_ratio:
            # Image is wider than target
            new_h = self.height
            new_w = int(new_h * aspect_ratio)
        else:
            # Image is taller than target
            new_w = self.width
            new_h = int(new_w / aspect_ratio)

        background_img = background_img.resize((new_w, new_h), Image.LANCZOS)

        # Center crop
        left = (new_w - self.width) / 2
        top = (new_h - self.height) / 2
        background_img = background_img.crop((int(left), int(top), int(left + self.width), int(top + self.height)))

        if bg_postprocess:
            background_img = background_img.convert("L").convert("RGBA")
            background_img = self.normalize_brightness(background_img)
            background_img = background_img.filter(ImageFilter.GaussianBlur(self.avatar_background_blur_radius))
            background_img.putalpha(int(255 * self.avatar_background_opacity))

        img.alpha_composite(background_img)

        # --- Foreground Elements ---
        draw = ImageDraw.Draw(img)

        # Avatar foreground with shadow
        avatar_foreground = ImageEnhance.Color(avatar.resize(self.avatar_foreground_size)).enhance(0.5)
        mask = Image.new("L", self.avatar_foreground_size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, *self.avatar_foreground_size), fill=255)
        shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        angle_rad = math.radians(self.shadow_angle)
        dx = int(self.shadow_distance * math.cos(angle_rad))
        dy = int(self.shadow_distance * math.sin(angle_rad))
        pos = tuple(map(int, self.avatar_position))
        shadow_layer.paste((*self.shadow_color, int(255 * self.shadow_opacity)), (pos[0] + dx, pos[1] + dy), mask)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(self.shadow_blur_radius))
        img.alpha_composite(shadow_layer)
        img.paste(avatar_foreground, pos, mask)

        # Username
        self.draw_text_with_shadow(img, (self.margin, self.margin), username, font=self.title_font)

        # Quote
        if ping_map:
            content, resolved_ping_color = self.replace_pings(content, ping_map, ping_color)
        else:
            resolved_ping_color = (255, 255, 255)

        # Skalowanie fontu względem długości tekstu
        quote_font_size = int(self.quote_base_font_size * self.calculate_quote_scale(len(content)))
        quote_font = self.load_font(self.quote_font_list, quote_font_size)

        # Zawijanie tekstu z nickami
        wrapped_lines = self.wrap_text(content, quote_font, self.wrap_max_width, draw)

        # Rysowanie tekstu
        block_height = len(wrapped_lines) * (quote_font_size + self.line_spacing)
        current_y = int((self.height - block_height) / 2) + self.quote_offset_y
        for line in wrapped_lines:
            text_width = draw.textlength(line.replace("[[[", "").replace("]]]", ""), font=quote_font)
            x = int(self.width * self.quote_center_x_ratio) + self.quote_offset_x - text_width // 2
            self.draw_multicolor_text(draw, img, (x, current_y), line, quote_font, resolved_ping_color)
            current_y += quote_font_size + self.line_spacing

        # Date
        date_width = draw.textlength(date, font=self.date_font)
        self.draw_text_with_shadow(img, (self.width - self.margin - date_width, self.height - 190), date,
                                   font=self.date_font)

        # Footer
        footer_width = draw.textlength(footer_text, font=self.footer_small_font)
        footer_y = self.height - self.margin + self.footer_offset_y
        gradient = self.create_bottom_gradient(self.footer_gradient_height)
        img.alpha_composite(gradient, (0, self.height - self.footer_gradient_height))
        draw = ImageDraw.Draw(img)
        draw.text(((self.width - footer_width) / 2, footer_y), footer_text, font=self.footer_small_font, fill="white",
                  anchor="lt")

        return img


class FQLoader:
    def __init__(self, payload: dict[str, any], folder="cogs"):
        self.payload = payload
        self.client = payload.get("client")
        self.folder = folder

        for filename in os.listdir(self.folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"{self.folder}.{filename[:-3]}"
                class_name = filename[:-3][0].upper() + filename[:-3][1:] + "Cog"

                try:
                    module = importlib.import_module(module_name)
                    cog_class = getattr(module, class_name)

                    sig = inspect.signature(cog_class.__init__)
                    params = list(sig.parameters)[1:]

                    args_map = {
                        "client": self.payload['client'],
                        "database": self.payload['database'],
                        "config": self.payload['config'],
                        "supervisors": self.payload['supervisors']
                    }

                    args = [args_map[p] for p in params if p in args_map]

                    cog_instance = cog_class(*args)
                    self.client.add_cog(cog_instance)

                    print(f"Loaded: {class_name}")
                except (ImportError, AttributeError, TypeError) as e:
                    print(f"\n > Failed to load: {module_name}.{class_name}: {e}\n")


class DateTools:
    @staticmethod
    def short_year(year: int):
        current_year = str(datetime.datetime.now().year)
        year_str = str(year)

        if len(year_str) == 3:
            return int(current_year[:1] + year_str)
        elif len(year_str) == 2:
            return int(current_year[:2] + year_str)
        elif len(year_str) == 1:
            return int(current_year[:3] + year_str)
        else:
            return int(current_year)

    @staticmethod
    def short_number(num: int):
        if num > 9: return str(num)
        else: return f"0{num}"

    @staticmethod
    def is_date_in_past(year, month, day, hour, minute):
        selected_date = datetime.datetime(year, month, day, hour, minute, 0)
        current_date = datetime.datetime.today()

        return selected_date < current_date

    @staticmethod
    def get_days_in_month(year, month):
        return calendar.monthrange(year, month)[1]
