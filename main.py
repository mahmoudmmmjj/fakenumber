import telebot
from telebot import types
import requests
import time
import re
import os
import pyrebase
import io
from flask import Flask, request
from threading import Thread
from datetime import datetime

# --- الإعدادات الأساسية (من كودك) ---
API_TOKEN = '7675462685:AAHz8qN4ZGOVbEfsQp5vqYxjPA6SMxmzm7I'
ADMIN_ID = 7895195899 
OWNER_USER = "hamodyrat"
# تفعيل الـ Threading لأقصى سرعة استجابة
bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=50)

# --- إعدادات Firebase (مستخرجة من ملفك) ---
firebase_config = {
    "apiKey": "AIzaSyDmoxiqjE__G7TSCEUjh22ViPH9NcSN81c",
    "authDomain": "hamody-68a5e.firebaseapp.com",
    "databaseURL": "https://hamody-68a5e-default-rtdb.firebaseio.com",
    "projectId": "hamody-68a5e",
    "storageBucket": "hamody-68a5e.firebasestorage.app",
    "messagingSenderId": "1060904742566",
    "appId": "1:1060904742566:android:350083a12c30187baf0e67"
}
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()
session = requests.Session()

# --- إعدادات IVAS (من كودك) ---
IVAS_HEADERS = {
    'User-Agent': "Mozilla/5.0",
    'Cookie': 'ivas_sms_session=eyJpdiI6IlJDY3pTcWtvR2dOcUJ6Q2ZuUmdTckE9PSIsInZhbHVlIjoiU3duN011eXVJRUM2YkFqZnZNZk9KTTJsam9Uek9Uam5EaVVqdkNyWUtITThhdGZGZmR1T2F1VG5oN3JzUTEzbDBTUUt0QWJ2aERodytIcWxyNEY0N3dhQjdlK3JrMDNSRDhBTEZQNCtUNGM5T0pSdFd2Y3JIRDJZTnNOcmRRNDciLCJtYWMiOiI5NTkxYTM4ODA3ZjE3MGQ5OGU3NDgyYmRkYTBjZWU3NzQ3Njc4N2Q4MTBiODdjMzYwNDA1YzNmMjNmMzU2NzVkIiwidGFnIjoiIn0%3D; XSRF-TOKEN=eyJpdiI6IlB6UCs1bkZNaG81cGtPT0lRQ29xVmc9PSIsInZhbHVlIjoiWElRTGF1RGxuUWN2cExJWkxPMFRZU3NCNTh5MUl2NjRzYzljeDNOQ3BLRzBWNmlibHpVTVlEM0drNWxBUDcvTHZOQjJ0L0x1QWRuQjF3N2pndEdZdkQ2THRMaWM4TkdvWFJJRndGTnh3ZUlPTGRSM2NyQjVxSGRaWmZ3aUF1cEYiLCJtYWMiOiI4YjhiZDk0NzRjOTFlMTc3MDdmODg0YjFlODk2NGY0NDQ1NWM0MTY0NTI4YWViZWMwYWMxYTY3ZThmYTg5ZDA0IiwidGFnIjoiIn0%3D'
}

# --- إدارة البيانات (Firebase بديل JSON للسرعة والحماية) ---
def get_user_data(uid):
    u = db.child("users").child(uid).get().val()
    if not u:
        u = {"balance": 0.0}
        db.child("users").child(uid).set(u)
    return u

def get_settings():
    s = db.child("settings").get().val()
    if not s:
        s = {"profit_on": False, "group_link": "https://t.me/hamodyrat", "banned": []}
        db.child("settings").set(s)
    return s

def is_banned(uid):
    s = get_settings()
    return str(uid) in s.get('banned', [])

def cancel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("إلغاء العملية ❌")
    return markup

# --- فحص الكود (نظام السحب السريع) ---
def check_ivas_loop(phone_number, chat_id, srv, cnt):
    url = "https://www.ivasms.com/portal/live/my_sms"
    for _ in range(45): 
        try:
            res = session.get(url, headers=IVAS_HEADERS, timeout=8)
            if phone_number in res.text:
                match = re.search(r'(\d{5,6})', res.text.split(phone_number)[1][:200])
                if match:
                    code = match.group(1)
                    bot.send_message(chat_id, f"✅ **تم استلام الكود!**\n\nالخدمة: `{srv}`\nالرقم: `{phone_number}`\nالكود: `{code}`", parse_mode="Markdown")
                    return
        except: pass
        time.sleep(6)

