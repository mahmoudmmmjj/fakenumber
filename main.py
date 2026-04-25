import telebot
from telebot import types
import json
import os
import requests
import time
import re
import io
from threading import Thread
from datetime import datetime
import flask

# --- الإعدادات ---
API_TOKEN = '7675462685:AAHz8qN4ZGOVbEfsQp5vqYxjPA6SMxmzm7I'
ADMIN_ID = 7895195899 
OWNER_USER = "hamodyrat"
bot = telebot.TeleBot(API_TOKEN)

# بيانات IVASMS المحدثة من ملفاتك
IVAS_TOKEN = "mdWCez8pRLYEzgI4LPDcbCrMwJR96czg8PFWD7Sp"
IVAS_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    'Cookie': "_fbp=fb.1.1776003227915.194465397404537711; cf_clearance=DYPKOA2ue315tKTGTtM_BydeHjQJKPmvaw9phITsOoI-1776629195-1.2.1.1-VmoaO1R37S_mE2vCKqwqcWvXbxDvAN8_a6ipyAB.0FJ90rzOna2WN.wF3_CWijy1sqUDGMYuoH_cUbcMEYX8WrNpF_bC2cM_g3xRSI1hg1FPMDBKcQtz45ozvFEHVQX766JkWTOYWApCobrqP4SjIdOJ5PZdZ8p423Pgxhoa9ErTdmrJOnuAco7a7WdrhD4zzX78qI9fsHhEjJ7_uyK2LxYE5xdJ23d05OAQnuwOYUapTLUE_z3TcCKyw30.hB.S3sX5HsjX3d1z3WVW28tkX2IZ4NhSsUNGwNrN_nM8GDX5sySrKHEmv_wtwH3hahjYjxgXRZ2YZOtiFY2K5RQqPg; XSRF-TOKEN=eyJpdiI6Imdob2dKMm84ZG1zS0ZMMTYwbEhRdmc9PSIsInZhbHVlIjoidzg4cmovU1F1RngzM3lCcmtaTVZ6S2RadHpTWTBrUjZEN3I5NElBVDRmSVVhMUJsZUJRSUZpeStSc2hGWWo4dGFaeFE0U0VyZWl0bUpqaE1HSjg0SmJ3WUtkclFEeXNyOHpxUmlMN21aZzhpVDdqQ3VTenJZWDFINzFLeGhjMHUiLCJtYWMiOiJhN2NlYzMxYWU0OTM5YWY2OTEzODc0YzA4ZDhlZTg2ZjMyNTU1ZjZhOGU3ZmEzYWQ3MmYyOTgyMDgzMGE4MDc5IiwidGFnIjoiIn0%3D; ivas_sms_session=eyJpdiI6ImZZZkN5dkhjUzRTdnR6WWp1dEQ0Y1E9PSIsInZhbHVlIjoiOFI0aHhycWI2ajNHUnArWGF0N1g5bUZVbzZ2MFdwUzE2YllmZmp4RDREb21adVJOYmZOdkN0dE9PVkwzVkZGSUNoMWRsK0F3SEJEVjYxZ3FFRzFGdWJBQ1ZHakM1QzNlY2xZWlhLSXV3VmJpb1daSTg1RXlUYnVXeDFRcVRYZ0YiLCJtYWMiOiI5MmMzYmYzNzhlZmU1OTRmYWYwMjk3MGJiNWM4NDNjMmQwNjQ5NDEwZjkwYzYwYTk3OGExYTRlMzg2ZTdjOTM3IiwidGFnIjoiIn0%3D"
}

DB_FILE = 'users.json'
NUMS_FILE = 'nums.json'
SET_FILE = 'settings.json'
LOG_FILE = 'sent_logs.json'

# --- إدارة البيانات ---
def load_data(f):
    if not os.path.exists(f): return {}
    try:
        with open(f, 'r', encoding='utf-8') as file: return json.load(file)
    except: return {}

def save_data(f, data):
    with open(f, 'w', encoding='utf-8') as file: json.dump(data, file, indent=4, ensure_ascii=False)

def is_banned(uid):
    s = load_data(SET_FILE)
    return str(uid) in s.get('banned', [])

