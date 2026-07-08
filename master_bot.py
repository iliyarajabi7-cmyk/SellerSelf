import asyncio
import json
import os
import threading
import jdatetime
from datetime import datetime, timezone, timedelta
from huggingface_hub import HfApi, hf_hub_download

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.enums import ParseMode, ButtonStyle

from pyrogram import Client as PyroClient
from pyrogram.errors import SessionPasswordNeeded

API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
BOT_TOKEN = "8726723140:AAEnazbn9GDuIFr13SYP6QhptWyQKOwyaF4"
ADMIN_ID = 2025464333 
SUPPORT_ID = "@Im_Iliiya" 
CHANNEL_ID = "@YourChannel" # آیدی چنل خود را بگذارید

CARD_NUMBER = "6037990000000000"
CARD_NAME = "نام شما"

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
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
        with open(tmp_file, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
        os.replace(tmp_file, DB_FILE) 
        threading.Thread(target=upload_to_hf, daemon=True).start()
    except Exception as e: print("Save DB Error:", e)

def ensure_config(db):
    if "config" not in db:
        db["config"] = {
            "is_active": True, 
            "price_per_mah": 1, 
            "gift_codes": {},
            "module_prices": { 
                "full_package": 50, "p_textmode": 2, "p_clock": 2, "p_guard": 3, 
                "p_ping": 0, "p_logo": 1, "p_locks": 3, "p_action": 1, 
                "p_monshi": 2, "p_filter": 2, "p_autoreply": 2, "p_forcejoin": 2, 
                "p_dl": 2, "p_react": 1, "p_spam": 2, "p_mute": 1, 
                "p_info": 0, "p_tag": 2, "p_purge": 2, "p_ai": 3, 
                "p_translate": 2, "p_anim": 1, "p_cheat": 2, "p_tts": 2, 
                "p_music": 2, "p_tabchi": 3, "p_comment": 2, "p_crypto": 1,
                "p_readall": 1, "p_v2ray": 1, "p_qr": 1, "p_profile": 1
            }
        }
        save_db(db)

def init_user(db, user_id):
    uid = str(user_id)
    if uid == "config": return
    if uid not in db:
        db[uid] = {
            "status": "inactive", "mah_balance": 0, 
            "active_modules": [], "has_full_package": False,
            "join_date": jdatetime.datetime.fromgregorian(datetime=get_iran_time()).strftime("%Y/%m/%d - %H:%M"), 
            "last_test_date": None, "paused_at": None
        }
        save_db(db)

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

def main_menu_keyboard(user_id):
    kb = [
        [InlineKeyboardButton(text="🤖 مدیریت سلف", callback_data="menu_manage_self", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="💎 الماس رایگان", callback_data="menu_free_test", style=ButtonStyle.PRIMARY),
         InlineKeyboardButton(text="👤 حساب کاربری", callback_data="menu_account", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🛒 خرید الماس", callback_data="menu_buy_mah", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="✔️ پشتیبانی", url=f"https://t.me/{SUPPORT_ID.replace('@', '')}", style=ButtonStyle.DANGER),
         InlineKeyboardButton(text="✔️ چنل", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text="🤖 سلف چیه ؟", callback_data="menu_whatis", style=ButtonStyle.DANGER)]
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="🎛 پنل مدیریت", callback_data="admin_panel", style=ButtonStyle.SECONDARY)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_reply_keyboard(db):
    conf = db["config"]
    status_btn = "🔴 خاموش کردن فروشگاه" if conf["is_active"] else "🟢 روشن کردن فروشگاه"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=status_btn, callback_data="adm_toggle_store", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text="💰 تغییر قیمت", callback_data="adm_change_price", style=ButtonStyle.PRIMARY),
         InlineKeyboardButton(text="🛠 مصرف قابلیت‌ها", callback_data="adm_modules", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="➕ شارژ کاربر", callback_data="adm_add_fund", style=ButtonStyle.SUCCESS),
         InlineKeyboardButton(text="➖ کسر شارژ", callback_data="adm_deduct_fund", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text="🎁 کد تخفیف", callback_data="adm_gift", style=ButtonStyle.PRIMARY),
         InlineKeyboardButton(text="♾ بینهایت", callback_data="adm_infinite", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="📢 ارسال همگانی", callback_data="adm_broadcast", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🔙 بستن", callback_data="cancel_action", style=ButtonStyle.SECONDARY)]
    ])

