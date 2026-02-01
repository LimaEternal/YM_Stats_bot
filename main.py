from datetime import datetime
from api_request import get_yesterday_music_stats
from loaded_dotenv import USER_TG_ID

# Импортируем твою глобальную переменную
from stats_manager import MusicStats, StatsStorage, day_before_yesterday_date


async def check_new_data(bot=None):
    """Получаем свежие данные и проверяем, отличаются ли они от последних сохраненных."""
    storage = StatsStorage()

    # Передаем bot в функцию запроса
    total_seconds, total_tracks = await get_yesterday_music_stats(bot)

    # Если API вернул None (ошибка), возвращаем False
    if total_seconds is None or total_tracks is None:
        return False, None, None, None, day_before_yesterday_date

    latest_stats = storage.get_latest_stats()
    has_new = not (
        latest_stats
        and latest_stats.total_seconds == total_seconds
        and latest_stats.total_tracks == total_tracks
    )

    return has_new, total_seconds, total_tracks, latest_stats, day_before_yesterday_date


async def main(bot=None, prefetched=None, user_id_override=None):
    storage = StatsStorage()
    """
    Основная логика сохранения статистики и отправки уведомления.
    """
    storage = StatsStorage()

    # Определяем, кому слать сообщение: тому, кто прописал /start, или тому, кто в .env
    # Если user_id_override передан, используем его. Если нет — берем из .env
    target_user_id = user_id_override or USER_TG_ID

    if prefetched:
        (
            has_new,
            total_seconds,
            total_tracks,
            latest_stats,
            _,  # Дата уже есть глобально, здесь можно пропустить
        ) = prefetched
    else:
        (
            has_new,
            total_seconds,
            total_tracks,
            latest_stats,
            _,
        ) = await check_new_data(bot)

    if total_seconds is None or total_tracks is None:
        message = "Не удалось получить данные из API Яндекса"
        # ТУТ ИЗМЕНЕНИЕ: используем target_user_id
        if bot and target_user_id:
            await bot.send_message(target_user_id, message)
        return False

    if not has_new:
        # Если это ручной запуск через /start, можно уведомить, что данных нет
        if bot and user_id_override:
            await bot.send_message(
                user_id_override, "Статистика не изменилась, новых данных пока нет."
            )
        return False

    # Превращаем объект datetime в строку "YYYY-MM-DD", чтобы он совпадал с форматом в JSON
    date_str = day_before_yesterday_date.strftime("%Y-%m-%d")

    # Создаем объект с датой-строкой
    yesterday_stats = MusicStats(date_str, total_seconds, total_tracks)

    # Вычисляем дневную разницу
    yesterday_seconds_diff, yesterday_tracks_diff = storage.calculate_daily_diff(
        yesterday_stats, latest_stats
    )

    # Сохраняем данные за вчера
    all_stats = storage.load_all_stats()
    all_stats.append(yesterday_stats)

    # Теперь сортировка сработает, так как все даты - строки
    all_stats.sort(key=lambda x: x.date)
    storage.save_stats(all_stats)

    # Отправляем результаты
    if yesterday_seconds_diff > 0 or yesterday_tracks_diff > 0:
        hrs_y = yesterday_seconds_diff / 3600
        mins_y = yesterday_seconds_diff // 60

        month_stats = storage.get_monthly_stats(
            day_before_yesterday_date.year, day_before_yesterday_date.month
        )

        if month_stats:
            hrs_m = month_stats.total_seconds / 3600
            mins_m = month_stats.total_seconds // 60
            total_tracks_m = month_stats.total_tracks
        else:
            hrs_m = 0
            mins_m = 0
            total_tracks_m = 0

        message = (
            f"ПОЗАВЧЕРА\n"
            f"{hrs_y:.02f} часов\n"
            f"({mins_y:.0f} мин.)\n"
            f"{yesterday_tracks_diff} треков\n"
            f"\n"
            f"ЗА МЕСЯЦ\n"
            f"{hrs_m:.0f} часов\n"
            f"({mins_m:.0f} мин.)\n"
            f"{total_tracks_m} треков"
        )

        if bot and target_user_id:
            await bot.send_message(target_user_id, message)

    return True


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
