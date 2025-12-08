from datetime import datetime, timedelta

from api_request import get_yesterday_music_stats
from loaded_dotenv import USER_TG_ID
from stats_manager import MusicStats, StatsStorage


async def check_new_data(bot=None):
    """Получаем свежие данные и проверяем, отличаются ли они от последних сохраненных."""
    storage = StatsStorage()

    # Определяем дату для сохранения (вчерашний день)
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    total_seconds, total_tracks = await get_yesterday_music_stats(bot)

    if total_seconds is None or total_tracks is None:
        return False, None, None, None, yesterday_date

    latest_stats = storage.get_latest_stats()
    has_new = not (
        latest_stats
        and latest_stats.total_seconds == total_seconds
        and latest_stats.total_tracks == total_tracks
    )

    return has_new, total_seconds, total_tracks, latest_stats, yesterday_date


async def main(bot=None, prefetched=None):
    """
    Основная логика сохранения статистики и отправки уведомления.
    Если prefetched передан, используем уже полученные данные, чтобы не делать повторный запрос.
    """
    storage = StatsStorage()

    if prefetched:
        has_new, total_seconds, total_tracks, latest_stats, yesterday_date = prefetched
    else:
        has_new, total_seconds, total_tracks, latest_stats, yesterday_date = (
            await check_new_data(bot)
        )

    if total_seconds is None or total_tracks is None:
        message = "❌ Не удалось получить данные из API Яндекса"
        if bot and USER_TG_ID:
            await bot.send_message(USER_TG_ID, message)
        return False

    if not has_new:
        return False

    # Создаем объект статистики за вчера
    yesterday_stats = MusicStats(yesterday_date, total_seconds, total_tracks)

    # Вычисляем дневную разницу (сколько было прослушано вчера)
    yesterday_seconds_diff, yesterday_tracks_diff = storage.calculate_daily_diff(
        yesterday_stats, latest_stats
    )

    # Сохраняем данные за вчера
    all_stats = storage.load_all_stats()
    all_stats.append(yesterday_stats)
    all_stats.sort(key=lambda x: x.date)
    storage.save_stats(all_stats)

    # Отправляем результаты только если есть новые данные
    if yesterday_seconds_diff > 0 or yesterday_tracks_diff > 0:
        hrs_y = yesterday_seconds_diff / 3600
        mins_y = yesterday_seconds_diff // 60

        # Данные за месяц
        now = datetime.now()
        month_stats = storage.get_monthly_stats(now.year, now.month)

        if month_stats:
            hrs_m = month_stats.total_seconds / 3600
            mins_m = month_stats.total_seconds // 60
            total_tracks_m = month_stats.total_tracks
        else:
            hrs_m = 0
            mins_m = 0
            total_tracks_m = 0

        message = (
            f"ВЧЕРА\n"
            f"{hrs_y:.02f} часов\n"
            f"({mins_y:.0f} мин.)\n"
            f"{yesterday_tracks_diff} треков\n"
            f"\n"
            f"ЗА МЕСЯЦ\n"
            f"{hrs_m:.0f} часов\n"
            f"({mins_m:.0f} мин.)\n"
            f"{total_tracks_m} треков"
        )

        if bot and USER_TG_ID:
            await bot.send_message(USER_TG_ID, message)

    return True


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
