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
ADMIN_ID = 2025464333 
SUPPORT_ID = "@Im_Iliiya" 
CHANNEL_ID = "https://t.me/Im_Iliiya"

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
if "config" not in _db: _db["config"] = {}
_db["config"]["is_active"] = _db["config"].get("is_active", True)
_db["config"]["price_per_mah"] = _db["config"].get("price_per_mah", 1)
_db["config"]["gift_codes"] = _db["config"].get("gift_codes", {})
_db["config"]["fjoin_active"] = _db["config"].get("fjoin_active", False)
_db["config"]["fjoin"] = _db["config"].get("fjoin", [])
_db["config"]["gateway"] = _db["config"].get("gateway", {"active": False, "merchant": ""})
if "reseller_market" not in _db: _db["reseller_market"] = {}

_db["config"]["module_prices"] = {
    "full_package": 50, "p_clock": 5, "p_guard": 3, "p_ai": 3, "p_tabchi": 3,
    "p_dl": 2, "p_music": 2, "p_v2ray": 2, "p_translate": 2, "p_forcejoin": 2,
    "p_locks": 2, "p_tag": 2, "p_purge": 2, "p_comment": 2, "p_cheat": 1,
    "p_action": 1, "p_textmode": 1, "p_monshi": 1, "p_filter": 1, "p_autoreply": 1,
    "p_react": 1, "p_spam": 1, "p_mute": 1, "p_tts": 1, "p_crypto": 1,
    "p_readall": 1, "p_qr": 1, "p_profile": 1, "p_logo": 1, "p_anim": 1,
    "p_schedule": 2, "p_screen": 1, "p_ping": 0, "p_info": 0
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
        ["p_comment", "p_crypto", "p_schedule", "p_screen"]
    ],
    "names": {
        "p_textmode": "حالت متن", "p_clock": "ساعت", "p_guard": "نگهبان چت", 
        "p_ping": "پینگ", "p_logo": "لوگو", "p_locks": "قفل‌ها", 
        "p_action": "اکشن", "p_monshi": "منشی", "p_filter": "فیلترکلمات", 
        "p_autoreply": "پاسخ‌خودکار", "p_forcejoin": "عضویت اجباری", 
        "p_dl": "دانلودر", "p_react": "ریکت", "p_spam": "اسپم", 
        "p_mute": "سکوت/آزادی", "p_info": "آیدی", "p_tag": "تگ", 
        "p_purge": "پاکسازی", "p_ai": "هوش مصنوعی", "p_translate": "ترجمه", 
        "p_anim": "انیمیشن", "p_cheat": "تقلب", "p_tts": "تبدیل به ویس", 
        "p_music": "سرچ آهنگ", "p_tabchi": "تبچی", "p_comment": "کامنت اول", 
        "p_crypto": "قیمت ارز", "p_readall": "سین‌زن همگانی", 
        "p_v2ray": "پروکسی و V2ray", "p_qr": "کیوآر کد", "p_profile": "مدیریت پروفایل",
        "p_schedule": "ارسال زمان‌دار", "p_screen": "اسکرین‌شات پیام"
    }
}
save_db(_db)

def init_user(db, user_id, message=None):
    uid = str(user_id)
    if uid == "config" or uid == "reseller_market": return
    if uid not in db:
        first_name = message.from_user.first_name if message else "کاربر"
        username = message.from_user.username if message else ""
        db[uid] = {
            "status": "inactive", "mah_balance": 0, 
            "active_modules": [], "has_full_package": False,
            "join_date": jdatetime.datetime.fromgregorian(datetime=get_iran_time()).strftime("%Y/%m/%d - %H:%M"), 
            "last_test_date": None, "paused_at": None, "phone": None,
            "first_name": first_name, "username": username,
            "is_reseller": False, "brand_name": "", "reseller_owner": None,
            "invited_by": None, "fjoin_passed": False
        }

async def check_fjoin_status(user_id, db):
    if not db["config"].get("fjoin_active", False) or not db["config"].get("fjoin"): return True, None
    kb = []
    all_joined = True
    for ch in db["config"]["fjoin"]:
        try:
            cid = ch["id"]
            if str(cid).startswith("-") and not str(cid).startswith("-100"): cid = int(f"-100{str(cid)[1:]}")
            elif str(cid).isdigit(): cid = int(f"-100{cid}")
            elif str(cid).startswith("@"): cid = str(cid)
            else: cid = int(cid)

            member = await bot.get_chat_member(cid, user_id)
            if member.status.value in ['left', 'kicked']: raise Exception
            kb.append([InlineKeyboardButton(text=f"✅ {ch['name']}", url=ch['link'])]) 
        except:
            kb.append([InlineKeyboardButton(text=f"❌ {ch['name']} (عضو نیستید)", url=ch['link'])])
            all_joined = False
    
    if not all_joined:
        kb.append([InlineKeyboardButton(text="🔄 بررسی مجدد عضویت", callback_data="check_fjoin_btn", style=ButtonStyle.PRIMARY)])
        return False, InlineKeyboardMarkup(inline_keyboard=kb)
    return True, None

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

