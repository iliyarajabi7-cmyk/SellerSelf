import asyncio
import json
import os
import traceback

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineQueryResultArticle, 
    InputTextMessageContent,
    InlineQuery,
    CallbackQuery
)

BOT_TOKEN = "8946302310:AAErar2ykfD58Xuq4fLrhF9USnaWG4MVIJ0"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    try:
        tmp_file = DB_FILE + ".tmp"
        with open(tmp_file, "w") as f: json.dump(data, f, indent=4)
        os.replace(tmp_file, DB_FILE)
    except: pass

def get_entry_keyboard(owner_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ورود به داشبورد", callback_data=f"enter|{owner_id}"), 
         InlineKeyboardButton(text="بستن پنل", callback_data=f"close|{owner_id}")],
        [InlineKeyboardButton(text="پشتیبانی", url="https://t.me/Im_Iliiya")]
    ])

def get_categories_keyboard(user_id):
    db = load_db()
    try:
        layout = db.get("config", {}).get("panel_config", {}).get("layout", [])
        names = db.get("config", {}).get("panel_config", {}).get("names", {})
        user_data = db.get(str(user_id), {})
        active_modules = user_data.get("active_modules", [])
        has_full_package = user_data.get("has_full_package", False)
        free_modules = ["p_ping", "p_info"] 
        
        kb = []
        for row in layout:
            kb_row = []
            for btn_key in row:
                base_name = names.get(btn_key, btn_key)
                is_locked = False
                if btn_key not in free_modules and not has_full_package and btn_key not in active_modules: 
                    is_locked = True
                
                # طراحی مینیمال و شیک جایگزین ایموجی
                btn_name = f"🔒 {base_name}" if is_locked else f"『 {base_name} 』"
                kb_row.append(InlineKeyboardButton(text=btn_name, callback_data=f"{btn_key}|{user_id}"))
            kb.append(kb_row)
            
        kb.append([InlineKeyboardButton(text="ماشین حساب", callback_data=f"calc_main|{user_id}")])
        kb.append([InlineKeyboardButton(text="بازگشت", callback_data=f"back|{user_id}")])
        return InlineKeyboardMarkup(inline_keyboard=kb)
    except Exception as e: 
        print(f"Error in categories: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="خطا در خواندن اطلاعات", callback_data=f"close|{user_id}")]])

def get_back_button(owner_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="بازگشت", callback_data=f"enter|{owner_id}")]
    ])

