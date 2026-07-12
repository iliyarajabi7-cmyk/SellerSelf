import asyncio
import json
import os
import traceback
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ButtonStyle
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent, InlineQuery, CallbackQuery

API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
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
        [InlineKeyboardButton(text="🎯 ورود به داشبورد", callback_data=f"enter|{owner_id}", style=ButtonStyle.SUCCESS), 
         InlineKeyboardButton(text="❌ بستن پنل", callback_data=f"close|{owner_id}", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text="📞 پشتیبانی", url="https://t.me/Im_Iliiya", style=ButtonStyle.PRIMARY)]
    ])

def get_categories_keyboard(user_id):
    db = load_db()
    layout = db.get("config", {}).get("panel_config", {}).get("layout", [])
    names = db.get("config", {}).get("panel_config", {}).get("names", {})
    user_data = db.get(str(user_id), {})
    active_modules = user_data.get("active_modules", [])
    has_full_package = user_data.get("has_full_package", False)
    free_modules = ["p_ping", "p_info"] 
    kb = []
    for row_idx, row in enumerate(layout):
        kb_row = []
        row_color = ButtonStyle.PRIMARY if row_idx % 2 == 0 else ButtonStyle.SUCCESS
        for btn_key in row:
            btn_name = names.get(btn_key, btn_key)
            is_locked = False
            if btn_key not in free_modules and not has_full_package and btn_key not in active_modules: 
                btn_name = f"🔒 {btn_name}"; is_locked = True
            btn_style = ButtonStyle.DANGER if is_locked else row_color
            kb_row.append(InlineKeyboardButton(text=btn_name, callback_data=f"{btn_key}|{user_id}", style=btn_style))
        kb.append(kb_row)
    kb.append([InlineKeyboardButton(text="🧮 ماشین حساب", callback_data=f"calc_main|{user_id}", style=ButtonStyle.DANGER)])
    kb.append([InlineKeyboardButton(text="🔙 بازگشت به صفحه اصلی", callback_data=f"back|{user_id}", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_back_button(owner_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"enter|{owner_id}", style=ButtonStyle.PRIMARY)]
    ])

