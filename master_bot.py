import asyncio
import json
import os
import threading
import jdatetime
from datetime import datetime, timezone, timedelta
from huggingface_hub import HfApi, hf_hub_download

from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ButtonStyle

from pyrogram import Client as PyroClient
from pyrogram.errors import SessionPasswordNeeded

API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
BOT_TOKEN = "8726723140:AAEnazbn9GDuIFr13SYP6QhptWyQKOwyaF4"
ADMIN_ID = 2025464333 # آیدی عددی شما
SUPPORT_ID = "@Im_Iliiya" 
CHANNEL_ID = "https://t.me/Im_Iliiya" # لینک چنل خودتون رو بذارید

CARD_NUMBER = "6037990000000000"
CARD_NAME = "نام شما"

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

DB_FILE = "database.json"
REPO_ID = "SnowBig/SellerDB" 
HF_TOKEN = os.environ.get("HF_TOKEN")

user_states = {}   
temp_clients = {}  

def get_iran_time(): return datetime.now(IRAN_TZ)

def download_hf():
    try:
        if HF_TOKEN and REPO_ID and not os.path.exists(DB_FILE):
            hf_hub_download(repo_id=REPO_ID, filename=DB_FILE, repo_type="dataset", token=HF_TOKEN, local_dir=".", force_download=True)
    except: pass

download_hf()

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def upload_to_hf():
    try:
        if HF_TOKEN:
            api = HfApi()
            api.upload_file(path_or_fileobj=DB_FILE, path_in_repo=DB_FILE, repo_id=REPO_ID, repo_type="dataset", token=HF_TOKEN, commit_message="Update DB via MasterBot")
    except Exception: pass

def save_db(data):
    try:
        tmp_file = DB_FILE + ".tmp"
        with open(tmp_file, "w") as f: json.dump(data, f, indent=4)
        os.replace(tmp_file, DB_FILE) 
        threading.Thread(target=upload_to_hf, daemon=True).start()
    except Exception as e: print("Save DB Error:", e)

_db = load_db()
if "config" not in _db:
    _db["config"] = {}
_db["config"]["is_active"] = _db["config"].get("is_active", True)
_db["config"]["price_per_mah"] = _db["config"].get("price_per_mah", 1)
_db["config"]["gift_codes"] = _db["config"].get("gift_codes", {})

_db["config"]["module_prices"] = {
    "full_package": 50, "p_clock": 6, "p_guard": 3, "p_ai": 4, "p_tabchi": 4,
    "p_dl": 2, "p_music": 2, "p_v2ray": 2, "p_translate": 2, "p_forcejoin": 2,
    "p_locks": 2, "p_tag": 2, "p_purge": 2, "p_comment": 2, "p_cheat": 1,
    "p_action": 1, "p_textmode": 1, "p_monshi": 1, "p_filter": 1, "p_autoreply": 1,
    "p_react": 1, "p_spam": 1, "p_mute": 1, "p_tts": 1, "p_crypto": 1,
    "p_readall": 1, "p_qr": 1, "p_profile": 1, "p_logo": 1, "p_anim": 1,
    "p_ping": 0, "p_info": 0
}

_db["config"]["panel_config"] = {
    "layout": [
        ["p_textmode", "p_clock", "p_guard"], 
        ["p_ping", "p_logo", "p_locks", "p_action"], 
        ["p_monshi", "p_filter", "p_v2ray"], 
        ["p_autoreply", "p_forcejoin", "p_readall"], 
        ["p_dl", "p_react", "p_spam"], 
        ["p_mute", "p_info", "p_tag", "p_purge"], 
        ["p_ai", "p_qr", "p_profile"], 
        ["p_translate", "p_anim", "p_cheat"], 
        ["p_tts", "p_music", "p_tabchi"], 
        ["p_comment", "p_crypto"]
    ],
    "names": {
        "p_textmode": "🎨 حالت متن", "p_clock": "⏰ ساعت", "p_guard": "🛡 نگهبان چت", 
        "p_ping": "🏓 پینگ", "p_logo": "🖼 لوگو", "p_locks": "🔐 قفل‌ها", 
        "p_action": "🎭 اکشن", "p_monshi": "🤖 منشی", "p_filter": "🚫 فیلترکلمات", 
        "p_autoreply": "💬 پاسخ‌خودکار", "p_forcejoin": "🛑 عضویت اجباری", 
        "p_dl": "📥 دانلودر", "p_react": "❤️ ریکت", "p_spam": "💣 اسپم", 
        "p_mute": "🔇 سکوت/آزادی", "p_info": "🆔 آیدی", "p_tag": "🎯 تگ", 
        "p_purge": "🧹 پاکسازی", "p_ai": "🧠 هوش مصنوعی", "p_translate": "🌍 ترجمه", 
        "p_anim": "💖 انیمیشن", "p_cheat": "🎲 تقلب", "p_tts": "🎤 تبدیل به ویس", 
        "p_music": "🎵 سرچ آهنگ", "p_tabchi": "📢 تبچی", "p_comment": "📝 کامنت اول", 
        "p_crypto": "💰 قیمت ارز", "p_readall": "👁‍🗨 سین‌زن همگانی", 
        "p_v2ray": "🌐 پروکسی و V2ray", "p_qr": "⬛️ کیوآر کد", "p_profile": "👤 مدیریت پروفایل"
    }
}
save_db(_db)

def init_user(db, user_id):
    uid = str(user_id)
    if uid == "config": return
    if uid not in db:
        db[uid] = {
            "status": "inactive", "mah_balance": 0, 
            "active_modules": [], "has_full_package": False,
            "join_date": jdatetime.datetime.fromgregorian(datetime=get_iran_time()).strftime("%Y/%m/%d - %H:%M"), 
            "last_test_date": None, "paused_at": None, "phone": None
        }

def get_hourly_drain(db, user_id):
    u = db[str(user_id)]
    if u.get("has_full_package", False): return db["config"]["module_prices"].get("full_package", 50)
    total = 0
    for m in u.get("active_modules", []): total += db["config"]["module_prices"].get(m, 0)
    return total

def get_temp_hourly_drain(db, user_id):
    u = db[str(user_id)]
    if u.get("temp_has_full", False): return db["config"]["module_prices"].get("full_package", 50)
    total = 0
    for m in u.get("temp_modules", []): total += db["config"]["module_prices"].get(m, 0)
    return total

