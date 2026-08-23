import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8931457977:AAGtHKIbrJDMJqinMhZMcm9Jfgr1-I23n_w'
bot = telebot.TeleBot(API_TOKEN)

# База данных привязок: telegram_id -> список кодов
linked_users = {}
waiting_for_link = {}

def get_main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔗 Привязать", callback_data="btn_link"),
        InlineKeyboardButton("📦 Моды", callback_data="btn_mods")
    )
    markup.add(
        InlineKeyboardButton("⭐ Подписка", callback_data="btn_sub")
    )
    if user_id in linked_users and len(linked_users[user_id]) > 0:
        markup.add(InlineKeyboardButton("✅ Привязанные", callback_data="btn_linked"))
    return markup

@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Добро пожаловать в панель управления модами.\nВыберите нужный пункт меню:",
        reply_markup=get_main_menu(message.from_user.id)
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    if call.data == "btn_mods":
        mods_text = (
            "📦 <b>Список ваших модов:</b>\n\n"
            "1. <b>PiarSend</b> — Мод для автоматизации рассылок, управления аккаунтами, "
            "быстрой регистрации и удобного HUD-интерфейса на клиенте Fabric.\n\n"
            "owner @Makoronpay"
        )
        bot.send_message(user_id, mods_text, parse_mode="HTML", reply_markup=get_main_menu(user_id))
    elif call.data == "btn_sub":
        bot.send_message(user_id, "⭐ Раздел подписки в разработке. Скоро здесь появится новый функционал!", reply_markup=get_main_menu(user_id))
    elif call.data == "btn_linked":
        if user_id in linked_users and linked_users[user_id]:
            codes = "\n".join([f"• <code>{code}</code>" for code in linked_users[user_id]])
            bot.send_message(user_id, f"✅ Ваши привязанные коды модов:\n{codes}", parse_mode="HTML", reply_markup=get_main_menu(user_id))
        else:
            bot.send_message(user_id, "У вас пока нет привязанных модов.", reply_markup=get_main_menu(user_id))
    elif call.data == "btn_link":
        waiting_for_link[user_id] = True
        bot.send_message(
            user_id,
            "📤 Отправь мне команду для привязки.\n\n"
            "Для этого впишите в майнкрафт чате:\n"
            "<code>/send mod link [ваш_код]</code>\n"
            "и отправьте полученную команду сюда.",
            parse_mode="HTML"
        )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text == "🔗 Привязать":
        waiting_for_link[user_id] = True
        bot.send_message(user_id, "📤 Отправьте команду вида: <code>/send mod link [ваш_код]</code>", parse_mode="HTML")
    elif text == "📦 Моды":
        bot.send_message(user_id, "📦 <b>PiarSend</b> — owner @Makoronpay", parse_mode="HTML", reply_markup=get_main_menu(user_id))
    elif text == "⭐ Подписка":
        bot.send_message(user_id, "⭐ Раздел подписки в разработке.", reply_markup=get_main_menu(user_id))
    elif text == "✅ Привязанные":
        if user_id in linked_users and linked_users[user_id]:
            codes = "\n".join([f"• <code>{code}</code>" for code in linked_users[user_id]])
            bot.send_message(user_id, f"✅ Ваши привязанные коды модов:\n{codes}", parse_mode="HTML", reply_markup=get_main_menu(user_id))
        else:
            bot.send_message(user_id, "У вас пока нет привязанных модов.", reply_markup=get_main_menu(user_id))
    elif waiting_for_link.get(user_id):
        if "/send mod link" in text:
            code = text.split()[-1].strip()
            if user_id not in linked_users:
                linked_users[user_id] = []
            if code not in linked_users[user_id]:
                linked_users[user_id].append(code)
            waiting_for_link[user_id] = False
            
            verify_cmd = f"/send mod verify SUCCESS-{code}"
            bot.send_message(
                user_id,
                f"🎉 Успешная привязка!\n\n"
                f"Введите эту команду в чат Minecraft для активации мода:\n"
                f"<code>{verify_cmd}</code>",
                parse_mode="HTML",
                reply_markup=get_main_menu(user_id)
            )
        else:
            bot.send_message(user_id, "❌ Неверный формат! Отправьте команду вида: <code>/send mod link ABC123</code>", parse_mode="HTML")
    else:
        bot.send_message(user_id, "Используйте кнопки меню для навигации.", reply_markup=get_main_menu(user_id))

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
