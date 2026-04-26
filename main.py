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

# --- الإعدادات (كودك الأصلي) ---
API_TOKEN = '7675462685:AAHz8qN4ZGOVbEfsQp5vqYxjPA6SMxmzm7I'
ADMIN_ID = 7895195899 
OWNER_USER = "hamodyrat"
bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=50)

IVAS_HEADERS = {
    'User-Agent': "Mozilla/5.0",
    'Cookie': 'ivas_sms_session=eyJpdiI6IlJDY3pTcWtvR2dOcUJ6Q2ZuUmdTckE9PSIsInZhbHVlIjoiU3duN011eXVJRUM2YkFqZnZNZk9KTTJsam9Uek9Uam5EaVVqdkNyWUtITThhdGZGZmR1T2F1VG5oN3JzUTEzbDBTUUt0QWJ2aERodytIcWxyNEY0N3dhQjdlK3JrMDNSRDhBTEZQNCtUNGM5T0pSdFd2Y3JIRDJZTnNOcmRRNDciLCJtYWMiOiI5NTkxYTM4ODA3ZjE3MGQ5OGU3NDgyYmRkYTBjZWU3NzQ3Njc4N2Q4MTBiODdjMzYwNDA1YzNmMjNmMzU2NzVkIiwidGFnIjoiIn0%3D; XSRF-TOKEN=eyJpdiI6IlB6UCs1bkZNaG81cGtPT0lRQ29xVmc9PSIsInZhbHVlIjoiWElRTGF1RGxuUWN2cExJWkxPMFRZU3NCNTh5MUl2NjRzYzljeDNOQ3BLRzBWNmlibHpVTVlEM0drNWxBUDcvTHZOQjJ0L0x1QWRuQjF3N2pndEdZdkQ2THRMaWM4TkdvWFJJRndGTnh3ZUlPTGRSM2NyQjVxSGRaWmZ3aUF1cEYiLCJtYWMiOiI4YjhiZDk0NzRjOTFlMTc3MDdmODg0YjFlODk2NGY0NDQ1NWM0MTY0NTI4YWViZWMwYWMxYTY3ZThmYTg5ZDA0IiwidGFnIjoiIn0%3D'
}

# --- إدارة البيانات (Firebase بديل للملفات عشان Vercel) ---
FIREBASE_URL = "https://hamody-68a5e-default-rtdb.firebaseio.com"

def load_data_remote(path):
    try:
        res = requests.get(f"{FIREBASE_URL}/{path}.json")
        return res.json() if res.json() else {}
    except: return {}

def save_data_remote(path, data):
    try: requests.put(f"{FIREBASE_URL}/{path}.json", json=data)
    except: pass

def is_banned(uid):
    s = load_data_remote("settings")
    if not s: s = {"banned": []}
    return str(uid) in s.get('banned', [])

def cancel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("إلغاء العملية ❌")
    return markup

# --- فحص الكود (التعديل المطلوب لسحب الرسايل) ---
def check_ivas_loop(phone_number, chat_id, srv, cnt):
    url = "https://www.ivasms.com/portal/live/my_sms"
    for _ in range(45): 
        try:
            res = requests.get(url, headers=IVAS_HEADERS, timeout=10)
            if phone_number in res.text:
                # سحب الكود من بعد الرقم بـ 200 حرف
                match = re.search(r'(\d{5,6})', res.text.split(phone_number)[1][:200])
                if match:
                    code = match.group(1)
                    bot.send_message(chat_id, f"✅ **تم استلام الكود!**\n\nالخدمة: `{srv}`\nالرقم: `{phone_number}`\nالكود: `{code}`", parse_mode="Markdown")
                    return
        except: pass
        time.sleep(5)
    bot.send_message(chat_id, f"❌ انتهى وقت الانتظار للرقم `{phone_number}`")

# --- أوامر المستخدم ---
@bot.message_handler(commands=['start'])
def start_msg(message):
    if is_banned(message.from_user.id): return
    uid = str(message.from_user.id)
    u = load_data_remote("users")
    if uid not in u:
        u[uid] = {"balance": 0.0}
        save_data_remote("users", u)
    
    s = load_data_remote("settings")
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

