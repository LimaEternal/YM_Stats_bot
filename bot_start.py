import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from bot_main import router as bot_main_router
from loaded_dotenv import TOKEN_TG
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
    bot = Bot(TOKEN_TG)
    dp = Dispatcher()
    dp.include_router(bot_main_router)

    try:
        logger.info("Запуск бота в режиме long polling (ожидание команд)")
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
        # Сначала проверяем наличие новых данных, чтобы не поднимать бота зря
        has_new, total_seconds, total_tracks, latest_stats, yesterday_date = (
            await check_new_data()
        )

        if not has_new:
            logger.info("Новых данных нет. Бот завершает работу.")
            return

        bot = Bot(TOKEN_TG)
        logger.info("Запуск бота и отправка уведомления")
        # Передаем уже полученные данные, чтобы не делать повторный запрос
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
        logger.info("Сообщение отправлено, завершаем работу бота")
    except Exception as e:
        logger.exception(f"Ошибка при работе бота: {e}")
    finally:
        # Корректно закрываем сессию бота, если бот был создан
        if "bot" in locals():
            await bot.session.close()
            logger.info("Бот успешно остановлен")


if __name__ == "__main__":
    # Определяем режим запуска: long или стандартный
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else None

    try:
        if mode == "long":
            logger.info("Активирован режим long polling (бот будет работать постоянно)")
            asyncio.run(run_long_polling())
        else:
            logger.info(
                "Запуск в стандартном режиме (проверка данных и отправка уведомления)"
            )
            asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Принудительная остановка бота пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка на верхнем уровне: {e}")
