from aiogram import Router, types
from aiogram.filters import Command

from keyboards.inline import get_main_menu_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "✂️ <b>Добро пожаловать в наш барбершоп!</b>\n\n"
        "Я помогу вам записаться к мастеру.\n"
        "Выберите действие в меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer(
        "📋 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard()
    )