def get_clock_menu(owner_id, db):
    u = db.get(str(owner_id), {})
    name_status = "🟢" if u.get("clock_status") else "🔴"
    bio_status = "🟢" if u.get("bio_clock_status") else "🔴"
    kb = [
        [InlineKeyboardButton(text=f"{name_status} ساعت اسم", callback_data=f"clock_name_menu|{owner_id}", style=ButtonStyle.DANGER),
         InlineKeyboardButton(text=f"{bio_status} ساعت بیو", callback_data=f"clock_bio_menu|{owner_id}", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text="🔴 خاموش کردن هردو", callback_data=f"clock_turn_off|{owner_id}", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"enter|{owner_id}", style=ButtonStyle.PRIMARY)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_font_menu(owner_id, target_type, current_font):
    fonts = {1: "12345", 2: "𝟏𝟐𝟑𝟒𝟓", 3: "¹²³⁴⁵", 4: "₁₂₃₄₅", 5: "۱۲۳۴۵", 6: "❶❷❸❹❺", 7: "①②③④⑤", 8: "𝟙𝟚𝟛𝟜𝟝", 9: "𝟭𝟮𝟯𝟰𝟱", 10: "𝟷𝟸𝟹𝟺𝟻"}
    kb = []; row = []
    for f_id, f_samp in fonts.items():
        style = ButtonStyle.SUCCESS if current_font == f_id else ButtonStyle.PRIMARY
        row.append(InlineKeyboardButton(text=f_samp, callback_data=f"setfont|{owner_id}|{target_type}|{f_id}", style=style))
        if len(row) == 2: kb.append(row); row = []
    kb.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"p_clock|{owner_id}", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_calculator_keyboard(owner_id):
    keys = [["7", "8", "9", "/"], ["4", "5", "6", "*"], ["1", "2", "3", "-"], ["C", "0", "=", "+"]]
    kb = []
    for row in keys:
        r_btns = []
        for k in row:
            style = ButtonStyle.DANGER if k == "C" else ButtonStyle.SUCCESS if k in ["=", "+", "-", "*", "/"] else ButtonStyle.PRIMARY
            r_btns.append(InlineKeyboardButton(text=k, callback_data=f"calc_act|{owner_id}|{k}", style=style))
        kb.append(r_btns)
    kb.append([InlineKeyboardButton(text="🔙 بازگشت به پنل", callback_data=f"enter|{owner_id}", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

PANEL_TEXTS = {
    "p_guard": "🛡 <b>نگهبان چت هوشمند</b>\n🔸 <code>.نگهبان پیوی حذف روشن</code>\n🎯 <code>.نگهبان گروه افزودن</code>",
    "p_clock": "⏰ <b>ساعت زنده (اسم و بیو)</b>\nاین قابلیت ساعت دقیق ایران را با فونت‌های جذاب روی پروفایل شما قرار می‌دهد:",
    "p_textmode": "✨ <b>حالت‌دهنده متن چت</b>\n🎨 <code>.حالت بولد/کج/اسپویلر/مونو/نقل‌قول</code>\n🔗 <code>.حالت لینکدار [لینک]</code>\n❌ <code>.حالت خاموش</code>",
    "p_action": "🎭 <b>اکشن‌ساز فیک</b>\n🔸 <code>.اکشن پیوی تایپ/ویس</code>\n🔸 <code>.اکشن گروه عکس/ویدیو</code>",
    "p_locks": "🔐 <b>قفل‌های امنیتی</b>\n🔸 <code>.قفل پیوی روشن</code>\n🔸 <code>.قفل لینک/عکس/فوروارد/یوزرنیم روشن</code>",
    "p_logo": "🎨 <b>لوگوی اختصاصی</b>\n🔸 <code>.لوگو [متن]</code>",
    "p_ping": "🏓 <b>تست سرعت</b>\n🔸 <code>.ping</code>",
    "p_filter": "🚫 <b>فیلتر کلمات</b>\n🔸 <code>.فیلتر افزودن/حذف [کلمه]</code>",
    "p_monshi": "🤖 <b>منشی هوشمند</b>\n🔸 <code>.منشی روشن/خاموش</code>\n🔸 <code>.منشی متن [پیام]</code>\n🔸 <code>.منشی زمان [ثانیه]</code>",
    "p_forcejoin": "🛑 <b>عضویت اجباری</b>\n🔸 <code>.اجباری تنظیم @channel</code>\n❌ <code>.اجباری خاموش</code>",
    "p_autoreply": "💬 <b>پاسخ‌دهنده خودکار</b>\n🔸 <code>.پاسخ افزودن سلام - علیک</code>",
    "p_dl": "📥 <b>دانلودر مدیا</b>\n🔸 <code>.دانلود [لینک]</code>",
    "p_react": "❤️ <b>ریکت‌زن خودکار</b>\n🔸 <code>.ریکت تنظیم ❤️</code>",
    "p_spam": "💣 <b>موتور اسپم</b>\n🔸 <code>.اسپم [متن] [تعداد] [سرعت]</code>",
    "p_mute": "🔇 <b>سکوت و آزادی</b>\n🔸 (ریپلای) <code>.سکوت/ازادی</code>",
    "p_info": "🆔 <b>اطلاعات حساب</b>\n🔸 (ریپلای) <code>.ایدی</code>",
    "p_tag": "🎯 <b>تگ همگانی</b>\n🔸 <code>.تگ [متن]</code>",
    "p_purge": "🧹 <b>پاکسازی هوشمند</b>\n🔸 <code>.حذف [تعداد]</code>\n🔸 <code>.پاکسازی 12</code>",
    "p_ai": "🧠 <b>هوش مصنوعی</b>\n🔸 <code>.هوش [سوال]</code>",
    "p_translate": "🌍 <b>مترجم آنلاین</b>\n🔸 (ریپلای) <code>.ترجمه فارسی/انگلیسی</code>",
    "p_anim": "💖 <b>انیمیشن‌های چت</b>\n🔸 <code>.قلب</code>",
    "p_cheat": "🎲 <b>تقلب در بازی‌ها</b>\n🔸 <code>.تقلب تاس 6</code>",
    "p_tts": "🎤 <b>تبدیل متن به ویس</b>\n🔸 <code>.ویس [متن]</code>",
    "p_music": "🎵 <b>جستجوی موسیقی</b>\n🔸 <code>.اهنگ [نام]</code>\n🔸 <code>.اهنگ [نام] 2</code>",
    "p_tabchi": "📢 <b>تبچی</b>\n🔸 <code>.تبچی متن [متن]</code>\n🔸 <code>.تبچی افزودن</code>\n🔸 <code>.تبچی زمان 30</code>\n🔸 <code>.تبچی روشن</code>",
    "p_comment": "📝 <b>کامنت‌گذار خودکار</b>\n🔸 <code>.کامنت افزودن @channel</code>\n🔸 <code>.کامنت متن [متن]</code>",
    "p_crypto": "💰 <b>قیمت ارزها</b>\n🔸 <code>.ارز</code>\n🔸 <code>.تتر</code>",
    "p_readall": "👁‍🗨 <b>سین‌زن چت‌ها</b>\n🔸 <code>.سین پیوی/گروه/کانال/ربات</code>",
    "p_v2ray": "🌐 <b>استخراج پروکسی و V2ray</b>\n🔸 <code>.کانفیگ/پروکسی</code>",
    "p_qr": "⬛️ <b>کیوآر کد</b>\n🔸 <code>.کیوار ساخت [متن]</code>\n🔸 (ریپلای) <code>.کیوار خواندن</code>",
    "p_profile": "👤 <b>پروفایل</b>\n🔸 (ریپلای عکس) <code>.پروفایل عکس</code>\n🔸 <code>.پروفایل اسم [نام] | [فامیل]</code>\n🔸 <code>.پروفایل بیو [متن]</code>\n🔸 <code>.پروفایل یوزرنیم [ID]</code>",
    "p_schedule": "⏱ <b>ارسال زمان‌دار هوشمند</b>\n🔸 <code>.زماندار [دقیقه] [متن پیام]</code>\nمثال: <code>.زماندار 5 سلام فردا میبینمت</code>\n(پیام دستور فوراً پاک شده و سر زمان مقرر پیام ارسال میشود)",
    "p_screen": "📸 <b>اسکرین‌شات از پیام</b>\n🔸 (ریپلای روی یک پیام) <code>.اسکرین</code>\n(ربات واسطه فایل را ارسال کرده و پیام های اضافه کاملا پاک میشوند)"
}

@dp.inline_query()
async def inline_helper_query(inline_query: InlineQuery):
    if "panel" in inline_query.query.lower():
        owner_id = inline_query.from_user.id
        result = InlineQueryResultArticle(
            id="panel_main", title="پنل مدیریت سلف‌ربات", 
            input_message_content=InputTextMessageContent(message_text="🤖 <b>داشبورد مدیریت سوپر سلف‌ربات VIP</b> 🤖\n\nبرای دسترسی به امکانات، روی دکمه زیر کلیک کنید 👇", parse_mode=ParseMode.HTML), 
            reply_markup=get_entry_keyboard(owner_id)
        )
        await inline_query.answer([result], cache_time=1)

calc_sessions = {}

@dp.callback_query()
async def helper_callback_handler(callback_query: CallbackQuery):
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
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="انتخاب فونت برای **ساعت اسم**:", reply_markup=get_font_menu(owner_id, "name", curr_font))
        elif action == "clock_bio_menu":
            curr_font = db.get(str(owner_id), {}).get("bio_font", 1)
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="انتخاب فونت برای **ساعت بیو**:", reply_markup=get_font_menu(owner_id, "bio", curr_font))
        elif action == "setfont":
            target = parts[2]; f_id = int(parts[3])
            if str(owner_id) not in db: db[str(owner_id)] = {}
            if target == "name": db[str(owner_id)]["font"] = f_id; db[str(owner_id)]["clock_status"] = True
            else: db[str(owner_id)]["bio_font"] = f_id; db[str(owner_id)]["bio_clock_status"] = True
            save_db(db)
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS["p_clock"], reply_markup=get_clock_menu(owner_id, db), parse_mode=ParseMode.HTML)
        elif action == "clock_turn_off":
            if str(owner_id) not in db: db[str(owner_id)] = {}
            db[str(owner_id)]["clock_status"] = False; db[str(owner_id)]["bio_clock_status"] = False
            save_db(db)
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS["p_clock"], reply_markup=get_clock_menu(owner_id, db), parse_mode=ParseMode.HTML)
        elif action in PANEL_TEXTS: 
            if action not in ["p_ping", "p_info"] and not db.get(str(owner_id), {}).get("has_full_package", False) and action not in db.get(str(owner_id), {}).get("active_modules", []):
                return await callback_query.answer("🔒 این قابلیت قفل است!", show_alert=True)
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS[action], reply_markup=get_back_button(owner_id), parse_mode=ParseMode.HTML)
    await callback_query.answer()

async def main():
    print("🚀 Panel Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
