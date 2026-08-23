import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = '8931457977:AAGtHKIbrJDMJqinMhZMcm9Jfgr1-I23n_w'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

linked_users = {}
waiting_for_link = {}

def get_main_menu(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔗 Привязать", callback_data="btn_link"),
        InlineKeyboardButton(text="📦 Моды", callback_data="btn_mods")
    )
    builder.row(
        InlineKeyboardButton(text="⭐ Подписка", callback_data="btn_sub")
    )
    if user_id in linked_users and len(linked_users[user_id]) > 0:
        builder.row(InlineKeyboardButton(text="✅ Привязанные", callback_data="btn_linked"))
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Добро пожаловать в панель управления модами.\nВыберите нужный пункт меню:",
        reply_markup=get_main_menu(message.from_user.id)
    )

@dp.callback_query(F.data == "btn_mods")
async def cb_mods(callback):
    mods_text = (
        "📦 <b>Список ваших модов:</b>\n\n"
        "1. <b>PiarSend</b> — Мод для автоматизации рассылок, управления аккаунтами, "
        "быстрой регистрации и удобного HUD-интерфейса на клиенте Fabric.\n\n"
        "owner @Makoronpay"
    )
    await callback.message.answer(mods_text, parse_mode="HTML", reply_markup=get_main_menu(callback.from_user.id))
    await callback.answer()

@dp.callback_query(F.data == "btn_sub")
async def cb_sub(callback):
    await callback.message.answer(
        "⭐ Раздел подписки в разработке. Скоро здесь появится новый функционал!",
        reply_markup=get_main_menu(callback.from_user.id)
    )
    await callback.answer()

@dp.callback_query(F.data == "btn_linked")
async def cb_linked(callback):
    user_id = callback.from_user.id
    if user_id in linked_users and linked_users[user_id]:
        codes = "\n".join([f"• <code>{code}</code>" for code in linked_users[user_id]])
        await callback.message.answer(f"✅ Ваши привязанные коды модов:\n{codes}", parse_mode="HTML", reply_markup=get_main_menu(user_id))
    else:
        await callback.message.answer("У вас пока нет привязанных модов.", reply_markup=get_main_menu(user_id))
    await callback.answer()

@dp.callback_query(F.data == "btn_link")
async def cb_link_click(callback):
    waiting_for_link[callback.from_user.id] = True
    await callback.message.answer(
        "📤 Отправь мне команду для привязки.\n\n"
        "Для этого впишите в майнкрафт чате:\n"
        "<code>/send mod link [ваш_код]</code>\n"
        "и отправьте полученную команду сюда.",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.message(F.text == "🔗 Привязать")
async def btn_link_text(message: Message):
    waiting_for_link[message.from_user.id] = True
    await message.answer(
        "📤 Отправь мне команду для привязки.\n\n"
        "Для этого впишите в майнкрафт чате:\n"
        "<code>/send mod link [ваш_код]</code>\n"
        "и отправьте полученную команду сюда.",
        parse_mode="HTML"
    )

@dp.message(F.text == "📦 Моды")
async def btn_mods_text(message: Message):
    mods_text = (
        "📦 <b>Список ваших модов:</b>\n\n"
        "1. <b>PiarSend</b> — Мод для автоматизации рассылок, управления аккаунтами, "
        "быстрой регистрации и удобного HUD-интерфейса на клиенте Fabric.\n\n"
        "owner @Makoronpay"
    )
    await message.answer(mods_text, parse_mode="HTML", reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text == "⭐ Подписка")
async def btn_sub_text(message: Message):
    await message.answer(
        "⭐ Раздел подписки в разработке. Скоро здесь появится новый функционал!",
        reply_markup=get_main_menu(message.from_user.id)
    )

@dp.message(F.text == "✅ Привязанные")
async def btn_linked_text(message: Message):
    user_id = message.from_user.id
    if user_id in linked_users and linked_users[user_id]:
        codes = "\n".join([f"• <code>{code}</code>" for code in linked_users[user_id]])
        await message.answer(f"✅ Ваши привязанные коды модов:\n{codes}", parse_mode="HTML", reply_markup=get_main_menu(user_id))
    else:
        await message.answer("У вас пока нет привязанных модов.", reply_markup=get_main_menu(user_id))

@dp.message()
async def handle_text(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if waiting_for_link.get(user_id):
        if "/send mod link" in text:
            code = text.split()[-1].strip()
            
            if user_id not in linked_users:
                linked_users[user_id] = []
            
            if code not in linked_users[user_id]:
                linked_users[user_id].append(code)
            
            waiting_for_link[user_id] = False
            
            # Бот выдает ключ подтверждения для игры
            verify_cmd = f"/send mod verify SUCCESS-{code}"
            await message.answer(
                f"🎉 Успешная привязка!\n\n"
                f"Введите эту команду в чат Minecraft для активации мода:\n"
                f"<code>{verify_cmd}</code>",
                parse_mode="HTML",
                reply_markup=get_main_menu(user_id)
            )
        else:
            await message.answer("❌ Неверный формат! Отправьте команду вида: <code>/send mod link ABC123</code>", parse_mode="HTML")
    else:
        await message.answer("Используйте кнопки меню для навигации.", reply_markup=get_main_menu(user_id))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())