import telebot
from telebot import types
import requests
import time
import re
import os
import pyrebase
from flask import Flask, request
from threading import Thread
from datetime import datetime

# --- إعدادات البوت والمسؤول ---
API_TOKEN = '7675462685:AAHz8qN4ZGOVbEfsQp5vqYxjPA6SMxmzm7I'
ADMIN_ID = 7895195899 
OWNER_USER = "hamodyrat"
bot = telebot.TeleBot(API_TOKEN)

# --- إعدادات Firebase من ملفك ---
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

# --- إعدادات IVASMS (التوكن والكوكيز المحدثة) ---
IVAS_TOKEN = "mdWCez8pRLYEzgI4LPDcbCrMwJR96czg8PFWD7Sp"
IVAS_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    'Cookie': "_fbp=fb.1.1776003227915.194465397404537711; cf_clearance=DYPKOA2ue315tKTGTtM_BydeHjQJKPmvaw9phITsOoI-1776629195-1.2.1.1-VmoaO1R37S_mE2vCKqwqcWvXbxDvAN8_a6ipyAB.0FJ90rzOna2WN.wF3_CWijy1sqUDGMYuoH_cUbcMEYX8WrNpF_bC2cM_g3xRSI1hg1FPMDBKcQtz45ozvFEHVQX766JkWTOYWApCobrqP4SjIdOJ5PZdZ8p423Pgxhoa9ErTdmrJOnuAco7a7WdrhD4zzX78qI9fsHhEjJ7_uyK2LxYE5xdJ23d05OAQnuwOYUapTLUE_z3TcCKyw30.hB.S3sX5HsjX3d1z3WVW28tkX2IZ4NhSsUNGwNrN_nM8GDX5sySrKHEmv_wtwH3hahjYjxgXRZ2YZOtiFY2K5RQqPg; XSRF-TOKEN=eyJpdiI6Imdob2dKMm84ZG1zS0ZMMTYwbEhRdmc9PSIsInZhbHVlIjoidzg4cmovU1F1RngzM3lCcmtaTVZ6S2RadHpTWTBrUjZEN3I5NElBVDRmSVVhMUJsZUJRSUZpeStSc2hGWWo4dGFaeFE0U0VyZWl0bUpqaE1HSjg0SmJ3WUtkclFEeXNyOHpxUmlMN21aZzhpVDdqQ3VTenJZWDFINzFLeGhjMHUiLCJtYWMiOiJhN2NlYzMxYWU0OTM5YWY2OTEzODc0YzA4ZDhlZTg2ZjMyNTU1ZjZhOGU3ZmEzYWQ3MmYyOTgyMDgzMGE4MDc5IiwidGFnIjoiIn0%3D; ivas_sms_session=eyJpdiI6ImZZZkN5dkhjUzRTdnR6WWp1dEQ0Y1E9PSIsInZhbHVlIjoiOFI0aHhycWI2ajNHUnArWGF0N1g5bUZVbzZ2MFdwUzE2YllmZmp4RDREb21adVJOYmZOdkN0dE9PVkwzVkZGSUNoMWRsK0F3SEJEVjYxZ3FFRzFGdWJBQ1ZHakM1QzNlY2xZWlhLSXV3VmJpb1daSTg1RXlUYnVXeDFRcVRYZ0YiLCJtYWMiOiI5MmMzYmYzNzhlZmU1OTRmYWYwMjk3MGJiNWM4NDNjMmQwNjQ5NDEwZjkwYzYwYTk3OGExYTRlMzg2ZTdjOTM3IiwidGFnIjoiIn0%3D"
}

# --- وظائف إدارة البيانات (Firebase) ---
def get_user_data(uid):
    u = db.child("users").child(uid).get().val()
    if not u:
        u = {"balance": 0.0}; db.child("users").child(uid).set(u)
    return u

def get_settings():
    s = db.child("settings").get().val()
    if not s:
        s = {"profit_on": False, "group_link": "https://t.me/xxxx", "banned": []}
        db.child("settings").set(s)
    return s

def get_nums():
    return db.child("nums").get().val() or {}

def is_banned(uid):
    s = get_settings(); return str(uid) in s.get('banned', [])

# --- وظيفة سحب الكود الجديدة ---
def fetch_sms(number, range_name):
    url = "https://www.ivasms.com/portal/sms/received/getsms/number/sms"
    today = datetime.now().strftime("%Y-%m-%d")
    payload = {'_token': IVAS_TOKEN, 'start': today, 'end': today, 'Number': number, 'Range': range_name}
    try:
        res = requests.post(url, data=payload, headers=IVAS_HEADERS, timeout=12)
        match = re.search(r'(\d{5,6})', res.text)
        return match.group(1) if match else None
    except: return None

