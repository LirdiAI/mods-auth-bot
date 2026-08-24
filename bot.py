import os
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import string

API_TOKEN = '8931457977:AAGtHKIbrJDMJqinMhZMcm9Jfgr1-I23n_w'
bot = telebot.TeleBot(API_TOKEN)

app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

# Базы данных
linked_users = {}         
user_subscriptions = {} 
user_sub_expiry = {}    # НОВОЕ: Время окончания подписок
user_nicknames = {}       
code_to_user = {}         
waiting_for_link = {}

pending_verifications = {} 
mod_commands = {}   

ADMIN_ID = 7885222957 

@app.route('/api/check', methods=['GET'])
def api_check_sub():
    code = request.args.get('code')
    if not code: return jsonify({"subscription": "нету"})
    target_user_id = code_to_user.get(code)
    if not target_user_id: return jsonify({"subscription": "нету"})
    
    # НОВОЕ: Проверка актуальности подписки по времени
    if target_user_id in user_sub_expiry:
        if datetime.now() > user_sub_expiry[target_user_id]:
            # Время вышло, сбрасываем подписку
            user_subscriptions[target_user_id] = "нету"
            del user_sub_expiry[target_user_id]

    return jsonify({"subscription": user_subscriptions.get(target_user_id, "нету")})

@app.route('/api/verify', methods=['GET'])
def api_verify():
    link = request.args.get('link')
    verify_code = request.args.get('code')
    
    if link in pending_verifications and pending_verifications[link]['verify_code'] == verify_code:
        user_id = pending_verifications[link]['user_id']
        username = pending_verifications[link]['username']
        
        if user_id not in linked_users: linked_users[user_id] = []
        if link not in linked_users[user_id]: linked_users[user_id].append(link)
        code_to_user[link] = user_id
        user_nicknames[user_id] = username
        
        del pending_verifications[link] 
        return jsonify({"status": "ok"})
    
    return jsonify({"status": "error"})

@app.route('/api/command', methods=['GET'])
def api_get_command():
    code = request.args.get('code')
    cmd = mod_commands.get(code, "")
    if code in mod_commands:
        mod_commands[code] = ""
    return jsonify({"command": cmd})

# НОВОЕ: Улучшенный API нотификаций (пункт 3)
@app.route('/api/notify', methods=['GET'])
def api_notify():
    code = request.args.get('code')
    text = request.args.get('text')
    user_id = code_to_user.get(code)
    if user_id and text:
        try:
            bot.send_message(user_id, f"⚠️ <b>Уведомление от мода:</b>\n{text}", parse_mode="HTML")
        except Exception:
            pass
    return jsonify({"status": "ok"})

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

PAYMENT_LINKS = {
    "pay_support": "http://t.tb.ru/mZirDH",
    "pay_medium": "http://t.tb.ru/atK75v",
    "pay_fauth": "http://t.tb.ru/vkJCGf"
}

# НОВОЕ: Интерактивная панель управления с кнопками (пункт 1)
def get_main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔗 Привязать", callback_data="btn_link"),
        InlineKeyboardButton("📦 Моды", callback_data="btn_mods")
    )
    markup.add(
        InlineKeyboardButton("⭐ Подписки", callback_data="btn_sub"),
        InlineKeyboardButton("🎁 Тест (1 день)", callback_data="btn_trial")
    )
    markup.add(
        InlineKeyboardButton("ℹ️ Информация", callback_data="btn_info"),
        InlineKeyboardButton("👥 Мои аккаунты", callback_data="btn_alts")
    )
    if user_id in linked_users and len(linked_users[user_id]) > 0:
        markup.add(
            InlineKeyboardButton("✅ Привязанные коды", callback_data="btn_linked"),
            InlineKeyboardButton("🛑 Стоп моды", callback_data="btn_stop_mods")
        )
    return markup

