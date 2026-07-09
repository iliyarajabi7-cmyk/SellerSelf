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
            with open(DB_FILE, "r", encoding="utf-8") as f: 
                return json.load(f)
        except: 
            return {}
    return {}

def get_entry_keyboard(owner_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 ورود به داشبورد", callback_data=f"enter|{owner_id}", style=ButtonStyle.SUCCESS), 
            InlineKeyboardButton(text="❌ بستن پنل", callback_data=f"close|{owner_id}", style=ButtonStyle.DANGER)
        ],
        [
            InlineKeyboardButton(text="📞 پشتیبانی", url="https://t.me/Im_Iliiya", style=ButtonStyle.PRIMARY)
        ]
    ])

def get_categories_keyboard(user_id):
    db = load_db()
    try:
        layout = db["config"]["panel_config"]["layout"]
        names = db["config"]["panel_config"]["names"]
        user_data = db.get(str(user_id), {})
        active_modules = user_data.get("active_modules", [])
        has_full_package = user_data.get("has_full_package", False)
        free_modules = ["p_ping", "p_info"] 
        
        kb = []
        for row_idx, row in enumerate(layout):
            kb_row = []
            
            if row_idx in [0, 1, 2]:
                row_color = ButtonStyle.SUCCESS
            elif row_idx in [3, 4, 5]:
                row_color = ButtonStyle.PRIMARY
            elif row_idx in [6, 7, 8]:
                row_color = ButtonStyle.SUCCESS
            else:
                row_color = ButtonStyle.DANGER

            for btn_key in row:
                btn_name = names.get(btn_key, btn_key)
                is_locked = False
                
                if btn_key not in free_modules and not has_full_package and btn_key not in active_modules: 
                    btn_name = f"🔒 {btn_name}"
                    is_locked = True
                
                btn_style = ButtonStyle.SECONDARY if is_locked else row_color
                kb_row.append(InlineKeyboardButton(text=btn_name, callback_data=f"{btn_key}|{user_id}", style=btn_style))
                
            kb.append(kb_row)
            
        kb.append([
            InlineKeyboardButton(text="🧮 ماشین حساب", callback_data=f"calc_main|{user_id}", style=ButtonStyle.DANGER)
        ])
        
        kb.append([
            InlineKeyboardButton(text="🔙 بازگشت به صفحه اصلی", callback_data=f"back|{user_id}", style=ButtonStyle.DANGER)
        ])
        return InlineKeyboardMarkup(inline_keyboard=kb)
    except Exception: 
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ خطا در خواندن اطلاعات", callback_data=f"close|{user_id}", style=ButtonStyle.DANGER)]])

