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

def get_entry_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 ورود به داشبورد", callback_data="enter_panel", style=ButtonStyle.PRIMARY), 
            InlineKeyboardButton(text="❌ بستن پنل", callback_data="close_panel", style=ButtonStyle.DANGER)
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
        for row in layout:
            kb_row = []
            for btn_key in row:
                btn_name = names.get(btn_key, btn_key)
                is_locked = False
                
                if btn_key not in free_modules and not has_full_package and btn_key not in active_modules: 
                    btn_name = f"🔒 {btn_name}"
                    is_locked = True
                
                btn_style = ButtonStyle.SECONDARY if is_locked else ButtonStyle.PRIMARY
                kb_row.append(InlineKeyboardButton(text=btn_name, callback_data=btn_key, style=btn_style))
                
            kb.append(kb_row)
            
        kb.append([InlineKeyboardButton(text="🔙 بازگشت به صفحه اصلی", callback_data="back_to_entry", style=ButtonStyle.DANGER)])
        return InlineKeyboardMarkup(inline_keyboard=kb)
    except Exception: 
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ خطا در خواندن اطلاعات", callback_data="close_panel", style=ButtonStyle.DANGER)]])

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="enter_panel", style=ButtonStyle.PRIMARY)]
    ])

PANEL_TEXTS = {
    "p_guard": "🛡 <b>نگهبان چت تفکیک‌شده (حفاظت از پیام‌ها)</b>\n\nامکان فعال‌سازی مجزا برای پیوی، گروه و کانال:\n🔸 <code>.نگهبان پیوی حذف روشن</code> ⇦ ارسال پیام‌های پاک شده پیوی برای شما\n🔸 <code>.نگهبان گروه ویرایش روشن</code> ⇦ نمایش متن قبل از ادیتِ افراد در گروه‌ها\n🔸 <code>.نگهبان کانال زماندار روشن</code> ⇦ دانلود مدیاهای زمان‌دار در کانال\n❌ جایگزین کردن کلمه <code>خاموش</code> برای غیرفعال‌سازی.\n\n🎯 <code>.نگهبان گروه افزودن/حذف</code> ⇦ اعمال نگهبان فقط روی گروه‌های هدف\n📋 <code>.نگهبان لیست</code> ⇦ مشاهده لیست گروه‌های تحت نظارت",
    "p_clock": "⏰ <b>تنظیمات ساعت جامع (نام و بیو)</b>\n\n🔸 <code>.ساعت اسم روشن 5</code> ⇦ فعال‌سازی ساعت اسم با فونت ۵\n🔸 <code>.ساعت بیو روشن 9</code> ⇦ ساعت در بیوگرافی با فونت ۹\n❌ <code>.ساعت [اسم/بیو] خاموش</code> ⇦ غیرفعال‌سازی\n\n📝 <b>فونت‌های ساعت:</b>\n<code>1</code>: 12:56 | <code>2</code>: 𝟏𝟐:𝟓𝟔 | <code>3</code>: ¹²:⁵⁶\n<code>4</code>: ₁₂:₅₆ | <code>5</code>: ۱۲:۵۶ | <code>6</code>: ❶❷:❺❻\n<code>7</code>: ①②:⑤⑥ | <code>8</code>: 𝟙𝟚:𝟝𝟞 | <code>9</code>: 𝟭𝟮:𝟱𝟲 | <code>10</code>: 𝟷𝟸:𝟻𝟼",
    "p_textmode": "✨ <b>حالت متن (تغییر استایل چت)</b>\n\nفونت تمام پیام‌های شما را تغییر می‌دهد:\n🎨 <code>.حالت بولد</code> ⇦ <b>متن ضخیم</b>\n🎨 <code>.حالت کج</code> ⇦ <i>متن کج</i>\n🎨 <code>.حالت مونو</code> ⇦ <code>متن کپی‌شونده</code>\n🎨 <code>.حالت خط‌خورده</code> ⇦ <s>متن خط‌خورده</s>\n🎨 <code>.حالت زیرخط</code> ⇦ <u>متن زیرخط‌دار</u>\n🎨 <code>.حالت اسپویلر</code> ⇦ <tg-spoiler>متن مخفی و تارار</tg-spoiler>\n🎨 <code>.حالت نقل‌قول</code> ⇦ ایجاد بلاک نقل‌قول رسمی (Blockquote)\n🔗 <code>.حالت لینکدار [لینک]</code> ⇦ پیام‌های شما را به لینک تبدیل می‌کند\n❌ <code>.حالت خاموش</code> ⇦ بازگشت به حالت عادی",
    "p_action": "🎭 <b>اکشن‌ساز (حالت فیک در حال...)</b>\n\n🔸 <code>.اکشن پیوی تایپ</code> ⇦ typing...\n🔸 <code>.اکشن گروه عکس</code> ⇦ sending photo...\n❌ <code>.اکشن پیوی/گروه خاموش</code>\n*(حالت‌های مجاز: تایپ، ویس، عکس، ویدیو، گرد، سند، بازی، استیکر)*",
    "p_locks": "🔐 <b>قفل‌های امنیتی</b>\n\n🔸 <code>.قفل پیوی روشن/خاموش</code> ⇦ پاک کردن پیام‌های دریافتی پیوی\n🔸 <code>.قفل [لینک/عکس/فوروارد/یوزرنیم/ویدیو] روشن/خاموش</code>\n🔸 <code>.انتی اسپم روشن/خاموش</code>",
    "p_logo": "🎨 <b>ساخت لوگو اختصاصی</b>\n\n🔸 <code>.لوگو [متن]</code> ⇦ ساخت سریع لوگو\n💡 مثال: <code>.لوگو Iliya</code>",
    "p_ping": "🏓 <b>تست سرعت پینگ</b>\n\n🔸 <code>.ping</code> یا <code>.پینگ</code> ⇦ نمایش سرعت پاسخگویی",
    "p_filter": "🚫 <b>فیلتر هوشمند کلمات</b>\n\n🔸 <code>.فیلتر افزودن [کلمه]</code> ⇦ افزودن به لیست سیاه\n🔸 <code>.فیلتر حذف [کلمه]</code>",
    "p_monshi": "🤖 <b>منشی هوشمند</b>\n\n🔸 <code>.منشی روشن/خاموش</code>\n🔸 <code>.منشی متن [پیام]</code>\n🔸 <code>.منشی زمان 60</code>",
    "p_forcejoin": "🛑 <b>عضویت اجباری</b>\n\n🔸 <code>.اجباری تنظیم @channel</code>\n🔸 <code>.اجباری خاموش</code>",
    "p_autoreply": "💬 <b>پاسخ خودکار</b>\n\n🔸 <code>.پاسخ افزودن سلام - علیک</code>\n🔸 <code>.پاسخ حذف سلام</code>",
    "p_dl": "📥 <b>دانلودر مدیا قدرتمند (بدون فوروارد)</b>\n\n🔸 <code>.دانلود [لینک]</code> ⇦ دانلود از اینستاگرام، تیک‌تاک، یوتیوب\n🔸 <code>.دانلود [لینک تلگرام]</code> ⇦ دانلود از کانال‌های قفل شده (t.me/c/...)\n*(ربات فایل را مخفیانه دانلود کرده و در چت آپلود می‌کند!)*",
    "p_react": "❤️ <b>ریکت خودکار</b>\n\n🔸 <code>.ریکت تنظیم ❤️</code>\n🔸 <code>.ریکت خاموش</code>",
    "p_spam": "💣 <b>موتور اسپم</b>\n\n🔸 <code>.اسپم [متن] [تعداد] [سرعت/زمان]</code>\n💡 مثال: <code>.اسپم سلام 20 0.5</code>",
    "p_mute": "🔇 <b>سکوت و آزادی</b>\n\n🔸 (ریپلای) <code>.سکوت</code>\n🔸 (ریپلای) <code>.ازادی</code>",
    "p_info": "🆔 <b>اطلاعات حساب</b>\n\n🔸 (ریپلای) <code>.ایدی</code> ⇦ استخراج آیدی و لینک پروفایل",
    "p_tag": "🎯 <b>تگ همگانی</b>\n\n🔸 <code>.تگ [متن]</code> ⇦ تگ مخفی تمام اعضا",
    "p_purge": "🧹 <b>پاکسازی هوشمند چت</b>\n\n🔸 <code>.پاکسازی 12</code> ⇦ پاک کردن خودکار کل چت هر ۱۲ ساعت\n🔸 <code>.پاکسازی خاموش</code> ⇦ توقف پاکسازی زمان‌دار\n🔸 <code>.حذف 50</code> ⇦ حذف ۵۰ پیام آخر خودتان در لحظه",
    "p_ai": "🧠 <b>هوش مصنوعی</b>\n\n🔸 <code>.هوش [سوال]</code>",
    "p_translate": "🌍 <b>مترجم آنلاین</b>\n\n🔸 (ریپلای) <code>.ترجمه انگلیسی</code>\n🔸 (ریپلای) <code>.ترجمه fa</code>",
    "p_anim": "💖 <b>انیمیشن‌های چت</b>\n\n🔸 <code>.قلب</code>",
    "p_cheat": "🎲 <b>تقلب در بازی‌ها</b>\n\n🔸 <code>.تقلب تاس 6</code>\n🔸 <code>.تقلب دارت 6</code>\n🔸 <code>.تقلب بسکتبال 5</code>\n🔸 <code>.تقلب فوتبال 5</code>\n🔸 <code>.تقلب بولینگ 6</code>\n🔸 <code>.تقلب کازینو 64</code>",
    "p_tts": "🎤 <b>تبدیل متن به ویس</b>\n\n🔸 <code>.ویس [متن]</code>",
    "p_music": "🎵 <b>جستجوی موسیقی</b>\n\n🔸 <code>.اهنگ [اسم]</code>",
    "p_tabchi": "📢 <b>موتور تبچی</b>\n\n🔸 <code>.تبچی متن [متن]</code>\n🔸 <code>.تبچی افزودن/حذف</code>\n🔸 <code>.تبچی زمان 30</code>\n🔸 <code>.تبچی روشن/خاموش</code>\n📋 <code>.تبچی لیست</code> ⇦ نمایش گروه‌های هدف",
    "p_comment": "📝 <b>کامنت‌گذار خودکار</b>\n\n🔸 <code>.کامنت افزودن @channel</code>\n🔸 <code>.کامنت متن [متن]</code>\n🔸 <code>.کامنت حذف @channel</code>",
    "p_crypto": "💰 <b>قیمت ارزهای دیجیتال</b>\n\n🔸 <code>.ارز</code> ⇦ نمایش قیمت تمام ارزهای معروف\n🔸 <code>.تتر</code>، <code>.بیتکوین</code>، <code>.اتریوم</code>، <code>.ترون</code>، <code>.دوج</code>، <code>.سولانا</code>، <code>.شیبا</code> و...\n*(دریافت لحظه‌ای قیمت تک‌ارزها به صورت مستقیم)*",
    "p_readall": "👁‍🗨 <b>سین زدن دسته‌جمعی</b>\n\n🔸 <code>.سین پیوی</code>\n🔸 <code>.سین گروه</code>\n🔸 <code>.سین کانال</code>\n🔸 <code>.سین ربات</code>",
    "p_v2ray": "🌐 <b>دریافت پروکسی و V2ray</b>\n\n🔸 <code>.کانفیگ</code>\n🔸 <code>.پروکسی</code>",
    "p_qr": "⬛️ <b>مدیریت QR Code</b>\n\n🔸 <code>.کیوار ساخت [متن]</code> یا ریپلای روی عکس\n🔸 (ریپلای روی بارکد) <code>.کیوار خواندن</code>",
    "p_profile": "👤 <b>مدیریت پیشرفته پروفایل</b>\n\n🔸 <code>.پروفایل عکس</code> (ریپلای روی یک عکس)\n🔸 <code>.پروفایل اسم نام | فامیل</code>\n🔸 <code>.پروفایل بیو [متن]</code>\n🔸 <code>.پروفایل یوزرنیم ID</code>\n🔸 <code>.پروفایل تولد YYYY-MM-DD</code> (مثال: 2005-04-15)"
}

