import os
import threading
from flask import Flask, request, jsonify
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import qrcode
import io

API_TOKEN = '8931457977:AAGtHKIbrJDMJqinMhZMcm9Jfgr1-I23n_w'
bot = telebot.TeleBot(API_TOKEN)

app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

# Базы данных для привязок, подписок, ников и состояний
linked_users = {}       # user_id -> [список кодов]
user_subscriptions = {} # user_id -> уровень подписки
user_nicknames = {}     # user_id -> ник в майнкрафте
code_to_user = {}       # код -> user_id
waiting_for_link = {}

# --- API для проверки подписки одного игрока ---
@app.route('/api/check', methods=['GET'])
def api_check_sub():
    code = request.args.get('code')
    if not code:
        return jsonify({"subscription": "нету"})
    
    target_user_id = code_to_user.get(code)
    if not target_user_id:
        return jsonify({"subscription": "нету"})
        
    sub = user_subscriptions.get(target_user_id, "нету")
    return jsonify({"subscription": sub})

# --- API для получения списка всех активных игроков с модом (для подсветки) ---
@app.route('/api/players', methods=['GET'])
def api_get_players():
    players_data = []
    for uid, codes in linked_users.items():
        if codes:
            nickname = user_nicknames.get(uid, "")
            sub = user_subscriptions.get(uid, "нету")
            players_data.append({
                "nickname": nickname,
                "subscription": sub
            })
    return jsonify(players_data)

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

PAYMENT_LINKS = {
    "pay_support": "http://t.tb.ru/mZirDH",
    "pay_medium": "http://t.tb.ru/atK75v",
    "pay_fauth": "http://t.tb.ru/vkJCGf"
}

def get_main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔗 Привязать", callback_data="btn_link"),
        InlineKeyboardButton("📦 Моды", callback_data="btn_mods")
    )
    markup.add(
        InlineKeyboardButton("⭐ Подписки", callback_data="btn_sub"),
        InlineKeyboardButton("ℹ️ Информация", callback_data="btn_info")
    )
    if user_id in linked_users and len(linked_users[user_id]) > 0:
        markup.add(InlineKeyboardButton("✅ Привязанные", callback_data="btn_linked"))
    return markup

@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Добро пожаловать в панель управления модами от @Makaronpay.\nВыберите нужный пункт меню:",
        reply_markup=get_main_menu(message.from_user.id)
    )

@bot.message_handler(commands=['sub'])
def cmd_sub_gift(message):
    username = message.from_user.username
    if not username or username.lower() != "makoronpay":
        bot.send_message(message.chat.id, "❌ У вас нет прав.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) >= 4 and parts[1].lower() == "gift":
            target_user_id = int(parts[2])
            tier = parts[3]
            user_subscriptions[target_user_id] = tier
            
            bot.send_message(
                target_user_id,
                f"🎉 <b>Ваша подписка подтверждена администратором @Makaronpay!</b>\nВам присвоен уровень: <b>{tier}</b>.",
                parse_mode="HTML"
            )
            bot.send_message(message.chat.id, f"✅ Успешно выдана подписка '{tier}' пользователю {target_user_id}.")
        else:
            bot.send_message(message.chat.id, "❌ Формат: <code>/sub gift [ID] [уровень]</code>", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка при выдаче.", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    if call.data == "btn_mods":
        bot.send_message(user_id, "📦 <b>PiarSend</b> — от @Makaronpay", parse_mode="HTML", reply_markup=get_main_menu(user_id))
    elif call.data == "btn_sub":
        support_markup = InlineKeyboardMarkup(row_width=1)
        support_markup.add(
            InlineKeyboardButton("🔸 Medium — 100 руб", callback_data="pay_medium"),
            InlineKeyboardButton("🔸 Fauth — 300 руб", callback_data="pay_fauth"),
            InlineKeyboardButton("🔸 Поддержка — 4 руб", callback_data="pay_support"),
            InlineKeyboardButton("⬅️ Назад", callback_data="btn_back")
        )
        bot.edit_message_text("❤️ <b>Выберите вариант поддержки проекта @Makaronpay:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=support_markup)
    elif call.data == "btn_info":
        sub_status = user_subscriptions.get(user_id, "нету")
        nick = user_nicknames.get(user_id, "не указан")
        codes_str = ", ".join([f"<code>{c}</code>" for c in linked_users.get(user_id, [])]) or "не привязан"
        info_text = f"ℹ️ <b>Аккаунт (@Makaronpay):</b>\n\n🆔 ID: <code>{user_id}</code>\n🎮 Ник: <b>{nick}</b>\n⭐ Подписка: <b>{sub_status}</b>\n🔗 Коды: {codes_str}"
        bot.send_message(user_id, info_text, parse_mode="HTML", reply_markup=get_main_menu(user_id))
    elif call.data.startswith("pay_"):
        pay_url = PAYMENT_LINKS.get(call.data, "http://t.tb.ru/mZirDH")
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(pay_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        bot.send_photo(user_id, photo=types.InputFile(bio, file_name="qr.png"), caption="💳 Отсканируйте QR-код для перевода через СБП", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Назад", callback_data="btn_sub")))
    elif call.data == "btn_back":
        bot.edit_message_text("👋 Меню управления:", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_main_menu(user_id))
    elif call.data == "btn_linked":
        codes = "\n".join([f"• <code>{c}</code>" for c in linked_users.get(user_id, [])])
        bot.send_message(user_id, f"✅ Ваши коды:\n{codes}", parse_mode="HTML", reply_markup=get_main_menu(user_id))
    elif call.data == "btn_link":
        waiting_for_link[user_id] = True
        bot.send_message(user_id, "📤 Введите в чате игры команду привязки: <code>/send mod link [код]</code> и отправьте её сюда.", parse_mode="HTML")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if waiting_for_link.get(user_id) and "/send mod link" in text:
        parts = text.split()
        code = parts[-1].strip()
        
        # Пытаемся извлечь ник игрока из текста, если игрок его указал, либо берем из профиля тг
        # Ожидаем формат команды от мода, например: /send mod link КОД НикИгрока
        nickname = message.from_user.username or "Player"
        if len(parts) >= 4:
            nickname = parts[3].strip()

        if user_id not in linked_users:
            linked_users[user_id] = []
        if code not in linked_users[user_id]:
            linked_users[user_id].append(code)
            
        code_to_user[code] = user_id
        user_nicknames[user_id] = nickname
        waiting_for_link[user_id] = False
        
        bot.send_message(user_id, f"🎉 Успешная привязка для игрока <b>{nickname}</b>!\nВведите в игре: <code>/send mod verify SUCCESS-{code}</code>", parse_mode="HTML", reply_markup=get_main_menu(user_id))
    else:
        bot.send_message(user_id, "Используйте кнопки меню.", reply_markup=get_main_menu(user_id))

if __name__ == "__main__":
    bot_thread = threading.Thread(target=lambda: bot.infinity_polling(none_stop=True))
    bot_thread.daemon = True
    bot_thread.start()
    print("Bot started...")
    run_web()