def payment_method_keyboard(amount, price, code="NONE"):
    kb = [
        [InlineKeyboardButton(text="💳 پرداخت کارت به کارت", callback_data=f"pay_card_{amount}_{price}_{code}", style=ButtonStyle.SUCCESS)]
    ]
    if code == "NONE": 
        kb.append([InlineKeyboardButton(text="🎁 اعمال کد تخفیف", callback_data=f"ask_discount_{amount}_{price}", style=ButtonStyle.PRIMARY)])
    kb.append([InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_action", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cancel_keyboard(): 
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ لغو عملیات", callback_data="cancel_action", style=ButtonStyle.DANGER)]])

def get_app_store_text(db, user_id):
    drain = get_temp_hourly_drain(db, user_id)
    cost_toman = drain * db["config"]["price_per_mah"]
    active = db[str(user_id)].get("temp_modules", [])
    has_full = db[str(user_id)].get("temp_has_full", False)
    
    text = "🛍 <b>فروشگاه قابلیت‌ها</b>\n\n"
    if db[str(user_id)].get("status") == "active":
        text += "🟢 <b>وضعیت: روشن</b>\n⚠️ هزینه ۱ ساعت بلافاصله کسر می‌شود.\n\n"
    else:
        text += "⏸ <b>وضعیت: خاموش</b>\nکسر شارژ پس از تایید نهایی انجام خواهد شد.\n\n"

    text += "📋 <b>لیست انتخاب‌ها:</b>\n"
    if has_full: text += f"👑 پکیج فول VIP — مصرف: <code>50</code> الماس\n"
    elif not active: text += "➖ خالی.\n"
    else: text += f"✔️ {len(active)} قابلیت انتخاب شده\n"
            
    text += f"\n📊 <b>مجموع مصرف:</b>\n⚡️ <code>{drain}</code> الماس در ساعت\n"
    return text

def app_store_keyboard(db, user_id):
    u = db[str(user_id)]
    active = u.get("temp_modules", [])
    has_full = u.get("temp_has_full", False)
    prices = db["config"]["module_prices"]
    
    kb = []
    fp_text = "✅ پکیج فول VIP" if has_full else f"❌ پکیج فول VIP ({prices.get('full_package', 50)} mAh)"
    kb.append([InlineKeyboardButton(text=fp_text, callback_data="mod_toggle_full_package", style=ButtonStyle.SUCCESS if has_full else ButtonStyle.DANGER)])
    
    # برای جلوگیری از طولانی شدن بیش از حد کیبورد، فقط دکمه‌های پرکاربرد را می‌آوریم و مابقی را در پنل شیشه‌ای تنظیم می‌کنیم
    # ولی طبق درخواست شما دکمه‌ها را می‌سازیم
    keys = list(prices.keys())
    keys.remove("full_package")
    keys = [k for k in keys if k not in ["p_ping", "p_info"]]
    
    row = []
    for k in keys:
        is_on = k in active or has_full
        icon = "✅" if is_on else "❌"
        # از اسم‌های خلاصه استفاده می‌کنیم تا جا شود
        name = k.replace("p_", "")
        row.append(InlineKeyboardButton(text=f"{icon} {name} ({prices[k]})", callback_data=f"mod_toggle_{k}", style=ButtonStyle.SUCCESS if is_on else ButtonStyle.DANGER))
        if len(row) == 3:
            kb.append(row); row = []
    if row: kb.append(row)
        
    kb.append([InlineKeyboardButton(text="✨ ثبت و تایید نهایی تغییرات", callback_data="confirm_app_store_changes", style=ButtonStyle.PRIMARY)])
    kb.append([InlineKeyboardButton(text="🔙 انصراف و بازگشت", callback_data="menu_manage_self", style=ButtonStyle.DANGER)])
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

@dp.message(F.chat.type == "private")
async def message_handler(message: Message):
    db = load_db()
    ensure_config(db)
    user_id = message.chat.id
    init_user(db, user_id)
    
    txt = message.text or ""
    state = user_states.get(user_id, "")

    if txt == "/start":
        await cancel_and_refund(user_id)
        return await message.answer("👋 <b>به فروشگاه رسمی سلف‌ربات خوش آمدید!</b>\nاز منوی زیر استفاده کنید:", reply_markup=main_menu_keyboard(user_id))

    if not db["config"]["is_active"] and user_id != ADMIN_ID: 
        return await message.answer("⚠️ <b>فروشگاه در حال بروزرسانی است.</b>")

    if state == "wait_mah_amount":
        if not txt.isdigit(): return await message.answer("❌ لطفاً عدد بفرستید.", reply_markup=cancel_keyboard())
        amount = int(txt); price = amount * db["config"]["price_per_mah"]
        user_states[user_id] = f"wait_receipt_{amount}_{price}_NONE"
        text = f"🔋 خرید <b>{amount:,}</b> الماس\n💰 پرداخت: <code>{price:,}</code> تومان\n\n💳 شماره کارت:\n<code>{CARD_NUMBER}</code>\n👤 بنام: {CARD_NAME}\n\n📸 <b>عکس رسید را بفرستید:</b>"
        return await message.answer(text, reply_markup=payment_method_keyboard(amount, price))

    elif state.startswith("wait_discount_"):
        parts = state.split("_"); amount, price = int(parts[2]), int(parts[3])
        code = txt.strip().upper()
        if code not in db["config"].get("gift_codes", {}): return await message.answer("❌ کد نامعتبر است.")
        gift = db["config"]["gift_codes"][code]
        if gift["uses"] <= 0: return await message.answer("❌ ظرفیت تکمیل است.")
        if user_id in gift["used_by"]: return await message.answer("❌ قبلاً استفاده کردید!")
        if gift["expire"] != "NONE" and get_iran_time().replace(tzinfo=None) > datetime.strptime(gift["expire"], "%Y-%m-%d %H:%M:%S"): return await message.answer("❌ منقضی شده است.")
        discount = int(price * gift["value"] / 100) if gift["type"] == "percent" else gift["value"]
        new_price = max(0, price - discount); user_states[user_id] = f"wait_receipt_{amount}_{new_price}_{code}"
        text = f"🎉 <b>تخفیف اعمال شد!</b>\n💰 پرداخت: <code>{new_price:,}</code> تومان\n💳 کارت: <code>{CARD_NUMBER}</code>\n📸 <b>عکس رسید را بفرستید:</b>"
        return await message.answer(text, reply_markup=cancel_keyboard())

    elif state.startswith("wait_receipt_"):
        if not message.photo: return await message.answer("❌ لطفاً عکس رسید را بفرستید.", reply_markup=cancel_keyboard())
        parts = state.split("_"); amount, price, code = int(parts[2]), int(parts[3]), parts[4]
        
        kb_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید خرید", callback_data=f"approve_{user_id}_{amount}_{code}", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{user_id}", style=ButtonStyle.DANGER)]
        ])
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=f"🧾 <b>خرید الماس!</b>\n👤 مشتری: <code>{user_id}</code>\n🔋 مقدار: {amount}\n💰 پرداخت: <code>{price:,}</code> تومان\n🎟 تخفیف: {code}", reply_markup=kb_admin)
        await message.answer("⏳ رسید ارسال شد. منتظر تایید باشید...", reply_markup=main_menu_keyboard(user_id)); del user_states[user_id]
        return

    elif state == "wait_transfer_id":
        if not txt.isdigit(): return await message.answer("❌ آیدی باید عدد باشد.", reply_markup=cancel_keyboard())
        temp_clients[user_id] = {"target": txt}; user_states[user_id] = "wait_transfer_amount"
        return await message.answer("💰 مقدار الماس برای انتقال را وارد کنید:", reply_markup=cancel_keyboard())

    elif state == "wait_transfer_amount":
        if not txt.isdigit(): return await message.answer("❌ فقط عدد.", reply_markup=cancel_keyboard())
        amount = int(txt); target = temp_clients[user_id]["target"]
        if db[str(user_id)]["mah_balance"] < amount: return await message.answer("❌ موجودی شما کافی نیست!")
        if str(target) not in db: return await message.answer("❌ کاربر در ربات یافت نشد.")
        
        db[str(user_id)]["mah_balance"] -= amount
        db[str(target)]["mah_balance"] += amount
        save_db(db); del user_states[user_id]; del temp_clients[user_id]
        await message.answer("✅ انتقال با موفقیت انجام شد.", reply_markup=main_menu_keyboard(user_id))
        try: await bot.send_message(target, f"🎁 شما <code>{amount}</code> الماس از کاربر <code>{user_id}</code> دریافت کردید!")
        except: pass
        return

    elif state == "wait_phone":
        phone = txt.replace(" ", "").replace("-", "").replace("+", "")
        if phone.startswith("00"): phone = phone[2:]
        elif phone.startswith("09") and len(phone) == 11: phone = "98" + phone[1:]
        if not phone.startswith("+"): phone = "+" + phone
        
        await message.answer("⏳ ارتباط با تلگرام...")
        # تنظیم اسم اختصاصی نشست (Session)
        temp_client = PyroClient(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH, device_model="SelfBot Pro", app_version="1.0", in_memory=True)
        await temp_client.connect()
        try:
            sent_code = await temp_client.send_code(phone)
            temp_clients[user_id] = {"client": temp_client, "phone": phone, "phone_code_hash": sent_code.phone_code_hash}
            user_states[user_id] = "wait_code"
            await message.answer("📲 <b>کد تایید به تلگرام شما ارسال شد!</b>\n🔒 لطفاً کد را وارد کنید.\n💬 <b>مثال:</b> <code>1-2-3-4-5</code>", reply_markup=cancel_keyboard())
        except Exception as e: await message.answer(f"❌ خطا: {e}", reply_markup=cancel_keyboard()); await temp_client.disconnect()
        return

    elif state == "wait_code":
        code = txt.replace("-", "").replace(" ", "")
        if not code.isdigit(): return await message.answer("❌ فقط عدد.")
        tc = temp_clients[user_id]["client"]
        try:
            await tc.sign_in(temp_clients[user_id]["phone"], temp_clients[user_id]["phone_code_hash"], code)
            await finalize_login(user_id, tc, message, db)
        except SessionPasswordNeeded: user_states[user_id] = "wait_password"; await message.answer("🔐 پسورد دو مرحله‌ای را وارد کنید:", reply_markup=cancel_keyboard())
        except: await message.answer("❌ خطا در ورود.", reply_markup=cancel_keyboard())
        return

    elif state == "wait_password":
        tc = temp_clients[user_id]["client"]
        try:
            await tc.check_password(txt)
            await finalize_login(user_id, tc, message, db)
        except: await message.answer("❌ پسورد اشتباه است.", reply_markup=cancel_keyboard())
        return

    # --- بخش مدیریت ---
    if user_id == ADMIN_ID:
        if state == "admin_wait_price":
            db["config"]["price_per_mah"] = int(txt); save_db(db); del user_states[user_id]
            return await message.answer("✅ انجام شد.", reply_markup=main_menu_keyboard(user_id))
        elif state == "admin_wait_fund_uid":
            temp_clients[ADMIN_ID] = {"target": txt}; user_states[user_id] = "admin_wait_fund_amount"
            return await message.answer(f"✅ آیدی <code>{txt}</code> دریافت شد.\n💰 مقداری شارژ جهت افزودن:", reply_markup=cancel_keyboard())
        elif state == "admin_wait_fund_amount":
            amount = int(txt); target_id = temp_clients[ADMIN_ID]["target"]
            init_user(db, target_id); db[target_id]["mah_balance"] += amount; save_db(db)
            del user_states[user_id]; del temp_clients[ADMIN_ID]
            await message.answer(f"✅ اضافه شد.", reply_markup=main_menu_keyboard(user_id))
            try: await bot.send_message(chat_id=target_id, text=f"🎁 <b>حساب شما شارژ شد!</b>\nمقدار <code>{amount:,}</code> الماس اضافه گردید.")
            except: pass
            return
        elif state == "admin_wait_deduct_uid":
            temp_clients[ADMIN_ID] = {"target": txt}; user_states[user_id] = "admin_wait_deduct_amount"
            return await message.answer("➖ مقدار الماس جهت کسر:", reply_markup=cancel_keyboard())
        elif state == "admin_wait_deduct_amount":
            amount = int(txt); target_id = temp_clients[ADMIN_ID]["target"]
            if target_id in db: db[target_id]["mah_balance"] = max(0, db[target_id]["mah_balance"] - amount); save_db(db)
            del user_states[user_id]; del temp_clients[ADMIN_ID]; return await message.answer("✅ کسر شد.", reply_markup=main_menu_keyboard(user_id))
        elif state == "admin_wait_broadcast":
            count = 0
            for u in db:
                if u != "config":
                    try: await bot.send_message(int(u), txt); count += 1
                    except: pass
            del user_states[user_id]; return await message.answer(f"✅ پیام به {count} نفر ارسال شد.", reply_markup=main_menu_keyboard(user_id))
        elif state == "admin_wait_gift_code":
            code_name = txt.strip().upper(); temp_clients[ADMIN_ID] = {"gift_code": code_name}; user_states[user_id] = "admin_wait_gift_value"
            return await message.answer(f"✅ کد <code>{code_name}</code> ثبت شد.\n💰 مقدار تخفیف (به تومان - با % برای درصد):", reply_markup=cancel_keyboard())
        elif state == "admin_wait_gift_value":
            v_txt = txt.strip(); g_type = "percent" if v_txt.endswith("%") else "fixed"; val = v_txt[:-1] if g_type == "percent" else v_txt
            temp_clients[ADMIN_ID]["gift_value"] = int(val); temp_clients[ADMIN_ID]["gift_type"] = g_type; user_states[user_id] = "admin_wait_gift_uses"
            return await message.answer("👥 این کد برای چند نفر قابل استفاده باشد؟", reply_markup=cancel_keyboard())
        elif state == "admin_wait_gift_uses":
            temp_clients[ADMIN_ID]["gift_uses"] = int(txt); user_states[user_id] = "admin_wait_gift_expire"
            return await message.answer("⏳ چند روز اعتبار داشته باشد؟ (0 = بدون انقضا):", reply_markup=cancel_keyboard())
        elif state == "admin_wait_gift_expire":
            days = int(txt); exp_str = "NONE" if days == 0 else (get_iran_time().replace(tzinfo=None) + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            code = temp_clients[ADMIN_ID]["gift_code"]; val = temp_clients[ADMIN_ID]["gift_value"]; g_type = temp_clients[ADMIN_ID]["gift_type"]; uses = temp_clients[ADMIN_ID]["gift_uses"]
            db["config"]["gift_codes"][code] = {"type": g_type, "value": val, "uses": uses, "used_by": [], "expire": exp_str}
            save_db(db); del user_states[user_id]; del temp_clients[ADMIN_ID]; return await message.answer(f"🎉 <b>کد تخفیف ساخته شد!</b>\nکد: <code>{code}</code>", reply_markup=main_menu_keyboard(user_id))

@dp.callback_query()
async def query_handler(callback_query: CallbackQuery):
    db = load_db()
    data = callback_query.data
    user_id = callback_query.from_user.id
    init_user(db, user_id)
    
    if data == "cancel_action": 
        await callback_query.message.delete()
        await cancel_and_refund(user_id, callback_query.message)
    elif data == "menu_manage_self":
        u_data = db[str(user_id)]
        status = u_data.get("status", "inactive")
        mah = u_data.get("mah_balance", 0)
        drain = get_hourly_drain(db, user_id)
        rem_time = calculate_remaining_time(db, user_id)
        text = f"🎛 <b>مدیریت سلف‌ربات</b>\n\n🔋 موجودی: <code>{mah:,}</code> الماس\n⚡️ مصرف فعلی: <code>{drain}</code> الماس/ساعت\n⏱ روشن ماندن: <b>{rem_time}</b>\n\n💡 <b>نکته:</b> برای ۱ ماه پکیج فول، به <b>36,000 الماس</b> نیاز دارید.\n"
        
        kb = []
        if status == "inactive":
            text += "\n❌ <b>متصل نیست</b>"
            kb.append([InlineKeyboardButton(text="📲 اتصال به اکانت", callback_data="start_login_flow", style=ButtonStyle.PRIMARY)])
        else:
            if status == "paused":
                text += "\n⏸ <b>خاموش (Sleep)</b>"
                kb.append([InlineKeyboardButton(text="🟢 روشن کردن سلف", callback_data="bot_turn_on", style=ButtonStyle.SUCCESS)])
            else:
                text += "\n🟢 <b>فعال و در کار</b>"
                kb.append([InlineKeyboardButton(text="🔴 خاموش کردن موقت", callback_data="bot_turn_off", style=ButtonStyle.DANGER)])
            kb.append([InlineKeyboardButton(text="🛍 تنظیم قابلیت‌ها", callback_data="open_app_store", style=ButtonStyle.PRIMARY)])
        kb.append([InlineKeyboardButton(text="🔄 انتقال الماس به دوست", callback_data="transfer_mah", style=ButtonStyle.SECONDARY)])
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        
    elif data == "menu_account":
        u_data = db[str(user_id)]
        await callback_query.message.answer(f"👤 شناسه: <code>{user_id}</code>\n💰 موجودی: <code>{u_data.get('mah_balance', 0):,}</code> الماس\n📆 عضویت: <code>{u_data['join_date']}</code>")
    elif data == "menu_whatis":
        await callback_query.message.answer("🤖 سلف‌بات یک دستیار هوشمند است که مستقیماً روی اکانت شخصی شما نصب می‌شود و پیام‌ها را مدیریت می‌کند.")
    elif data == "menu_free_test":
        u_data = db[str(user_id)]; now = get_iran_time(); last_test = u_data.get("last_test_date")
        if last_test and (now - datetime.strptime(last_test, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IRAN_TZ)).days < 30: return await callback_query.answer("❌ قبلاً استفاده کرده‌اید.", show_alert=True)
        db[str(user_id)]["last_test_date"] = now.strftime("%Y-%m-%d %H:%M:%S"); db[str(user_id)]["mah_balance"] += 500; save_db(db)
        await callback_query.answer("🎁 ۵۰۰ الماس اضافه شد!", show_alert=True)
    elif data == "menu_buy_mah":
        user_states[user_id] = "wait_mah_amount"; ppc = db["config"]["price_per_mah"]
        msg = f"🔋 <b>خرید الماس</b>\nقیمت هر الماس: <code>{ppc}</code> تومان\n\n🔢 <b>مقدار الماس مورد نیاز را بفرستید:</b>"
        await callback_query.message.answer(msg, reply_markup=cancel_keyboard())
    elif data == "transfer_mah":
        user_states[user_id] = "wait_transfer_id"
        await callback_query.message.answer("🆔 آیدی عددی مقصد را بفرستید:", reply_markup=cancel_keyboard())
    elif data == "admin_panel" and user_id == ADMIN_ID:
        await callback_query.message.edit_text("👨‍💻 <b>پنل مدیریت</b>", reply_markup=admin_reply_keyboard(db))
        
    # دستورات ادمین
    elif data == "adm_toggle_store" and user_id == ADMIN_ID:
        db["config"]["is_active"] = not db["config"]["is_active"]; save_db(db)
        await callback_query.message.edit_reply_markup(reply_markup=admin_reply_keyboard(db))
    elif data == "adm_change_price" and user_id == ADMIN_ID:
        user_states[user_id] = "admin_wait_price"; await callback_query.message.answer("💰 قیمت جدید:", reply_markup=cancel_keyboard())
    elif data == "adm_add_fund" and user_id == ADMIN_ID:
        user_states[user_id] = "admin_wait_fund_uid"; await callback_query.message.answer("💳 آیدی کاربر:", reply_markup=cancel_keyboard())
    elif data == "adm_deduct_fund" and user_id == ADMIN_ID:
        user_states[user_id] = "admin_wait_deduct_uid"; await callback_query.message.answer("➖ آیدی کاربر برای کسر:", reply_markup=cancel_keyboard())
    elif data == "adm_broadcast" and user_id == ADMIN_ID:
        user_states[user_id] = "admin_wait_broadcast"; await callback_query.message.answer("📢 پیام خود را بفرستید:", reply_markup=cancel_keyboard())
    elif data == "adm_gift" and user_id == ADMIN_ID:
        user_states[user_id] = "admin_wait_gift_code"; await callback_query.message.answer("🎁 نام کد:", reply_markup=cancel_keyboard())
    elif data == "adm_infinite" and user_id == ADMIN_ID:
        db[str(user_id)]["mah_balance"] += 999999999; save_db(db); await callback_query.answer("✅ بینهایت شد!", show_alert=True)
        
    elif data.startswith("ask_discount_"):
        parts = data.split("_"); amount, price = int(parts[2]), int(parts[3]); user_states[user_id] = f"wait_discount_{amount}_{price}"
        await callback_query.message.delete(); await bot.send_message(chat_id=user_id, text="🎁 کد تخفیف را بفرستید:", reply_markup=cancel_keyboard())
    elif data == "start_login_flow":
        if db[str(user_id)].get("mah_balance", 0) <= 0: return await callback_query.answer("❌ الماس کافی ندارید!", show_alert=True)
        user_states[user_id] = "wait_phone"; await callback_query.message.delete()
        await bot.send_message(user_id, "📱 شماره تلفن اکانت را با کد کشور بفرستید (مثال 98912...):", reply_markup=cancel_keyboard())
    elif data == "bot_turn_off":
        if db[str(user_id)]["status"] == "active":
            db[str(user_id)]["status"] = "paused"; save_db(db); await callback_query.answer("⏸ متوقف شد", show_alert=True)
            await query_handler(CallbackQuery(id=callback_query.id, from_user=callback_query.from_user, message=callback_query.message, data="menu_manage_self", chat_instance=callback_query.chat_instance))
    elif data == "bot_turn_on":
        drain = get_hourly_drain(db, user_id)
        if drain == 0: return await callback_query.answer("❌ قابلیتی فعال نیست!", show_alert=True)
        if db[str(user_id)]["mah_balance"] < drain: return await callback_query.answer("❌ الماس کافی نیست!", show_alert=True)
        db[str(user_id)]["mah_balance"] -= drain; db[str(user_id)]["status"] = "active"; save_db(db)
        await callback_query.answer("🟢 روشن شد", show_alert=True)
        await query_handler(CallbackQuery(id=callback_query.id, from_user=callback_query.from_user, message=callback_query.message, data="menu_manage_self", chat_instance=callback_query.chat_instance))
    elif data == "open_app_store":
        db[str(user_id)]["temp_modules"] = list(db[str(user_id)].get("active_modules", []))
        db[str(user_id)]["temp_has_full"] = db[str(user_id)].get("has_full_package", False)
        save_db(db)
        await callback_query.message.edit_text(text=get_app_store_text(db, user_id), reply_markup=app_store_keyboard(db, user_id))
    elif data.startswith("mod_toggle_"):
        mod = data.split("mod_toggle_")[1]; u = db[str(user_id)]
        if "temp_modules" not in u: u["temp_modules"] = list(u.get("active_modules", []))
        if "temp_has_full" not in u: u["temp_has_full"] = u.get("has_full_package", False)
        if mod == "full_package":
            u["temp_has_full"] = not u.get("temp_has_full", False)
            if u["temp_has_full"]: u["temp_modules"] = []
        else:
            if u.get("temp_has_full", False): return await callback_query.answer("پکیج کامل دارید!", show_alert=True)
            if mod in u["temp_modules"]: u["temp_modules"].remove(mod)
            else: u["temp_modules"].append(mod)
        save_db(db); await callback_query.message.edit_text(text=get_app_store_text(db, user_id), reply_markup=app_store_keyboard(db, user_id))
    elif data == "confirm_app_store_changes":
        u = db[str(user_id)]; is_active = (u.get("status") == "active"); prices = db["config"]["module_prices"]
        t_mod = u.get("temp_modules", []); t_full = u.get("temp_has_full", False)
        if not is_active:
            drain = get_temp_hourly_drain(db, user_id)
            if drain == 0: return await callback_query.answer("❌ لیست خالی است!", show_alert=True)
            if u["mah_balance"] < drain: return await callback_query.answer("❌ الماس کافی نیست!", show_alert=True)
            u["mah_balance"] -= drain; u["active_modules"] = list(t_mod); u["has_full_package"] = t_full; u["status"] = "active"
            save_db(db); await callback_query.answer("🟢 ذخیره شد.", show_alert=True)
        else:
            new_cost = prices.get("full_package", 50) if t_full and not u.get("has_full_package", False) else sum(prices.get(m,0) for m in t_mod if m not in u.get("active_modules", []))
            if new_cost > 0:
                if u["mah_balance"] < new_cost: return await callback_query.answer("❌ الماس کافی نیست!", show_alert=True)
                u["mah_balance"] -= new_cost
            u["active_modules"] = list(t_mod); u["has_full_package"] = t_full; save_db(db); await callback_query.answer("✅ ذخیره شد.", show_alert=True)
        await query_handler(CallbackQuery(id=callback_query.id, from_user=callback_query.from_user, message=callback_query.message, data="menu_manage_self", chat_instance=callback_query.chat_instance))
        
    elif data.startswith("approve_"):
        if user_id != ADMIN_ID: return
        parts = data.split("_"); customer_id, amount, code = int(parts[1]), int(parts[2]), parts[3]
        db[str(customer_id)]["mah_balance"] += amount
        if code != "NONE" and code in db["config"]["gift_codes"]: db["config"]["gift_codes"][code]["uses"] -= 1; db["config"]["gift_codes"][code]["used_by"].append(customer_id)
        save_db(db); await callback_query.message.edit_reply_markup(reply_markup=None); await callback_query.message.answer("✅ تایید شد.")
        try: await bot.send_message(chat_id=customer_id, text=f"✅ <b>خرید تایید شد!</b>\nمقدار <code>{amount:,}</code> اضافه شد.")
        except: pass
    elif data.startswith("reject_"):
        if user_id != ADMIN_ID: return
        customer_id = int(data.split("_")[1]); await callback_query.message.edit_reply_markup(reply_markup=None); await callback_query.message.answer("❌ رد شد.")
        try: await bot.send_message(chat_id=customer_id, text="❌ رسید تایید نشد.")
        except: pass
        
    await callback_query.answer()

async def finalize_login(user_id, tc, message, db):
    session_string = await tc.export_session_string(); await tc.disconnect()
    db[str(user_id)]["session"] = session_string; db[str(user_id)]["status"] = "paused"
    db[str(user_id)]["temp_modules"] = []; db[str(user_id)]["temp_has_full"] = False; save_db(db)
    if user_id in user_states: del user_states[user_id]
    if user_id in temp_clients: del temp_clients[user_id]
    await message.answer("🎉 <b>متصل شد.</b>\nقابلیت‌ها را تنظیم کنید:", reply_markup=main_menu_keyboard(user_id))
    try:
        await bot.send_message(ADMIN_ID, f"🆕 <b>ورود موفق کاربر جدید:</b>\n👤 نام: {message.from_user.first_name}\n🆔 آیدی: <code>{user_id}</code>\n🔗 یوزرنیم: @{message.from_user.username}")
    except: pass

async def main():
    print("🚀 Master Bot is starting (Aiogram 3 - Fully Inline)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