@dp.inline_query()
async def inline_helper_query(inline_query: InlineQuery):
    if "panel" in inline_query.query.lower():
        result = InlineQueryResultArticle(
            id="panel_main",
            title="پنل مدیریت سلف‌ربات", 
            input_message_content=InputTextMessageContent(
                message_text="🤖 <b>داشبورد مدیریت سوپر سلف‌ربات VIP</b> 🤖\n\nبرای دسترسی به امکانات، روی دکمه زیر کلیک کنید 👇",
                parse_mode=ParseMode.HTML
            ), 
            reply_markup=get_entry_keyboard()
        )
        await inline_query.answer([result], cache_time=1)

@dp.callback_query()
async def helper_callback_handler(callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # اطمینان از اینکه کالبک مربوط به پیام اینلاین است
    if callback_query.inline_message_id:
        if data == "close_panel": 
            await bot.edit_message_text(
                inline_message_id=callback_query.inline_message_id,
                text="✅ <b>پنل بسته شد.</b>", 
                parse_mode=ParseMode.HTML
            )
        elif data == "enter_panel": 
            await bot.edit_message_text(
                inline_message_id=callback_query.inline_message_id,
                text="🗂 <b>لیست امکانات سلف‌ربات</b>", 
                reply_markup=get_categories_keyboard(user_id), 
                parse_mode=ParseMode.HTML
            )
        elif data == "back_to_entry": 
            await bot.edit_message_text(
                inline_message_id=callback_query.inline_message_id,
                text="🤖 <b>داشبورد مدیریت سوپر سلف‌ربات VIP</b> 🤖\n\nبرای دسترسی به امکانات، روی دکمه زیر کلیک کنید 👇", 
                reply_markup=get_entry_keyboard(), 
                parse_mode=ParseMode.HTML
            )
        elif data in PANEL_TEXTS: 
            db = load_db()
            if data not in ["p_ping", "p_info"] and not db.get(str(user_id), {}).get("has_full_package", False) and data not in db.get(str(user_id), {}).get("active_modules", []):
                return await callback_query.answer("🔒 این قابلیت قفل است!", show_alert=True)
            
            await bot.edit_message_text(
                inline_message_id=callback_query.inline_message_id,
                text=PANEL_TEXTS[data], 
                reply_markup=get_back_button(), 
                parse_mode=ParseMode.HTML
            )
            
    await callback_query.answer()

async def main():
    print("🚀 Panel Bot is starting via Aiogram 3 with Inline Query Support & Colored Buttons...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