# --- لوحة التحكم للإدارة (كاملة كما طلبت) ---
@bot.message_handler(commands=['hamo'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    s = load_data_remote("settings")
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

@bot.message_handler(func=lambda m: m.text == "إلغاء العملية ❌")
def cancel_all(m):
    bot.clear_step_handler_by_chat_id(m.chat.id)
    bot.send_message(m.chat.id, "✅ تم إلغاء العملية.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

# --- Callbacks (بدون حذف) ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    n = load_data_remote("nums")
    s = load_data_remote("settings")

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
            num = n[srv][cnt].pop(0)
            save_data_remote("nums", n)
            txt = f"◈ **الرقم:** `{num}`\n◈ **الدولة:** `{cnt}`\n◈ **الحالة:** ⏳ جاري الانتظار..."
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("قناة الأكواد 📩", url=s.get('group_link')))
            markup.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"chg_{srv}_{cnt}"),
                       types.InlineKeyboardButton("⬅️ رجوع", callback_data="u_get"))
            bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            Thread(target=check_ivas_loop, args=(num, call.message.chat.id, srv, cnt)).start()
        else: bot.answer_callback_query(call.id, "الأرقام خلصت!")

    elif call.data == "adm_add":
        m = bot.send_message(call.message.chat.id, "📌 اكتب اسم الخدمة:", reply_markup=cancel_markup())
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
        if srv in n: del n[srv]; save_data_remote("nums", n)
        bot.answer_callback_query(call.id, f"تم حذف {srv}")
        admin_panel(call.message)

    elif call.data.startswith("final_dcnt_"):
        p = call.data.split("_")
        srv, cnt = p[2], p[3]
        if srv in n and cnt in n[srv]: 
            del n[srv][cnt]
            if not n[srv]: del n[srv]
            save_data_remote("nums", n)
        bot.answer_callback_query(call.id, f"تم حذف {cnt}")
        admin_panel(call.message)

    elif call.data == "adm_tog_p":
        s['profit_on'] = not s.get('profit_on', False)
        save_data_remote("settings", s); admin_panel(call.message)

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
        u = load_data_remote("users")
        txt = f"📊 **إحصائيات البوت:**\n\n👥 عدد المستخدمين: `{len(u)}`"
        for k, v in n.items():
            total = sum(len(x) for x in v.values())
            txt += f"\n📱 {k}: `{total} رقم`"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

    elif call.data == "adm_exp":
        u = load_data_remote("users"); ids = "\n".join(u.keys())
        bot.send_document(call.message.chat.id, io.BytesIO(ids.encode()), caption=f"👥 IDs list ({len(u)})")

# --- Steps (كاملة) ---
def get_srv_name(m):
    if m.text == "إلغاء العملية ❌": return
    srv = m.text
    m2 = bot.send_message(m.chat.id, f"🌍 اكتب اسم الدولة لـ {srv}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m2, lambda msg: get_cnt_name(msg, srv))

def get_cnt_name(m, srv):
    if m.text == "إلغاء العملية ❌": return
    cnt = m.text
    m3 = bot.send_message(m.chat.id, f"📄 ارفع ملف .txt لـ {srv}/{cnt}:", reply_markup=cancel_markup())
    bot.register_next_step_handler(m3, lambda msg: save_file(msg, srv, cnt))

def save_file(m, srv, cnt):
    if m.text == "إلغاء العملية ❌": return
    if not m.document: return
    info = bot.get_file(m.document.file_id)
    raw = bot.download_file(info.file_path).decode('utf-8').splitlines()
    n = load_data_remote("nums")
    if srv not in n: n[srv] = {}
    n[srv][cnt] = n[srv].get(cnt, []) + [x.strip() for x in raw if x.strip()]
    save_data_remote("nums", n)
    bot.send_message(m.chat.id, "✅ تم الإضافة.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

def ban_user_step(m):
    if m.text == "إلغاء العملية ❌": return
    s = load_data_remote("settings")
    if 'banned' not in s: s['banned'] = []
    s['banned'].append(str(m.text))
    save_data_remote("settings", s)
    bot.send_message(m.chat.id, "✅ تم الحظر.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

def set_link_step(m):
    if m.text == "إلغاء العملية ❌": return
    s = load_data_remote("settings"); s['group_link'] = m.text
    save_data_remote("settings", s)
    bot.send_message(m.chat.id, "✅ تم تحديث الرابط.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

def broadcast_step(m):
    if m.text == "إلغاء العملية ❌": return
    u = load_data_remote("users")
    for uid in u.keys():
        try: bot.copy_message(uid, m.chat.id, m.message_id)
        except: pass
    bot.send_message(m.chat.id, "✅ تم.", reply_markup=types.ReplyKeyboardRemove())
    admin_panel(m)

# --- Vercel Webhook Configuration ---
app = Flask(__name__)
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    Thread(target=bot.process_new_updates, args=([update],)).start()
    return "!", 200

@app.route("/")
def index(): return "Bot Active!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