# --- الاتصال الجديد لسحب الكود ---
def fetch_sms(number, range_name):
    url = "https://www.ivasms.com/portal/sms/received/getsms/number/sms"
    today = datetime.now().strftime("%Y-%m-%d")
    payload = {
        '_token': IVAS_TOKEN,
        'start': today, 'end': today,
        'Number': number, 'Range': range_name
    }
    try:
        res = requests.post(url, data=payload, headers=IVAS_HEADERS, timeout=12)
        match = re.search(r'code: (\d{5,6})', res.text)
        if not match: match = re.search(r'(\d{5,6})', res.text)
        if match: return match.group(1)
    except: pass
    return None

# --- المراقب العام للرينجات (Global Monitor) ---
def global_monitor():
    while True:
        try:
            n = load_data(NUMS_FILE)
            s = load_data(SET_FILE)
            logs = load_data(LOG_FILE)
            group = s.get('group_link', str(ADMIN_ID))
            target_chat = group.split('/')[-1] if 't.me' in group else ADMIN_ID

            for srv, countries in n.items():
                for cnt, details in countries.items():
                    if isinstance(details, dict):
                        rng = details.get('range')
                        num_list = details.get('list', [])
                        if rng:
                            for num in num_list[:3]:
                                code = fetch_sms(num, rng)
                                if code and logs.get(f"{num}_{code}") is None:
                                    bot.send_message(target_chat, f"📩 **رسالة جديدة تم التقاطها!**\nالرقم: `{num}`\nالكود: `{code}`")
                                    logs[f"{num}_{code}"] = True
                                    save_data(LOG_FILE, logs)
        except: pass
        time.sleep(60)

# --- فحص الكود للمستخدم ---
def check_ivas_loop(phone_number, chat_id, srv, cnt, rng):
    for _ in range(40): 
        code = fetch_sms(phone_number, rng)
        if code:
            bot.send_message(chat_id, f"✅ **تم استلام الكود!**\n\nالخدمة: `{srv}`\nالرقم: `{phone_number}`\nالكود: `{code}`", parse_mode="Markdown")
            return
        time.sleep(10)
    bot.send_message(chat_id, f"❌ انتهى وقت الانتظار للرقم `{phone_number}`.")

# --- الأوامر الأساسية ---
@bot.message_handler(commands=['start'])
def start_msg(message):
    if is_banned(message.from_user.id): return
    uid = str(message.from_user.id); u = load_data(DB_FILE)
    if uid not in u: u[uid] = {"balance": 0.0}; save_data(DB_FILE, u)
    s = load_data(SET_FILE)
    bal_txt = f"💰 **رصيدك:** `{u[uid]['balance']}$`" if s.get('profit_on') else ""
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
    s = load_data(SET_FILE); p_stat = "✅" if s.get('profit_on') else "❌"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("➕ إضافة رينج", callback_data="adm_add"),
               types.InlineKeyboardButton("🗑️ حذف الكل", callback_data="adm_del_main"),
               types.InlineKeyboardButton(f"الربح: {p_stat}", callback_data="adm_tog_p"),
               types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
               types.InlineKeyboardButton("🌐 الجروب", callback_data="adm_set_gl"),
               types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data="adm_ban"),
               types.InlineKeyboardButton("📊 إحصائيات", callback_data="adm_stats"),
               types.InlineKeyboardButton("📑 تصدير IDs", callback_data="adm_exp"),
               types.InlineKeyboardButton("💰 تعديل رصيد", callback_data="adm_edit_bal"))
    bot.send_message(message.chat.id, "🛠️ **لوحة التحكم المركزية - كاملة**", reply_markup=markup)

