import requests
from datetime import datetime
from loaded_dotenv import TOKEN_YANDEX, USER_TG_ID


async def get_yesterday_music_stats(bot=None):
    """Получает статистику прослушиваний за вчерашний день из API Яндекса"""
    # В API мы запрашиваем данные за текущий месяц, но получаем данные с задержкой (фактически за вчера)
    now = datetime.now()
    year = str(now.year)
    month = str(now.month)

    url = "https://api.plus.yandex.ru/graphql"

    oauth_token = TOKEN_YANDEX
    headers = {
        "Authorization": f"OAuth {oauth_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": "\n    query entertainmentStatistics($input: StatisticsInput!) {\n  user {\n    entertainmentStatistics(input: $input) {\n      alltimeStartDate\n      afisha {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      bookmate {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      city {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      daily {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      delivery {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      eda {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      kinopoisk {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      lavka {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      market {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      music {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      taxi {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      zapravki {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n      plus {\n        type\n        valueWrapper {\n          ... on LongValue {\n            value\n          }\n        }\n      }\n    }\n  }\n}\n    ",
        "variables": {
            "input": {"period": {"month": month, "year": year}, "scale": "MONTH"}
        },
        "operationName": "entertainmentStatistics",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            error_message = f"❌ Ошибка запроса к API Яндекса\nСтатус: {response.status_code}\nОтвет: {response.text}"
            if bot and USER_TG_ID:
                await bot.send_message(USER_TG_ID, error_message)
            return None, None

        data = response.json()
        music_list = data["data"]["user"]["entertainmentStatistics"]["music"]

        if len(music_list) > 8:
            music_time = music_list[8]["valueWrapper"]["value"]  # MUSIC_USAGE_TIME
            music_count = music_list[7]["valueWrapper"]["value"]  # MUSIC_USAGE_CNT
            return music_time, music_count
        else:
            error_message = "❌ Недостаточно данных в разделе music."
            if bot and USER_TG_ID:
                await bot.send_message(USER_TG_ID, error_message)
            return None, None

    except Exception as e:
        error_message = f"❌ Ошибка при работе с API: {e}"
        if bot and USER_TG_ID:
            await bot.send_message(USER_TG_ID, error_message)
        return None, None