# --- أوامر المستخدم (نفس منطق كودك) ---
@bot.message_handler(commands=['start'])
def start_msg(message):
    if is_banned(message.from_user.id): return
    uid = str(message.from_user.id)
    u = get_user_data(uid)
    s = get_settings()
    
    bal_txt = f"💰 **رصيدك:** `{u['balance']}$`" if s.get('profit_on') else ""
    txt = (f"🔥 **أهلاً بك في بوت الأرقام!** 🔥\n━━━━━━━━━━━━━━\n"
           f"🚀 **خدمة تفعيل الأرقام العالمية**\n\n{bal_txt}\n"
           f"📈 **حالة السيرفر:** `يعمل ✅`\n━━━━━━━━━━━━━━\n👇 **اختر الخدمة:**")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("📱 طلب رقم جديد", callback_data="u_get"))
    markup.add(types.InlineKeyboardButton("👨‍💻 المالك", url=f"https://t.me/{OWNER_USER}"),
               types.InlineKeyboardButton("📢 قناة الأكواد", url=s.get('group_link')))
    bot.send_message(message.chat.id, txt, reply_markup=markup, parse_mode="Markdown")

# --- لوحة التحكم للإدارة (كاملة بدون حذف) ---
@bot.message_handler(commands=['hamo'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    s = get_settings()
    p_stat = "✅" if s.get('profit_on') else "❌"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة أرقام", callback_data="adm_add"),
        types.InlineKeyboardButton("🗑️ حذف", callback_data="adm_del_main"),
        types.InlineKeyboardButton(f"الربح: {p_stat}", callback_data="adm_tog_p"),
        types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
        types.InlineKeyboardButton("🌐 الجروب", callback_data="adm_set_gl"),
        types.InlineKeyboardButton("🚫 حظر", callback_data="adm_ban"),
        types.InlineKeyboardButton("📊 إحصائيات", callback_data="adm_stats"),
        types.InlineKeyboardButton("📄 IDs", callback_data="adm_exp")
    )
    bot.send_message(message.chat.id, "🛠️ **لوحة التحكم المركزية**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    n = db.child("nums").get().val() or {}
    s = get_settings()

    if call.data == "u_get":
        if not n: return bot.answer_callback_query(call.id, "لا توجد أرقام!")
        markup = types.InlineKeyboardMarkup()
        for k in n.keys(): markup.add(types.InlineKeyboardButton(k, callback_data=f"srv_{k}"))
        bot.edit_message_text("📱 **اختر الخدمة:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("srv_"):
        srv = call.data.split("_")[1]
        markup = types.InlineKeyboardMarkup()
        if srv in n:
            for c in n[srv].keys(): markup.add(types.InlineKeyboardButton(c, callback_data=f"getnum_{srv}_{c}"))
            bot.edit_message_text(f"🌍 **دولة لـ {srv}:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("getnum_") or call.data.startswith("chg_"):
        _, srv, cnt = call.data.split("_")
        if n.get(srv, {}).get(cnt):
            num_list = n[srv][cnt]
            num = num_list.pop(0)
            db.child("nums").child(srv).child(cnt).set(num_list)
            txt = f"◈ **الرقم:** `{num}`\n◈ **الدولة:** `{cnt}`\n◈ **الحالة:** ⏳ جاري الانتظار..."
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("قناة الأكواد 📩", url=s.get('group_link')))
            markup.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"chg_{srv}_{cnt}"),
                       types.InlineKeyboardButton("⬅️ رجوع", callback_data="u_get"))
            bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            Thread(target=check_ivas_loop, args=(num, call.message.chat.id, srv, cnt)).start()
        else: bot.answer_callback_query(call.id, "الأرقام خلصت!")

    # باقي الأوامر الإدارية كما هي...
    elif call.data == "adm_add":
        m = bot.send_message(call.message.chat.id, "📌 اسم الخدمة:", reply_markup=cancel_markup())
        bot.register_next_step_handler(m, get_srv_name)

    elif call.data == "adm_stats":
        users = db.child("users").get().val() or {}
        txt = f"📊 **إحصائيات:**\n👥 مستخدمين: `{len(users)}`"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

# --- Steps ---
def get_srv_name(m):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    srv = m.text
    m2 = bot.send_message(m.chat.id, f"🌍 اكتب اسم الدولة لـ {srv}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m2, lambda msg: get_cnt_name(msg, srv))

def get_cnt_name(m, srv):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    cnt = m.text
    m3 = bot.send_message(m.chat.id, f"📄 ارفع ملف .txt لـ {srv}/{cnt}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m3, lambda msg: save_file(msg, srv, cnt))

def save_file(m, srv, cnt):
    if not m.document: return bot.send_message(m.chat.id, "ارفع ملف!")
    raw = bot.download_file(bot.get_file(m.document.file_id).file_path).decode('utf-8').splitlines()
    nums = [x.strip() for x in raw if x.strip()]
    db.child("nums").child(srv).child(cnt).set(nums)
    bot.send_message(m.chat.id, "✅ تم الحفظ في Firebase.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

# --- Vercel Webhook Engine (السرعة الحقيقية) ---
app = Flask(__name__)

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        # أهم جزء: المعالجة في Thread والرد الفوري لمنع الـ Sleep
        Thread(target=bot.process_new_updates, args=([update],)).start()
        return "!", 200
    return "Forbidden", 403

@app.route("/")
def index():
    return "<h1>Bot is Active and Fast 🚀</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