@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.send_message(message.chat.id, "👋 Привет! Панель управления PiarSend.", reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(commands=['sub'])
def cmd_sub_gift(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        if len(parts) >= 4 and parts[1].lower() == "gift":
            target_user_id, tier = int(parts[2]), parts[3]
            user_subscriptions[target_user_id] = tier
            if target_user_id in user_sub_expiry: del user_sub_expiry[target_user_id] # Бессрочная от админа
            bot.send_message(target_user_id, f"🎉 <b>Подписка выдана администратором: {tier}</b>.", parse_mode="HTML")
            bot.send_message(message.chat.id, f"✅ Успешно выдан '{tier}' ID {target_user_id}.")
    except Exception: pass

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
        bot.edit_message_text("❤️ <b>Выберите вариант:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=support_markup)
    elif call.data == "btn_info":
        sub_status = user_subscriptions.get(user_id, "нету")
        
        # Проверка срока подписки для текста
        if user_id in user_sub_expiry:
            if datetime.now() > user_sub_expiry[user_id]:
                sub_status = "нету"
                user_subscriptions[user_id] = "нету"
            else:
                remaining = str(user_sub_expiry[user_id] - datetime.now()).split('.')[0]
                sub_status += f" (ещё истекает через {remaining})"

        nick = user_nicknames.get(user_id, "не указан")
        codes_str = ", ".join([f"<code>{c}</code>" for c in linked_users.get(user_id, [])]) or "не привязан"
        info_text = f"ℹ️ <b>Аккаунт:</b>\n\n🆔 ID: <code>{user_id}</code>\n🎮 Ник: <b>{nick}</b>\n⭐ Подписка: <b>{sub_status}</b>\n🔗 Коды: {codes_str}"
        bot.send_message(user_id, info_text, parse_mode="HTML", reply_markup=get_main_menu(user_id))
    
    # НОВОЕ: Обработка кнопки выдачи теста на 1 день (пункт 4)
    elif call.data == "btn_trial":
        current_sub = user_subscriptions.get(user_id, "нету")
        if current_sub != "нету":
            bot.answer_callback_query(call.id, "❌ У вас уже есть активная подписка!", show_alert=True)
            return
        
        user_subscriptions[user_id] = "Medium"
        user_sub_expiry[user_id] = datetime.now() + timedelta(days=1) # Ровно на 1 день
        bot.answer_callback_query(call.id, "🎁 Тестовый период Medium активирован на 24 часа!", show_alert=True)
        bot.send_message(user_id, "🎉 Поздравляем! Вам успешно активирована тестовая подписка **Medium** на **1 день**.", parse_mode="HTML", reply_markup=get_main_menu(user_id))

    # НОВОЕ: Менеджер аккаунтов (пункт 5)
    elif call.data == "btn_alts":
        codes = linked_users.get(user_id, [])
        nick = user_nicknames.get(user_id, "Не указан")
        if not codes:
            text = "👥 <b>Менеджер аккаунтов:</b>\n\nУ вас пока нет привязанных модов/аккаунтов."
        else:
            codes_formatted = "\n".join([f"• Код: <code>{c}</code>" for c in codes])
            text = f"👥 <b>Менеджер аккаунтов:</b>\n\n🎮 Основной ник: <b>{nick}</b>\n🔗 Привязанные коды мода:\n{codes_formatted}"
        bot.send_message(user_id, text, parse_mode="HTML", reply_markup=get_main_menu(user_id))

    elif call.data.startswith("pay_"):
        bot.send_message(user_id, f"💳 Оплата СБП по ссылке: {PAYMENT_LINKS.get(call.data)}", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Назад", callback_data="btn_sub")))
    elif call.data == "btn_back":
        bot.edit_message_text("👋 Меню:", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_main_menu(user_id))
    elif call.data == "btn_linked":
        codes = "\n".join([f"• <code>{c}</code>" for c in linked_users.get(user_id, [])])
        bot.send_message(user_id, f"✅ Ваши коды:\n{codes}", parse_mode="HTML", reply_markup=get_main_menu(user_id))
    elif call.data == "btn_link":
        waiting_for_link[user_id] = True
        bot.send_message(user_id, "📤 <b>Отправьте мне код</b>, который мод написал вам в чат игры (например: AUTH-1234):", parse_mode="HTML")
    elif call.data == "btn_stop_mods":
        codes = linked_users.get(user_id, [])
        for c in codes: mod_commands[c] = "stop"
        bot.answer_callback_query(call.id, "🛑 Сигнал остановки отправлен на все ваши моды!", show_alert=True)
        return
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if waiting_for_link.get(user_id):
        link_code = text.split()[0] 
        verify_code = "V-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        pending_verifications[link_code] = {
            "user_id": user_id,
            "verify_code": verify_code,
            "username": message.from_user.username or "Игрок"
        }
        waiting_for_link[user_id] = False
        
        response_msg = (
            f"🎉 Код получен!\n\n"
            f"Теперь скопируй эту команду и введи в Майнкрафте:\n"
            f"<code>/send mod verify {verify_code}</code>"
        )
        bot.send_message(user_id, response_msg, parse_mode="HTML", reply_markup=get_main_menu(user_id))

if __name__ == "__main__":
    bot_thread = threading.Thread(target=lambda: bot.infinity_polling(none_stop=True))
    bot_thread.daemon = True
    bot_thread.start()
    run_web()
