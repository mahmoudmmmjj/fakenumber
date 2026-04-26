import telebot
from telebot import types
import json
import os
import requests
import time
import re
import io
from flask import Flask, request
from threading import Thread
from datetime import datetime

# --- الإعدادات ---
API_TOKEN = '7675462685:AAHz8qN4ZGOVbEfsQp5vqYxjPA6SMxmzm7I'
ADMIN_ID = 7895195899 
OWNER_USER = "hamodyrat"

# ⚠️ مهم جداً: حط رابط مشروعك على فيرسل هنا (عشان يستقبل الرسايل)
WEBHOOK_URL = "https://fakenumbers-seven.vercel.app/"

bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=50)

# --- إعدادات قاعدة البيانات السحابية (Firebase بديل JSON لـ Vercel) ---
FIREBASE_URL = "https://hamody-68a5e-default-rtdb.firebaseio.com"

def load_data(path):
    try:
        res = requests.get(f"{FIREBASE_URL}/{path}.json")
        return res.json() if res.json() else {}
    except: return {}

def save_data(path, data):
    try: requests.put(f"{FIREBASE_URL}/{path}.json", json=data)
    except: pass

def is_banned(uid):
    s = load_data("settings")
    if not s: return False
    return str(uid) in s.get('banned', [])

def cancel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("إلغاء العملية ❌")
    return markup

# --- إعدادات IVASMS (من ملفك اللي باعته بالظبط) ---
IVAS_TOKEN = "mdWCez8pRLYEzgI4LPDcbCrMwJR96czg8PFWD7Sp"
IVAS_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    'Accept': "text/html, */*; q=0.01",
    'x-requested-with': "XMLHttpRequest",
    'origin': "https://www.ivasms.com",
    'referer': "https://www.ivasms.com/portal/sms/received",
    'Cookie': "_fbp=fb.1.1776003227915.194465397404537711; cf_clearance=DYPKOA2ue315tKTGTtM_BydeHjQJKPmvaw9phITsOoI-1776629195-1.2.1.1-VmoaO1R37S_mE2vCKqwqcWvXbxDvAN8_a6ipyAB.0FJ90rzOna2WN.wF3_CWijy1sqUDGMYuoH_cUbcMEYX8WrNpF_bC2cM_g3xRSI1hg1FPMDBKcQtz45ozvFEHVQX766JkWTOYWApCobrqP4SjIdOJ5PZdZ8p423Pgxhoa9ErTdmrJOnuAco7a7WdrhD4zzX78qI9fsHhEjJ7_uyK2LxYE5xdJ23d05OAQnuwOYUapTLUE_z3TcCKyw30.hB.S3sX5HsjX3d1z3WVW28tkX2IZ4NhSsUNGwNrN_nM8GDX5sySrKHEmv_wtwH3hahjYjxgXRZ2YZOtiFY2K5RQqPg; XSRF-TOKEN=eyJpdiI6Imdob2dKMm84ZG1zS0ZMMTYwbEhRdmc9PSIsInZhbHVlIjoidzg4cmovU1F1RngzM3lCcmtaTVZ6S2RadHpTWTBrUjZEN3I5NElBVDRmSVVhMUJsZUJRSUZpeStSc2hGWWo4dGFaeFE0U0VyZWl0bUpqaE1HSjg0SmJ3WUtkclFEeXNyOHpxUmlMN21aZzhpVDdqQ3VTenJZWDFINzFLeGhjMHUiLCJtYWMiOiJhN2NlYzMxYWU0OTM5YWY2OTEzODc0YzA4ZDhlZTg2ZjMyNTU1ZjZhOGU3ZmEzYWQ3MmYyOTgyMDgzMGE4MDc5IiwidGFnIjoiIn0%3D; ivas_sms_session=eyJpdiI6ImZZZkN5dkhjUzRTdnR6WWp1dEQ0Y1E9PSIsInZhbHVlIjoiOFI0aHhycWI2ajNHUnArWGF0N1g5bUZVbzZ2MFdwUzE2YllmZmp4RDREb21adVJOYmZOdkN0dE9PVkwzVkZGSUNoMWRsK0F3SEJEVjYxZ3FFRzFGdWJBQ1ZHakM1QzNlY2xZWlhLSXV3VmJpb1daSTg1RXlUYnVXeDFRcVRYZ0YiLCJtYWMiOiI5MmMzYmYzNzhlZmU1OTRmYWYwMjk3MGJiNWM4NDNjMmQwNjQ5NDEwZjkwYzYwYTk3OGExYTRlMzg2ZTdjOTM3IiwidGFnIjoiIn0%3D"
}

