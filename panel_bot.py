import asyncio
import json
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ButtonStyle
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineQueryResultArticle, 
    InputTextMessageContent,
    InlineQuery,
    CallbackQuery
)

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
    fonts = {
        1: "12345", 2: "𝟏𝟐𝟑𝟒𝟓", 3: "¹²³⁴⁵", 4: "₁₂₃₄₅", 5: "۱۲۳۴۵",
        6: "❶❷❸❹❺", 7: "①②③④⑤", 8: "𝟙𝟚𝟛𝟜𝟝", 9: "𝟭𝟮𝟯𝟰𝟱", 10: "𝟷𝟸𝟹𝟺𝟻"
    }
    kb = []
    row = []
    for f_id, f_samp in fonts.items():
        style = ButtonStyle.SUCCESS if current_font == f_id else ButtonStyle.PRIMARY
        row.append(InlineKeyboardButton(text=f_samp, callback_data=f"setfont|{owner_id}|{target_type}|{f_id}", style=style))
        if len(row) == 2:
            kb.append(row); row = []
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
    "p_guard": "🛡 <b>نگهبان چت هوشمند (تامین امنیت)</b>\n\nبا این قابلیت می‌توانید از حذف، ویرایش یا ارسال پیام‌های زمان‌دار در چت‌های مختلف مطلع شوید.\n\n🔸 <code>.نگهبان پیوی حذف روشن</code>\n🔸 <code>.نگهبان گروه ویرایش روشن</code>\n🔸 <code>.نگهبان کانال زماندار روشن</code>\n🎯 <code>.نگهبان گروه افزودن</code> (محدود کردن نگهبان فقط به گروه فعلی)\n📋 <code>.نگهبان لیست</code>",
    "p_clock": "⏰ <b>ساعت زنده (اسم و بیو)</b>\n\nاین قابلیت ساعت دقیق ایران را با فونت‌های جذاب روی پروفایل شما قرار می‌دهد. از دکمه‌های زیر برای تنظیم استفاده کنید:",
    "p_textmode": "✨ <b>حالت‌دهنده متن چت (استایل‌ساز)</b>\n\nمتون خود را حرفه‌ای کنید! این قابلیت تمام پیام‌های ساده شما را به فرمت دلخواه تبدیل می‌کند:\n\n🎨 <code>.حالت بولد</code>\n🎨 <code>.حالت کج</code>\n🎨 <code>.حالت اسپویلر</code> (مخفی کردن متن)\n🎨 <code>.حالت نقل‌قول</code> (بلاک‌کوت)\n🎨 <code>.حالت مونو</code>\n🔗 <code>.حالت لینکدار [لینک شما]</code>\n❌ <code>.حالت خاموش</code>",
    "p_action": "🎭 <b>اکشن‌ساز (حالت فیک)</b>\n\nبه بقیه نشان دهید در حال انجام کاری هستید (حتی وقتی نیستید!)\n\n🔸 <code>.اکشن پیوی تایپ</code>\n🔸 <code>.اکشن پیوی ویس</code>\n🔸 <code>.اکشن گروه عکس</code>\n🔸 <code>.اکشن گروه ویدیو</code>\n🔸 <code>.اکشن گروه بازی</code>\n❌ <code>.اکشن پیوی خاموش</code>",
    "p_locks": "🔐 <b>قفل‌های امنیتی ضد مزاحمت</b>\n\nگروه‌ها و پیوی خود را امن کنید!\n\n🔸 <code>.قفل پیوی روشن</code> (حذف خودکار پیام مزاحم‌ها)\n🔸 <code>.قفل لینک روشن</code> (در گروه)\n🔸 <code>.قفل عکس روشن</code>\n🔸 <code>.قفل فوروارد روشن</code>\n🔸 <code>.قفل یوزرنیم روشن</code>\n❌ <code>.قفل لینک خاموش</code>",
    "p_logo": "🎨 <b>طراح لوگوی اختصاصی</b>\n\nبا یک دستور ساده لوگوی متنی زیبا دریافت کنید.\n\n🔸 <code>.لوگو [متن دلخواه شما]</code>",
    "p_ping": "🏓 <b>تست سرعت (پینگ)</b>\n\nبررسی وضعیت اتصال سلف‌ربات شما به سرورهای تلگرام.\n\n🔸 <code>.ping</code> یا <code>.پینگ</code>",
    "p_filter": "🚫 <b>فیلتر هوشمند کلمات</b>\n\nکلمات رکیک یا نامناسب را به ربات بدهید تا در همان چت فوراً حذف شوند.\n\n🔸 <code>.فیلتر افزودن [کلمه]</code>\n🔸 <code>.فیلتر حذف [کلمه]</code>",
    "p_monshi": "🤖 <b>منشی هوشمند پیوی</b>\n\nوقتی آفلاین هستید، منشی جواب پیوی‌ها را می‌دهد.\n\n🔸 <code>.منشی روشن</code>\n🔸 <code>.منشی خاموش</code>\n🔸 <code>.منشی متن [پیام دلخواه]</code>\n🔸 <code>.منشی زمان [عدد به ثانیه]</code> (فاصله بین پاسخ‌ها)",
    "p_forcejoin": "🛑 <b>عضویت اجباری شیشه‌ای</b>\n\nکاربران تا در کانال شما عضو نشوند، پیامشان در گروه حذف می‌شود (اخطار شیشه‌ای).\n\n🔸 <code>.اجباری تنظیم @channel</code>\n❌ <code>.اجباری خاموش</code>",
    "p_autoreply": "💬 <b>پاسخ‌دهنده خودکار</b>\n\nربات به کلمات خاص حساس شده و جواب تعیین شده را می‌دهد.\n\n🔸 <code>.پاسخ افزودن سلام - علیک</code>\n🔸 <code>.پاسخ حذف سلام</code>",
    "p_dl": "📥 <b>دانلودر مدیا (تیک‌تاک، یوتیوب، اینستاگرام)</b>\n\nبدون افتادن آیدی بات دانلودر، فایل‌ها را مستقیماً دریافت کنید!\n\n🔸 <code>.دانلود [لینک]</code>",
    "p_react": "❤️ <b>ریکت‌زن خودکار (لایک پیام‌ها)</b>\n\nبه محض پیام دادن دیگران، روی پیامشان ری‌اکشن بزنید!\n\n🔸 <code>.ریکت تنظیم ❤️</code>\n🔸 <code>.ریکت تنظیم 🔥</code>\n❌ <code>.ریکت خاموش</code>",
    "p_spam": "💣 <b>موتور اسپم قدرتمند</b>\n\nارسال رگباری متن در چت (استفاده با احتیاط!).\n\n🔸 <code>.اسپم [متن] [تعداد] [سریع/معمولی/اهسته]</code>\nمثال: <code>.اسپم سلام 10 سریع</code>",
    "p_mute": "🔇 <b>سکوت و آزادی کاربران</b>\n\nکاربر مورد نظر را در پیوی یا گروه خفه کنید!\n\n🔸 (روی پیام شخص ریپلای کنید) <code>.سکوت</code>\n🔸 (روی پیام شخص ریپلای کنید) <code>.ازادی</code>",
    "p_info": "🆔 <b>استخراج اطلاعات حساب</b>\n\n🔸 (ریپلای روی پیام فرد) <code>.ایدی</code>",
    "p_tag": "🎯 <b>تگ همگانی اعضای گروه</b>\n\nاعضای گروه را ۵ تا ۵ تا برای یک پیام مهم تگ کنید.\n\n🔸 <code>.تگ [متن دلخواه]</code>",
    "p_purge": "🧹 <b>پاکسازی هوشمند چت</b>\n\nپیام‌های خود را در کسری از ثانیه پاک کنید.\n\n🔸 <code>.حذف [تعداد]</code> (پاک کردن پیام‌های اخیر خودتان)\n🔸 <code>.پاکسازی 12</code> (پاکسازی کامل این چت هر ۱۲ ساعت)",
    "p_ai": "🧠 <b>هوش مصنوعی قدرتمند</b>\n\nبدون فیلترشکن از هوش مصنوعی بپرسید!\n\n🔸 <code>.هوش [سوال شما]</code>",
    "p_translate": "🌍 <b>مترجم آنلاین پیشرفته</b>\n\nپیام‌ها را به هر زبانی ترجمه کنید.\n\n🔸 (ریپلای روی پیام خارجی) <code>.ترجمه فارسی</code>\n🔸 (ریپلای روی پیام فارسی) <code>.ترجمه انگلیسی</code>\nپشتیبانی از: المانی، روسی، ترکی، عربی، فرانسوی و...",
    "p_anim": "💖 <b>انیمیشن‌های چت</b>\n\nزیبایی چت با قلب‌های رنگی.\n\n🔸 <code>.قلب</code>",
    "p_cheat": "🎲 <b>تقلب در بازی‌های تلگرام</b>\n\nهمیشه برنده باشید!\n\n🔸 <code>.تقلب تاس 6</code>\n🔸 <code>.تقلب دارت 6</code>\n🔸 <code>.تقلب بسکتبال 5</code>",
    "p_tts": "🎤 <b>تبدیل متن به ویس (صدا)</b>\n\nمتن بدهید، ویس طبیعی تحویل بگیرید.\n\n🔸 <code>.ویس [متن شما]</code>",
    "p_music": "🎵 <b>موتور جستجوی موسیقی</b>\n\nآهنگ‌ها را مستقیماً پیدا و دانلود کنید.\n\n🔸 <code>.اهنگ [نام خواننده یا اهنگ]</code>\n🔸 <code>.اهنگ [نام] 2</code> (دریافت نتیجه دوم)",
    "p_tabchi": "📢 <b>موتور تبچی (تبلیغ‌گر)</b>\n\nارسال خودکار پیام به گروه‌ها و پیوی‌ها در زمان‌های مشخص.\n\n🔸 <code>.تبچی متن [متن تبلیغ]</code>\n🔸 <code>.تبچی افزودن</code> (اضافه شدن این چت به لیست)\n🔸 <code>.تبچی زمان 30</code> (ارسال هر 30 دقیقه)\n🔸 <code>.تبچی روشن/خاموش</code>",
    "p_comment": "📝 <b>کامنت‌گذار خودکار کانال‌ها (اولین نفر باش!)</b>\n\nبه محض پست گذاشتن کانال، کامنت شما ثبت می‌شود.\n\n🔸 <code>.کامنت افزودن @channel</code>\n🔸 <code>.کامنت متن [متن کامنت]</code>\n🔸 <code>.کامنت حذف @channel</code>",
    "p_crypto": "💰 <b>قیمت لحظه‌ای ارزها و کریپتو</b>\n\n🔸 <code>.ارز</code> (نمایش لیست کامل شامل تتر، طلا، تون، نات و...)\n🔸 <code>.تتر</code> یا <code>.تون</code> (دریافت قیمت تکی)",
    "p_readall": "👁‍🗨 <b>سین‌زن دسته‌جمعی چت‌ها</b>\n\nدیگر پیام نخوانده نداشته باشید.\n\n🔸 <code>.سین پیوی</code>\n🔸 <code>.سین گروه</code>\n🔸 <code>.سین کانال</code>\n🔸 <code>.سین ربات</code>",
    "p_v2ray": "🌐 <b>استخراج پروکسی و V2ray</b>\n\nجدیدترین کانفیگ‌ها و پروکسی‌ها را از کانال‌های اسپانسر جمع‌آوری می‌کند.\n\n🔸 <code>.کانفیگ</code>\n🔸 <code>.پروکسی</code>",
    "p_qr": "⬛️ <b>ساخت و خواندن کیوآر کد</b>\n\n🔸 <code>.کیوار ساخت [متن یا لینک]</code>\n🔸 (ریپلای روی کیوآر کد) <code>.کیوار خواندن</code>",
    "p_profile": "👤 <b>مدیریت پیشرفته پروفایل</b>\n\nبدون رفتن به تنظیمات تلگرام، حسابتان را تغییر دهید.\n\n🔸 (ریپلای روی عکس) <code>.پروفایل عکس</code>\n🔸 <code>.پروفایل اسم [نام] | [فامیل]</code>\n🔸 <code>.پروفایل بیو [متن]</code>\n🔸 <code>.پروفایل یوزرنیم [ID]</code>\n🔸 <code>.پروفایل تولد [سال-ماه-روز]</code>",
    "p_schedule": "⏱ <b>ارسال زمان‌دار هوشمند</b>\n\nبا این قابلیت ربات پیام شما را نگه می‌دارد و سر وقت در چت می‌فرستد.\n\n🔸 <code>.زماندار [دقیقه] [متن پیام]</code>\nمثال: <code>.زماندار 5 سلام فردا میبینمت</code>\n(پیام دستور فوراً پاک شده و 5 دقیقه بعد پیام اصلی ارسال میشود)",
    "p_screen": "📸 <b>اسکرین‌شات از پیام</b>\n\nعکسی تمیز و بدون بک‌گراند از یک پیام تلگرامی بگیرید.\n\n🔸 کافیست روی پیام مورد نظر ریپلای کنید و بفرستید:\n<code>.اسکرین</code>\n(ربات اسکرین‌شات را برای شما فرستاده و پیام‌های اضافه را پاک می‌کند)"
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
    data = callback_query.data
    clicker_id = callback_query.from_user.id
    parts = data.split("|")
    action = parts[0]
    owner_id = int(parts[1]) if len(parts) > 1 else clicker_id
    
    if clicker_id != owner_id:
        return await callback_query.answer("⚠️ این پنل برای شما نیست! (فقط احضارکننده دسترسی دارد)", show_alert=True)
    
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

async def main():
    print("🚀 Panel Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
