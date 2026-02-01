import os
from aiogram import Router, types
from aiogram.filters import Command
from dotenv import set_key, find_dotenv

# Импортируем нашу логику проверки
from main import check_new_data, main as process_stats

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    # 1. Находим файл .env
    env_file = find_dotenv()
    if not env_file:
        # Если файла нет, создаем его (хотя он должен быть по инструкции)
        with open(".env", "w") as f:
            pass
        env_file = ".env"

    # 2. Сохраняем ID в файл .env
    # Это физически изменит текст в файле
    try:
        set_key(env_file, "USER_TG_ID", str(user_id))
        save_msg = "Ваш Telegram ID успешно сохранен в настройки бота!"
    except Exception as e:
        save_msg = f"Не удалось сохранить ID в файл: {e}"
    await message.answer(save_msg)
    # 3. Сразу запускаем проверку статистики
    # Важно: мы передаем user_id вручную, так как глобальная переменная USER_TG_ID
    # обновится только при перезапуске скрипта.
    try:
        # Получаем данные
        has_new, total_seconds, total_tracks, latest_stats, yesterday_date = (
            await check_new_data(bot=message.bot)
        )

        # Запускаем обработку, передавая ID принудительно (user_id_override)
        await process_stats(
            bot=message.bot,
            prefetched=(
                has_new,
                total_seconds,
                total_tracks,
                latest_stats,
                yesterday_date,
            ),
            user_id_override=user_id,
        )

    except Exception as e:
        await message.answer(f"Произошла ошибка при проверке статистики: {e}")