def check_ivas_loop(phone_number, chat_id, srv, cnt, rng):
    for _ in range(40):
        code = fetch_sms(phone_number, rng)
        if code:
            bot.send_message(chat_id, f"✅ **تم استلام الكود!**\n\nالخدمة: `{srv}`\nالرقم: `{phone_number}`\nالكود: `{code}`", parse_mode="Markdown")
            return
        time.sleep(10)
    bot.send_message(chat_id, f"❌ انتهى وقت الانتظار للرقم `{phone_number}`.")

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def start_msg(message):
    if is_banned(message.from_user.id): return
    uid = str(message.from_user.id); u = get_user_data(uid); s = get_settings()
    bal_txt = f"💰 **رصيدك:** `{u['balance']}$`" if s.get('profit_on') else ""
    txt = (f"🔥 **أهلاً بك في بوت الأرقام!** 🔥\n━━━━━━━━━━━━━━\n"
           f"🚀 **خدمة تفعيل الأرقام العالمية**\n\n{bal_txt}\n"
           f"📈 **حالة السيرفر:** `يعمل ✅`\n━━━━━━━━━━━━━━\n👇 **اختر الخدمة:**")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("📱 طلب رقم جديد", callback_data="u_get"))
    markup.add(types.InlineKeyboardButton("👨‍💻 المالك", url=f"https://t.me/{OWNER_USER}"),
               types.InlineKeyboardButton("📢 قناة الأكواد", url=s.get('group_link')))
    bot.send_message(message.chat.id, txt, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['hamo'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    s = get_settings(); p_stat = "✅" if s.get('profit_on') else "❌"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("➕ إضافة رينج", callback_data="adm_add"),
               types.InlineKeyboardButton("🗑️ حذف الكل", callback_data="adm_del_main"),
               types.InlineKeyboardButton(f"الربح: {p_stat}", callback_data="adm_tog_p"),
               types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
               types.InlineKeyboardButton("🌐 الجروب", callback_data="adm_set_gl"),
               types.InlineKeyboardButton("🚫 حظر", callback_data="adm_ban"),
               types.InlineKeyboardButton("📊 إحصائيات", callback_data="adm_stats"),
               types.InlineKeyboardButton("💰 تعديل رصيد", callback_data="adm_edit_bal"))
    bot.send_message(message.chat.id, "🛠️ **لوحة التحكم المركزية - Firebase Mode**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    n = get_nums(); s = get_settings(); uid = str(call.from_user.id)
    if call.data == "u_get":
        if not n: return bot.answer_callback_query(call.id, "لا توجد أرقام!")
        markup = types.InlineKeyboardMarkup()
        for k in n.keys(): markup.add(types.InlineKeyboardButton(k, callback_data=f"srv_{k}"))
        bot.edit_message_text("📱 **اختر الخدمة:**", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data.startswith("srv_"):
        srv = call.data.split("_")[1]; markup = types.InlineKeyboardMarkup()
        if srv in n:
            for c in n[srv].keys(): markup.add(types.InlineKeyboardButton(c, callback_data=f"getnum_{srv}_{c}"))
            bot.edit_message_text(f"🌍 **اختر الدولة لخدمة {srv}:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("getnum_"):
        _, srv, cnt = call.data.split("_")
        details = n.get(srv, {}).get(cnt)
        if details and details.get('list'):
            num = details['list'].pop(0); rng = details['range']
            db.child("nums").child(srv).child(cnt).update({"list": details['list']})
            bot.edit_message_text(f"◈ **الرقم:** `{num}`\n⏳ جاري الانتظار...", call.message.chat.id, call.message.message_id)
            Thread(target=check_ivas_loop, args=(num, call.message.chat.id, srv, cnt, rng)).start()
        else: bot.answer_callback_query(call.id, "انتهت الأرقام!")

    elif call.data == "adm_add":
        m = bot.send_message(call.message.chat.id, "📌 اسم الخدمة:", reply_markup=cancel_markup())
        bot.register_next_step_handler(m, get_srv_name)

# --- خطوات الإضافة (get_srv_name, get_cnt_name, get_range, save_file_with_range) تضاف هنا بنفس المنطق ---
def cancel_markup():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    m.add("إلغاء العملية ❌"); return m

def get_srv_name(m):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    srv = m.text
    m2 = bot.send_message(m.chat.id, f"🌍 الدولة لـ {srv}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m2, lambda msg: get_cnt_name(msg, srv))

def get_cnt_name(m, srv):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    cnt = m.text
    m3 = bot.send_message(m.chat.id, f"🔢 الـ Range لـ {cnt}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m3, lambda msg: get_range(msg, srv, cnt))

def get_range(m, srv, cnt):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    rng = m.text
    m4 = bot.send_message(m.chat.id, f"📄 ارفع ملف الأرقام (.txt):", reply_markup=cancel_markup())
    bot.register_next_step_handler(m4, lambda msg: save_file_with_range(msg, srv, cnt, rng))

def save_file_with_range(m, srv, cnt, rng):
    if not m.document: return bot.send_message(m.chat.id, "ارفع ملف!")
    raw = bot.download_file(bot.get_file(m.document.file_id).file_path).decode('utf-8').splitlines()
    db.child("nums").child(srv).child(cnt).set({"range": rng, "list": [x.strip() for x in raw if x.strip()]})
    bot.send_message(m.chat.id, "✅ تم الحفظ في Firebase.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

# --- إعدادات Vercel Webhook ---
app = Flask(__name__)
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # استبدل YOUR_URL بالرابط اللي Vercel هتديهولك
    bot.set_webhook(url='https://fakenumber-xhw7.vercel.app/' + API_TOKEN)
    return "✅ Webhook & Firebase Connected!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
