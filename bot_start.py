import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from bot_main import router as bot_main_router

# Импортируем USER_TG_ID, чтобы проверять его наличие
from loaded_dotenv import BOT_TOKEN_TG, USER_TG_ID
from main import check_new_data, main as process_stats

# КОНФИГУРАЦИЯ ЛОГГЕРА
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def run_long_polling() -> None:
    """Запускает бота в режиме долгого опроса (ожидание команд)"""
    bot = Bot(BOT_TOKEN_TG)
    dp = Dispatcher()
    dp.include_router(bot_main_router)

    try:
        logger.info("Запуск бота в режиме long polling.")
        logger.info("Бот ждет сообщений (напишите /start для получения ID)...")
        # В этом режиме мы НЕ проверяем статистику сами, только отвечаем на команды
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Критическая ошибка в режиме long polling: {e}")
        raise
    finally:
        await bot.session.close()
        logger.info("Бот в режиме long polling остановлен")


async def main() -> None:
    """Стандартный режим: проверка данных и отправка уведомления"""
    try:
        # Импортируем функции для артистов
        from api_request_artists import (
            get_top_artists_month,
            load_cached_artists,
            save_artists_cache,
            artists_changed,
            format_artists_output,
        )

        bot = Bot(BOT_TOKEN_TG)

        # Проверяем артистов НЕЗАВИСИМО от статистики времени
        top_artists = await get_top_artists_month(bot)
        artists_updated = False

        if top_artists:
            old_artists = load_cached_artists()
            if artists_changed(top_artists, old_artists):
                save_artists_cache(top_artists)
                artists_updated = True
                if USER_TG_ID:
                    artists_message = format_artists_output(top_artists)
                    await bot.send_message(USER_TG_ID, artists_message)
                    logger.info("Отправлена обновлённая статистика по артистам")

        # Проверяем статистику времени
        has_new, total_seconds, total_tracks, latest_stats, yesterday_date = (
            await check_new_data()
        )

        if not has_new and not artists_updated:
            logger.info("Новых данных нет. Бот завершает работу.")
            await bot.session.close()
            return

        if has_new:
            logger.info("Запуск бота для обработки статистики...")

            await process_stats(
                bot,
                prefetched=(
                    has_new,
                    total_seconds,
                    total_tracks,
                    latest_stats,
                    yesterday_date,
                ),
            )

            if USER_TG_ID:
                logger.info(f"Сообщение успешно отправлено пользователю {USER_TG_ID}")
            else:
                logger.warning(
                    "Статистика сохранена, но сообщение НЕ отправлено (в .env не указан USER_TG_ID)"
                )

        logger.info("Завершаем работу бота")

    except Exception as e:
        logger.exception(f"Ошибка при работе бота: {e}")
    finally:
        if "bot" in locals():
            await bot.session.close()
            logger.info("Сессия бота закрыта")


if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else None

    try:
        if mode == "long":
            # Режим для получения ID и тестов
            asyncio.run(run_long_polling())
        else:
            # Режим для Cron/Task Scheduler
            asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Принудительная остановка бота пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка на верхнем уровне: {e}")
