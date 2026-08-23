import os
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import qrcode
import io

API_TOKEN = '8931457977:AAGtHKIbrJDMJqinMhZMcm9Jfgr1-I23n_w'
bot = telebot.TeleBot(API_TOKEN)

# Создаем легкий веб-сервер для Render (для 24/7 работы)
app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# База данных привязок и состояний
linked_users = {}
waiting_for_link = {}

# Ваши ссылки на оплату через Т-Банк для каждого уровня
PAYMENT_LINKS = {
    "pay_support": "http://t.tb.ru/mZirDH",    # 4 руб
    "pay_medium": "http://t.tb.ru/atK75v",     # 100 руб
    "pay_fauth": "http://t.tb.ru/vkJCGf"       # 300 руб
}

def get_main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔗 Привязать", callback_data="btn_link"),
        InlineKeyboardButton("📦 Моды", callback_data="btn_mods")
    )
    markup.add(
        InlineKeyboardButton("⭐ Поддержка", callback_data="btn_sub")
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

# Команда для выдачи подписки: /grant [user_id] [уровень]
@bot.message_handler(commands=['grant'])
def cmd_grant(message):
    username = message.from_user.username
    if not username or username.lower() != "makoronpay":
        bot.send_message(message.chat.id, "❌ У вас нет прав на использование этой команды.")
        return
    
    try:
        parts = message.text.split()
        target_user_id = int(parts[1])
        tier = parts[2]
        
        bot.send_message(
            target_user_id,
            f"🎉 <b>Ваша поддержка подтверждена!</b>\n"
            f"Вам присвоен уровень: <b>{tier}</b>.\n"
            f"Спасибо за поддержку проекта!",
            parse_mode="HTML"
        )
        
        bot.send_message(message.chat.id, f"✅ Успешно выдано пользователю {target_user_id} уровень {tier}.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка! Используйте формат: <code>/grant [user_id] [уровень]</code>", parse_mode="HTML")

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
        support_markup = InlineKeyboardMarkup(row_width=1)
        support_markup.add(
            InlineKeyboardButton("🔸 Medium — 100 руб", callback_data="pay_medium"),
            InlineKeyboardButton("🔸 Fauth — 300 руб", callback_data="pay_fauth"),
            InlineKeyboardButton("🔸 Поддержка — 4 руб", callback_data="pay_support"),
            InlineKeyboardButton("⬅️ Назад", callback_data="btn_back")
        )
        bot.edit_message_text(
            "❤️ <b>Выберите вариант поддержки проекта:</b>\n\n"
            "Нажмите на нужную сумму, чтобы получить QR-код для перевода через СБП.",
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=support_markup
        )
        
    elif call.data.startswith("pay_"):
        tier_names = {
            "pay_medium": "Medium (100 руб)",
            "pay_fauth": "Fauth (300 руб)",
            "pay_support": "Поддержка (4 руб)"
        }
        tier_title = tier_names.get(call.data, "Поддержка")
        pay_url = PAYMENT_LINKS.get(call.data, "http://t.tb.ru/mZirDH")

        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(pay_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        
        caption = (
            f"💳 <b>Выбрано: {tier_title}</b>\n\n"
            f"📷 <b>QR-код для перевода по СБП:</b>\n"
            f"1. Отсканируйте код через приложение своего банка (Т-Банк, Сбер и др.).\n"
            f"2. После оплаты отправьте чек или скриншот администратору (@Makoronpay), чтобы подтвердить поддержку!"
        )
        
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton("⬅️ Назад к выбору", callback_data="btn_sub"))
        
        bot.send_photo(user_id, photo=types.InputFile(bio, filename="qr.png"), caption=caption, parse_mode="HTML", reply_markup=back_markup)
        
    elif call.data == "btn_back":
        bot.edit_message_text(
            "👋 Выберите нужный пункт меню:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=get_main_menu(user_id)
        )
        
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
    elif text == "⭐ Поддержка":
        support_markup = InlineKeyboardMarkup(row_width=1)
        support_markup.add(
            InlineKeyboardButton("🔸 Medium — 100 руб", callback_data="pay_medium"),
            InlineKeyboardButton("🔸 Fauth — 300 руб", callback_data="pay_fauth"),
            InlineKeyboardButton("🔸 Поддержка — 4 руб", callback_data="pay_support")
        )
        bot.send_message(user_id, "❤️ <b>Выберите вариант поддержки проекта:</b>", parse_mode="HTML", reply_markup=support_markup)
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
    bot_thread = threading.Thread(target=lambda: bot.infinity_polling(none_stop=True))
    bot_thread.daemon = True
    bot_thread.start()
    
    print("Telegram bot started in background thread...")
    run_web()
