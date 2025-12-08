from aiogram.types import Message
from aiogram import Router
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Привет, вот твой USER-ID:\n`{message.from_user.id}`", parse_mode="Markdown"
    )