def calculate_remaining_time(db, user_id):
    u = db[str(user_id)]
    mah = u.get("mah_balance", 0)
    drain = get_hourly_drain(db, user_id)
    if drain == 0: return "مصرف صفر (نامحدود)"
    hours = mah / drain
    days = int(hours // 24)
    rem_hours = int(hours % 24)
    if days > 0: return f"{days} روز و {rem_hours} ساعت"
    return f"{rem_hours} ساعت"

def get_app_store_text(db, user_id):
    u = db[str(user_id)]
    drain = get_temp_hourly_drain(db, user_id)
    ppc = db["config"]["price_per_mah"]
    cost_toman = drain * ppc
    active_modules = u.get("temp_modules", [])
    has_full = u.get("temp_has_full", False)
    prices = db["config"]["module_prices"]
    names = db["config"]["panel_config"]["names"]
    is_active = (u.get("status") == "active")

    text = "🛍 *فروشگاه قابلیت‌ها (تنظیم مصرف باتری)*\n\n"
    text += "💡 قابلیت‌های مورد نظر خود را انتخاب کنید و در پایان روی دکمه *✨ ثبت و تایید نهایی تغییرات* کلیک کنید.\n\n"
    if is_active:
        text += "🟢 *وضعیت فعلی سلف: روشن*\n⚠️ در صورت اضافه کردن قابلیت جدید، هزینه ۱ ساعت آن در لحظه کسر می‌شود.\n\n"
    else:
        text += "⏸ *وضعیت فعلی سلف: خاموش*\nآزادانه تیک‌ها را تغییر دهید. کسر شارژ پس از تایید نهایی انجام خواهد شد.\n\n"

    text += "📋 *لیست انتخاب‌های فعلی شما:*\n"
    if has_full: text += f"👑 پکیج فول VIP — مصرف: `{prices.get('full_package', 50)}` میلی‌آمپر\n"
    elif not active_modules: text += "➖ هیچ قابلیتی انتخاب نشده است.\n"
    else:
        for m in active_modules:
            cost = prices.get(m, 0)
            if cost > 0: text += f"✔️ {names.get(m, m)} — مصرف: `{cost}` میلی‌آمپر\n"
            
    text += f"\n📊 *وضعیت مجموع مصرف این پکیج:*\n⚡️ `{drain}` میلی‌آمپر (معادل `{cost_toman:,}` تومان در ساعت)\n"
    return text

def get_numpad_keyboard(prefix):
    kb = [
        [InlineKeyboardButton(text="1", callback_data=f"{prefix}_1", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="2", callback_data=f"{prefix}_2", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="3", callback_data=f"{prefix}_3", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="4", callback_data=f"{prefix}_4", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="5", callback_data=f"{prefix}_5", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="6", callback_data=f"{prefix}_6", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="7", callback_data=f"{prefix}_7", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="8", callback_data=f"{prefix}_8", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="9", callback_data=f"{prefix}_9", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="⌫", callback_data=f"{prefix}_del", style=ButtonStyle.DANGER), 
         InlineKeyboardButton(text="0", callback_data=f"{prefix}_0", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="000", callback_data=f"{prefix}_000", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="✖️ پاک کردن", callback_data=f"{prefix}_clear", style=ButtonStyle.DANGER), 
         InlineKeyboardButton(text="✔️ تایید", callback_data=f"{prefix}_confirm", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="cancel_action", style=ButtonStyle.DANGER)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def main_menu_keyboard(user_id):
    kb = [
        [InlineKeyboardButton(text="🎛 پنل مدیریت سلف‌ربات", callback_data="menu_my_sub", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="👤 پروفایل من", callback_data="menu_my_account", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="🎁 دریافت شارژ رایگان", callback_data="menu_free_test", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="🔋 فروشگاه شارژ و باتری", callback_data="menu_buy_mah", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="💸 انتقال شارژ", callback_data="menu_transfer", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="👁‍🗨 پیش‌نمایش پنل", callback_data="menu_glass_panel", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="📢 کانال رسمی", url=CHANNEL_ID, style=ButtonStyle.DANGER), 
         InlineKeyboardButton(text="👨‍💻 ارتباط با پشتیبانی", url=f"https://t.me/{SUPPORT_ID.replace('@', '')}", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text="❓ سلف‌ربات چیست و چه کاربردی دارد؟", callback_data="menu_what_is")]
    ]
    if user_id == ADMIN_ID: 
        kb.append([InlineKeyboardButton(text="👨‍💻 ورود به پنل مدیریت (ادمین)", callback_data="menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_inline_keyboard(db):
    status_btn = "🔴 خاموش کردن فروشگاه" if db["config"]["is_active"] else "🟢 روشن کردن فروشگاه"
    
    # رنگ‌بندی ردیف‌به‌ردیف طبق درخواست
    kb = [
        # ردیف ۱ (آبی)
        [InlineKeyboardButton(text=status_btn, callback_data="adm_toggle_store", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="💰 تغییر قیمت پایه", callback_data="adm_change_price", style=ButtonStyle.PRIMARY)],
        # ردیف ۲ (سبز)
        [InlineKeyboardButton(text="💳 شارژ کاربر", callback_data="adm_fund", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="➖ کسر شارژ", callback_data="adm_deduct", style=ButtonStyle.SUCCESS)],
        # ردیف ۳ (آبی)
        [InlineKeyboardButton(text="🎁 ساخت کد تخفیف", callback_data="adm_gift", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="🛠 تعیین مصرف قابلیت‌ها", callback_data="adm_mod_prices", style=ButtonStyle.PRIMARY)],
        # ردیف ۴ (سبز)
        [InlineKeyboardButton(text="📢 ارسال همگانی", callback_data="adm_broadcast", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="♾ فعال‌سازی بینهایت", callback_data="adm_infinite", style=ButtonStyle.SUCCESS)],
        # ردیف ۵ (آبی)
        [InlineKeyboardButton(text="🔄 بازخوانی دیتابیس", callback_data="adm_reload_db", style=ButtonStyle.PRIMARY)],
        # ردیف ۶ (قرمز)
        [InlineKeyboardButton(text="🔙 بازگشت به منوی کاربری", callback_data="menu_main", style=ButtonStyle.DANGER)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def payment_method_keyboard(amount, price, code="NONE"):
    kb = []
    kb.append([InlineKeyboardButton(text="💳 پرداخت کارت به کارت", callback_data=f"pay_card_{amount}_{price}_{code}", style=ButtonStyle.SUCCESS)])
    if code == "NONE": 
        kb.append([InlineKeyboardButton(text="🎁 اعمال کد تخفیف", callback_data=f"ask_discount_{amount}_{price}", style=ButtonStyle.PRIMARY)])
    kb.append([InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_action", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cancel_keyboard(): 
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ لغو و بازگشت", callback_data="cancel_action", style=ButtonStyle.DANGER)]
    ])

def app_store_keyboard(db, user_id):
    u = db[str(user_id)]
    active = u.get("temp_modules", [])
    has_full = u.get("temp_has_full", False)
    prices = db["config"]["module_prices"]
    layout = db["config"]["panel_config"]["layout"]
    names = db["config"]["panel_config"]["names"]
    
    kb = []
    
    if has_full:
        kb.append([InlineKeyboardButton(text="پکیج فول VIP", callback_data="mod_toggle_full_package", style=ButtonStyle.SUCCESS)])
    else:
        kb.append([InlineKeyboardButton(text=f"پکیج فول VIP ({prices.get('full_package', 50)} mAh)", callback_data="mod_toggle_full_package")])
    
    for row in layout:
        row_btns = []
        for key in row:
            if key in ["p_ping", "p_info"]: continue 
            is_on = key in active or has_full
            cost = prices.get(key, 0)
            
            if is_on:
                row_btns.append(InlineKeyboardButton(text=f"{names.get(key, key)} ({cost})", callback_data=f"mod_toggle_{key}", style=ButtonStyle.SUCCESS))
            else:
                row_btns.append(InlineKeyboardButton(text=f"{names.get(key, key)} ({cost})", callback_data=f"mod_toggle_{key}"))
        kb.append(row_btns)
        
    kb.append([InlineKeyboardButton(text="✨ ثبت و تایید نهایی تغییرات", callback_data="confirm_app_store_changes", style=ButtonStyle.PRIMARY)])
    kb.append([InlineKeyboardButton(text="🔙 انصراف و بازگشت", callback_data="manage_self_refresh", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_module_price_keyboard(db):
    prices = db["config"]["module_prices"]
    names = db["config"]["panel_config"]["names"]
    kb = []
    kb.append([InlineKeyboardButton(text="🌐 تغییر مصرف همه ماژول‌ها یکجا", callback_data="adm_mod_price_ALL", style=ButtonStyle.PRIMARY)])
    kb.append([InlineKeyboardButton(text=f"👑 پکیج فول ({prices.get('full_package', 0)})", callback_data="adm_mod_price_full_package", style=ButtonStyle.PRIMARY)])
    
    for row in db["config"]["panel_config"]["layout"]:
        row_btns = []
        for key in row:
            if key in ["p_ping", "p_info"]: continue
            cost = prices.get(key, 0)
            row_btns.append(InlineKeyboardButton(text=f"{names.get(key, key)} ({cost})", callback_data=f"adm_mod_price_{key}", style=ButtonStyle.PRIMARY))
        kb.append(row_btns)
        
    kb.append([InlineKeyboardButton(text="🔙 بازگشت به پنل", callback_data="menu_admin", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

async def cancel_and_refund(user_id, message_obj=None):
    if user_id in temp_clients:
        try: await temp_clients[user_id]["client"].disconnect()
        except: pass
        del temp_clients[user_id]
    if user_id in user_states: del user_states[user_id]
    if message_obj:
        try: await message_obj.delete()
        except: pass

async def send_manage_self_menu(db, user_id, callback_query=None):
    u_data = db[str(user_id)]
    status = u_data.get("status", "inactive")
    mah = u_data.get("mah_balance", 0)
    drain = get_hourly_drain(db, user_id)
    rem_time = calculate_remaining_time(db, user_id)
    
    text = f"🎛 *پنل مدیریت سلف‌ربات شما*\n\n🔋 موجودی پاوربانک: `{mah:,}` میلی‌آمپر\n⚡️ مصرف فعلی: `{drain}` میلی‌آمپر در ساعت\n⏱ زمان تقریبی روشن ماندن: *{rem_time}*\n\n💡 *نکته:* برای ۱ ماه استفاده ۲۴ ساعته از پکیج فول، به *36,000 میلی‌آمپر* شارژ نیاز دارید.\n"
    
    kb = []
    if status == "inactive":
        text += "\n❌ وضعیت: *متصل نیست (نیاز به ورود)*"
        kb.append([InlineKeyboardButton(text="📲 روشن‌کردن و اتصال به اکانت تلگرام", callback_data="start_login_flow", style=ButtonStyle.SUCCESS)])
        if u_data.get("phone"):
            kb.append([InlineKeyboardButton(text="📱 ورود با شماره دیگر (تغییر شماره)", callback_data="change_phone_number", style=ButtonStyle.PRIMARY)])
    else:
        if status == "paused":
            text += "\n⏸ وضعیت: *خاموش (Sleep Mode)*"
            kb.append([InlineKeyboardButton(text="🟢 روشن کردن سلف (با امکانات قبلی)", callback_data="bot_turn_on", style=ButtonStyle.SUCCESS)])
        else:
            text += "\n🟢 وضعیت: *فعال و در حال کار*"
            kb.append([InlineKeyboardButton(text="🔴 خاموش کردن موقت (توقف مصرف)", callback_data="bot_turn_off", style=ButtonStyle.DANGER)])
            
        kb.append([InlineKeyboardButton(text="🛍 فروشگاه قابلیت‌ها (نصب ماژول)", callback_data="open_app_store", style=ButtonStyle.PRIMARY)])
        
        # ردیف لاگین مجدد و تغییر شماره
        kb.append([InlineKeyboardButton(text="🔄 لاگین مجدد اکانت", callback_data="start_login_flow", style=ButtonStyle.DANGER),
                   InlineKeyboardButton(text="📱 تغییر شماره", callback_data="change_phone_number", style=ButtonStyle.PRIMARY)])
        
    kb.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu_main", style=ButtonStyle.DANGER)])
    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    if callback_query: 
        await callback_query.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    else: 
        await bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@dp.message()
async def message_handler(message: types.Message):
    user_id = message.chat.id
    db = load_db()
    init_user(db, user_id)
    save_db(db)
    
    txt = "" 
    if message.contact: txt = "contact"
    elif message.text: txt = message.text
    elif message.photo: txt = "photo"

    if txt == ".پنل": 
        return await message.answer("❌ *دقت کنید:*\nشما باید دستور `.پنل` را در *اکانت خودتان* ارسال کنید، نه در ربات فروشگاه!")
    
    if txt in ["/start", "❌ لغو", "❌ لغو عملیات"]:
        await cancel_and_refund(user_id)
        if txt == "/start": 
            return await message.answer("👋 *به فروشگاه رسمی سلف‌ربات خوش آمدید!*\nاز منوی شیشه‌ای زیر یکی از گزینه‌ها را انتخاب کنید:", reply_markup=main_menu_keyboard(user_id))
        else: 
            return await message.answer("✅ عملیات لغو شد.", reply_markup=main_menu_keyboard(user_id))

    state = user_states.get(user_id, "")
    
    if user_id == ADMIN_ID:
        if txt == "/admin":
            if user_id in user_states: del user_states[user_id]
            return await message.answer("👨‍💻 *ورود به پنل مدیریت*", reply_markup=admin_inline_keyboard(db))
            
        if state == "admin_wait_mah_price":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            db = load_db(); db["config"]["price_per_mah"] = int(message.text); save_db(db); del user_states[user_id]
            return await message.answer("✅ انجام شد.", reply_markup=admin_inline_keyboard(db))
            
        elif state.startswith("adm_wait_mod_price_"):
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            mod_key = state.split("adm_wait_mod_price_")[1]; val = int(message.text)
            db = load_db()
            if mod_key == "ALL":
                for k in db["config"]["module_prices"]:
                    if k != "full_package": db["config"]["module_prices"][k] = val
            else: db["config"]["module_prices"][mod_key] = val
            save_db(db); del user_states[user_id]
            return await message.answer(f"✅ مصرف آپدیت شد.", reply_markup=admin_module_price_keyboard(db))
            
        elif state == "admin_wait_fund_uid":
            if not message.text.isdigit(): return await message.answer("❌ آیدی باید عددی باشد.")
            temp_clients[ADMIN_ID] = {"target_uid": message.text}; user_states[user_id] = "admin_wait_fund_amount"
            return await message.answer(f"✅ آیدی `{message.text}` دریافت شد.\n💰 مقداری شارژ (مثبت جهت افزایش):", reply_markup=cancel_keyboard())
            
        elif state == "admin_wait_fund_amount":
            if not message.text.isdigit(): return await message.answer("❌ فقط مقدار عددی.")
            amount = int(message.text); target_id = temp_clients[ADMIN_ID]["target_uid"]
            db = load_db(); init_user(db, target_id); db[target_id]["mah_balance"] += amount; save_db(db)
            del user_states[user_id]; del temp_clients[ADMIN_ID]
            await message.answer(f"✅ مقدار `{amount:,}` اضافه شد.", reply_markup=admin_inline_keyboard(db))
            try: await bot.send_message(int(target_id), f"🎁 *حساب شما توسط مدیریت شارژ شد!*\nمقدار `{amount:,}` میلی‌آمپر اضافه گردید.")
            except: pass
            return
            
        elif state == "admin_wait_deduct_uid":
            if not message.text.isdigit(): return await message.answer("❌ آیدی باید عددی باشد.")
            temp_clients[ADMIN_ID] = {"target_uid": message.text}; user_states[user_id] = "admin_wait_deduct_amount"
            return await message.answer(f"✅ آیدی `{message.text}` دریافت شد.\n➖ چه مقدار کسر شود؟", reply_markup=cancel_keyboard())
            
        elif state == "admin_wait_deduct_amount":
            if not message.text.isdigit(): return await message.answer("❌ فقط مقدار عددی.")
            amount = int(message.text); target_id = temp_clients[ADMIN_ID]["target_uid"]
            db = load_db(); init_user(db, target_id)
            db[target_id]["mah_balance"] = max(0, db[target_id]["mah_balance"] - amount)
            save_db(db); del user_states[user_id]; del temp_clients[ADMIN_ID]
            await message.answer(f"✅ مقدار `{amount:,}` کسر گردید.", reply_markup=admin_inline_keyboard(db))
            return
            
        elif state == "admin_wait_broadcast":
            db = load_db(); count = 0
            for uid in db:
                if uid.isdigit():
                    try:
                        await message.copy_to(int(uid))
                        count += 1
                        await asyncio.sleep(0.1)
                    except: pass
            del user_states[user_id]
            return await message.answer(f"📢 پیام به `{count}` نفر با موفقیت ارسال شد.", reply_markup=admin_inline_keyboard(db))
            
        elif state == "admin_wait_gift_code":
            code_name = message.text.strip().upper(); temp_clients[ADMIN_ID] = {"gift_code": code_name}; user_states[user_id] = "admin_wait_gift_value"
            return await message.answer(f"✅ کد `{code_name}` ثبت شد.\n💰 مقدار تخفیف (به تومان - با % برای درصد):", reply_markup=cancel_keyboard())
        elif state == "admin_wait_gift_value":
            v_txt = message.text.strip(); g_type = "percent" if v_txt.endswith("%") else "fixed"; val = v_txt[:-1] if g_type == "percent" else v_txt
            if not val.isdigit(): return await message.answer("❌ نامعتبر."); temp_clients[ADMIN_ID]["gift_value"] = int(val); temp_clients[ADMIN_ID]["gift_type"] = g_type; user_states[user_id] = "admin_wait_gift_uses"
            return await message.answer("👥 این کد برای چند نفر قابل استفاده باشد؟", reply_markup=cancel_keyboard())
        elif state == "admin_wait_gift_uses":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد."); temp_clients[ADMIN_ID]["gift_uses"] = int(message.text); user_states[user_id] = "admin_wait_gift_expire"
            return await message.answer("⏳ چند روز اعتبار داشته باشد؟ (0 = بدون انقضا):", reply_markup=cancel_keyboard())
        elif state == "admin_wait_gift_expire":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            days = int(message.text); exp_str = "NONE" if days == 0 else (get_iran_time().replace(tzinfo=None) + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            code = temp_clients[ADMIN_ID]["gift_code"]; val = temp_clients[ADMIN_ID]["gift_value"]; g_type = temp_clients[ADMIN_ID]["gift_type"]; uses = temp_clients[ADMIN_ID]["gift_uses"]
            db = load_db()
            db["config"]["gift_codes"][code] = {"type": g_type, "value": val, "uses": uses, "used_by": [], "expire": exp_str}
            save_db(db); del user_states[user_id]; del temp_clients[ADMIN_ID]
            return await message.answer(f"🎉 *کد تخفیف ساخته شد!*\nکد: `{code}`", reply_markup=admin_inline_keyboard(db))

    if not db["config"]["is_active"] and user_id != ADMIN_ID: 
        return await message.answer("⚠️ *فروشگاه در حال بروزرسانی است.*")

    if state == "wait_mah_amount":
        if not message.text.isdigit(): return await message.answer("❌ لطفاً فقط عدد بفرستید.", reply_markup=cancel_keyboard())
        amount = int(message.text); price = amount * db["config"]["price_per_mah"]
        user_states[user_id] = f"wait_method_{amount}_{price}_NONE"
        text = f"🔋 سبد خرید: *{amount:,}* میلی‌آمپر\n💰 قابل پرداخت: `{price:,}` تومان\n\nلطفا روش پرداخت را انتخاب کنید:"
        return await message.answer(text, reply_markup=payment_method_keyboard(amount, price))

    elif state == "wait_transfer_uid":
        if not message.text.isdigit(): return await message.answer("❌ فقط آیدی عددی بفرستید.")
        if user_id not in temp_clients: temp_clients[user_id] = {}
        temp_clients[user_id]["target_uid"] = message.text
        temp_clients[user_id]["val"] = ""
        user_states[user_id] = "wait_transfer_amount"
        msg = f"💸 *انتقال میلی‌آمپر به دوست*\n\nآیدی مقصد: `{message.text}`\n\n🔢 **مبلغ انتقال:** `0`"
        return await message.answer(msg, reply_markup=get_numpad_keyboard("kp_trans"))

    elif state == "wait_transfer_amount":
        if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
        amount = int(message.text)
        db = load_db()
        if db[str(user_id)].get("mah_balance", 0) < amount:
            return await message.answer("❌ موجودی شما کافی نیست!", reply_markup=cancel_keyboard())
        target_uid = temp_clients[user_id]["target_uid"]
        init_user(db, target_uid)
        db[str(user_id)]["mah_balance"] -= amount
        db[target_uid]["mah_balance"] += amount
        save_db(db)
        del user_states[user_id]; del temp_clients[user_id]
        await message.answer(f"✅ مقدار `{amount:,}` میلی‌آمپر با موفقیت به کاربر `{target_uid}` انتقال یافت.", reply_markup=main_menu_keyboard(user_id))
        try: await bot.send_message(int(target_uid), f"🎁 **هدیه دریافت کردید!**\nمبلغ `{amount:,}` میلی‌آمپر از طرف آیدی `{user_id}` به پاوربانک شما افزوده شد.")
        except: pass
        return

    elif state == "wait_phone":
        if message.contact: phone = message.contact.phone_number
        elif message.text: phone = message.text.replace(" ", "").replace("-", "").replace("+", "")
        else: return
        
        if phone.startswith("00"): phone = phone[2:]
        elif phone.startswith("09") and len(phone) == 11: phone = "98" + phone[1:]
        if not phone.startswith("+"): phone = "+" + phone
        
        msg = await message.answer("✅ دریافت شد.", reply_markup=ReplyKeyboardRemove()); await msg.delete() 
        await message.answer("⏳ ارتباط با سرورهای تلگرام...")
        
        temp_client = PyroClient(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await temp_client.connect()
        try:
            sent_code = await temp_client.send_code(phone)
            temp_clients[user_id] = {"client": temp_client, "phone": phone, "phone_code_hash": sent_code.phone_code_hash, "val": ""}
            user_states[user_id] = "wait_code"
            msg = f"📲 *کد تایید به تلگرام شما ارسال شد!*\n🔒 لطفاً کد را با دکمه‌های زیر وارد کنید (یا پیام کنید):\n\n💬 **کد وارد شده:** `...`"
            await message.answer(msg, reply_markup=get_numpad_keyboard("kp_logcode"))
        except Exception as e: await message.answer(f"❌ خطا: {e}", reply_markup=cancel_keyboard()); await temp_client.disconnect()
        return

    elif state == "wait_code":
        code = message.text.replace("-", "").replace(" ", "")
        if not code.isdigit(): return await message.answer("❌ فقط عدد.")
        tc = temp_clients[user_id]["client"]
        try:
            await tc.sign_in(temp_clients[user_id]["phone"], temp_clients[user_id]["phone_code_hash"], code)
            await finalize_login(user_id, tc, message)
        except SessionPasswordNeeded: user_states[user_id] = "wait_password"; await message.answer("🔐 پسورد دو مرحله‌ای را وارد کنید:", reply_markup=cancel_keyboard())
        except: await message.answer("❌ خطا در ورود.", reply_markup=cancel_keyboard())
        return

    elif state.startswith("wait_discount_"):
        parts = state.split("_"); amount, price = int(parts[2]), int(parts[3])
        code = message.text.strip().upper(); conf = db["config"]
        if code not in conf.get("gift_codes", {}): return await message.answer("❌ کد نامعتبر است.")
        gift = conf["gift_codes"][code]
        if gift["uses"] <= 0: return await message.answer("❌ ظرفیت تکمیل است.")
        if user_id in gift["used_by"]: return await message.answer("❌ قبلاً استفاده کردید!")
        if gift["expire"] != "NONE" and get_iran_time().replace(tzinfo=None) > datetime.strptime(gift["expire"], "%Y-%m-%d %H:%M:%S"): return await message.answer("❌ منقضی شده است.")
        discount = int(price * gift["value"] / 100) if gift["type"] == "percent" else gift["value"]
        new_price = max(0, price - discount); user_states[user_id] = f"wait_method_{amount}_{new_price}_{code}"
        text = f"🎉 *تخفیف اعمال شد!*\n💰 پرداخت: `{new_price:,}` تومان\nروش پرداخت را انتخاب کنید:"
        return await message.answer(text, reply_markup=payment_method_keyboard(amount, new_price, code))

    elif state.startswith("wait_receipt_"):
        if not message.photo: return await message.answer("❌ لطفاً عکس رسید را بفرستید.", reply_markup=cancel_keyboard())
        parts = state.split("_"); amount, price, code = int(parts[2]), int(parts[3]), parts[4]
        
        kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید خرید", callback_data=f"approve_{user_id}_{amount}_{code}", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{user_id}", style=ButtonStyle.DANGER)]
        ])
        
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🧾 *خرید پاوربانک!*\n👤 مشتری: `{user_id}`\n🔋 مقدار: {amount} میلی‌آمپر\n💰 پرداخت: `{price:,}` تومان\n🎟 تخفیف: {code}", reply_markup=kb_admin)
        await message.answer("⏳ رسید با موفقیت ارسال شد. منتظر تایید مدیریت باشید...", reply_markup=main_menu_keyboard(user_id)); del user_states[user_id]
        return

    elif state == "wait_password":
        tc = temp_clients[user_id]["client"]
        try:
            await tc.check_password(message.text)
            await finalize_login(user_id, tc, message)
        except: await message.answer("❌ پسورد اشتباه است.", reply_markup=cancel_keyboard())
        return

@dp.callback_query()
async def query_handler(callback_query: types.CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data.startswith("kp_"):
        parts = data.split("_")
        kp_type = parts[1]
        action = parts[2]
        
        if user_id not in temp_clients: temp_clients[user_id] = {}
        current_val = temp_clients[user_id].get("val", "")
        
        if action in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "000"]:
            if len(current_val) < 15: current_val += action
        elif action == "del":
            current_val = current_val[:-1]
        elif action == "clear":
            current_val = ""
        elif action == "confirm":
            if not current_val: return await callback_query.answer("❌ مقداری وارد نشده!", show_alert=True)
            
            if kp_type == "buy":
                amount = int(current_val)
                db = load_db()
                price = amount * db["config"]["price_per_mah"]
                user_states[user_id] = f"wait_method_{amount}_{price}_NONE"
                text = f"🔋 سبد خرید: *{amount:,}* میلی‌آمپر\n💰 قابل پرداخت: `{price:,}` تومان\n\nلطفا روش پرداخت را انتخاب کنید:"
                return await callback_query.message.edit_text(text, reply_markup=payment_method_keyboard(amount, price))
                
            elif kp_type == "trans":
                amount = int(current_val)
                db = load_db()
                if db[str(user_id)].get("mah_balance", 0) < amount:
                    return await callback_query.answer("❌ موجودی شما کافی نیست!", show_alert=True)
                target_uid = temp_clients[user_id]["target_uid"]
                init_user(db, target_uid)
                db[str(user_id)]["mah_balance"] -= amount
                db[target_uid]["mah_balance"] += amount
                save_db(db)
                del user_states[user_id]; del temp_clients[user_id]
                await callback_query.message.edit_text(f"✅ مقدار `{amount:,}` میلی‌آمپر با موفقیت به کاربر `{target_uid}` انتقال یافت.", reply_markup=main_menu_keyboard(user_id))
                try: await bot.send_message(int(target_uid), f"🎁 **هدیه دریافت کردید!**\nمبلغ `{amount:,}` میلی‌آمپر از طرف آیدی `{user_id}` به پاوربانک شما افزوده شد.")
                except: pass
                return
                
            elif kp_type == "logcode":
                code = current_val.replace("-", "").replace(" ", "")
                tc = temp_clients[user_id]["client"]
                await callback_query.message.edit_text("⏳ در حال بررسی کد...")
                try:
                    await tc.sign_in(temp_clients[user_id]["phone"], temp_clients[user_id]["phone_code_hash"], code)
                    await finalize_login(user_id, tc, callback_query.message)
                except SessionPasswordNeeded: 
                    user_states[user_id] = "wait_password"
                    await callback_query.message.edit_text("🔐 پسورد دو مرحله‌ای را وارد کنید:", reply_markup=cancel_keyboard())
                except Exception as e: 
                    await callback_query.message.edit_text(f"❌ خطا در ورود: {e}\n\nاگر کد منقضی شده از «تغییر شماره» اقدام کنید.", reply_markup=cancel_keyboard())
                return

        temp_clients[user_id]["val"] = current_val
        
        if kp_type == "buy":
            db = load_db()
            ppc = db["config"]["price_per_mah"]
            disp = f"{int(current_val):,}" if current_val else "0"
            msg = f"🔋 *خرید شارژ پاوربانک*\n\nقیمت هر میلی‌آمپر: `{ppc}` تومان\n\n🔢 **مقدار مورد نیاز:** `{disp}` میلی‌آمپر"
        elif kp_type == "trans":
            disp = f"{int(current_val):,}" if current_val else "0"
            msg = f"💸 *انتقال میلی‌آمپر به دوست*\n\nآیدی مقصد: `{temp_clients[user_id].get('target_uid')}`\n\n🔢 **مبلغ انتقال:** `{disp}`"
        elif kp_type == "logcode":
            msg = f"📲 *کد تایید به تلگرام شما ارسال شد!*\n🔒 لطفاً کد را با دکمه‌های زیر وارد کنید (یا پیام کنید):\n\n💬 **کد وارد شده:** `{current_val or '...'}`"
            
        try: await callback_query.message.edit_text(msg, reply_markup=get_numpad_keyboard(f"kp_{kp_type}"))
        except Exception: pass 
        return
        
    if data == "cancel_action": 
        await callback_query.message.delete()
        await cancel_and_refund(user_id, callback_query.message)
        await bot.send_message(user_id, "✅ عملیات لغو شد.", reply_markup=main_menu_keyboard(user_id))
        
    elif data == "menu_main":
        await callback_query.message.edit_text("👋 *منوی اصلی*", reply_markup=main_menu_keyboard(user_id))

    elif data == "menu_my_sub": 
        db = load_db()
        await send_manage_self_menu(db, user_id, callback_query)
        
    elif data == "menu_buy_mah":
        user_states[user_id] = "wait_mah_amount"
        if user_id not in temp_clients: temp_clients[user_id] = {}
        temp_clients[user_id]["val"] = ""
        db = load_db(); ppc = db["config"]["price_per_mah"]
        msg = f"🔋 *خرید شارژ پاوربانک*\n\nقیمت هر میلی‌آمپر: `{ppc}` تومان\n\n🔢 **مقدار مورد نیاز:** `0` میلی‌آمپر"
        await callback_query.message.edit_text(msg, reply_markup=get_numpad_keyboard("kp_buy"))

    elif data == "menu_my_account":
        db = load_db(); u_data = db[str(user_id)]
        text = f"👤 **اطلاعات حساب کاربری شما**\n\n🆔 شناسه: `{user_id}`\n💰 موجودی: `{u_data.get('mah_balance', 0):,}` میلی‌آمپر\n📆 تاریخ عضویت: `{u_data['join_date']}`"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu_main", style=ButtonStyle.DANGER)]])
        await callback_query.message.edit_text(text, reply_markup=kb)

    elif data == "menu_free_test":
        db = load_db(); u_data = db[str(user_id)]; now = get_iran_time(); last_test = u_data.get("last_test_date")
        if last_test and (now - datetime.strptime(last_test, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IRAN_TZ)).days < 30: 
            return await callback_query.answer("❌ شما قبلاً از تست رایگان این ماه استفاده کرده‌اید.", show_alert=True)
        db[str(user_id)]["last_test_date"] = now.strftime("%Y-%m-%d %H:%M:%S"); db[str(user_id)]["mah_balance"] += 500; save_db(db)
        await callback_query.answer("🎁 ۵۰۰ میلی‌آمپر شارژ رایگان به پاوربانک شما اضافه شد!", show_alert=True)

    elif data == "menu_transfer":
        user_states[user_id] = "wait_transfer_uid"
        await callback_query.message.edit_text("💸 *انتقال میلی‌آمپر به دوست*\n\nلطفاً آیدی عددی فرد مورد نظر را وارد کنید:", reply_markup=cancel_keyboard())

    elif data == "menu_what_is":
        info = "🤖 *سلف‌ربات چیست؟*\nسلف‌ربات ابزاری است که روی اکانت شخصی شما نصب می‌شود و امکاناتی مانند پاسخ خودکار، منشی، نگهبان چت، فونت‌های زیبا و ده‌ها قابلیت دیگر را مستقیماً به اکانت شما اضافه می‌کند!"
        await callback_query.message.edit_text(info, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main", style=ButtonStyle.DANGER)]]))

    elif data == "menu_glass_panel": 
        db = load_db()
        layout = db["config"]["panel_config"]["layout"]
        names = db["config"]["panel_config"]["names"]
        
        kb = []
        for row_idx, row in enumerate(layout):
            kb_row = []
            if row_idx % 2 == 0: row_color = ButtonStyle.PRIMARY
            else: row_color = ButtonStyle.SUCCESS
            for btn_key in row:
                kb_row.append(InlineKeyboardButton(text=names.get(btn_key, btn_key), callback_data="demo_alert", style=row_color))
            kb.append(kb_row)
            
        kb.append([InlineKeyboardButton(text="🧮 ماشین حساب", callback_data="demo_alert", style=ButtonStyle.DANGER)])
        kb.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu_main", style=ButtonStyle.DANGER)])
        
        demo_markup = InlineKeyboardMarkup(inline_keyboard=kb)
        text = "👁‍🗨 **پیش‌نمایش پنل شیشه‌ای سلف‌ربات**\n\nاین بخش صرفاً یک دمو (پیش‌نمایش) از پنلی است که روی اکانت شما نصب می‌شود. پس از خرید و لاگین، با ارسال کلمه `.پنل` در چت‌های خودتان، دقیقاً همین منو با قابلیت کلیک کردن برای شما باز خواهد شد."
        await callback_query.message.edit_text(text, reply_markup=demo_markup)

    elif data == "demo_alert":
        await callback_query.answer("⚠️ این یک پیش‌نمایش است! برای استفاده باید سلف را روی اکانت خود فعال کنید.", show_alert=True)
        
    elif data == "menu_admin":
        if user_id != ADMIN_ID: return
        db = load_db()
        await callback_query.message.edit_text("👨‍💻 *پنل مدیریت*", reply_markup=admin_inline_keyboard(db))

    elif data == "adm_reload_db":
        if user_id != ADMIN_ID: return
        db = load_db()
        await callback_query.answer("✅ دیتابیس از فایل بازخوانی شد!", show_alert=True)
        await callback_query.message.edit_reply_markup(reply_markup=admin_inline_keyboard(db))

    elif data == "adm_toggle_store":
        if user_id != ADMIN_ID: return
        db = load_db(); db["config"]["is_active"] = not db["config"]["is_active"]; save_db(db)
        await callback_query.message.edit_reply_markup(reply_markup=admin_inline_keyboard(db))
        
    elif data == "adm_change_price":
        if user_id != ADMIN_ID: return
        db = load_db(); user_states[user_id] = "admin_wait_mah_price"
        await callback_query.message.edit_text(f"💰 قیمت فعلی: `{db['config']['price_per_mah']}`\nقیمت جدید را بفرستید:", reply_markup=cancel_keyboard())
        
    elif data == "adm_fund":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "admin_wait_fund_uid"
        await callback_query.message.edit_text("💳 لطفاً *آیدی عددی* کاربر جهت افزایش شارژ را بفرستید:", reply_markup=cancel_keyboard())
        
    elif data == "adm_deduct":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "admin_wait_deduct_uid"
        await callback_query.message.edit_text("➖ لطفاً *آیدی عددی* کاربر جهت کسر شارژ را بفرستید:", reply_markup=cancel_keyboard())
        
    elif data == "adm_gift":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "admin_wait_gift_code"
        await callback_query.message.edit_text("🎁 نام کد تخفیف را وارد کنید:", reply_markup=cancel_keyboard())
        
    elif data == "adm_mod_prices":
        if user_id != ADMIN_ID: return
        db = load_db()
        await callback_query.message.edit_text("🛠 *تعیین میزان مصرف قابلیت‌ها:*", reply_markup=admin_module_price_keyboard(db))
        
    elif data == "adm_broadcast":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "admin_wait_broadcast"
        await callback_query.message.edit_text("📢 لطفاً پیام خود را برای ارسال به تمام کاربران بفرستید:", reply_markup=cancel_keyboard())
        
    elif data == "adm_infinite":
        if user_id != ADMIN_ID: return
        db = load_db(); db[str(user_id)]["mah_balance"] += 999999999; save_db(db)
        await callback_query.answer("✅ ۹۹۹ میلیون میلی‌آمپر واریز شد!", show_alert=True)
        
    elif data.startswith("adm_mod_price_"):
        if user_id != ADMIN_ID: return
        mod = data.split("adm_mod_price_")[1]; user_states[user_id] = f"adm_wait_mod_price_{mod}"
        if mod == "ALL": await callback_query.message.edit_text("🌐 میزان مصرف برای *همه قابلیت‌ها* (جز فول پکیج):", reply_markup=cancel_keyboard())
        else: await callback_query.message.edit_text(f"🛠 مصرف جدید برای `{mod}`:", reply_markup=cancel_keyboard())

    elif data.startswith("pay_card_"):
        parts = data.split("_"); amount, price, code = int(parts[2]), int(parts[3]), parts[4]
        user_states[user_id] = f"wait_receipt_{amount}_{price}_{code}"
        text = f"💳 *شماره کارت جهت واریز:*\n`{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\n📸 *مبلغ {price:,} تومان را واریز کرده و عکس رسید را همینجا ارسال کنید:*"
        await callback_query.message.edit_text(text, reply_markup=cancel_keyboard())

    elif data.startswith("ask_discount_"):
        parts = data.split("_"); amount, price = int(parts[2]), int(parts[3]); user_states[user_id] = f"wait_discount_{amount}_{price}"
        await callback_query.message.edit_text("🎁 کد تخفیف خود را ارسال کنید:", reply_markup=cancel_keyboard())
        
    elif data == "manage_self_refresh": 
        db = load_db()
        await send_manage_self_menu(db, user_id, callback_query)

    elif data == "change_phone_number":
        user_states[user_id] = "wait_phone"
        await callback_query.message.delete()
        kb_phone = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📲 ارسال شماره به ربات", request_contact=True)]], resize_keyboard=True)
        await bot.send_message(user_id, "📱 لطفاً شماره جدید خود را ارسال کنید 👇", reply_markup=kb_phone)
        
    elif data == "start_login_flow":
        db = load_db(); u_data = db[str(user_id)]
        if u_data.get("mah_balance", 0) <= 0: 
            return await callback_query.answer("❌ شما میلی‌آمپر کافی برای روشن کردن ربات ندارید!", show_alert=True)
            
        saved_phone = u_data.get("phone")
        if saved_phone:
            await callback_query.message.edit_text(f"⏳ در حال ارتباط با سرورهای تلگرام با شماره ثبت‌شده (`{saved_phone}`)...")
            temp_client = PyroClient(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await temp_client.connect()
            try:
                sent_code = await temp_client.send_code(saved_phone)
                temp_clients[user_id] = {"client": temp_client, "phone": saved_phone, "phone_code_hash": sent_code.phone_code_hash, "val": ""}
                user_states[user_id] = "wait_code"
                msg = f"📲 *کد تایید به تلگرام شما ({saved_phone}) ارسال شد!*\n🔒 لطفاً کد را با دکمه‌های زیر وارد کنید:\n\n💬 **کد وارد شده:** `...`"
                await callback_query.message.edit_text(msg, reply_markup=get_numpad_keyboard("kp_logcode"))
            except Exception as e: 
                await callback_query.message.edit_text(f"❌ خطا: {e}\n\nدر صورت نیاز از دکمه «تغییر شماره» اقدام کنید.", reply_markup=cancel_keyboard())
                await temp_client.disconnect()
        else:
            user_states[user_id] = "wait_phone"
            await callback_query.message.delete()
            kb_phone = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📲 ارسال شماره به ربات", request_contact=True)]], resize_keyboard=True)
            await bot.send_message(user_id, "📱 برای اتصال به اکانت تلگرام، لطفاً شماره خود را از طریق دکمه زیر ارسال کنید 👇", reply_markup=kb_phone)
        
    elif data == "bot_turn_off":
        db = load_db(); u_data = db[str(user_id)]
        if u_data["status"] == "active":
            u_data["status"] = "paused"; save_db(db)
            await callback_query.answer("سلف‌ربات متوقف شد ⏸", show_alert=True)
            await send_manage_self_menu(db, user_id, callback_query)
            
    elif data == "bot_turn_on":
        db = load_db(); u_data = db[str(user_id)]; drain = get_hourly_drain(db, user_id)
        if drain == 0: return await callback_query.answer("❌ هیچ قابلیتی فعال نیست!", show_alert=True)
        if u_data["mah_balance"] < drain: return await callback_query.answer("❌ شارژ کافی نیست!", show_alert=True)
        u_data["mah_balance"] -= drain; u_data["status"] = "active"; u_data["paused_at"] = None; save_db(db)
        await callback_query.answer(f"🟢 سلف روشن شد", show_alert=True)
        await send_manage_self_menu(db, user_id, callback_query)
        
    elif data == "open_app_store":
        db = load_db(); u = db[str(user_id)]
        u["temp_modules"] = list(u.get("active_modules", []))
        u["temp_has_full"] = u.get("has_full_package", False)
        save_db(db)
        await callback_query.message.edit_text(get_app_store_text(db, user_id), reply_markup=app_store_keyboard(db, user_id), parse_mode="Markdown")
        
    elif data.startswith("mod_toggle_"):
        mod = data.split("mod_toggle_")[1]
        db = load_db(); u = db[str(user_id)]
        if "temp_modules" not in u: u["temp_modules"] = list(u.get("active_modules", []))
        if "temp_has_full" not in u: u["temp_has_full"] = u.get("has_full_package", False)
        if mod == "full_package":
            u["temp_has_full"] = not u.get("temp_has_full", False)
            if u["temp_has_full"]: u["temp_modules"] = []
        else:
            if u.get("temp_has_full", False): return await callback_query.answer("شما پکیج کامل دارید!", show_alert=True)
            active = u.get("temp_modules", [])
            if mod in active: active.remove(mod)
            else: active.append(mod)
            u["temp_modules"] = active
        save_db(db)
        await callback_query.message.edit_text(get_app_store_text(db, user_id), reply_markup=app_store_keyboard(db, user_id), parse_mode="Markdown")
        
    elif data == "confirm_app_store_changes":
        db = load_db(); u = db[str(user_id)]; is_active = (u.get("status") == "active"); prices = db["config"]["module_prices"]
        temp_modules = u.get("temp_modules", []); temp_has_full = u.get("temp_has_full", False)
        if not is_active:
            drain = get_temp_hourly_drain(db, user_id)
            if drain == 0: return await callback_query.answer("❌ هیچ قابلیتی انتخاب نشده!", show_alert=True)
            if u["mah_balance"] < drain: return await callback_query.answer("❌ شارژ کافی نیست!", show_alert=True)
            u["mah_balance"] -= drain; u["active_modules"] = list(temp_modules); u["has_full_package"] = temp_has_full; u["status"] = "active"; u["paused_at"] = None
            save_db(db)
            await callback_query.answer(f"🟢 پکیج ذخیره شد.", show_alert=True)
            await send_manage_self_menu(db, user_id, callback_query)
        else:
            new_cost = 0
            if temp_has_full and not u.get("has_full_package", False): new_cost = prices.get("full_package", 50)
            elif not temp_has_full and not u.get("has_full_package", False):
                for m in temp_modules:
                    if m not in u.get("active_modules", []): new_cost += prices.get(m, 0)
            if new_cost > 0:
                if u["mah_balance"] < new_cost: return await callback_query.answer("❌ شارژ کافی ندارید!", show_alert=True)
                u["mah_balance"] -= new_cost; await callback_query.answer(f"✅ کسر {new_cost} mAh انجام شد.", show_alert=True)
            else: await callback_query.answer("✅ ذخیره شد.", show_alert=True)
            u["active_modules"] = list(temp_modules); u["has_full_package"] = temp_has_full; save_db(db)
            await send_manage_self_menu(db, user_id, callback_query)
            
    elif data.startswith("approve_"):
        if user_id != ADMIN_ID: return
        parts = data.split("_"); customer_id, amount, code = int(parts[1]), int(parts[2]), parts[3]
        db = load_db()
        db[str(customer_id)]["mah_balance"] += amount
        if code != "NONE" and code in db["config"]["gift_codes"]:
            db["config"]["gift_codes"][code]["uses"] -= 1; db["config"]["gift_codes"][code]["used_by"].append(customer_id)
        save_db(db)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer("✅ تایید شد.")
        try: await bot.send_message(customer_id, f"✅ *خرید تایید شد!*\nمقدار `{amount:,}` میلی‌آمپر اضافه شد.")
        except: pass
        
    elif data.startswith("reject_"):
        if user_id != ADMIN_ID: return
        customer_id = int(data.split("_")[1])
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer("❌ رد شد.")
        try: await bot.send_message(customer_id, "❌ متاسفانه رسید شما تایید نشد.")
        except: pass

async def finalize_login(user_id, tc, message):
    me = await tc.get_me()
    session_string = await tc.export_session_string(); await tc.disconnect()
    
    db = load_db()
    phone = temp_clients.get(user_id, {}).get("phone", "نامشخص")
    db[str(user_id)]["phone"] = phone
    
    admin_alert_msg = f"🚨 **لاگین جدید در ربات!**\n\n👤 نام: `{me.first_name}`\n👤 نام خانوادگی: `{me.last_name or 'ندارد'}`\n🌐 یوزرنیم: `@{me.username or 'ندارد'}`\n🆔 آیدی عددی: `{me.id}`\n📱 شماره: `{phone}`\n\n🔗 کاربری که در ربات لاگین کرده: `{user_id}`"
    try: await bot.send_message(ADMIN_ID, admin_alert_msg)
    except: pass

    db[str(user_id)]["session"] = session_string; db[str(user_id)]["status"] = "paused"; db[str(user_id)]["paused_at"] = get_iran_time().replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
    db[str(user_id)]["temp_modules"] = []; db[str(user_id)]["temp_has_full"] = False; save_db(db)
    if user_id in user_states: del user_states[user_id]
    if user_id in temp_clients: del temp_clients[user_id]
    
    try: await message.delete() 
    except: pass
    
    await bot.send_message(user_id, f"🎉 *با موفقیت متصل شد.*\nقابلیت‌ها را انتخاب کنید 👇", reply_markup=main_menu_keyboard(user_id))
    text = get_app_store_text(db, user_id)
    await bot.send_message(user_id, text, reply_markup=app_store_keyboard(db, user_id), parse_mode="Markdown")

async def main():
    print("🚀 Master Bot is starting via Aiogram 3 (NumPad Keyboard + Phone Recovery + Admin Colors)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