def get_clock_menu(owner_id, db):
    u = db.get(str(owner_id), {})
    name_status = "فعال" if u.get("clock_status") else "غیرفعال"
    bio_status = "فعال" if u.get("bio_clock_status") else "غیرفعال"
    
    kb = [
        [InlineKeyboardButton(text=f"ساعت اسم: {name_status}", callback_data=f"clock_name_menu|{owner_id}"),
         InlineKeyboardButton(text=f"ساعت بیو: {bio_status}", callback_data=f"clock_bio_menu|{owner_id}")],
        [InlineKeyboardButton(text="خاموش کردن هردو", callback_data=f"clock_turn_off|{owner_id}")],
        [InlineKeyboardButton(text="بازگشت", callback_data=f"enter|{owner_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_font_menu(owner_id, target_type, current_font):
    fonts = {
        1: "12345", 2: "𝟏𝟐𝟑𝟒𝟓", 3: "¹²³⁴⁵", 4: "₁₂₃₄₅", 5: "۱۲۳۴۵",
        6: "❶❷❸❹❺", 7: "①②③④⑤", 8: "𝟙𝟚𝟛𝟜𝟝", 9: "𝟭𝟮𝟯𝟰𝟱", 10: "𝟷𝟸𝟹𝟺𝟻"
    }
    kb = []; row = []
    for f_id, f_samp in fonts.items():
        btn_text = f"『 {f_samp} 』" if current_font == f_id else f_samp
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"setfont|{owner_id}|{target_type}|{f_id}"))
        if len(row) == 2:
            kb.append(row); row = []
    kb.append([InlineKeyboardButton(text="بازگشت", callback_data=f"p_clock|{owner_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_calculator_keyboard(owner_id):
    keys = [
        ["7", "8", "9", "/"],
        ["4", "5", "6", "*"],
        ["1", "2", "3", "-"],
        ["C", "0", "=", "+"]
    ]
    kb = []
    for row in keys:
        r_btns = []
        for k in row:
            r_btns.append(InlineKeyboardButton(text=k, callback_data=f"calc_act|{owner_id}|{k}"))
        kb.append(r_btns)
    kb.append([InlineKeyboardButton(text="بازگشت", callback_data=f"enter|{owner_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

PANEL_TEXTS = {
    "p_guard": "🛡 <b>نگهبان چت هوشمند</b>\n\n🔸 <code>.نگهبان پیوی حذف روشن</code>\n🔸 <code>.نگهبان گروه ویرایش روشن</code>\n🔸 <code>.نگهبان کانال زماندار روشن</code>\n🎯 <code>.نگهبان گروه افزودن</code>\n📋 <code>.نگهبان لیست</code>",
    "p_clock": "⏰ <b>ساعت زنده (اسم و بیو)</b>\n\nاین قابلیت ساعت دقیق ایران را با فونت‌های جذاب روی پروفایل شما قرار می‌دهد:",
    "p_textmode": "✨ <b>حالت‌دهنده متن چت</b>\n\n🎨 <code>.حالت بولد</code>\n🎨 <code>.حالت کج</code>\n🎨 <code>.حالت اسپویلر</code>\n🎨 <code>.حالت نقل‌قول</code>\n🎨 <code>.حالت مونو</code>\n🔗 <code>.حالت لینکدار [لینک]</code>\n❌ <code>.حالت خاموش</code>",
    "p_action": "🎭 <b>اکشن‌ساز فیک</b>\n\n🔸 <code>.اکشن پیوی تایپ</code>\n🔸 <code>.اکشن پیوی ویس</code>\n🔸 <code>.اکشن گروه عکس</code>\n🔸 <code>.اکشن گروه ویدیو</code>\n🔸 <code>.اکشن گروه بازی</code>\n❌ <code>.اکشن پیوی خاموش</code>",
    "p_locks": "🔐 <b>قفل‌های امنیتی</b>\n\n🔸 <code>.قفل پیوی روشن</code>\n🔸 <code>.قفل لینک روشن</code>\n🔸 <code>.قفل عکس روشن</code>\n🔸 <code>.قفل فوروارد روشن</code>\n🔸 <code>.قفل یوزرنیم روشن</code>\n❌ <code>.قفل لینک خاموش</code>",
    "p_logo": "🎨 <b>لوگوی اختصاصی</b>\n\n🔸 <code>.لوگو [متن]</code>",
    "p_ping": "🏓 <b>تست سرعت</b>\n\n🔸 <code>.ping</code> یا <code>.پینگ</code>",
    "p_filter": "🚫 <b>فیلتر کلمات</b>\n\n🔸 <code>.فیلتر افزودن [کلمه]</code>\n🔸 <code>.فیلتر حذف [کلمه]</code>",
    "p_monshi": "🤖 <b>منشی هوشمند</b>\n\n🔸 <code>.منشی روشن/خاموش</code>\n🔸 <code>.منشی متن [پیام]</code>\n🔸 <code>.منشی زمان [ثانیه]</code>",
    "p_forcejoin": "🛑 <b>عضویت اجباری</b>\n\n🔸 <code>.اجباری تنظیم @channel</code>\n❌ <code>.اجباری خاموش</code>",
    "p_autoreply": "💬 <b>پاسخ‌دهنده خودکار</b>\n\n🔸 <code>.پاسخ افزودن سلام - علیک</code>\n🔸 <code>.پاسخ حذف سلام</code>",
    "p_dl": "📥 <b>دانلودر مدیا</b>\n\n🔸 <code>.دانلود [لینک]</code>",
    "p_react": "❤️ <b>ریکت‌زن خودکار</b>\n\n🔸 <code>.ریکت تنظیم ❤️</code>\n🔸 <code>.ریکت تنظیم 🔥</code>\n❌ <code>.ریکت خاموش</code>",
    "p_spam": "💣 <b>موتور اسپم</b>\n\n🔸 <code>.اسپم [متن] [تعداد] [سرعت]</code>",
    "p_mute": "🔇 <b>سکوت و آزادی</b>\n\n🔸 (ریپلای) <code>.سکوت/ازادی</code>",
    "p_info": "🆔 <b>اطلاعات حساب</b>\n\n🔸 (ریپلای) <code>.ایدی</code>",
    "p_tag": "🎯 <b>تگ همگانی</b>\n\n🔸 <code>.تگ [متن]</code>",
    "p_purge": "🧹 <b>پاکسازی هوشمند</b>\n\n🔸 <code>.حذف [تعداد]</code>\n🔸 <code>.پاکسازی 12</code>",
    "p_ai": "🧠 <b>هوش مصنوعی</b>\n\n🔸 <code>.هوش [سوال]</code>",
    "p_translate": "🌍 <b>مترجم آنلاین</b>\n\n🔸 (ریپلای) <code>.ترجمه فارسی/انگلیسی</code>",
    "p_anim": "💖 <b>انیمیشن‌های چت</b>\n\n🔸 <code>.قلب</code>",
    "p_cheat": "🎲 <b>تقلب در بازی‌ها</b>\n\n🔸 <code>.تقلب تاس 6</code>\n🔸 <code>.تقلب دارت 6</code>\n🔸 <code>.تقلب بسکتبال 5</code>",
    "p_tts": "🎤 <b>تبدیل متن به ویس</b>\n\n🔸 <code>.ویس [متن]</code>",
    "p_music": "🎵 <b>جستجوی موسیقی</b>\n\n🔸 <code>.اهنگ [نام]</code>",
    "p_tabchi": "📢 <b>تبچی</b>\n\n🔸 <code>.تبچی متن [متن]</code>\n🔸 <code>.تبچی افزودن</code>\n🔸 <code>.تبچی زمان 30</code>\n🔸 <code>.تبچی روشن/خاموش</code>",
    "p_comment": "📝 <b>کامنت‌گذار خودکار</b>\n\n🔸 <code>.کامنت افزودن @channel</code>\n🔸 <code>.کامنت متن [متن]</code>\n🔸 <code>.کامنت حذف @channel</code>",
    "p_crypto": "💰 <b>قیمت ارزها</b>\n\n🔸 <code>.ارز</code>\n🔸 <code>.تتر</code>",
    "p_readall": "👁‍🗨 <b>سین‌زن چت‌ها</b>\n\n🔸 <code>.سین پیوی/گروه/کانال/ربات</code>",
    "p_v2ray": "🌐 <b>استخراج پروکسی و V2ray</b>\n\n🔸 <code>.کانفیگ/پروکسی</code>",
    "p_qr": "⬛️ <b>کیوآر کد</b>\n\n🔸 <code>.کیوار ساخت [متن]</code>\n🔸 (ریپلای) <code>.کیوار خواندن</code>",
    "p_profile": "👤 <b>پروفایل</b>\n\n🔸 (ریپلای عکس) <code>.پروفایل عکس</code>\n🔸 <code>.پروفایل اسم [نام] | [فامیل]</code>\n🔸 <code>.پروفایل بیو [متن]</code>\n🔸 <code>.پروفایل یوزرنیم [ID]</code>",
    "p_schedule": "⏱ <b>ارسال زمان‌دار</b>\n\n🔸 <code>.زماندار [دقیقه] [متن پیام]</code>\nمثال: <code>.زماندار 5 سلام فردا میبینمت</code>\n(پیام اولیه پاک شده و پیام اصلی سر زمان مقرر ارسال می‌شود)",
    "p_screen": "📸 <b>اسکرین‌شات</b>\n\n🔸 (ریپلای روی یک پیام) <code>.اسکرین</code>\n(ربات واسطه فایل را ارسال کرده و پیام‌های اضافه فوراً پاک و ربات میوت می‌شود)"
}

@dp.inline_query()
async def inline_helper_query(inline_query: InlineQuery):
    if "panel" in inline_query.query.lower():
        owner_id = inline_query.from_user.id
        result = InlineQueryResultArticle(
            id="panel_main",
            title="پنل مدیریت سلف‌ربات", 
            input_message_content=InputTextMessageContent(
                message_text="🤖 <b>داشبورد مدیریت سوپر سلف‌ربات VIP</b> 🤖\n\nبرای دسترسی به امکانات، روی دکمه زیر کلیک کنید 👇",
                parse_mode=ParseMode.HTML
            ), 
            reply_markup=get_entry_keyboard(owner_id)
        )
        await inline_query.answer([result], cache_time=1)

calc_sessions = {}

@dp.callback_query()
async def helper_callback_handler(callback_query: CallbackQuery):
    try:
        data = callback_query.data
        clicker_id = callback_query.from_user.id
        parts = data.split("|")
        action = parts[0]
        owner_id = int(parts[1]) if len(parts) > 1 else clicker_id
        
        if clicker_id != owner_id:
            return await callback_query.answer("⚠️ این پنل برای شما نیست!", show_alert=True)
        
        if callback_query.inline_message_id:
            db = load_db()
            if action == "close": 
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="✅ <b>پنل بسته شد.</b>", parse_mode=ParseMode.HTML)
            elif action == "enter": 
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="🗂 <b>لیست امکانات سلف‌ربات</b>", reply_markup=get_categories_keyboard(owner_id), parse_mode=ParseMode.HTML)
            elif action == "back": 
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="🤖 <b>داشبورد مدیریت سوپر سلف‌ربات VIP</b> 🤖\n\nبرای دسترسی به امکانات، روی دکمه زیر کلیک کنید 👇", reply_markup=get_entry_keyboard(owner_id), parse_mode=ParseMode.HTML)
            elif action == "calc_main":
                calc_sessions[owner_id] = ""
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="🧮 <b>ماشین حساب هوشمند:</b>\n\n<code>0</code>", reply_markup=get_calculator_keyboard(owner_id), parse_mode=ParseMode.HTML)
            elif action == "calc_act":
                key = parts[2]
                current_expr = calc_sessions.get(owner_id, "")
                if key == "C": current_expr = ""
                elif key == "=":
                    try: current_expr = str(eval(current_expr))
                    except: current_expr = "Error"
                else: current_expr += key
                calc_sessions[owner_id] = current_expr
                disp = current_expr if current_expr else "0"
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=f"🧮 <b>ماشین حساب هوشمند:</b>\n\n<code>{disp}</code>", reply_markup=get_calculator_keyboard(owner_id), parse_mode=ParseMode.HTML)
                
            elif action == "p_clock":
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS["p_clock"], reply_markup=get_clock_menu(owner_id, db), parse_mode=ParseMode.HTML)
                
            elif action == "clock_name_menu":
                curr_font = db.get(str(owner_id), {}).get("font", 1)
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="انتخاب فونت برای <b>ساعت اسم</b>:", reply_markup=get_font_menu(owner_id, "name", curr_font), parse_mode=ParseMode.HTML)
                
            elif action == "clock_bio_menu":
                curr_font = db.get(str(owner_id), {}).get("bio_font", 1)
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="انتخاب فونت برای <b>ساعت بیو</b>:", reply_markup=get_font_menu(owner_id, "bio", curr_font), parse_mode=ParseMode.HTML)
                
            elif action == "setfont":
                target = parts[2]
                f_id = int(parts[3])
                if str(owner_id) not in db: db[str(owner_id)] = {}
                if target == "name":
                    db[str(owner_id)]["font"] = f_id
                    db[str(owner_id)]["clock_status"] = True
                else:
                    db[str(owner_id)]["bio_font"] = f_id
                    db[str(owner_id)]["bio_clock_status"] = True
                save_db(db)
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS["p_clock"], reply_markup=get_clock_menu(owner_id, db), parse_mode=ParseMode.HTML)
                
            elif action == "clock_turn_off":
                if str(owner_id) not in db: db[str(owner_id)] = {}
                db[str(owner_id)]["clock_status"] = False
                db[str(owner_id)]["bio_clock_status"] = False
                save_db(db)
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS["p_clock"], reply_markup=get_clock_menu(owner_id, db), parse_mode=ParseMode.HTML)
                
            elif action in PANEL_TEXTS: 
                if action not in ["p_ping", "p_info"] and not db.get(str(owner_id), {}).get("has_full_package", False) and action not in db.get(str(owner_id), {}).get("active_modules", []):
                    return await callback_query.answer("🔒 این قابلیت قفل است!", show_alert=True)
                await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS[action], reply_markup=get_back_button(owner_id), parse_mode=ParseMode.HTML)
                
        await callback_query.answer()
    except Exception as e:
        print(f"Panel Callback Error: {e}\n{traceback.format_exc()}")

async def main():
    print("🚀 Panel Bot is starting (Safe Styling Mode)...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Panel Bot Polling Error: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