# --- دالة سحب الرسايل المحدثة من اتصالك ---
def fetch_sms(number, range_name):
    url = "https://www.ivasms.com/portal/sms/received/getsms/number/sms"
    today = datetime.now().strftime("%Y-%m-%d")
    payload = {
        '_token': IVAS_TOKEN,
        'start': today,
        'end': today,
        'Number': number,
        'Range': range_name
    }
    try:
        res = requests.post(url, data=payload, headers=IVAS_HEADERS, timeout=12)
        match = re.search(r'(\d{5,6})', res.text) # البحث عن كود 5 أو 6 أرقام
        if match: return match.group(1)
    except Exception as e: pass
    return None

def check_ivas_loop(phone_number, chat_id, srv, rng):
    for _ in range(30):
        code = fetch_sms(phone_number, rng)
        if code:
            bot.send_message(chat_id, f"✅ **تم استلام الكود!**\n\nالخدمة: `{srv}`\nالرقم: `{phone_number}`\nالكود: `{code}`", parse_mode="Markdown")
            return
        time.sleep(10)
    bot.send_message(chat_id, f"❌ انتهى وقت الانتظار للرقم `{phone_number}`.")

# --- أوامر المستخدم ---
@bot.message_handler(commands=['start'])
def start_msg(message):
    if is_banned(message.from_user.id): return
    uid = str(message.from_user.id)
    u = load_data("users")
    if uid not in u:
        u[uid] = {"balance": 0.0}
        save_data("users", u)
    
    s = load_data("settings")
    if not s: s = {"profit_on": False, "group_link": "https://t.me/hamodyrat"}
    
    bal_txt = f"💰 **رصيدك:** `{u[uid]['balance']}$`" if s.get('profit_on') else ""
    
    txt = (f"🔥 **أهلاً بك في بوت الأرقام!** 🔥\n━━━━━━━━━━━━━━\n"
           f"🚀 **خدمة تفعيل الأرقام العالمية**\n\n{bal_txt}\n"
           f"📈 **حالة السيرفر:** `يعمل ✅`\n━━━━━━━━━━━━━━\n👇 **اختر الخدمة:**")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("📱 طلب رقم جديد", callback_data="u_get"))
    markup.add(types.InlineKeyboardButton("👨‍💻 المالك", url=f"https://t.me/{OWNER_USER}"),
               types.InlineKeyboardButton("📢 قناة الأكواد", url=s.get('group_link')))
    bot.send_message(message.chat.id, txt, reply_markup=markup, parse_mode="Markdown")