def main_menu_keyboard(db, user_id):
    u = db[str(user_id)]
    is_reseller = u.get("is_reseller", False)
    brand = u.get("brand_name", "")
    
    # محاسبه تعداد دعوت شده‌های موفق
    invites_count = len([x for x in db if x != "config" and x != "reseller_market" and x.isdigit() and db[x].get('invited_by') == user_id and db[x].get('fjoin_passed')])
    
    kb = [
        [InlineKeyboardButton(text="🎛 پنل مدیریت سلف‌ربات", callback_data="menu_my_sub", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="👤 پروفایل من", callback_data="menu_my_account", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="🎁 دریافت تست رایگان", callback_data="menu_free_test", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="🔋 فروشگاه شارژ و باتری", callback_data="menu_buy_mah", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="💸 انتقال شارژ", callback_data="menu_transfer", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="👁‍🗨 پیش‌نمایش پنل", callback_data="menu_glass_panel", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="👨‍💻 ارتباط با پشتیبانی", url=f"https://t.me/{SUPPORT_ID.replace('@', '')}", style=ButtonStyle.DANGER),
         InlineKeyboardButton(text="📢 کانال رسمی", url=CHANNEL_ID, style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text=f"🔗 شارژ رایگان (دعوت: {invites_count})", callback_data="menu_referral", style=ButtonStyle.SUCCESS)]
    ]
    
    if is_reseller:
        kb.append([InlineKeyboardButton(text=f"🏢 پنل نمایندگی ({brand or 'بدون نام'})", callback_data="menu_reseller_panel", style=ButtonStyle.PRIMARY)])
    else:
        kb.append([InlineKeyboardButton(text="🤝 درخواست نمایندگی", callback_data="menu_req_reseller", style=ButtonStyle.PRIMARY)])
        
    kb.append([InlineKeyboardButton(text="❓ سلف چیست؟", callback_data="menu_what_is", style=ButtonStyle.DANGER)])
    
    if user_id == ADMIN_ID: 
        kb.append([InlineKeyboardButton(text="👨‍💻 ورود به پنل مدیریت (ادمین)", callback_data="menu_admin", style=ButtonStyle.PRIMARY)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_inline_keyboard(db):
    status_btn = "🔴 خاموش کردن فروشگاه" if db["config"]["is_active"] else "🟢 روشن کردن فروشگاه"
    fjoin_btn = "🔴 خاموش کردن قفل کانال" if db["config"].get("fjoin_active") else "🟢 روشن کردن قفل کانال"
    gateway_btn = "🔴 خاموش کردن درگاه" if db["config"]["gateway"]["active"] else "🟢 روشن کردن درگاه"
    
    kb = [
        [InlineKeyboardButton(text=status_btn, callback_data="adm_toggle_store", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="💰 تغییر قیمت پایه", callback_data="adm_change_price", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="💳 شارژ کاربر", callback_data="adm_fund", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="➖ کسر شارژ", callback_data="adm_deduct", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="🎁 ساخت کد تخفیف", callback_data="adm_gift", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="🛠 تعیین مصرف قابلیت‌ها", callback_data="adm_mod_prices", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="📢 ارسال همگانی", callback_data="adm_broadcast", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="♾ فعال‌سازی بینهایت", callback_data="adm_infinite", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text=fjoin_btn, callback_data="adm_toggle_fjoin", style=ButtonStyle.PRIMARY), 
         InlineKeyboardButton(text="➕ افزودن کانال اجباری", callback_data="adm_add_fjoin", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="👥 مدیریت کاربران", callback_data="adm_users_list_page_0", style=ButtonStyle.SUCCESS),
         InlineKeyboardButton(text="🤝 مدیریت نمایندگان", callback_data="adm_resellers_list_page_0", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text=gateway_btn, callback_data="adm_toggle_gateway", style=ButtonStyle.PRIMARY),
         InlineKeyboardButton(text="تنظیم درگاه پرداخت", callback_data="adm_set_gateway", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🔄 بازخوانی دیتابیس", callback_data="adm_reload_db", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="🔙 بازگشت به منوی کاربری", callback_data="menu_main", style=ButtonStyle.DANGER)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def generate_4col_users_keyboard(db, users, page, prefix, extra_btns=None):
    items_per_page = 7
    total_pages = max(1, (len(users) + items_per_page - 1) // items_per_page)
    page = min(page, total_pages - 1) if total_pages > 0 else 0
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_users = users[start_idx:end_idx]
    
    kb = []
    # هدر جدول (بدون استایل = خاکستری/پیش‌فرض)
    kb.append([
        InlineKeyboardButton(text="📌 وضعیت", callback_data="ignore"),
        InlineKeyboardButton(text="🔋 میلی آمپر", callback_data="ignore"),
        InlineKeyboardButton(text="👤 اسم", callback_data="ignore"),
        InlineKeyboardButton(text="🆔 شناسه", callback_data="ignore")
    ])
    for u in page_users:
        ud = db[u]
        status = "🟢" if ud.get("status") == "active" else "🔴"
        balance = f"{ud.get('mah_balance', 0):,}"
        name = ud.get("first_name", "")[:8]
        if not name: name = "بدون‌نام"
        uid_short = u[:5] + ".." if len(u) > 5 else u
        
        kb.append([
            InlineKeyboardButton(text=status, callback_data=f"{prefix}_info_{u}", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=balance, callback_data=f"{prefix}_info_{u}", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=name, callback_data=f"{prefix}_info_{u}", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=uid_short, callback_data=f"{prefix}_info_{u}", style=ButtonStyle.PRIMARY)
        ])
        
    nav_btns = []
    if page > 0: nav_btns.append(InlineKeyboardButton(text="⬅️ قبلی", callback_data=f"{prefix}_page_{page-1}", style=ButtonStyle.SUCCESS))
    nav_btns.append(InlineKeyboardButton(text=f"صفحه {page+1}/{total_pages}", callback_data="ignore"))
    if page < total_pages - 1: nav_btns.append(InlineKeyboardButton(text="بعدی ➡️", callback_data=f"{prefix}_page_{page+1}", style=ButtonStyle.SUCCESS))
    if nav_btns: kb.append(nav_btns)
    
    if extra_btns:
        for b in extra_btns: kb.append(b)
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

def payment_method_keyboard(db, amount, price, code="NONE"):
    kb = []
    gw = db["config"].get("gateway", {})
    if gw.get("active") and gw.get("merchant"):
        kb.append([InlineKeyboardButton(text="🌐 پرداخت آنلاین (درگاه امن)", url=f"https://zarinpal.com/pg/StartPay/{gw['merchant']}?amount={price}", style=ButtonStyle.PRIMARY)])
        
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
                row_btns.append(InlineKeyboardButton(text=f"{names.get(key, key)} ({cost})", callback_data=f"mod_toggle_{key}")])
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
        kb.append([InlineKeyboardButton(text="🔄 لاگین مجدد اکانت", callback_data="start_login_flow", style=ButtonStyle.PRIMARY),
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
    init_user(db, user_id, message)
    save_db(db)
    
    txt = message.text or ""
    
    if txt in ["/start", "❌ لغو", "❌ لغو عملیات"] or txt.startswith("/start "):
        await cancel_and_refund(user_id)
        
        if txt.startswith("/start "):
            inviter = txt.split(" ")[1]
            if inviter.isdigit() and inviter != str(user_id):
                db[str(user_id)]["invited_by"] = int(inviter)
                save_db(db)
                
        fjoin_passed, fjoin_kb = await check_fjoin_status(user_id, db)
        if not fjoin_passed and user_id != ADMIN_ID:
            return await message.answer("⚠️ *دوست عزیز!*\nبرای استفاده از ربات، لطفاً ابتدا در کانال‌های زیر عضو شوید، سپس روی دکمه «بررسی مجدد» کلیک کنید:", reply_markup=fjoin_kb)
        else:
            inviter = db[str(user_id)].get("invited_by")
            if inviter and not db[str(user_id)].get("fjoin_passed"):
                db[str(user_id)]["fjoin_passed"] = True
                if str(inviter) in db:
                    db[str(inviter)]["mah_balance"] += 500
                    try: await bot.send_message(inviter, "🎁 شما `500` میلی‌آمپر هدیه بابت ورود زیرمجموعه جدید دریافت کردید!")
                    except: pass
                save_db(db)
                
        if txt.startswith("/start") or txt == "❌ لغو" or txt == "❌ لغو عملیات":
            return await message.answer("👋 *به فروشگاه نیترو سلف خوش آمدید!*\nاز منوی شیشه‌ای زیر یکی از گزینه‌ها را انتخاب کنید:", reply_markup=main_menu_keyboard(db, user_id))

    fjoin_passed, fjoin_kb = await check_fjoin_status(user_id, db)
    if not fjoin_passed and user_id != ADMIN_ID:
        return await message.answer("⚠️ برای ادامه کار با ربات، عضویت در کانال‌های اسپانسر الزامی است:", reply_markup=fjoin_kb)

    if txt == ".پنل": 
        return await message.answer("❌ *دقت کنید:*\nشما باید دستور `.پنل` را در *اکانت خودتان* ارسال کنید، نه در ربات فروشگاه!")

    state = user_states.get(user_id, "")
    
    if user_id == ADMIN_ID:
        if txt == "/admin":
            if user_id in user_states: del user_states[user_id]
            return await message.answer("👨‍💻 *ورود به پنل مدیریت*", reply_markup=admin_inline_keyboard(db))
            
        if state == "admin_wait_mah_price":
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            db["config"]["price_per_mah"] = int(message.text); save_db(db); del user_states[user_id]
            return await message.answer("✅ انجام شد.", reply_markup=admin_inline_keyboard(db))
            
        elif state == "adm_wait_gateway_merchant":
            db["config"]["gateway"]["merchant"] = message.text; save_db(db); del user_states[user_id]
            return await message.answer("✅ مرچنت درگاه با موفقیت ذخیره شد.", reply_markup=admin_inline_keyboard(db))
            
        elif state.startswith("adm_wait_mod_price_"):
            if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
            mod_key = state.split("adm_wait_mod_price_")[1]; val = int(message.text)
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
            init_user(db, target_id); db[target_id]["mah_balance"] += amount; save_db(db)
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
            init_user(db, target_id); db[target_id]["mah_balance"] = max(0, db[target_id]["mah_balance"] - amount)
            save_db(db); del user_states[user_id]; del temp_clients[ADMIN_ID]
            await message.answer(f"✅ مقدار `{amount:,}` کسر گردید.", reply_markup=admin_inline_keyboard(db))
            return
            
        elif state == "admin_wait_broadcast":
            count = 0
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
            db["config"]["gift_codes"][code] = {"type": g_type, "value": val, "uses": uses, "used_by": [], "expire": exp_str}
            save_db(db); del user_states[user_id]; del temp_clients[ADMIN_ID]
            return await message.answer(f"🎉 *کد تخفیف ساخته شد!*\nکد: `{code}`", reply_markup=admin_inline_keyboard(db))

        elif state == "adm_wait_fjoin_id":
            temp_clients[ADMIN_ID] = {"fjoin_id": message.text}; user_states[user_id] = "adm_wait_fjoin_name"
            return await message.answer("📝 نام کانال (برای نمایش روی دکمه):", reply_markup=cancel_keyboard())
        elif state == "adm_wait_fjoin_name":
            temp_clients[ADMIN_ID]["fjoin_name"] = message.text; user_states[user_id] = "adm_wait_fjoin_link"
            return await message.answer("🔗 لینک جوین کانال (با https):", reply_markup=cancel_keyboard())
        elif state == "adm_wait_fjoin_link":
            db["config"]["fjoin"].append({"id": temp_clients[ADMIN_ID]["fjoin_id"], "name": temp_clients[ADMIN_ID]["fjoin_name"], "link": message.text})
            save_db(db); del user_states[user_id]; del temp_clients[ADMIN_ID]
            return await message.answer("✅ کانال اجباری افزوده شد.", reply_markup=admin_inline_keyboard(db))
            
        elif state == "adm_wait_search_user":
            del user_states[user_id]
            users = [u for u in db if u != "config" and u != "reseller_market" and u.isdigit()]
            sq = message.text.lower()
            users = [u for u in users if sq in db[u].get("first_name", "").lower() or sq in db[u].get("username", "").lower() or sq in str(db[u].get("phone", "")) or sq in u]
            return await message.answer("🔍 نتیجه جستجوی کاربران:", reply_markup=generate_4col_users_keyboard(db, users, 0, "adm_user", [[InlineKeyboardButton(text="🔍 سرچ مجدد", callback_data="adm_search_user", style=ButtonStyle.PRIMARY)], [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_admin", style=ButtonStyle.DANGER)]]))
            
        elif state == "adm_wait_search_reseller":
            del user_states[user_id]
            users = [u for u in db if u != "config" and u != "reseller_market" and u.isdigit() and db[u].get("is_reseller")]
            sq = message.text.lower()
            users = [u for u in users if sq in db[u].get("first_name", "").lower() or sq in db[u].get("username", "").lower() or sq in str(db[u].get("phone", "")) or sq in u]
            return await message.answer("🔍 نتیجه جستجوی نمایندگان:", reply_markup=generate_4col_users_keyboard(db, users, 0, "adm_reseller", [[InlineKeyboardButton(text="🔍 سرچ مجدد", callback_data="adm_search_reseller", style=ButtonStyle.PRIMARY)], [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_admin", style=ButtonStyle.DANGER)]]))

    if not db["config"]["is_active"] and user_id != ADMIN_ID: 
        return await message.answer("⚠️ *فروشگاه در حال بروزرسانی است.*")

    if state == "wait_mah_amount":
        if not message.text.isdigit(): return await message.answer("❌ لطفاً فقط عدد بفرستید.", reply_markup=cancel_keyboard())
        amount = int(message.text); price = amount * db["config"]["price_per_mah"]
        user_states[user_id] = f"wait_method_{amount}_{price}_NONE"
        text = f"🔋 سبد خرید: *{amount:,}* میلی‌آمپر\n💰 قابل پرداخت: `{price:,}` تومان\n\nلطفا روش پرداخت را انتخاب کنید:"
        return await message.answer(text, reply_markup=payment_method_keyboard(db, amount, price))

    elif state == "wait_transfer_uid":
        if not message.text.isdigit(): return await message.answer("❌ فقط آیدی عددی بفرستید.")
        if user_id not in temp_clients: temp_clients[user_id] = {}
        temp_clients[user_id]["target_uid"] = message.text; temp_clients[user_id]["val"] = ""; user_states[user_id] = "wait_transfer_amount"
        msg = f"💸 *انتقال میلی‌آمپر به دوست*\n\nآیدی مقصد: `{message.text}`\n\n🔢 **مبلغ انتقال:** `0`"
        return await message.answer(msg, reply_markup=get_numpad_keyboard("kp_trans"))

    elif state == "wait_transfer_amount":
        if not message.text.isdigit(): return await message.answer("❌ فقط عدد.")
        amount = int(message.text)
        if db[str(user_id)].get("mah_balance", 0) < amount: return await message.answer("❌ موجودی شما کافی نیست!", reply_markup=cancel_keyboard())
        target_uid = temp_clients[user_id]["target_uid"]
        init_user(db, target_uid); db[str(user_id)]["mah_balance"] -= amount; db[target_uid]["mah_balance"] += amount; save_db(db)
        del user_states[user_id]; del temp_clients[user_id]
        await message.answer(f"✅ مقدار `{amount:,}` میلی‌آمپر با موفقیت به کاربر `{target_uid}` انتقال یافت.", reply_markup=main_menu_keyboard(db, user_id))
        try: await bot.send_message(int(target_uid), f"🎁 **هدیه دریافت کردید!**\nمبلغ `{amount:,}` میلی‌آمپر از طرف آیدی `{user_id}` به پاوربانک شما افزوده شد.")
        except: pass
        return

    # سیستم جدید فروش نمایندگی
    elif state == "wait_resell_sell_price":
        if not message.text.isdigit(): return await message.answer("❌ فقط عدد بفرستید.")
        temp_clients[user_id]["sell_price"] = int(message.text)
        user_states[user_id] = "wait_resell_sell_card"
        return await message.answer("💳 شماره کارت خود جهت واریز وجه توسط خریدار را وارد کنید:", reply_markup=cancel_keyboard())
        
    elif state == "wait_resell_sell_card":
        temp_clients[user_id]["sell_card"] = message.text
        user_states[user_id] = "wait_resell_sell_name"
        return await message.answer("👤 نام و نام خانوادگی صاحب کارت را وارد کنید:", reply_markup=cancel_keyboard())
        
    elif state == "wait_resell_sell_name":
        temp_clients[user_id]["sell_name"] = message.text
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ بله، منتقل شوند", callback_data="r_sell_cust_yes", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="❌ خیر، فقط پنل", callback_data="r_sell_cust_no", style=ButtonStyle.DANGER)]
        ])
        return await message.answer("👥 آیا می‌خواهید مشتریان فعلی شما نیز به خریدار منتقل شوند؟", reply_markup=kb)

    elif state == "wait_resell_sell_uid":
        if not message.text.isdigit(): return await message.answer("❌ فقط آیدی عددی.")
        target = message.text
        price = temp_clients[user_id]["sell_price"]
        card = temp_clients[user_id]["sell_card"]
        name = temp_clients[user_id]["sell_name"]
        trans_c = temp_clients[user_id]["trans_c"]
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ قبول و ارسال رسید", callback_data=f"buy_resell_{user_id}", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="❌ رد پیشنهاد", callback_data=f"rej_resell_offer_{user_id}", style=ButtonStyle.DANGER)]
        ])
        text = f"🤝 **پیشنهاد خرید پنل نمایندگی!**\n\nفردی با آیدی `{user_id}` قصد فروش نمایندگی خود به شما را دارد.\n💰 **قیمت:** `{price:,}` تومان\n👥 انتقال مشتریان: {'بله' if trans_c else 'خیر'}\n\n💳 کارت: `{card}`\nبنام: {name}\n\nدر صورت تمایل مبلغ را واریز و روی دکمه ارسال رسید کلیک کنید."
        try:
            await bot.send_message(int(target), text, reply_markup=kb)
            await message.answer("✅ پیشنهاد شما با موفقیت برای خریدار ارسال شد. در صورت تایید و واریز، رسید برای شما ارسال خواهد شد.", reply_markup=main_menu_keyboard(db, user_id))
        except:
            await message.answer("❌ کاربر ربات را استارت نکرده است.", reply_markup=cancel_keyboard())
        del user_states[user_id]; del temp_clients[user_id]
        return

    elif state.startswith("wait_resell_buyer_receipt_"):
        seller_id = state.split("_")[4]
        if not message.photo: return await message.answer("❌ عکس رسید بفرستید.", reply_markup=cancel_keyboard())
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید رسید و انتقال", callback_data=f"transfer_resell_{user_id}", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="❌ رد رسید", callback_data=f"fail_resell_{user_id}", style=ButtonStyle.DANGER)]
        ])
        await bot.send_photo(int(seller_id), message.photo[-1].file_id, caption=f"🧾 **رسید خرید نمایندگی شما**\n\nخریدار: `{user_id}`\n\nدر صورت تایید، نمایندگی فوراً به ایشان منتقل می‌شود.", reply_markup=kb)
        await message.answer("⏳ رسید برای فروشنده ارسال شد. منتظر تایید باشید...", reply_markup=main_menu_keyboard(db, user_id))
        del user_states[user_id]
        return

    elif state == "wait_change_phone":
        if message.contact: 
            if message.contact.user_id != message.from_user.id:
                return await message.answer("❌ لطفاً فقط شماره اصلی خودتان را با استفاده از دکمه «ارسال شماره» بفرستید!")
            phone = message.contact.phone_number
        else: return await message.answer("❌ لطفاً فقط از دکمه پایین استفاده کنید.")
        if phone.startswith("00"): phone = phone[2:]
        elif phone.startswith("09") and len(phone) == 11: phone = "98" + phone[1:]
        if not phone.startswith("+"): phone = "+" + phone
        db[str(user_id)]["phone"] = phone; save_db(db)
        del user_states[user_id]
        msg = await message.answer("✅ دریافت شد.", reply_markup=ReplyKeyboardRemove()); await msg.delete() 
        return await message.answer(f"✅ شماره `{phone}` برای حساب شما ذخیره شد.", reply_markup=main_menu_keyboard(db, user_id))

    elif state in ["wait_phone", "resell_wait_phone"]:
        is_reseller_add = (state == "resell_wait_phone")
        if message.contact: 
            if message.contact.user_id != message.from_user.id and not is_reseller_add:
                return await message.answer("❌ لطفاً فقط شماره اصلی خودتان را با استفاده از دکمه پایین بفرستید!")
            phone = message.contact.phone_number
        else: return await message.answer("❌ لطفاً فقط از دکمه پایین استفاده کنید.")
        if phone.startswith("00"): phone = phone[2:]
        elif phone.startswith("09") and len(phone) == 11: phone = "98" + phone[1:]
        if not phone.startswith("+"): phone = "+" + phone
        
        msg = await message.answer("✅ دریافت شد.", reply_markup=ReplyKeyboardRemove()); await msg.delete() 
        await message.answer("⏳ ارتباط با سرورهای تلگرام...")
        
        brand = db[str(user_id)].get("brand_name", "nitroself") if is_reseller_add else "nitroself"
        if not brand: brand = "nitroself"
        temp_client = PyroClient(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True, app_version=brand, device_model=brand)
        await temp_client.connect()
        try:
            sent_code = await temp_client.send_code(phone)
            temp_clients[user_id] = {"client": temp_client, "phone": phone, "phone_code_hash": sent_code.phone_code_hash, "val": "", "is_resell_add": is_reseller_add}
            user_states[user_id] = "wait_code"
            msg = f"📲 *کد تایید به تلگرام ارسال شد!*\n🔒 لطفاً کد را با دکمه‌های زیر وارد کنید:\n\n💬 **کد وارد شده:** `...`"
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
        return await message.answer(text, reply_markup=payment_method_keyboard(db, amount, new_price, code))

    elif state == "wait_reseller_receipt":
        if not message.photo: return await message.answer("❌ لطفاً عکس رسید را بفرستید.", reply_markup=cancel_keyboard())
        kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید نمایندگی", callback_data=f"approve_resell_{user_id}", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="❌ رد درخواست", callback_data=f"reject_resell_{user_id}", style=ButtonStyle.DANGER)]
        ])
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🧾 *درخواست نمایندگی!*\n👤 متقاضی: `{user_id}`\n💰 پرداخت: `250,000` تومان", reply_markup=kb_admin)
        await message.answer("⏳ رسید با موفقیت ارسال شد. منتظر تایید مدیریت باشید...", reply_markup=main_menu_keyboard(db, user_id)); del user_states[user_id]
        return

    elif state == "wait_brand_name":
        db[str(user_id)]["brand_name"] = message.text.strip()
        save_db(db); del user_states[user_id]
        return await message.answer(f"✅ نام برند شما با موفقیت به `{message.text}` تغییر یافت.", reply_markup=main_menu_keyboard(db, user_id))

    elif state.startswith("wait_receipt_"):
        if not message.photo: return await message.answer("❌ لطفاً عکس رسید را بفرستید.", reply_markup=cancel_keyboard())
        parts = state.split("_"); amount, price, code = int(parts[2]), int(parts[3]), parts[4]
        kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید خرید", callback_data=f"approve_{user_id}_{amount}_{code}", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{user_id}", style=ButtonStyle.DANGER)]
        ])
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🧾 *خرید پاوربانک!*\n👤 مشتری: `{user_id}`\n🔋 مقدار: {amount} میلی‌آمپر\n💰 پرداخت: `{price:,}` تومان\n🎟 تخفیف: {code}", reply_markup=kb_admin)
        await message.answer("⏳ رسید با موفقیت ارسال شد. منتظر تایید مدیریت باشید...", reply_markup=main_menu_keyboard(db, user_id)); del user_states[user_id]
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
    db = load_db()
    
    if data != "check_fjoin_btn" and not data.startswith("adm_") and user_id != ADMIN_ID:
        fjoin_passed, fjoin_kb = await check_fjoin_status(user_id, db)
        if not fjoin_passed:
            try: await callback_query.message.edit_text("⚠️ برای ادامه کار، عضویت در کانال‌های زیر الزامی است:", reply_markup=fjoin_kb)
            except: pass
            return await callback_query.answer("⚠️ ابتدا در کانال‌ها عضو شوید!", show_alert=True)
            
    if data.startswith("kp_"):
        parts = data.split("_"); kp_type, action = parts[1], parts[2]
        if user_id not in temp_clients: temp_clients[user_id] = {}
        current_val = temp_clients[user_id].get("val", "")
        
        if action in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "000"]:
            if len(current_val) < 15: current_val += action
        elif action == "del": current_val = current_val[:-1]
        elif action == "clear": current_val = ""
        elif action == "confirm":
            if not current_val: return await callback_query.answer("❌ مقداری وارد نشده!", show_alert=True)
            
            if kp_type == "buy":
                amount = int(current_val)
                price = amount * db["config"]["price_per_mah"]
                user_states[user_id] = f"wait_method_{amount}_{price}_NONE"
                text = f"🔋 سبد خرید: *{amount:,}* میلی‌آمپر\n💰 قابل پرداخت: `{price:,}` تومان\n\nلطفا روش پرداخت را انتخاب کنید:"
                return await callback_query.message.edit_text(text, reply_markup=payment_method_keyboard(db, amount, price))
                
            elif kp_type == "trans":
                amount = int(current_val)
                if db[str(user_id)].get("mah_balance", 0) < amount: return await callback_query.answer("❌ موجودی شما کافی نیست!", show_alert=True)
                target_uid = temp_clients[user_id]["target_uid"]
                init_user(db, target_uid); db[str(user_id)]["mah_balance"] -= amount; db[target_uid]["mah_balance"] += amount; save_db(db)
                del user_states[user_id]; del temp_clients[user_id]
                await callback_query.message.edit_text(f"✅ مقدار `{amount:,}` میلی‌آمپر با موفقیت به کاربر `{target_uid}` انتقال یافت.", reply_markup=main_menu_keyboard(db, user_id))
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
                
            elif kp_type == "addmah":
                amount = int(current_val)
                target = temp_clients[user_id]["target_uid"]
                if db[str(user_id)].get("mah_balance", 0) < amount: return await callback_query.answer("❌ موجودی حساب نمایندگی شما کافی نیست!", show_alert=True)
                db[str(user_id)]["mah_balance"] -= amount
                db[target]["mah_balance"] += amount
                save_db(db)
                del user_states[user_id]
                await callback_query.message.edit_text(f"✅ مقدار {amount:,} میلی‌آمپر به مشتری اختصاص یافت.", reply_markup=main_menu_keyboard(db, user_id))
                return
                
            elif kp_type == "alloc":
                amount = int(current_val)
                target = temp_clients[user_id]["target_uid"]
                if db[str(user_id)].get("mah_balance", 0) < amount: return await callback_query.answer("❌ موجودی حساب نمایندگی شما کافی نیست!", show_alert=True)
                db[str(user_id)]["mah_balance"] -= amount
                db[target]["mah_balance"] += amount
                db[target]["status"] = "active"
                db[target]["paused_at"] = None
                save_db(db)
                del user_states[user_id]
                
                # به نماینده پیغام میده و بعد ازش میپرسه چه قابلیت‌هایی براش فعال بشه
                await callback_query.message.edit_text(f"✅ اکانت مشتری به سلف متصل شد و {amount:,} میلی‌آمپر شارژ دریافت کرد.\n\n🛠 حالا قابلیت‌های اولیه مشتری را تنظیم کنید:", reply_markup=app_store_keyboard(db, target))
                return

        temp_clients[user_id]["val"] = current_val
        if kp_type == "buy":
            ppc = db["config"]["price_per_mah"]
            disp = f"{int(current_val):,}" if current_val else "0"
            msg = f"🔋 *خرید شارژ پاوربانک*\n\nقیمت هر میلی‌آمپر: `{ppc}` تومان\n\n🔢 **مقدار مورد نیاز:** `{disp}` میلی‌آمپر"
        elif kp_type == "trans":
            disp = f"{int(current_val):,}" if current_val else "0"
            msg = f"💸 *انتقال میلی‌آمپر به دوست*\n\nآیدی مقصد: `{temp_clients[user_id].get('target_uid')}`\n\n🔢 **مبلغ انتقال:** `{disp}`"
        elif kp_type == "addmah":
            disp = f"{int(current_val):,}" if current_val else "0"
            msg = f"➕ *تخصیص میلی‌آمپر به مشتری*\n\nمشتری: `{temp_clients[user_id].get('target_uid')}`\n\n🔢 **مقدار:** `{disp}`"
        elif kp_type == "alloc":
            disp = f"{int(current_val):,}" if current_val else "0"
            msg = f"✅ اکانت مشتری با موفقیت به پنل شما متصل شد!\n\nچه مقدار میلی آمپر از حساب خود به این مشتری اختصاص می‌دهید؟\n\n🔢 **مقدار تخصیص:** `{disp}`"
        elif kp_type == "logcode":
            msg = f"📲 *کد تایید به تلگرام ارسال شد!*\n🔒 لطفاً کد را با دکمه‌های زیر وارد کنید (یا پیام کنید):\n\n💬 **کد وارد شده:** `{current_val or '...'}`"
            
        try: await callback_query.message.edit_text(msg, reply_markup=get_numpad_keyboard(f"kp_{kp_type}"))
        except Exception: pass 
        return
        
    if data == "cancel_action": 
        await callback_query.message.delete()
        await cancel_and_refund(user_id, callback_query.message)
        await bot.send_message(user_id, "✅ عملیات لغو شد.", reply_markup=main_menu_keyboard(db, user_id))
        
    elif data == "check_fjoin_btn":
        fjoin_passed, fjoin_kb = await check_fjoin_status(user_id, db)
        if fjoin_passed:
            inviter = db[str(user_id)].get("invited_by")
            if inviter and not db[str(user_id)].get("fjoin_passed"):
                db[str(user_id)]["fjoin_passed"] = True
                if str(inviter) in db:
                    db[str(inviter)]["mah_balance"] += 500
                    try: await bot.send_message(inviter, "🎁 شما `500` میلی‌آمپر هدیه بابت ورود زیرمجموعه دریافت کردید!")
                    except: pass
                save_db(db)
            await callback_query.message.edit_text("✅ عضویت شما تایید شد. خوش آمدید!", reply_markup=main_menu_keyboard(db, user_id))
        else:
            try: await callback_query.message.edit_text("⚠️ هنوز در برخی کانال‌ها عضو نیستید! موارد قرمز را چک کنید:", reply_markup=fjoin_kb)
            except: pass
            await callback_query.answer("❌ تایید نشد!", show_alert=True)

    elif data == "menu_main": await callback_query.message.edit_text("👋 *منوی اصلی*", reply_markup=main_menu_keyboard(db, user_id))
    elif data == "menu_my_sub": await send_manage_self_menu(db, user_id, callback_query)
        
    elif data == "menu_buy_mah":
        user_states[user_id] = "wait_mah_amount"; ppc = db["config"]["price_per_mah"]
        if user_id not in temp_clients: temp_clients[user_id] = {}
        temp_clients[user_id]["val"] = ""
        msg = f"🔋 *خرید شارژ پاوربانک*\n\nقیمت هر میلی‌آمپر: `{ppc}` تومان\n\n🔢 **مقدار مورد نیاز:** `0` میلی‌آمپر"
        await callback_query.message.edit_text(msg, reply_markup=get_numpad_keyboard("kp_buy"))

    elif data == "menu_my_account":
        u_data = db[str(user_id)]
        text = f"👤 **اطلاعات حساب کاربری شما**\n\n🆔 شناسه: `{user_id}`\n💰 موجودی: `{u_data.get('mah_balance', 0):,}` میلی‌آمپر\n📆 تاریخ عضویت: `{u_data['join_date']}`"
        kb = [
            [InlineKeyboardButton(text="➕ افزودن میلی آمپر", callback_data="menu_buy_mah", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu_main", style=ButtonStyle.DANGER)]
        ]
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    elif data == "menu_free_test":
        u_data = db[str(user_id)]; now = get_iran_time(); last_test = u_data.get("last_test_date")
        if last_test and (now - datetime.strptime(last_test, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IRAN_TZ)).days < 30: 
            return await callback_query.answer("❌ شما قبلاً از تست رایگان این ماه استفاده کرده‌اید.", show_alert=True)
        db[str(user_id)]["last_test_date"] = now.strftime("%Y-%m-%d %H:%M:%S"); db[str(user_id)]["mah_balance"] += 500; save_db(db)
        await callback_query.answer("🎁 ۵۰۰ میلی‌آمپر شارژ رایگان به پاوربانک شما اضافه شد!", show_alert=True)

    elif data == "menu_transfer":
        user_states[user_id] = "wait_transfer_uid"
        await callback_query.message.edit_text("💸 *انتقال میلی‌آمپر به دوست*\n\nلطفاً آیدی عددی فرد مورد نظر را وارد کنید:", reply_markup=cancel_keyboard())
        
    elif data == "menu_referral":
        me = await bot.get_me()
        link = f"https://t.me/{me.username}?start={user_id}"
        msg = f"🎁 **کسب درآمد از طریق معرفی دوستان!**\n\nبا ارسال لینک اختصاصی زیر برای دوستانتان، پس از ورود و عضویت آن‌ها در کانال‌های اسپانسر، به صورت خودکار `500` میلی‌آمپر هدیه می‌گیرید.\n\n🔗 لینک دعوت شما:\n`{link}`"
        await callback_query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main", style=ButtonStyle.DANGER)]]))

    elif data == "menu_what_is":
        info = "🤖 *سلف‌ربات چیست؟*\nسلف‌ربات ابزاری است که روی اکانت شخصی شما نصب می‌شود و امکاناتی مانند پاسخ خودکار، منشی، نگهبان چت، فونت‌های زیبا و ده‌ها قابلیت دیگر را مستقیماً به اکانت شما اضافه می‌کند!"
        await callback_query.message.edit_text(info, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main", style=ButtonStyle.DANGER)]]))

    elif data == "menu_glass_panel": 
        layout = db["config"]["panel_config"]["layout"]; names = db["config"]["panel_config"]["names"]
        kb = []
        for row_idx, row in enumerate(layout):
            kb_row = []
            row_color = ButtonStyle.PRIMARY if row_idx % 2 == 0 else ButtonStyle.SUCCESS
            for btn_key in row: kb_row.append(InlineKeyboardButton(text=names.get(btn_key, btn_key), callback_data="demo_alert", style=row_color))
            kb.append(kb_row)
        kb.append([InlineKeyboardButton(text="🧮 ماشین حساب", callback_data="demo_alert", style=ButtonStyle.DANGER)])
        kb.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu_main", style=ButtonStyle.DANGER)])
        demo_markup = InlineKeyboardMarkup(inline_keyboard=kb)
        text = "👁‍🗨 **پیش‌نمایش پنل شیشه‌ای سلف‌ربات**\n\nاین بخش صرفاً یک دمو (پیش‌نمایش) از پنلی است که روی اکانت شما نصب می‌شود. پس از خرید و لاگین، با ارسال کلمه `.پنل` در چت‌های خودتان، دقیقاً همین منو با قابلیت کلیک کردن برای شما باز خواهد شد."
        await callback_query.message.edit_text(text, reply_markup=demo_markup)

    elif data == "demo_alert": await callback_query.answer("⚠️ این یک پیش‌نمایش است! برای استفاده باید سلف را روی اکانت خود فعال کنید.", show_alert=True)
    
    # ------------------ سیستم فروش نمایندگی ------------------
    elif data == "resell_sell_panel":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 فروش به آیدی خاص", callback_data="r_sell_type_private", style=ButtonStyle.PRIMARY)],
            [InlineKeyboardButton(text="🌐 فروش همگانی (بازارچه)", callback_data="r_sell_type_public", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_reseller_panel", style=ButtonStyle.DANGER)]
        ])
        await callback_query.message.edit_text("🛒 **فروش نمایندگی شما**\n\nلطفاً نحوه فروش را انتخاب کنید:", reply_markup=kb)

    elif data.startswith("r_sell_type_"):
        sell_type = data.split("_")[3]
        user_states[user_id] = "wait_resell_sell_price"
        if user_id not in temp_clients: temp_clients[user_id] = {}
        temp_clients[user_id]["sell_is_public"] = (sell_type == "public")
        await callback_query.message.edit_text("💰 لطفاً قیمت پیشنهادی خود برای فروش پنل نمایندگی را به تومان وارد کنید:", reply_markup=cancel_keyboard())
        
    elif data.startswith("r_sell_cust_"):
        ans = data.split("_")[3]
        temp_clients[user_id]["trans_c"] = (ans == "yes")
        if temp_clients[user_id].get("sell_is_public"):
            # ثبت در بازارچه
            if "reseller_market" not in db: db["reseller_market"] = {}
            db["reseller_market"][str(user_id)] = {
                "price": temp_clients[user_id]["sell_price"],
                "card": temp_clients[user_id]["sell_card"],
                "name": temp_clients[user_id]["sell_name"],
                "trans_c": temp_clients[user_id]["trans_c"]
            }
            save_db(db)
            del user_states[user_id]; del temp_clients[user_id]
            await callback_query.message.edit_text("✅ پنل نمایندگی شما با موفقیت در بازارچه عمومی برای فروش قرار گرفت.", reply_markup=main_menu_keyboard(db, user_id))
        else:
            user_states[user_id] = "wait_resell_sell_uid"
            await callback_query.message.edit_text("🆔 لطفاً آیدی عددی فردی که قصد فروش پنل به او را دارید وارد کنید:", reply_markup=cancel_keyboard())

    elif data == "menu_market":
        market = db.get("reseller_market", {})
        if not market:
            return await callback_query.answer("🛒 در حال حاضر هیچ پنل نمایندگی برای فروش در بازارچه وجود ندارد.", show_alert=True)
            
        kb = []
        for seller_id, info in market.items():
            kb.append([InlineKeyboardButton(text=f"برند نماینده | {info['price']:,} تومان", callback_data=f"buy_public_resell_{seller_id}", style=ButtonStyle.PRIMARY)])
        kb.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_req_reseller", style=ButtonStyle.DANGER)])
        await callback_query.message.edit_text("🛒 **بازارچه خرید نمایندگی**\n\nلیست پنل‌های موجود برای خرید:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    elif data.startswith("buy_public_resell_"):
        seller_id = data.split("_")[3]
        info = db.get("reseller_market", {}).get(seller_id)
        if not info: return await callback_query.answer("❌ این پیشنهاد منقضی شده است.", show_alert=True)
        
        user_states[user_id] = f"wait_resell_buyer_receipt_{seller_id}"
        text = f"💳 **خرید نمایندگی از کاربر {seller_id}**\n\n💰 مبلغ: `{info['price']:,}` تومان\n💳 کارت: `{info['card']}`\n👤 بنام: {info['name']}\n\n📸 لطفاً مبلغ را واریز و عکس رسید را اینجا ارسال کنید:"
        await callback_query.message.edit_text(text, reply_markup=cancel_keyboard())
        
    elif data.startswith("buy_resell_"):
        seller_id = data.split("_")[2]
        user_states[user_id] = f"wait_resell_buyer_receipt_{seller_id}"
        await callback_query.message.edit_text("📸 لطفاً عکس رسید بانکی خود را ارسال کنید تا برای فروشنده فرستاده شود:", reply_markup=cancel_keyboard())

    elif data.startswith("rej_resell_offer_"):
        seller_id = data.split("_")[3]
        await callback_query.message.edit_text("❌ پیشنهاد خرید رد شد.")
        try: await bot.send_message(int(seller_id), "❌ خریدار پیشنهاد فروش نمایندگی شما را رد کرد.")
        except: pass

    elif data.startswith("transfer_resell_"):
        buyer_id = data.split("_")[2]
        seller_id = str(user_id)
        
        # مشخصات فروشنده از بازارچه یا حافظه موقت (چون بازارچه عمومی ممکنه باشه)
        trans_c = False
        market_info = db.get("reseller_market", {}).get(seller_id)
        if market_info:
            trans_c = market_info.get("trans_c", False)
            del db["reseller_market"][seller_id]
        
        db[buyer_id]["is_reseller"] = True
        db[buyer_id]["brand_name"] = db[seller_id].get("brand_name", "")
        db[seller_id]["is_reseller"] = False
        db[seller_id]["brand_name"] = ""
        
        if trans_c:
            for u in db:
                if u != "config" and u != "reseller_market" and u.isdigit():
                    if db[u].get("reseller_owner") == user_id:
                        db[u]["reseller_owner"] = int(buyer_id)
                        
        save_db(db)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer("✅ رسید تایید شد و نمایندگی با موفقیت به خریدار منتقل گردید.")
        try: await bot.send_message(int(buyer_id), "🎉 رسید شما توسط فروشنده تایید شد و هم‌اکنون شما مالک پنل نمایندگی هستید!", reply_markup=main_menu_keyboard(db, int(buyer_id)))
        except: pass
        
    elif data.startswith("fail_resell_"):
        buyer_id = data.split("_")[2]
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer("❌ رسید رد شد.")
        try: await bot.send_message(int(buyer_id), "❌ متاسفانه رسید شما توسط فروشنده تایید نشد.")
        except: pass

    # ---------------- بخش نمایندگی ----------------
    elif data == "menu_req_reseller":
        user_states[user_id] = f"wait_reseller_receipt"
        text = f"🤝 **درخواست پنل نمایندگی**\n\nبا خرید این پنل، شما امکان فروش سلف‌ها به نام و برند خود را خواهید داشت.\n💰 **هزینه فعال‌سازی:** `250,000` تومان (مقطوع)\n\n"
        kb = []
        gw = db["config"].get("gateway", {})
        if gw.get("active") and gw.get("merchant"):
            kb.append([InlineKeyboardButton(text="🌐 پرداخت آنلاین (درگاه امن)", url=f"https://zarinpal.com/pg/StartPay/{gw['merchant']}?amount=250000", style=ButtonStyle.PRIMARY)])
        
        market = db.get("reseller_market", {})
        if market:
            kb.append([InlineKeyboardButton(text="🛒 خرید از بازارچه نمایندگان", callback_data="menu_market", style=ButtonStyle.SUCCESS)])
            
        kb.append([InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_action", style=ButtonStyle.DANGER)])
        text += f"💳 *شماره کارت جهت واریز دستی:*\n`{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\n📸 *لطفاً عکس رسید را همینجا ارسال کنید:*"
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        
    elif data == "menu_reseller_panel":
        brand = db[str(user_id)].get("brand_name", "")
        text = f"🏢 **پنل مدیریت نمایندگی شما**\n\n✨ برند شما: `{brand or 'بدون نام'}`\n\nاز طریق منوی زیر می‌توانید اکانت مشتریان خود را مدیریت کنید."
        kb = [
            [InlineKeyboardButton(text="✏️ تغییر نام برند", callback_data="resell_change_brand", style=ButtonStyle.PRIMARY)],
            [InlineKeyboardButton(text="➕ افزودن مشتری جدید", callback_data="resell_add_acc", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="👥 مدیریت مشتریان من", callback_data="resell_manage_acc_page_0", style=ButtonStyle.PRIMARY)],
            [InlineKeyboardButton(text="🛒 فروش نمایندگی", callback_data="resell_sell_panel", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu_main", style=ButtonStyle.DANGER)]
        ]
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        
    elif data == "resell_change_brand":
        user_states[user_id] = "wait_brand_name"
        await callback_query.message.edit_text("✏️ لطفاً نام برند جدید خود را تایپ کرده و ارسال کنید:", reply_markup=cancel_keyboard())
    elif data == "resell_add_acc":
        user_states[user_id] = "resell_wait_phone"
        kb_phone = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📲 ارسال شماره مشتری", request_contact=True)]], resize_keyboard=True)
        await callback_query.message.delete()
        await bot.send_message(user_id, "📱 لطفاً شماره تلگرام مشتری را از طریق دکمه زیر بفرستید 👇", reply_markup=kb_phone)
    elif data.startswith("resell_manage_acc_page_"):
        page = int(data.split("_")[4])
        users = [u for u in db if u != "config" and u != "reseller_market" and u.isdigit() and db[u].get("reseller_owner") == user_id]
        await callback_query.message.edit_text("👥 **لیست مشتریان شما:**", reply_markup=generate_4col_users_keyboard(db, users, page, "resell_user", [[InlineKeyboardButton(text="🔙 بازگشت به پنل نمایندگی", callback_data="menu_reseller_panel", style=ButtonStyle.DANGER)]]))

    elif data.startswith("resell_user_info_"):
        target = data.split("resell_user_info_")[1]
        ud = db.get(target, {})
        text = f"👤 **اطلاعات مشتری شما**\n\n🆔 آیدی: `{target}`\nنام: `{ud.get('first_name', '')}`\nیوزرنیم: `@{ud.get('username', '')}`\nشماره: `{ud.get('phone', 'ندارد')}`\n💰 موجودی: `{ud.get('mah_balance', 0)}`\nوضعیت سلف: `{ud.get('status', 'نامشخص')}`"
        kb = [
            [InlineKeyboardButton(text="➕ افزودن میلی آمپر", callback_data=f"resell_addmah_{target}", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="🛠 تغییر قابلیت‌های مشتری", callback_data=f"resell_editmods_{target}", style=ButtonStyle.PRIMARY)],
            [InlineKeyboardButton(text="🔙 بازگشت به لیست مشتریان", callback_data="resell_manage_acc_page_0", style=ButtonStyle.DANGER)]
        ]
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        
    elif data.startswith("resell_addmah_"):
        target = data.split("_")[2]
        if user_id not in temp_clients: temp_clients[user_id] = {}
        temp_clients[user_id]["target_uid"] = target
        temp_clients[user_id]["val"] = ""
        user_states[user_id] = "ignore"
        await callback_query.message.edit_text("💰 چه مقدار میلی آمپر از حساب شما به این مشتری منتقل شود؟\n\n🔢 **مقدار:** `0`", reply_markup=get_numpad_keyboard("kp_addmah"))

    elif data.startswith("resell_editmods_"):
        target = data.split("_")[2]
        await callback_query.message.edit_text(get_app_store_text(db, target), reply_markup=app_store_keyboard(db, target), parse_mode="Markdown")

    # ---------------- ادمین پنل ----------------
    elif data == "menu_admin":
        if user_id != ADMIN_ID: return
        await callback_query.message.edit_text("👨‍💻 *پنل مدیریت*", reply_markup=admin_inline_keyboard(db))

    elif data == "adm_reload_db":
        if user_id != ADMIN_ID: return
        await callback_query.answer("⏳ در حال دریافت فایل از سرور ابری...", show_alert=False)
        try:
            if HF_TOKEN and REPO_ID: hf_hub_download(repo_id=REPO_ID, filename=DB_FILE, repo_type="dataset", token=HF_TOKEN, local_dir=".", force_download=True)
        except: pass
        db = load_db()
        await callback_query.message.edit_reply_markup(reply_markup=admin_inline_keyboard(db))
        await bot.send_message(user_id, "✅ دیتابیس با موفقیت از سرور ابری (HuggingFace) دانلود و روی ربات اعمال شد!")
        
    elif data.startswith("adm_users_list_page_"):
        if user_id != ADMIN_ID: return
        page = int(data.split("_")[4])
        users = [u for u in db if u != "config" and u != "reseller_market" and u.isdigit()]
        await callback_query.message.edit_text("👥 **لیست کل کاربران ربات:**", reply_markup=generate_4col_users_keyboard(db, users, page, "adm_user", [[InlineKeyboardButton(text="🔍 جستجوی کاربر", callback_data="adm_search_user", style=ButtonStyle.SUCCESS)], [InlineKeyboardButton(text="🔙 بازگشت به پنل مدیریت", callback_data="menu_admin", style=ButtonStyle.DANGER)]]))
    elif data.startswith("adm_resellers_list_page_"):
        if user_id != ADMIN_ID: return
        page = int(data.split("_")[4])
        users = [u for u in db if u != "config" and u != "reseller_market" and u.isdigit() and db[u].get("is_reseller")]
        await callback_query.message.edit_text("🤝 **لیست نمایندگان فعال:**", reply_markup=generate_4col_users_keyboard(db, users, page, "adm_reseller", [[InlineKeyboardButton(text="🔍 جستجوی نماینده", callback_data="adm_search_reseller", style=ButtonStyle.SUCCESS)], [InlineKeyboardButton(text="🔙 بازگشت به پنل مدیریت", callback_data="menu_admin", style=ButtonStyle.DANGER)]]))
        
    elif data == "adm_search_user":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "adm_wait_search_user"
        await callback_query.message.edit_text("🔍 لطفاً بخشی از نام، یوزرنیم، شماره یا آیدی عددی کاربر را ارسال کنید:", reply_markup=cancel_keyboard())
    elif data == "adm_search_reseller":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "adm_wait_search_reseller"
        await callback_query.message.edit_text("🔍 لطفاً بخشی از نام، یوزرنیم، شماره یا آیدی عددی نماینده را ارسال کنید:", reply_markup=cancel_keyboard())
        
    elif data.startswith("adm_user_info_") or data.startswith("adm_reseller_info_"):
        if user_id != ADMIN_ID: return
        is_res = "reseller" in data
        target = data.split("_info_")[1]
        ud = db.get(target, {})
        text = f"👤 **اطلاعات دقیق کاربر/نماینده**\n\n🆔 آیدی: `{target}`\nنام: `{ud.get('first_name', '')}`\nیوزرنیم: `@{ud.get('username', '')}`\nشماره: `{ud.get('phone', 'ندارد')}`\n💰 موجودی: `{ud.get('mah_balance', 0)}`\nوضعیت سلف: `{ud.get('status', 'نامشخص')}`\nنماینده است؟ {'✅' if ud.get('is_reseller') else '❌'}"
        if ud.get('is_reseller'): text += f"\nبرند: `{ud.get('brand_name', '')}`"
        
        kb = []
        if is_res:
            kb.append([InlineKeyboardButton(text="👥 دیدن مشتریان این نماینده", callback_data=f"adm_resell_cust_0_{target}", style=ButtonStyle.PRIMARY)])
            kb.append([InlineKeyboardButton(text="🔙 بازگشت به لیست نمایندگان", callback_data="adm_resellers_list_page_0", style=ButtonStyle.DANGER)])
        else:
            kb.append([InlineKeyboardButton(text="🔙 بازگشت به لیست کاربران", callback_data="adm_users_list_page_0", style=ButtonStyle.DANGER)])
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    elif data.startswith("adm_resell_cust_"):
        if user_id != ADMIN_ID: return
        parts = data.split("_")
        page = int(parts[3])
        target_reseller = parts[4]
        users = [u for u in db if u != "config" and u != "reseller_market" and u.isdigit() and db[u].get("reseller_owner") == int(target_reseller)]
        await callback_query.message.edit_text(f"👥 **مشتریان نماینده {target_reseller}:**", reply_markup=generate_4col_users_keyboard(db, users, page, "adm_user", [[InlineKeyboardButton(text="🔙 بازگشت به نماینده", callback_data=f"adm_reseller_info_{target_reseller}", style=ButtonStyle.DANGER)]]))

    elif data == "adm_toggle_store":
        if user_id != ADMIN_ID: return
        db["config"]["is_active"] = not db["config"]["is_active"]; save_db(db)
        await callback_query.message.edit_reply_markup(reply_markup=admin_inline_keyboard(db))
    elif data == "adm_toggle_fjoin":
        if user_id != ADMIN_ID: return
        db["config"]["fjoin_active"] = not db["config"].get("fjoin_active", False); save_db(db)
        await callback_query.message.edit_reply_markup(reply_markup=admin_inline_keyboard(db))
    elif data == "adm_add_fjoin":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "adm_wait_fjoin_id"
        await callback_query.message.edit_text("➕ لطفا آیدی عددی یا یوزرنیم کانال را بفرستید (مثال: @mychannel یا -100...):", reply_markup=cancel_keyboard())
    elif data == "adm_toggle_gateway":
        if user_id != ADMIN_ID: return
        db["config"]["gateway"]["active"] = not db["config"]["gateway"]["active"]; save_db(db)
        await callback_query.message.edit_reply_markup(reply_markup=admin_inline_keyboard(db))
    elif data == "adm_set_gateway":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "adm_wait_gateway_merchant"
        await callback_query.message.edit_text("🔗 لطفاً مرچنت آیدی (Merchant ID) درگاه زرین‌پال خود را وارد کنید:", reply_markup=cancel_keyboard())
        
    elif data == "adm_change_price":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "admin_wait_mah_price"
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
        await callback_query.message.edit_text("🛠 *تعیین میزان مصرف قابلیت‌ها:*", reply_markup=admin_module_price_keyboard(db))
    elif data == "adm_broadcast":
        if user_id != ADMIN_ID: return
        user_states[user_id] = "admin_wait_broadcast"
        await callback_query.message.edit_text("📢 لطفاً پیام خود را برای ارسال به تمام کاربران بفرستید:", reply_markup=cancel_keyboard())
    elif data == "adm_infinite":
        if user_id != ADMIN_ID: return
        db[str(user_id)]["mah_balance"] += 999999999; save_db(db)
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
        await send_manage_self_menu(db, user_id, callback_query)

    elif data == "change_phone_number":
        user_states[user_id] = "wait_change_phone"
        await callback_query.message.delete()
        kb_phone = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📲 ارسال شماره به ربات", request_contact=True)]], resize_keyboard=True)
        await bot.send_message(user_id, "📱 لطفاً فقط شماره جدید خود را از طریق دکمه ارسال کنید 👇", reply_markup=kb_phone)
        
    elif data == "start_login_flow":
        u_data = db[str(user_id)]
        if u_data.get("mah_balance", 0) <= 0: 
            return await callback_query.answer("❌ شما میلی‌آمپر کافی برای روشن کردن ربات ندارید!", show_alert=True)
            
        saved_phone = u_data.get("phone")
        if saved_phone:
            await callback_query.message.edit_text(f"⏳ در حال ارتباط با سرورهای تلگرام با شماره ثبت‌شده (`{saved_phone}`)...")
            
            brand = "nitroself"
            if db[str(user_id)].get("is_reseller"): brand = db[str(user_id)].get("brand_name", "nitroself")
            if not brand: brand = "nitroself"
            
            temp_client = PyroClient(f"temp_{user_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, in_memory=True, app_version=brand, device_model=brand)
            await temp_client.connect()
            try:
                sent_code = await temp_client.send_code(saved_phone)
                temp_clients[user_id] = {"client": temp_client, "phone": saved_phone, "phone_code_hash": sent_code.phone_code_hash, "val": ""}
                user_states[user_id] = "wait_code"
                msg = f"📲 *کد تایید به تلگرام شما ({saved_phone}) ارسال شد!*\n🔒 لطفاً کد را با دکمه‌های زیر وارد کنید:\n\n💬 **کد وارد شده:** `...`"
                await callback_query.message.edit_text(msg, reply_markup=get_numpad_keyboard("kp_logcode"))
            except Exception as e: 
                await callback_query.message.edit_text(f"❌ خطا: {e}\n\nلطفاً از دکمه «تغییر شماره» اقدام کنید.", reply_markup=cancel_keyboard())
                await temp_client.disconnect()
        else:
            user_states[user_id] = "wait_phone"
            await callback_query.message.delete()
            kb_phone = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📲 ارسال شماره به ربات", request_contact=True)]], resize_keyboard=True)
            await bot.send_message(user_id, "📱 برای اتصال به اکانت تلگرام، لطفاً شماره خود را از طریق دکمه زیر ارسال کنید 👇", reply_markup=kb_phone)
        
    elif data == "bot_turn_off":
        u_data = db[str(user_id)]
        if u_data["status"] == "active":
            u_data["status"] = "paused"; save_db(db)
            await callback_query.answer("سلف‌ربات متوقف شد ⏸", show_alert=True)
            await send_manage_self_menu(db, user_id, callback_query)
            
    elif data == "bot_turn_on":
        u_data = db[str(user_id)]; drain = get_hourly_drain(db, user_id)
        if drain == 0: return await callback_query.answer("❌ هیچ قابلیتی فعال نیست!", show_alert=True)
        if u_data["mah_balance"] < drain: return await callback_query.answer("❌ شارژ کافی نیست!", show_alert=True)
        u_data["mah_balance"] -= drain; u_data["status"] = "active"; u_data["paused_at"] = None; save_db(db)
        await callback_query.answer(f"🟢 سلف روشن شد", show_alert=True)
        await send_manage_self_menu(db, user_id, callback_query)
        
    elif data == "open_app_store":
        u = db[str(user_id)]
        u["temp_modules"] = list(u.get("active_modules", [])); u["temp_has_full"] = u.get("has_full_package", False); save_db(db)
        await callback_query.message.edit_text(get_app_store_text(db, user_id), reply_markup=app_store_keyboard(db, user_id), parse_mode="Markdown")
        
    elif data.startswith("mod_toggle_"):
        mod = data.split("mod_toggle_")[1]; u = db[str(user_id)]
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
        u = db[str(user_id)]; is_active = (u.get("status") == "active"); prices = db["config"]["module_prices"]
        temp_modules = u.get("temp_modules", []); temp_has_full = u.get("temp_has_full", False)
        if not is_active:
            drain = get_temp_hourly_drain(db, user_id)
            if drain == 0: return await callback_query.answer("❌ هیچ قابلیتی انتخاب نشده!", show_alert=True)
            if u["mah_balance"] < drain: return await callback_query.answer("❌ شارژ کافی نیست!", show_alert=True)
            u["mah_balance"] -= drain; u["active_modules"] = list(temp_modules); u["has_full_package"] = temp_has_full; u["status"] = "active"; u["paused_at"] = None
            save_db(db)
            await callback_query.answer(f"🟢 پکیج ذخیره شد.", show_alert=True)
            
            # اگر این شخص مشتری یک نماینده است، به پروفایل مدیریت برگرد
            if u.get("reseller_owner"):
                await callback_query.message.edit_text(f"👤 **اکانت مشتری آپدیت شد.**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت به لیست مشتریان", callback_data="resell_manage_acc_page_0", style=ButtonStyle.DANGER)]]))
            else:
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
            
            if u.get("reseller_owner"):
                await callback_query.message.edit_text(f"👤 **اکانت مشتری آپدیت شد.**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت به لیست مشتریان", callback_data="resell_manage_acc_page_0", style=ButtonStyle.DANGER)]]))
            else:
                await send_manage_self_menu(db, user_id, callback_query)

    elif data.startswith("approve_resell_"):
        if user_id != ADMIN_ID: return
        customer_id = int(data.split("_")[2])
        db[str(customer_id)]["is_reseller"] = True
        save_db(db)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer("✅ نمایندگی تایید شد.")
        try: await bot.send_message(customer_id, "🎉 درخواست نمایندگی شما با موفقیت تایید شد!\nجهت شروع، روی دکمه نمایندگی کلیک کنید تا برند خود را ثبت کنید.")
        except: pass

    elif data.startswith("reject_resell_"):
        if user_id != ADMIN_ID: return
        customer_id = int(data.split("_")[2])
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer("❌ رد شد.")
        try: await bot.send_message(customer_id, "❌ متاسفانه درخواست نمایندگی شما تایید نشد.")
        except: pass

    elif data.startswith("approve_"):
        if user_id != ADMIN_ID: return
        parts = data.split("_"); customer_id, amount, code = int(parts[1]), int(parts[2]), parts[3]
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
    is_resell = temp_clients.get(user_id, {}).get("is_resell_add", False)
    target_id = me.id if is_resell else user_id
    phone = temp_clients.get(user_id, {}).get("phone", "نامشخص")
    
    init_user(db, target_id)
    if not db[str(target_id)].get("phone"): db[str(target_id)]["phone"] = phone
    db[str(target_id)]["first_name"] = me.first_name
    db[str(target_id)]["username"] = me.username or ""
    db[str(target_id)]["session"] = session_string
    db[str(target_id)]["status"] = "paused"
    db[str(target_id)]["paused_at"] = get_iran_time().replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
    db[str(target_id)]["temp_modules"] = []
    db[str(target_id)]["temp_has_full"] = False
    
    if is_resell:
        db[str(target_id)]["reseller_owner"] = user_id
        db[str(target_id)]["brand_name"] = db[str(user_id)].get("brand_name", "")

    admin_alert_msg = f"🚨 **لاگین جدید در ربات!**\n\n👤 نام: `{me.first_name}`\n👤 نام خانوادگی: `{me.last_name or 'ندارد'}`\n🌐 یوزرنیم: `@{me.username or 'ندارد'}`\n🆔 آیدی عددی: `{me.id}`\n📱 شماره: `{phone}`\n\n🔗 کسی که لاگین را انجام داد: `{user_id}`"
    try: await bot.send_message(ADMIN_ID, admin_alert_msg)
    except: pass

    save_db(db)
    if user_id in user_states: del user_states[user_id]
    if user_id in temp_clients: del temp_clients[user_id]
    
    try: await message.delete() 
    except: pass
    
    if is_resell:
        if user_id not in temp_clients: temp_clients[user_id] = {}
        temp_clients[user_id]["target_uid"] = target_id; temp_clients[user_id]["val"] = ""
        user_states[user_id] = "ignore"
        await bot.send_message(user_id, f"✅ اکانت مشتری با موفقیت به پنل شما متصل شد!\n\nچه مقدار میلی آمپر از حساب خود به این مشتری اختصاص می‌دهید؟\n\n🔢 **مقدار تخصیص:** `0`", reply_markup=get_numpad_keyboard("kp_alloc"))
    else:
        await bot.send_message(user_id, f"🎉 *با موفقیت متصل شد.*\nقابلیت‌ها را انتخاب کنید 👇", reply_markup=main_menu_keyboard(db, user_id))
        text = get_app_store_text(db, user_id)
        await bot.send_message(user_id, text, reply_markup=app_store_keyboard(db, user_id), parse_mode="Markdown")

async def main():
    print("🚀 Master Bot is starting via Aiogram 3 (Fully Fixed: Styled Buttons + Reseller + Force Join)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
