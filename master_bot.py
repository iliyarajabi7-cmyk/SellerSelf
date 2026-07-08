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
        if HF_TOKEN and REPO_ID:
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
            api.upload_file(path_or_fileobj=DB_FILE, path_in_repo=DB_FILE, repo_id=REPO_ID, repo_type="dataset", token=HF_TOKEN, commit_message="Update DB via MasterBot (Aiogram 3 Colored)")
    except Exception: pass

def save_db(data):
    try:
        tmp_file = DB_FILE + ".tmp"
        with open(tmp_file, "w") as f: json.dump(data, f, indent=4)
        os.replace(tmp_file, DB_FILE) 
        threading.Thread(target=upload_to_hf, daemon=True).start()
    except Exception as e: print("Save DB Error:", e)

users_db = load_db()

if "config" not in users_db:
    users_db["config"] = {
        "is_active": True, 
        "price_per_mah": 1, 
        "gift_codes": {},
        "module_prices": { 
            "full_package": 46, "p_textmode": 1, "p_clock": 3, "p_guard": 2, 
            "p_ping": 0, "p_logo": 1, "p_locks": 2, "p_action": 1, 
            "p_monshi": 1, "p_filter": 1, "p_autoreply": 1, "p_forcejoin": 2, 
            "p_dl": 2, "p_react": 1, "p_spam": 2, "p_mute": 1, 
            "p_info": 0, "p_tag": 2, "p_purge": 2, "p_ai": 3, 
            "p_translate": 2, "p_anim": 1, "p_cheat": 2, "p_tts": 1, 
            "p_music": 2, "p_tabchi": 3, "p_comment": 2, "p_crypto": 1,
            "p_readall": 1, "p_v2ray": 2, "p_qr": 1, "p_profile": 1
        },
        "menu_layout": [
            ["my_sub", "buy_mah"],
            ["my_account", "free_test"],
            ["support_menu"]
        ],
        "menu_names": {
            "my_sub": "🎛 مدیریت سلف من", "buy_mah": "🔋 خرید شارژ (میلی‌آمپر)",
            "my_account": "👤 حساب کاربری", "free_test": "🎁 سرویس تست (رایگان)", 
            "support_menu": "👨‍💻 پشتیبانی", "admin_panel": "🎛 پنل مدیریت"
        },
        "panel_config": {
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
    }
    save_db(users_db)

def init_user(user_id):
    uid = str(user_id)
    if uid == "config": return
    if uid not in users_db:
        users_db[uid] = {
            "status": "inactive", "mah_balance": 0, 
            "active_modules": [], "has_full_package": False,
            "join_date": jdatetime.datetime.fromgregorian(datetime=get_iran_time()).strftime("%Y/%m/%d - %H:%M"), 
            "last_test_date": None, "paused_at": None
        }
        save_db(users_db)

def get_hourly_drain(user_id):
    u = users_db[str(user_id)]
    if u.get("has_full_package", False): return users_db["config"]["module_prices"].get("full_package", 46)
    total = 0
    for m in u.get("active_modules", []): total += users_db["config"]["module_prices"].get(m, 0)
    return total

def get_temp_hourly_drain(user_id):
    u = users_db[str(user_id)]
    if u.get("temp_has_full", False): return users_db["config"]["module_prices"].get("full_package", 46)
    total = 0
    for m in u.get("temp_modules", []): total += users_db["config"]["module_prices"].get(m, 0)
    return total

def calculate_remaining_time(user_id):
    u = users_db[str(user_id)]
    mah = u.get("mah_balance", 0)
    drain = get_hourly_drain(user_id)
    if drain == 0: return "مصرف صفر (نامحدود)"
    hours = mah / drain
    days = int(hours // 24)
    rem_hours = int(hours % 24)
    if days > 0: return f"{days} روز و {rem_hours} ساعت"
    return f"{rem_hours} ساعت"

def get_app_store_text(user_id):
    u = users_db[str(user_id)]
    drain = get_temp_hourly_drain(user_id)
    ppc = users_db["config"]["price_per_mah"]
    cost_toman = drain * ppc
    active_modules = u.get("temp_modules", [])
    has_full = u.get("temp_has_full", False)
    prices = users_db["config"]["module_prices"]
    names = users_db["config"]["panel_config"]["names"]
    is_active = (u.get("status") == "active")

    text = "🛍 *فروشگاه قابلیت‌ها (تنظیم مصرف باتری)*\n\n"
    text += "💡 قابلیت‌های مورد نظر خود را انتخاب کنید و در پایان روی دکمه *✨ ثبت و تایید نهایی تغییرات* کلیک کنید.\n\n"
    if is_active:
        text += "🟢 *وضعیت فعلی سلف: روشن*\n⚠️ در صورت اضافه کردن قابلیت جدید، هزینه ۱ ساعت آن در لحظه کسر می‌شود.\n\n"
    else:
        text += "⏸ *وضعیت فعلی سلف: خاموش*\nآزادانه تیک‌ها را تغییر دهید. کسر شارژ پس از تایید نهایی انجام خواهد شد.\n\n"

    text += "📋 *لیست انتخاب‌های فعلی شما:*\n"
    if has_full: text += f"👑 پکیج فول VIP — مصرف: `{prices.get('full_package', 46)}` میلی‌آمپر\n"
    elif not active_modules: text += "➖ هیچ قابلیتی انتخاب نشده است.\n"
    else:
        for m in active_modules:
            cost = prices.get(m, 0)
            if cost > 0: text += f"✔️ {names.get(m, m)} — مصرف: `{cost}` میلی‌آمپر\n"
            
    text += f"\n📊 *وضعیت مجموع مصرف این پکیج:*\n⚡️ `{drain}` میلی‌آمپر (معادل `{cost_toman:,}` تومان در ساعت)\n"
    return text

def main_menu_keyboard(user_id):
    b_names = users_db["config"]["menu_names"]
    b_layout = users_db["config"]["menu_layout"]
    kb = []
    
    for row in b_layout:
        row_buttons = [KeyboardButton(text=b_names.get(key, key)) for key in row]
        if row_buttons: kb.append(row_buttons)
        
    if user_id == ADMIN_ID: 
        kb.append([KeyboardButton(text=b_names.get("admin_panel", "🎛 پنل مدیریت"))])
    kb.append([KeyboardButton(text="🎛 پنل امکانات شیشه‌ای")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def payment_method_keyboard(amount, price, code="NONE"):
    kb = []
    kb.append([InlineKeyboardButton(text="💳 پرداخت کارت به کارت", callback_data=f"pay_card_{amount}_{price}_{code}", style=ButtonStyle.SUCCESS)])
    if code == "NONE": 
        kb.append([InlineKeyboardButton(text="🎁 اعمال کد تخفیف", callback_data=f"ask_discount_{amount}_{price}", style=ButtonStyle.PRIMARY)])
    kb.append([InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_action", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_reply_keyboard():
    conf = users_db["config"]
    status_btn = "🔴 خاموش کردن فروشگاه" if conf["is_active"] else "🟢 روشن کردن فروشگاه"
    kb = [
        [KeyboardButton(text=status_btn), KeyboardButton(text="💰 تغییر قیمت میلی‌آمپر")],
        [KeyboardButton(text="🛠 تعیین مصرف قابلیت‌ها"), KeyboardButton(text="🎁 ساخت کد تخفیف")],
        [KeyboardButton(text="💳 شارژ پاوربانک کاربر"), KeyboardButton(text="🎮 شخصی‌سازی منو")],
        [KeyboardButton(text="♾ فعال‌سازی بینهایت")],
        [KeyboardButton(text="🔙 خروج از پنل مدیریت")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def menu_customize_keyboard():
    kb = [
        [KeyboardButton(text="✏️ تغییر نام دکمه"), KeyboardButton(text="🔀 جابجایی دکمه‌ها")],
        [KeyboardButton(text="🗑 حذف دکمه"), KeyboardButton(text="➕ بازگردانی دکمه")],
        [KeyboardButton(text="🔙 بازگشت به تنظیمات")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def cancel_keyboard(admin=False): 
    if admin: 
        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ لغو")]], resize_keyboard=True)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ لغو عملیات", callback_data="cancel_action", style=ButtonStyle.DANGER)]
    ])

def app_store_keyboard(user_id):
    u = users_db[str(user_id)]
    active = u.get("temp_modules", [])
    has_full = u.get("temp_has_full", False)
    prices = users_db["config"]["module_prices"]
    layout = users_db["config"]["panel_config"]["layout"]
    names = users_db["config"]["panel_config"]["names"]
    
    kb = []
    
    fp_text = "✅ پکیج فول VIP" if has_full else f"❌ پکیج فول VIP ({prices.get('full_package', 46)} mAh)"
    fp_style = ButtonStyle.SUCCESS if has_full else ButtonStyle.DANGER
    kb.append([InlineKeyboardButton(text=fp_text, callback_data="mod_toggle_full_package", style=fp_style)])
    
    for row in layout:
        row_btns = []
        for key in row:
            if key in ["p_ping", "p_info"]: continue 
            is_on = key in active or has_full
            icon = "✅" if is_on else "❌"
            btn_style = ButtonStyle.SUCCESS if is_on else ButtonStyle.DANGER
            cost = prices.get(key, 0)
            row_btns.append(InlineKeyboardButton(text=f"{icon} {names.get(key, key)} ({cost})", callback_data=f"mod_toggle_{key}", style=btn_style))
        kb.append(row_btns)
        
    kb.append([InlineKeyboardButton(text="✨ ثبت و تایید نهایی تغییرات", callback_data="confirm_app_store_changes", style=ButtonStyle.PRIMARY)])
    kb.append([InlineKeyboardButton(text="🔙 انصراف و بازگشت", callback_data="manage_self_refresh", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_module_price_keyboard():
    prices = users_db["config"]["module_prices"]
    names = users_db["config"]["panel_config"]["names"]
    kb = []
    
    kb.append([InlineKeyboardButton(text="🌐 تغییر مصرف همه ماژول‌ها یکجا", callback_data="adm_mod_price_ALL", style=ButtonStyle.PRIMARY)])
    kb.append([InlineKeyboardButton(text=f"👑 پکیج فول ({prices.get('full_package', 0)})", callback_data="adm_mod_price_full_package", style=ButtonStyle.PRIMARY)])
    
    for row in users_db["config"]["panel_config"]["layout"]:
        row_btns = []
        for key in row:
            if key in ["p_ping", "p_info"]: continue
            cost = prices.get(key, 0)
            row_btns.append(InlineKeyboardButton(text=f"{names.get(key, key)} ({cost})", callback_data=f"adm_mod_price_{key}", style=ButtonStyle.PRIMARY))
        kb.append(row_btns)
        
    kb.append([InlineKeyboardButton(text="❌ بستن", callback_data="cancel_action", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_active_buttons():
    active = []
    for row in users_db["config"]["menu_layout"]:
        for k in row: active.append(k)
    return active

async def cancel_and_refund(user_id, message_obj=None):
    if user_id in temp_clients:
        try: await temp_clients[user_id]["client"].disconnect()
        except: pass
        del temp_clients[user_id]
    if user_id in user_states: del user_states[user_id]
    if message_obj:
        try: await message_obj.delete()
        except: pass

async def send_manage_self_menu(user_id, callback_query=None):
    u_data = users_db[str(user_id)]
    status = u_data.get("status", "inactive")
    mah = u_data.get("mah_balance", 0)
    drain = get_hourly_drain(user_id)
    rem_time = calculate_remaining_time(user_id)
    
    text = f"🎛 *پنل مدیریت سلف‌ربات شما*\n\n🔋 موجودی پاوربانک: `{mah:,}` میلی‌آمپر\n⚡️ مصرف فعلی: `{drain}` میلی‌آمپر در ساعت\n⏱ زمان تقریبی روشن ماندن: *{rem_time}*\n\n💡 *نکته:* برای ۱ ماه استفاده ۲۴ ساعته از پکیج فول، به *33,120 میلی‌آمپر* شارژ نیاز دارید.\n"
    
    kb = []
    if status == "inactive":
        text += "\n❌ وضعیت: *متصل نیست (نیاز به ورود)*"
        kb.append([InlineKeyboardButton(text="📲 روشن‌کردن و اتصال به اکانت تلگرام", callback_data="start_login_flow", style=ButtonStyle.PRIMARY)])
    else:
        if status == "paused":
            text += "\n⏸ وضعیت: *خاموش (Sleep Mode)*"
            kb.append([InlineKeyboardButton(text="🟢 روشن کردن سلف (با امکانات قبلی)", callback_data="bot_turn_on", style=ButtonStyle.SUCCESS)])
        else:
            text += "\n🟢 وضعیت: *فعال و در حال کار*"
            kb.append([InlineKeyboardButton(text="🔴 خاموش کردن موقت (توقف مصرف)", callback_data="bot_turn_off", style=ButtonStyle.DANGER)])
            
        kb.append([InlineKeyboardButton(text="🛍 فروشگاه قابلیت‌ها (نصب ماژول)", callback_data="open_app_store", style=ButtonStyle.PRIMARY)])
        kb.append([InlineKeyboardButton(text="🔄 لاگین مجدد اکانت", callback_data="start_login_flow", style=ButtonStyle.DANGER)])
        
    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    if callback_query: 
        await callback_query.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    else: 
        await bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@dp.message()
async def message_handler(message: types.Message):
    global users_db; users_db = load_db(); user_id = message.chat.id
    init_user(user_id)
    b_names = users_db["config"]["menu_names"]
    
    txt = "" 
    if message.contact: txt = "contact"
    elif message.text: txt = message.text
    elif message.photo: txt = "photo"

    if txt == ".پنل": 
        return await message.answer("❌ *دقت کنید:*\nشما باید دستور `.پنل` را در *اکانت خودتان* ارسال کنید، نه در ربات فروشگاه!")
    
    if txt in ["/start", "❌ لغو", "❌ لغو عملیات"]:
        await cancel_and_refund(user_id)
        if txt == "/start": 
            return await message.answer("👋 *به فروشگاه رسمی سلف‌ربات خوش آمدید!*", reply_markup=main_menu_keyboard(user_id))
        elif user_id == ADMIN_ID and txt == "❌ لغو": 
            return await message.answer("✅ عملیات لغو شد.", reply_markup=admin_reply_keyboard())
        else: 
            return await message.answer("✅ عملیات لغو شد.", reply_markup=main_menu_keyboard(user_id))

    state = user_states.get(user_id, "")

    if user_id == ADMIN_ID:
        if txt in [b_names.get("admin_panel", "🎛 پنل مدیریت"), "/admin"]:
            if user_id in user_states: del user_states[user_id]
            return await message.answer("👨‍💻 *ورود به پنل مدیریت کیبوردی ادمین*", reply_markup=admin_reply_keyboard())
        elif txt == "🔙 خروج از پنل مدیریت": return await message.answer("✅ خارج شدید.", reply_markup=main_menu_keyboard(user_id))
        elif txt == "🔙 بازگشت به تنظیمات": return await message.answer("👨‍💻 پنل ادمین:", reply_markup=admin_reply_keyboard())
        elif txt in ["🔴 خاموش کردن فروشگاه", "🟢 روشن کردن فروشگاه"]:
            users_db["config"]["is_active"] = not users_db["config"]["is_active"]; save_db(users_db)
            return await message.answer(f"✅ انجام شد.", reply_markup=admin_reply_keyboard())
        elif txt == "🎮 شخصی‌سازی منو": return await message.answer("🛠 *تنظیمات پیشرفته دکمه‌های فروشگاه*", reply_markup=menu_customize_keyboard())
        elif txt == "🗑 حذف دکمه":
            active = get_active_buttons(); user_states[user_id] = "admin_wait_btn_del"
            msg = "کدام دکمه را می‌خواهید حذف کنید؟\n\n" + "".join([f"{i+1}. {b_names.get(k, k)}\n" for i, k in enumerate(active)])
            return await message.answer(msg, reply_markup=cancel_keyboard(admin=True))
        elif txt == "➕ بازگردانی دکمه":
            active = get_active_buttons(); all_keys = list(b_names.keys()); all_keys.remove("admin_panel"); hidden = [k for k in all_keys if k not in active]
            if not hidden: return await message.answer("هیچ دکمه پنهانی وجود ندارد.")
            user_states[user_id] = "admin_wait_btn_add"; temp_clients[user_id] = {"hidden": hidden}
            msg = "کدام دکمه را برمی‌گردانید؟\n\n" + "".join([f"{i+1}. {b_names.get(k, k)}\n" for i, k in enumerate(hidden)])
            return await message.answer(msg, reply_markup=cancel_keyboard(admin=True))
        elif txt == "✏️ تغییر نام دکمه":
            active = get_active_buttons(); user_states[user_id] = "admin_wait_btn_ren_sel"; temp_clients[user_id] = {"active": active}
            msg = "نام کدام دکمه را تغییر می‌دهید؟\n\n" + "".join([f"{i+1}. {b_names.get(k, k)}\n" for i, k in enumerate(active)])
            return await message.answer(msg, reply_markup=cancel_keyboard(admin=True))
        elif txt == "🔀 جابجایی دکمه‌ها":
            active = get_active_buttons(); user_states[user_id] = "admin_wait_btn_swap"; temp_clients[user_id] = {"active": active}
            msg = "شماره دو دکمه را با خط تیره بفرستید:\n\n" + "".join([f"{i+1}. {b_names.get(k, k)}\n" for i, k in enumerate(active)])
            return await message.answer(msg, reply_markup=cancel_keyboard(admin=True))
        elif txt == "💰 تغییر قیمت میلی‌آمپر":
            user_states[user_id] = "admin_wait_mah_price"
            return await message.answer(f"💰 قیمت فعلی: `{users_db['config']['price_per_mah']}`\nقیمت جدید:", reply_markup=cancel_keyboard(admin=True))
        elif txt == "🛠 تعیین مصرف قابلیت‌ها": return await message.answer("🛠 *تعیین میزان مصرف باتری:*", reply_markup=admin_module_price_keyboard())
        elif txt == "💳 شارژ پاوربانک کاربر":
            user_states[user_id] = "admin_wait_fund_uid"
            return await message.answer("💳 لطفاً *آیدی عددی* کاربر را بفرستید:", reply_markup=cancel_keyboard(admin=True))
        elif txt == "🎁 ساخت کد تخفیف":
            user_states[user_id] = "admin_wait_gift_code"
            return await message.answer("🎁 *نام کد* را وارد کنید:", reply_markup=cancel_keyboard(admin=True))
        elif txt == "♾ فعال‌سازی بینهایت":
            users_db[str(user_id)]["mah_balance"] += 999999999; save_db(users_db)
            return await message.answer("✅ ۹۹۹ میلیون میلی‌آمپر واریز شد!", reply_markup=admin_reply_keyboard())

        if state == "admin_wait_mah_price":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            users_db["config"]["price_per_mah"] = int(message.text); save_db(users_db); del user_states[user_id]
            return await message.answer("✅ انجام شد.", reply_markup=admin_reply_keyboard())
        elif state.startswith("adm_wait_mod_price_"):
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            mod_key = state.split("adm_wait_mod_price_")[1]; val = int(message.text)
            if mod_key == "ALL":
                for k in users_db["config"]["module_prices"]:
                    if k != "full_package": users_db["config"]["module_prices"][k] = val
            else: users_db["config"]["module_prices"][mod_key] = val
            save_db(users_db); del user_states[user_id]; return await message.answer(f"✅ مصرف آپدیت شد.", reply_markup=admin_module_price_keyboard())
        elif state == "admin_wait_btn_del":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            idx = int(message.text) - 1; active = get_active_buttons()
            if idx < 0 or idx >= len(active): return await message.answer("❌ نامعتبر.")
            target_key = active[idx]
            for row in users_db["config"]["menu_layout"]:
                if target_key in row:
                    row.remove(target_key)
                    if not row: users_db["config"]["menu_layout"].remove(row)
                    break
            save_db(users_db); del user_states[user_id]; return await message.answer(f"✅ دکمه مخفی شد.", reply_markup=menu_customize_keyboard())
        elif state == "admin_wait_btn_add":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            hidden = temp_clients[user_id]["hidden"]; idx = int(message.text) - 1
            if idx < 0 or idx >= len(hidden): return await message.answer("❌ نامعتبر.")
            users_db["config"]["menu_layout"].append([hidden[idx]]); save_db(users_db); del user_states[user_id]; del temp_clients[user_id]
            return await message.answer("✅ دکمه اضافه شد.", reply_markup=menu_customize_keyboard())
        elif state == "admin_wait_btn_ren_sel":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            active = temp_clients[user_id]["active"]; idx = int(message.text) - 1
            if idx < 0 or idx >= len(active): return await message.answer("❌ نامعتبر.")
            temp_clients[user_id]["target_key"] = active[idx]; user_states[user_id] = "admin_wait_btn_ren_val"
            return await message.answer("✏️ نام جدید:", reply_markup=cancel_keyboard(admin=True))
        elif state == "admin_wait_btn_ren_val":
            target = temp_clients[user_id]["target_key"]; users_db["config"]["menu_names"][target] = message.text.strip(); save_db(users_db)
            del user_states[user_id]; del temp_clients[user_id]; return await message.answer("✅ نام دکمه تغییر یافت.", reply_markup=menu_customize_keyboard())
        elif state == "admin_wait_btn_swap":
            if "-" not in message.text: return await message.answer("❌ با خط تیره جدا کنید.")
            try: i1, i2 = map(int, message.text.split("-")); i1 -= 1; i2 -= 1
            except: return await message.answer("❌ نامعتبر.")
            layout = users_db["config"]["menu_layout"]; flat_coords = [(r, c) for r in range(len(layout)) for c in range(len(layout[r]))]
            if i1 < 0 or i1 >= len(flat_coords) or i2 < 0 or i2 >= len(flat_coords): return await message.answer("❌ نامعتبر.")
            r1, c1 = flat_coords[i1]; r2, c2 = flat_coords[i2]
            layout[r1][c1], layout[r2][c2] = layout[r2][c2], layout[r1][c1]; save_db(users_db)
            del user_states[user_id]; del temp_clients[user_id]; return await message.answer("✅ جای دکمه‌ها عوض شد.", reply_markup=menu_customize_keyboard())
        elif state == "admin_wait_fund_uid":
            if not message.text.isdigit(): return await message.answer("❌ آیدی باید عددی باشد.")
            temp_clients[ADMIN_ID] = {"target_fund_uid": message.text}; user_states[user_id] = "admin_wait_fund_amount"
            return await message.answer(f"✅ آیدی `{message.text}` دریافت شد.\n💰 مقداری شارژ:", reply_markup=cancel_keyboard(admin=True))
        elif state == "admin_wait_fund_amount":
            if not message.text.isdigit(): return await message.answer("❌ فقط مقدار عددی.")
            amount = int(message.text); target_id = temp_clients[ADMIN_ID]["target_fund_uid"]
            init_user(target_id); users_db[target_id]["mah_balance"] += amount; save_db(users_db)
            del user_states[user_id]; del temp_clients[ADMIN_ID]
            await message.answer(f"✅ مقدار `{amount:,}` اضافه شد.", reply_markup=admin_reply_keyboard())
            try: await bot.send_message(int(target_id), f"🎁 *حساب شما توسط مدیریت شارژ شد!*\nمقدار `{amount:,}` میلی‌آمپر اضافه گردید.")
            except: pass
            return
        elif state == "admin_wait_gift_code":
            code_name = message.text.strip().upper(); temp_clients[ADMIN_ID] = {"gift_code": code_name}; user_states[user_id] = "admin_wait_gift_value"
            return await message.answer(f"✅ کد `{code_name}` ثبت شد.\n💰 مقدار تخفیف (به تومان - با % برای درصد):", reply_markup=cancel_keyboard(admin=True))
        elif state == "admin_wait_gift_value":
            v_txt = message.text.strip(); g_type = "percent" if v_txt.endswith("%") else "fixed"; val = v_txt[:-1] if g_type == "percent" else v_txt
            if not val.isdigit(): return await message.answer("❌ نامعتبر."); temp_clients[ADMIN_ID]["gift_value"] = int(val); temp_clients[ADMIN_ID]["gift_type"] = g_type; user_states[user_id] = "admin_wait_gift_uses"
            return await message.answer("👥 این کد برای چند نفر قابل استفاده باشد؟", reply_markup=cancel_keyboard(admin=True))
        elif state == "admin_wait_gift_uses":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد."); temp_clients[ADMIN_ID]["gift_uses"] = int(message.text); user_states[user_id] = "admin_wait_gift_expire"
            return await message.answer("⏳ چند روز اعتبار داشته باشد؟ (0 = بدون انقضا):", reply_markup=cancel_keyboard(admin=True))
        elif state == "admin_wait_gift_expire":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            days = int(message.text); exp_str = "NONE" if days == 0 else (get_iran_time().replace(tzinfo=None) + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            code = temp_clients[ADMIN_ID]["gift_code"]; val = temp_clients[ADMIN_ID]["gift_value"]; g_type = temp_clients[ADMIN_ID]["gift_type"]; uses = temp_clients[ADMIN_ID]["gift_uses"]
            users_db["config"]["gift_codes"][code] = {"type": g_type, "value": val, "uses": uses, "used_by": [], "expire": exp_str}
            save_db(users_db); del user_states[user_id]; del temp_clients[ADMIN_ID]; return await message.answer(f"🎉 *کد تخفیف ساخته شد!*\nکد: `{code}`", reply_markup=admin_reply_keyboard())

    if not users_db["config"]["is_active"] and user_id != ADMIN_ID: return await message.answer("⚠️ *فروشگاه در حال بروزرسانی است.*")

    if txt == b_names.get("buy_mah", "🔋 خرید شارژ (میلی‌آمپر)"):
        user_states[user_id] = "wait_mah_amount"; ppc = users_db["config"]["price_per_mah"]
        msg = f"🔋 *خرید شارژ پاوربانک*\n\nقیمت هر میلی‌آمپر: `{ppc}` تومان\n\n🔢 *لطفاً مقدار میلی‌آمپر مورد نیاز را به عدد بفرستید:*"
        return await message.answer(msg, reply_markup=cancel_keyboard())

    elif txt == b_names.get("my_sub", "🎛 مدیریت سلف من"): return await send_manage_self_menu(user_id)
    elif txt == b_names.get("my_account", "👤 حساب کاربری"):
        u_data = users_db[str(user_id)]
        return await message.answer(f"👤 شناسه: `{user_id}`\n💰 موجودی: `{u_data.get('mah_balance', 0):,}` میلی‌آمپر\n📆 عضویت: `{u_data['join_date']}`")
    elif txt == "🎛 پنل امکانات شیشه‌ای": return await message.answer("🤖 برای باز کردن پنل شیشه‌ای امکانات، در اکانت خود بنویسید:\n👉 `.پنل`")
    elif txt == b_names.get("free_test", "🎁 سرویس تست (رایگان)"):
        u_data = users_db[str(user_id)]; now = get_iran_time(); last_test = u_data.get("last_test_date")
        if last_test and (now - datetime.strptime(last_test, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IRAN_TZ)).days < 30: return await message.answer("❌ شما قبلاً از تست این ماه استفاده کرده‌اید.")
        users_db[str(user_id)]["last_test_date"] = now.strftime("%Y-%m-%d %H:%M:%S"); users_db[str(user_id)]["mah_balance"] += 500; save_db(users_db)
        return await message.answer("🎁 *۵۰۰ میلی‌آمپر شارژ رایگان به پاوربانک شما اضافه شد!*")
    elif txt == b_names.get("support_menu", "👨‍💻 پشتیبانی"): return await message.answer(f"📞 ارتباط با پشتیبانی:\n{SUPPORT_ID}")

    if state == "wait_mah_amount":
        if not message.text.isdigit(): return await message.answer("❌ لطفاً عدد بفرستید.", reply_markup=cancel_keyboard())
        amount = int(message.text); price = amount * users_db["config"]["price_per_mah"]
        user_states[user_id] = f"wait_receipt_{amount}_{price}_NONE"
        text = f"🔋 خرید *{amount:,}* میلی‌آمپر\n💰 پرداخت: `{price:,}` تومان\n\n💳 شماره کارت:\n`{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\n📸 *عکس رسید را بفرستید:*"
        return await message.answer(text, reply_markup=payment_method_keyboard(amount, price))

    elif state.startswith("wait_discount_"):
        parts = state.split("_"); amount, price = int(parts[2]), int(parts[3])
        code = message.text.strip().upper(); conf = users_db["config"]
        if code not in conf.get("gift_codes", {}): return await message.answer("❌ کد نامعتبر است.")
        gift = conf["gift_codes"][code]
        if gift["uses"] <= 0: return await message.answer("❌ ظرفیت تکمیل است.")
        if user_id in gift["used_by"]: return await message.answer("❌ قبلاً استفاده کردید!")
        if gift["expire"] != "NONE" and get_iran_time().replace(tzinfo=None) > datetime.strptime(gift["expire"], "%Y-%m-%d %H:%M:%S"): return await message.answer("❌ منقضی شده است.")
        discount = int(price * gift["value"] / 100) if gift["type"] == "percent" else gift["value"]
        new_price = max(0, price - discount); user_states[user_id] = f"wait_receipt_{amount}_{new_price}_{code}"
        text = f"🎉 *تخفیف اعمال شد!*\n💰 پرداخت: `{new_price:,}` تومان\n💳 کارت: `{CARD_NUMBER}`\n📸 *عکس رسید را بفرستید:*"
        return await message.answer(text, reply_markup=cancel_keyboard())

    elif state.startswith("wait_receipt_"):
        if not message.photo: return await message.answer("❌ لطفاً عکس رسید را بفرستید.", reply_markup=cancel_keyboard())
        parts = state.split("_"); amount, price, code = int(parts[2]), int(parts[3]), parts[4]
        
        kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید خرید", callback_data=f"approve_{user_id}_{amount}_{code}", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{user_id}", style=ButtonStyle.DANGER)]
        ])
        
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🧾 *خرید پاوربانک!*\n👤 مشتری: `{user_id}`\n🔋 مقدار: {amount} میلی‌آمپر\n💰 پرداخت: `{price:,}` تومان\n🎟 تخفیف: {code}", reply_markup=kb_admin)
        await message.answer("⏳ رسید ارسال شد. منتظر تایید باشید...", reply_markup=main_menu_keyboard(user_id)); del user_states[user_id]
        return

    elif state == "wait_phone":
        if message.contact: phone = message.contact.phone_number
        elif message.text: phone = message.text.replace(" ", "").replace("-", "").replace("+", "")
        else: return
        
        if phone.startswith("00"): phone = phone[2:]
        elif phone.startswith("09") and len(phone) == 11: phone = "98" + phone[1:]
        if not phone.startswith("+"): phone = "+" + phone
        
        msg = await message.answer("✅ دریافت شد.", reply_markup=ReplyKeyboardRemove()); await msg.delete() 
        await message.answer("⏳ ارتباط با تلگرام...")
        
        temp_client = PyroClient(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await temp_client.connect()
        try:
            sent_code = await temp_client.send_code(phone)
            temp_clients[user_id] = {"client": temp_client, "phone": phone, "phone_code_hash": sent_code.phone_code_hash}
            user_states[user_id] = "wait_code"
            await message.answer("📲 *کد تایید به تلگرام شما ارسال شد!*\n🔒 لطفاً کد را وارد کنید.\n💬 *مثال:* `1-2-3-4-5`", reply_markup=cancel_keyboard())
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

    elif state == "wait_password":
        tc = temp_clients[user_id]["client"]
        try:
            await tc.check_password(message.text)
            await finalize_login(user_id, tc, message)
        except: await message.answer("❌ پسورد اشتباه است.", reply_markup=cancel_keyboard())
        return

@dp.callback_query()
async def query_handler(callback_query: types.CallbackQuery):
    global users_db; users_db = load_db(); data = callback_query.data; user_id = callback_query.from_user.id
    
    if data == "cancel_action": 
        await callback_query.message.delete()
        await cancel_and_refund(user_id, callback_query.message)
        
    elif data.startswith("ask_discount_"):
        parts = data.split("_"); amount, price = int(parts[2]), int(parts[3]); user_states[user_id] = f"wait_discount_{amount}_{price}"
        await callback_query.message.delete()
        await bot.send_message(user_id, "🎁 کد تخفیف را بفرستید:", reply_markup=cancel_keyboard())
        
    elif data == "manage_self_refresh": 
        await send_manage_self_menu(user_id, callback_query)
        
    elif data == "start_login_flow":
        u_data = users_db[str(user_id)]
        if u_data.get("mah_balance", 0) <= 0: 
            return await callback_query.answer("❌ شما میلی‌آمپر کافی برای روشن کردن ربات ندارید!", show_alert=True)
        user_states[user_id] = "wait_phone"
        await callback_query.message.delete()
        
        kb_phone = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📲 ارسال شماره", request_contact=True)]], resize_keyboard=True)
        await bot.send_message(user_id, "📱 برای اتصال، شماره خود را بفرستید 👇", reply_markup=kb_phone)
        
    elif data == "bot_turn_off":
        u_data = users_db[str(user_id)]
        if u_data["status"] == "active":
            u_data["status"] = "paused"; save_db(users_db)
            await callback_query.answer("سلف‌ربات متوقف شد ⏸", show_alert=True)
            await send_manage_self_menu(user_id, callback_query)
            
    elif data == "bot_turn_on":
        u_data = users_db[str(user_id)]; drain = get_hourly_drain(user_id)
        if drain == 0: return await callback_query.answer("❌ هیچ قابلیتی فعال نیست!", show_alert=True)
        if u_data["mah_balance"] < drain: return await callback_query.answer("❌ شارژ کافی نیست!", show_alert=True)
        u_data["mah_balance"] -= drain; u_data["status"] = "active"; u_data["paused_at"] = None; save_db(users_db)
        await callback_query.answer(f"🟢 سلف روشن شد", show_alert=True)
        await send_manage_self_menu(user_id, callback_query)
        
    elif data == "open_app_store":
        u = users_db[str(user_id)]
        u["temp_modules"] = list(u.get("active_modules", []))
        u["temp_has_full"] = u.get("has_full_package", False)
        save_db(users_db)
        await callback_query.message.edit_text(get_app_store_text(user_id), reply_markup=app_store_keyboard(user_id), parse_mode="Markdown")
        
    elif data.startswith("mod_toggle_"):
        mod = data.split("mod_toggle_")[1]; u = users_db[str(user_id)]
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
        save_db(users_db)
        await callback_query.message.edit_text(get_app_store_text(user_id), reply_markup=app_store_keyboard(user_id), parse_mode="Markdown")
        
    elif data == "confirm_app_store_changes":
        u = users_db[str(user_id)]; is_active = (u.get("status") == "active"); prices = users_db["config"]["module_prices"]
        temp_modules = u.get("temp_modules", []); temp_has_full = u.get("temp_has_full", False)
        if not is_active:
            drain = get_temp_hourly_drain(user_id)
            if drain == 0: return await callback_query.answer("❌ هیچ قابلیتی انتخاب نشده!", show_alert=True)
            if u["mah_balance"] < drain: return await callback_query.answer("❌ شارژ کافی نیست!", show_alert=True)
            u["mah_balance"] -= drain; u["active_modules"] = list(temp_modules); u["has_full_package"] = temp_has_full; u["status"] = "active"; u["paused_at"] = None
            save_db(users_db)
            await callback_query.answer(f"🟢 پکیج ذخیره شد.", show_alert=True)
            await send_manage_self_menu(user_id, callback_query)
        else:
            new_cost = 0
            if temp_has_full and not u.get("has_full_package", False): new_cost = prices.get("full_package", 46)
            elif not temp_has_full and not u.get("has_full_package", False):
                for m in temp_modules:
                    if m not in u.get("active_modules", []): new_cost += prices.get(m, 0)
            if new_cost > 0:
                if u["mah_balance"] < new_cost: return await callback_query.answer("❌ شارژ کافی ندارید!", show_alert=True)
                u["mah_balance"] -= new_cost; await callback_query.answer(f"✅ کسر {new_cost} mAh انجام شد.", show_alert=True)
            else: await callback_query.answer("✅ ذخیره شد.", show_alert=True)
            u["active_modules"] = list(temp_modules); u["has_full_package"] = temp_has_full; save_db(users_db)
            await send_manage_self_menu(user_id, callback_query)
            
    elif data.startswith("adm_mod_price_"):
        if user_id != ADMIN_ID: return
        mod = data.split("adm_mod_price_")[1]; user_states[user_id] = f"adm_wait_mod_price_{mod}"
        await callback_query.message.delete()
        if mod == "ALL": await bot.send_message(user_id, "🌐 میزان مصرف برای *همه قابلیت‌ها*:", reply_markup=cancel_keyboard(admin=True))
        else: await bot.send_message(user_id, f"🛠 مصرف برای `{mod}`:", reply_markup=cancel_keyboard(admin=True))
        
    elif data.startswith("approve_"):
        if user_id != ADMIN_ID: return
        parts = data.split("_"); customer_id, amount, code = int(parts[1]), int(parts[2]), parts[3]
        users_db[str(customer_id)]["mah_balance"] += amount
        if code != "NONE" and code in users_db["config"]["gift_codes"]:
            users_db["config"]["gift_codes"][code]["uses"] -= 1; users_db["config"]["gift_codes"][code]["used_by"].append(customer_id)
        save_db(users_db)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer("✅ تایید شد.")
        try: await bot.send_message(customer_id, f"✅ *خرید تایید شد!*\nمقدار `{amount:,}` میلی‌آمپر اضافه شد.")
        except: pass
        
    elif data.startswith("reject_"):
        if user_id != ADMIN_ID: return
        customer_id = int(data.split("_")[1])
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer("❌ رد شد.")
        try: await bot.send_message(customer_id, "❌ رسید تایید نشد.")
        except: pass

async def finalize_login(user_id, tc, message):
    session_string = await tc.export_session_string(); await tc.disconnect()
    users_db[str(user_id)]["session"] = session_string; users_db[str(user_id)]["status"] = "paused"; users_db[str(user_id)]["paused_at"] = get_iran_time().replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
    users_db[str(user_id)]["temp_modules"] = []; users_db[str(user_id)]["temp_has_full"] = False; save_db(users_db)
    if user_id in user_states: del user_states[user_id]
    if user_id in temp_clients: del temp_clients[user_id]
    await message.answer(f"🎉 *متصل شد.*\nقابلیت‌ها را انتخاب کنید 👇", reply_markup=main_menu_keyboard(user_id))
    text = get_app_store_text(user_id)
    await message.answer(text, reply_markup=app_store_keyboard(user_id), parse_mode="Markdown")

async def main():
    print("🚀 Master Bot is starting via Aiogram 3 with Colored Buttons...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
