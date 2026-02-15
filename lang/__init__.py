import json
import os
import re

LANG_DIR = os.path.dirname(__file__)
translations = {}

for filename in os.listdir(LANG_DIR):
    if filename.endswith(".json"):
        lang_code = filename[:-5]
        filepath = os.path.join(LANG_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                translations[lang_code] = json.load(f)
            except json.JSONDecodeError:
                print(f" > [LANG] Error in language file: {filename}")


def _substitute_placeholders(text: str, values: dict) -> str:
    def repl(match):
        key = match.group(1)
        return str(values.get(key, f"%{key}%"))

    return re.sub(r"%(\w+)%", repl, text)


def lang(key: str, field: str, lang_code: str = "en", **kwargs) -> str:
    val = translations.get(lang_code, {}).get(key, {}).get(field)
    if not val:
        val = translations.get("en", {}).get(key, {}).get(field, f"{key}.{field}")
    if kwargs:
        val = _substitute_placeholders(val, kwargs)
    return val


def localizations(key: str, field: str) -> dict:
    return {
        lang_code: data[key][field]
        for lang_code, data in translations.items()
        if key in data and field in data[key]
    }


def available_languages() -> list[str]:
    return sorted(translations.keys())


def language_display_names() -> dict[str, str]:
    return {
        lang_code: data.get("metadata", {}).get("name", lang_code)
        for lang_code, data in translations.items()
    }


lang.localizations = localizations
lang.available_languages = available_languages
lang.language_display_names = language_display_names
