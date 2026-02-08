import requests
import asyncio
from loaded_dotenv import TOKEN_YANDEX, USER_TG_ID
import json


async def get_top_artists_month(bot=None, return_debug_info=False):
    """Получает топ-5 артистов за текущий месяц из API Яндекс.Музыки"""

    url = "https://api.music.yandex.ru/personal/top/artists/month"
    headers = {"Authorization": f"OAuth {TOKEN_YANDEX}"}

    try:
        response = requests.get(url, headers=headers)

        debug_data = {
            "url_with_token": f"{url}?OAuth={TOKEN_YANDEX}",
            "status_code": response.status_code,
        }

        if response.status_code != 200:
            if return_debug_info:
                return None, debug_data
            return None

        try:
            data = response.json()

            if isinstance(data, dict) and "error" in data:
                if return_debug_info:
                    debug_data["error"] = data["error"]
                    return None, debug_data
                return None

        except ValueError:
            if return_debug_info:
                debug_data["error"] = "JSON parse error"
                return None, debug_data
            return None

        if "artists" not in data or not data["artists"]:
            if bot and USER_TG_ID:
                await bot.send_message(
                    USER_TG_ID, "Нет данных об артистах в ответе API"
                )
            if return_debug_info:
                return None, debug_data
            return None

        top_artists = []
        for i, artist_data in enumerate(data["artists"][:5], 1):
            artist_info = {
                "position": i,
                "name": artist_data["artist"]["name"],
                "listen_time_formatted": f"{(artist_data['listenTimeSeconds'] / 3600):.01f}",
            }
            top_artists.append(artist_info)

        if return_debug_info:
            return top_artists, debug_data
        return top_artists

    except Exception as e:
        if bot and USER_TG_ID:
            await bot.send_message(USER_TG_ID, f"Ошибка: {e}")
        if return_debug_info:
            return None, {
                "url_with_token": f"{url}?OAuth={TOKEN_YANDEX}",
                "status_code": None,
                "error": str(e),
            }
        return None


def format_artists_output(artists):
    """Форматирует список артистов для вывода"""
    if not artists:
        return "Нет данных о топ артистах"

    output = "Топ-5 артистов за месяц:\n"

    for artist in artists:
        output += f"{artist['position']}. {artist['name']}: {artist['listen_time_formatted']} Ч.\n"

    return output


ARTISTS_CACHE_FILE = "top_artists.json"


def load_cached_artists():
    """Загружает предыдущий топ артистов из файла"""
    try:
        with open(ARTISTS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_artists_cache(artists):
    """Сохраняет топ артистов в файл"""
    with open(ARTISTS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)


def artists_changed(new_artists, old_artists):
    """Проверяет, изменился ли топ артистов"""
    if old_artists is None:
        return True
    if len(new_artists) != len(old_artists):
        return True
    for new, old in zip(new_artists, old_artists):
        if (
            new["name"] != old["name"]
            or new["listen_time_formatted"] != old["listen_time_formatted"]
        ):
            return True
    return False


if __name__ == "__main__":

    async def main():
        artists, debug_info = await get_top_artists_month(return_debug_info=True)

        print(f"URL с токеном: {debug_info['url_with_token']}")
        print(f"Статус: {debug_info['status_code']}")
        if "error" in debug_info:
            print(f"Ошибка: {debug_info['error']}")
        print("=" * 40)

        if artists:
            print(format_artists_output(artists))
        else:
            print("Не удалось получить данные")

    asyncio.run(main())