# --- لوحة التحكم للإدارة ---
@bot.message_handler(commands=['hamo'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    s = load_data("settings")
    p_stat = "✅" if s.get('profit_on') else "❌"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة أرقام ورينج", callback_data="adm_add"),
        types.InlineKeyboardButton("🗑️ حذف", callback_data="adm_del_main"),
        types.InlineKeyboardButton(f"الربح: {p_stat}", callback_data="adm_tog_p"),
        types.InlineKeyboardButton("📢 إذاعة", callback_data="adm_bc"),
        types.InlineKeyboardButton("🌐 الجروب", callback_data="adm_set_gl"),
        types.InlineKeyboardButton("🚫 حظر", callback_data="adm_ban"),
        types.InlineKeyboardButton("📊 إحصائيات", callback_data="adm_stats"),
        types.InlineKeyboardButton("📄 IDs", callback_data="adm_exp")
    )
    bot.send_message(message.chat.id, "🛠️ **لوحة التحكم المركزية**", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "إلغاء العملية ❌")
def cancel_all(m):
    bot.clear_step_handler_by_chat_id(m.chat.id)
    bot.send_message(m.chat.id, "✅ تم إلغاء العملية.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

# --- Callbacks ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    n = load_data("nums")
    s = load_data("settings")

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
        details = n.get(srv, {}).get(cnt, {})
        if details and details.get('list'):
            num = details['list'].pop(0)
            rng = details['range'] # سحب الرينج عشان الـ API
            save_data("nums", n)
            txt = f"◈ **الرقم:** `{num}`\n◈ **الدولة:** `{cnt}`\n◈ **الحالة:** ⏳ جاري الانتظار..."
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("قناة الأكواد 📩", url=s.get('group_link')))
            markup.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"chg_{srv}_{cnt}"),
                       types.InlineKeyboardButton("⬅️ رجوع", callback_data="u_get"))
            bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            
            # تشغيل المراقبة في Thread عشان Vercel ما يوقفش
            Thread(target=check_ivas_loop, args=(num, call.message.chat.id, srv, rng)).start()
        else: bot.answer_callback_query(call.id, "الأرقام خلصت!")

    elif call.data == "adm_add":
        m = bot.send_message(call.message.chat.id, "📌 اكتب اسم الخدمة (مثل: واتساب):", reply_markup=cancel_markup())
        bot.register_next_step_handler(m, get_srv_name)

    elif call.data == "adm_del_main":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑️ حذف قسم كامل", callback_data="del_srv_list"),
                   types.InlineKeyboardButton("🏳️ حذف دولة فقط", callback_data="del_cnt_list"))
        bot.edit_message_text("اختر نوع الحذف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "del_srv_list":
        markup = types.InlineKeyboardMarkup()
        for k in n.keys(): markup.add(types.InlineKeyboardButton(k, callback_data=f"final_dsrv_{k}"))
        bot.edit_message_text("اختر القسم للحذف نهائياً:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "del_cnt_list":
        markup = types.InlineKeyboardMarkup()
        for k in n.keys(): markup.add(types.InlineKeyboardButton(k, callback_data=f"listcnt_{k}"))
        bot.edit_message_text("اختر القسم الذي تتبع له الدولة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("listcnt_"):
        srv = call.data.split("_")[1]
        markup = types.InlineKeyboardMarkup()
        if srv in n:
            for c in n[srv].keys(): markup.add(types.InlineKeyboardButton(c, callback_data=f"final_dcnt_{srv}_{c}"))
            bot.edit_message_text(f"اختر دولة من {srv} لحذفها:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("final_dsrv_"):
        srv = call.data.split("_")[2]
        if srv in n: del n[srv]; save_data("nums", n)
        bot.answer_callback_query(call.id, f"تم حذف {srv}")
        admin_panel(call.message)

    elif call.data.startswith("final_dcnt_"):
        p = call.data.split("_")
        srv, cnt = p[2], p[3]
        if srv in n and cnt in n[srv]: 
            del n[srv][cnt]
            if not n[srv]: del n[srv] 
            save_data("nums", n)
        bot.answer_callback_query(call.id, f"تم حذف {cnt}")
        admin_panel(call.message)

    elif call.data == "adm_tog_p":
        s['profit_on'] = not s.get('profit_on', False)
        save_data("settings", s); admin_panel(call.message)

    elif call.data == "adm_bc":
        m = bot.send_message(call.message.chat.id, "📣 ارسل الرسالة الآن:", reply_markup=cancel_markup())
        bot.register_next_step_handler(m, broadcast_step)

    elif call.data == "adm_ban":
        m = bot.send_message(call.message.chat.id, "🚫 ارسل الـ ID لحظره:", reply_markup=cancel_markup())
        bot.register_next_step_handler(m, ban_user_step)

    elif call.data == "adm_set_gl":
        m = bot.send_message(call.message.chat.id, "🔗 ارسل رابط الجروب الجديد:", reply_markup=cancel_markup())
        bot.register_next_step_handler(m, set_link_step)

    elif call.data == "adm_stats":
        u = load_data("users")
        txt = f"📊 **إحصائيات البوت:**\n\n👥 عدد المستخدمين: `{len(u)}`"
        for k, v in n.items():
            total = sum(len(x.get('list', [])) for x in v.values())
            txt += f"\n📱 {k}: `{total} رقم`"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

    elif call.data == "adm_exp":
        u = load_data("users"); ids = "\n".join(u.keys())
        bot.send_document(call.message.chat.id, io.BytesIO(ids.encode()), caption=f"👥 IDs list ({len(u)})")

# --- Steps ---
def get_srv_name(m):
    if m.text == "إلغاء العملية ❌": return
    srv = m.text
    m2 = bot.send_message(m.chat.id, f"🌍 اكتب اسم الدولة لـ {srv}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m2, lambda msg: get_cnt_name(msg, srv))

def get_cnt_name(m, srv):
    if m.text == "إلغاء العملية ❌": return
    cnt = m.text
    m3 = bot.send_message(m.chat.id, f"🔢 اكتب اسم الـ Range (مثال: EGYPT 5130):", reply_markup=cancel_markup())
    bot.register_next_step_handler(m3, lambda msg: get_rng_name(msg, srv, cnt))

def get_rng_name(m, srv, cnt):
    if m.text == "إلغاء العملية ❌": return
    rng = m.text
    m4 = bot.send_message(m.chat.id, f"📄 ارفع ملف .txt لـ {srv}/{cnt}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m4, lambda msg: save_file_logic(msg, srv, cnt, rng))

def save_file_logic(m, srv, cnt, rng):
    if m.text == "إلغاء العملية ❌": return
    if not m.document: return bot.send_message(m.chat.id, "خطأ: ارفع ملف txt!")
    info = bot.get_file(m.document.file_id)
    raw = bot.download_file(info.file_path).decode('utf-8').splitlines()
    n = load_data("nums")
    if srv not in n: n[srv] = {}
    if cnt not in n[srv]: n[srv][cnt] = {"range": rng, "list": []}
    
    n[srv][cnt]['list'].extend([x.strip() for x in raw if x.strip()])
    n[srv][cnt]['range'] = rng 
    save_data("nums", n)
    bot.send_message(m.chat.id, "✅ تم الإضافة.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

def ban_user_step(m):
    if m.text == "إلغاء العملية ❌": return
    s = load_data("settings")
    if 'banned' not in s: s['banned'] = []
    s['banned'].append(str(m.text))
    save_data("settings", s)
    bot.send_message(m.chat.id, "✅ تم الحظر.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

def set_link_step(m):
    if m.text == "إلغاء العملية ❌": return
    s = load_data("settings"); s['group_link'] = m.text
    save_data("settings", s)
    bot.send_message(m.chat.id, "✅ تم تحديث الرابط.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

def broadcast_step(m):
    if m.text == "إلغاء العملية ❌": return
    u = load_data("users")
    for uid in u.keys():
        try: bot.copy_message(uid, m.chat.id, m.message_id)
        except: pass
    bot.send_message(m.chat.id, "✅ تم.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

# --- Vercel Webhook + Flask ---
app = Flask(__name__)

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    Thread(target=bot.process_new_updates, args=([update],)).start()
    return "!", 200

@app.route("/")
def index():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + '/' + API_TOKEN)
    return "Bot is Connected & Ready! ✅", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