def get_back_button(owner_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"enter|{owner_id}", style=ButtonStyle.PRIMARY)]
    ])

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
            if k == "C": style = ButtonStyle.DANGER
            elif k in ["=", "+", "-", "*", "/"]: style = ButtonStyle.SUCCESS
            else: style = ButtonStyle.PRIMARY
            r_btns.append(InlineKeyboardButton(text=k, callback_data=f"calc_act|{owner_id}|{k}", style=style))
        kb.append(r_btns)
    kb.append([InlineKeyboardButton(text="🔙 بازگشت به پنل", callback_data=f"enter|{owner_id}", style=ButtonStyle.DANGER)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

PANEL_TEXTS = {
    "p_guard": "🛡 <b>نگهبان چت تفکیک‌شده</b>\nکنترل کامل پیام‌ها در پیوی، گروه و کانال.\n\n🔸 <code>.نگهبان پیوی حذف روشن</code>\n🔸 <code>.نگهبان گروه ویرایش روشن</code>\n🎯 <code>.نگهبان کانال زماندار روشن</code>\n🎯 <code>.نگهبان گروه افزودن</code> (اضافه کردن گروه به لیست نگهبان)\n🎯 <code>.نگهبان لیست</code>",
    "p_clock": "⏰ <b>تنظیمات ساعت جامع</b>\nنمایش فونت‌های جذاب برای ساعت نام و بیوگرافی:\n\n1️⃣ <code>0123</code>\n2️⃣ <code>𝟎𝟏𝟐𝟑</code>\n3️⃣ <code>⁰¹²³</code>\n4️⃣ <code>₀₁₂₃</code>\n5️⃣ <code>۰۱۲۳</code>\n6️⃣ <code>⓿❶❷❸</code>\n7️⃣ <code>⓪①②③</code>\n8️⃣ <code>𝟘𝟙𝟚𝟛</code>\n9️⃣ <code>𝟬𝟭𝟮𝟯</code>\n🔟 <code>𝟶𝟷𝟸𝟹</code>\n\n🔸 <code>.ساعت اسم روشن 2</code>\n🔸 <code>.ساعت بیو روشن 5</code>\n❌ <code>.ساعت اسم خاموش</code>",
    "p_textmode": "✨ <b>حالت متن (تغییر استایل چت)</b>\nنوشتن پیام‌ها با استایل‌های مختلف به صورت خودکار.\n\n🎨 <code>.حالت بولد</code>\n🎨 <code>.حالت کج</code>\n🎨 <code>.حالت مونو</code>\n🎨 <code>.حالت خط‌خورده</code>\n🎨 <code>.حالت زیرخط</code>\n🎨 <code>.حالت اسپویلر</code>\n🎨 <code>.حالت نقل قول</code>\n🔗 <code>.حالت لینکدار [لینک]</code>\n❌ <code>.حالت خاموش</code>",
    "p_action": "🎭 <b>اکشن‌ساز (حالت فیک)</b>\nنمایش وضعیت در حال تایپ، ارسال عکس و... به صورت فیک.\n\n🔸 <code>.اکشن پیوی تایپ</code>\n🔸 <code>.اکشن گروه عکس</code>\n🔸 <code>.اکشن پیوی ویس</code>\n❌ <code>.اکشن پیوی خاموش</code>",
    "p_locks": "🔐 <b>قفل‌های امنیتی</b>\nقفل کردن محتوا در پیوی و گروه‌ها.\n\n🔸 <code>.قفل پیوی روشن</code>\n🔸 <code>.قفل لینک روشن</code>\n🔸 <code>.قفل عکس خاموش</code>\n🔸 <code>.انتی اسپم روشن</code>",
    "p_logo": "🎨 <b>ساخت لوگو اختصاصی</b>\nتولید لوگوی زیبا با متن دلخواه شما.\n\n🔸 <code>.لوگو [متن شما]</code>",
    "p_ping": "🏓 <b>تست سرعت پینگ</b>\nبررسی وضعیت اتصال سلف‌ربات.\n\n🔸 <code>.ping</code> یا <code>.پینگ</code>",
    "p_filter": "🚫 <b>فیلتر هوشمند کلمات</b>\nحذف خودکار پیام‌های حاوی کلمات زشت یا ممنوعه.\n\n🔸 <code>.فیلتر افزودن [کلمه]</code>\n🔸 <code>.فیلتر حذف [کلمه]</code>",
    "p_monshi": "🤖 <b>منشی هوشمند</b>\nپاسخگویی خودکار به پیام‌های پیوی زمانی که نیستید.\n\n🔸 <code>.منشی روشن</code>\n🔸 <code>.منشی متن [پیام دلخواه]</code>\n❌ <code>.منشی خاموش</code>",
    "p_forcejoin": "🛑 <b>عضویت اجباری</b>\nمحدود کردن ارسال پیام در گروه تا زمانی که کاربر در کانال شما عضو شود.\n\n🔸 <code>.اجباری تنظیم @channel</code>\n❌ <code>.اجباری خاموش</code>",
    "p_autoreply": "💬 <b>پاسخ خودکار</b>\nتنظیم کلمه و دریافت پاسخ اتوماتیک.\n\n🔸 <code>.پاسخ افزودن سلام - سلام عزیزم</code>\n🔸 <code>.پاسخ حذف سلام</code>",
    "p_dl": "📥 <b>دانلودر مدیا قدرتمند</b>\nدانلود مخفیانه از یوتیوب، اینستاگرام و تیک‌تاک.\n\n🔸 <code>.دانلود [لینک]</code>\n🔗 (ریپلای روی فایل) <code>.لینک</code>",
    "p_react": "❤️ <b>ریکت خودکار</b>\nثبت ری‌اکشن خودکار روی پیام‌های کاربران.\n\n🔸 <code>.ریکت تنظیم ⚡️</code>\n❌ <code>.ریکت خاموش</code>",
    "p_spam": "💣 <b>موتور اسپم</b>\nارسال پیام پشت سر هم به پیوی یا گروه.\n\n🔸 <code>.اسپم [متن] [تعداد] [سرعت]</code>\n(مثال سرعت: سریع، معمولی، اهسته)",
    "p_mute": "🔇 <b>سکوت و آزادی</b>\nمحدود کردن کاربران خاص از پیام دادن به شما.\n\n🔸 (ریپلای) <code>.سکوت</code>\n🔸 (ریپلای) <code>.ازادی</code>",
    "p_info": "🆔 <b>اطلاعات حساب</b>\nدریافت اطلاعات دقیق شخص مقابل.\n\n🔸 (ریپلای) <code>.ایدی</code>",
    "p_tag": "🎯 <b>تگ همگانی</b>\nتگ کردن همه اعضای گروه به صورت مخفی.\n\n🔸 <code>.تگ [متن دلخواه]</code>",
    "p_purge": "🧹 <b>پاکسازی هوشمند چت</b>\nحذف خودکار یا دستی پیام‌های ارسال شده.\n\n🔸 <code>.حذف 50</code>\n🔸 <code>.پاکسازی 12</code> (پاکسازی کل گروه هر 12 ساعت)",
    "p_ai": "🧠 <b>هوش مصنوعی</b>\nاتصال به هوش مصنوعی قدرتمند برای پاسخ به سوالات.\n\n🔸 <code>.هوش [سوال شما]</code>",
    "p_translate": "🌍 <b>مترجم آنلاین</b>\nترجمه پیام‌ها به تمام زبان‌های زنده دنیا.\n\n🔸 (ریپلای) <code>.ترجمه انگلیسی</code>\n🔸 (ریپلای) <code>.ترجمه فارسی</code>",
    "p_anim": "💖 <b>انیمیشن‌های چت</b>\nارسال قلب‌های متحرک و رنگارنگ.\n\n🔸 <code>.قلب</code>",
    "p_cheat": "🎲 <b>تقلب در بازی‌ها</b>\nپرتاب تاس، دارت و... با نتیجه دلخواه شما.\n\n🔸 <code>.تقلب تاس 6</code>\n🔸 <code>.تقلب دارت 6</code>",
    "p_tts": "🎤 <b>تبدیل متن به ویس</b>\nخواندن پیام متنی شما با صدای طبیعی.\n\n🔸 <code>.ویس [متن شما]</code>",
    "p_music": "🎵 <b>جستجوی موسیقی</b>\nپیدا کردن سریع آهنگ در تلگرام.\n\n🔸 <code>.اهنگ [اسم خواننده یا موزیک]</code>",
    "p_tabchi": "📢 <b>موتور تبچی</b>\nارسال پیام تبلیغاتی به گروه‌ها در زمان‌های معین.\n\n🔸 <code>.تبچی متن [متن]</code>\n🔸 <code>.تبچی افزودن</code>\n🔸 <code>.تبچی زمان 30</code>\n🔸 <code>.تبچی روشن</code>",
    "p_comment": "📝 <b>کامنت‌گذار خودکار</b>\nثبت اولین کامنت زیر پست‌های کانال.\n\n🔸 <code>.کامنت افزودن @channel</code>\n🔸 <code>.کامنت متن [متن]</code>\n🔸 <code>.کامنت حذف @channel</code>",
    "p_crypto": "💰 <b>قیمت ارزهای دیجیتال</b>\nدریافت قیمت لحظه‌ای تتر، بیت‌کوین و...\n\n🔸 <code>.ارز</code>\n🔸 <code>.تتر</code>",
    "p_readall": "👁‍🗨 <b>سین زدن دسته‌جمعی</b>\nخواندن تمام پیام‌های نخوانده با یک دستور.\n\n🔸 <code>.سین پیوی</code>\n🔸 <code>.سین گروه</code>\n🔸 <code>.سین کانال</code>",
    "p_v2ray": "🌐 <b>دریافت پروکسی و V2ray</b>\nاستخراج کانفیگ‌های فعال از کانال‌ها.\n\n🔸 <code>.کانفیگ</code>\n🔸 <code>.پروکسی</code>",
    "p_qr": "⬛️ <b>مدیریت QR Code</b>\nساخت و خواندن بارکد.\n\n🔸 <code>.کیوار ساخت [متن]</code>\n🔸 (ریپلای روی عکس) <code>.کیوار خواندن</code>",
    "p_profile": "👤 <b>مدیریت پیشرفته پروفایل</b>\nتغییر مشخصات اکانت.\n\n🔸 <code>.پروفایل عکس</code> (ریپلای روی عکس)\n🔸 <code>.پروفایل اسم رضا | احمدی</code>\n🔸 <code>.پروفایل بیو [متن]</code>\n🔸 <code>.پروفایل یوزرنیم [ID]</code>"
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
        if action == "close": 
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="✅ <b>پنل بسته شد.</b>", parse_mode=ParseMode.HTML)
        elif action == "enter": 
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text="🗂 <b>لیست امکانات سلف‌ربات</b>\nاز لیست زیر قابلیت مورد نظر را انتخاب کنید:", reply_markup=get_categories_keyboard(owner_id), parse_mode=ParseMode.HTML)
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
            
        elif action in PANEL_TEXTS: 
            db = load_db()
            if action not in ["p_ping", "p_info"] and not db.get(str(owner_id), {}).get("has_full_package", False) and action not in db.get(str(owner_id), {}).get("active_modules", []):
                return await callback_query.answer("🔒 این قابلیت قفل است!", show_alert=True)
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS[action], reply_markup=get_back_button(owner_id), parse_mode=ParseMode.HTML)
            
    await callback_query.answer()

async def main():
    print("🚀 Panel Bot is starting (Enhanced Layout & Security)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