# --- Callbacks ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    n = load_data(NUMS_FILE); s = load_data(SET_FILE); u = load_data(DB_FILE)
    if call.data == "u_get":
        if not n: return bot.answer_callback_query(call.id, "لا توجد أرقام متوفرة!")
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
        if details and isinstance(details, dict) and details.get('list'):
            num = details['list'].pop(0); rng = details['range']; save_data(NUMS_FILE, n)
            bot.edit_message_text(f"◈ **الرقم:** `{num}`\n⏳ جاري البحث عن الكود (Range: {rng})...", call.message.chat.id, call.message.message_id)
            Thread(target=check_ivas_loop, args=(num, call.message.chat.id, srv, cnt, rng)).start()
        else: bot.answer_callback_query(call.id, "عذراً، انتهت الأرقام لهذه الدولة.")

    elif call.data == "adm_add":
        m = bot.send_message(call.message.chat.id, "📌 اسم الخدمة الجديدة:", reply_markup=cancel_markup())
        bot.register_next_step_handler(m, get_srv_name)

    elif call.data == "adm_stats":
        txt = f"📊 **إحصائيات البوت:**\n- مستخدمين: {len(u)}\n- خدمات: {len(n)}\n- محظورين: {len(s.get('banned', []))}"
        bot.answer_callback_query(call.id, txt, show_alert=True)

    elif call.data == "adm_tog_p":
        s['profit_on'] = not s.get('profit_on', False)
        save_data(SET_FILE, s); bot.answer_callback_query(call.id, f"الربح الآن: {s['profit_on']}")
        admin_panel(call.message)

# --- خطوات الإضافة الكاملة بالرينج ---
def cancel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("إلغاء العملية ❌")
    return markup

def get_srv_name(m):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    srv = m.text
    m2 = bot.send_message(m.chat.id, f"🌍 الدولة لـ {srv}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m2, lambda msg: get_cnt_name(msg, srv))

def get_cnt_name(m, srv):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    cnt = m.text
    m3 = bot.send_message(m.chat.id, f"🔢 الـ Range لـ {cnt} (مثال: EGYPT 5130):", reply_markup=cancel_markup())
    bot.register_next_step_handler(m3, lambda msg: get_range(msg, srv, cnt))

def get_range(m, srv, cnt):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    rng = m.text
    m4 = bot.send_message(m.chat.id, f"📄 الآن ارفع ملف الأرقام (.txt):", reply_markup=cancel_markup())
    bot.register_next_step_handler(m4, lambda msg: save_file_with_range(msg, srv, cnt, rng))

def save_file_with_range(m, srv, cnt, rng):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    if not m.document: return bot.send_message(m.chat.id, "خطأ: لازم ترفع ملف!")
    info = bot.get_file(m.document.file_id)
    raw = bot.download_file(info.file_path).decode('utf-8').splitlines()
    n = load_data(NUMS_FILE)
    if srv not in n: n[srv] = {}
    n[srv][cnt] = {"range": rng, "list": [x.strip() for x in raw if x.strip()]}
    save_data(NUMS_FILE, n)
    bot.send_message(m.chat.id, "✅ تم إضافة الرينج والأرقام بنجاح.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

# --- إدارة المستخدمين (حظر/رصيد) من كودك ---
@bot.callback_query_handler(func=lambda call: call.data == "adm_ban")
def ban_call(call):
    m = bot.send_message(call.message.chat.id, "🆔 أرسل ID المستخدم لحظره:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m, ban_user_step)

def ban_user_step(m):
    if m.text == "إلغاء العملية ❌": return admin_panel(m)
    s = load_data(SET_FILE); bans = s.get('banned', [])
    bans.append(str(m.text)); s['banned'] = bans; save_data(SET_FILE, s)
    bot.send_message(m.chat.id, f"✅ تم حظر {m.text}", reply_markup=types.ReplyKeyboardRemove())

# --- تشغيل البوت مع معالجة أخطاء الشبكة ---
Thread(target=global_monitor, daemon=True).start()

print("🚀 البوت يعمل الآن بكامل طاقته (270 سطر محدث)...")
from flask import Flask, request

app = Flask(__name__)

# دي النقطة اللي تليجرام هيبعت عليها الرسايل
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# دي صفحة بتفتحها مرة واحدة في المتصفح عشان تربط البوت بالرابط الجديد
@app.route("/")
def webhook():
    bot.remove_webhook()
    # استبدل الرابط ده برابط المشروع اللي فيرسل هتديهولك
    bot.set_webhook(url='https://fakenumber-zeta.vercel.app/' + API_TOKEN)
    return "✅ Webhook has been set successfully!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
