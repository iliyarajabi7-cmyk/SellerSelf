from pyrogram import Client
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, 
                            InlineQueryResultArticle, InputTextMessageContent)
import json
import os

API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
BOT_TOKEN = "8946302310:AAErar2ykfD58Xuq4fLrhF9USnaWG4MVIJ0"

bot = Client("PanelBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def get_entry_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 ورود به داشبورد", callback_data="enter_panel"), InlineKeyboardButton("❌ بستن پنل", callback_data="close_panel")]
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
                if btn_key not in free_modules and not has_full_package and btn_key not in active_modules: btn_name = f"🔒 {btn_name}"
                kb_row.append(InlineKeyboardButton(btn_name, callback_data=btn_key))
            kb.append(kb_row)
        kb.append([InlineKeyboardButton("🔙 بازگشت به صفحه اصلی", callback_data="back_to_entry")])
        return InlineKeyboardMarkup(kb)
    except Exception: return InlineKeyboardMarkup([[InlineKeyboardButton("❌ خطا در خواندن اطلاعات", callback_data="close_panel")]])

def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="enter_panel")]])

PANEL_TEXTS = {
    "p_guard": "🛡 **نگهبان چت تفکیک‌شده (حفاظت از پیام‌ها)**\n\nامکان فعال‌سازی مجزا برای پیوی، گروه و کانال:\n🔸 `.نگهبان پیوی حذف روشن` ⇦ ارسال پیام‌های پاک شده پیوی برای شما\n🔸 `.نگهبان گروه ویرایش روشن` ⇦ نمایش متن قبل از ادیتِ افراد در گروه‌ها\n🔸 `.نگهبان کانال زماندار روشن` ⇦ دانلود مدیاهای زمان‌دار در کانال\n❌ جایگزین کردن کلمه `خاموش` برای غیرفعال‌سازی.\n\n🎯 `.نگهبان گروه افزودن/حذف` ⇦ اعمال نگهبان فقط روی گروه‌های هدف\n📋 `.نگهبان لیست` ⇦ مشاهده لیست گروه‌های تحت نظارت",
    "p_clock": "⏰ **تنظیمات ساعت جامع (نام و بیو)**\n\n🔸 `.ساعت اسم روشن 5` ⇦ فعال‌سازی ساعت اسم با فونت ۵\n🔸 `.ساعت بیو روشن 9` ⇦ ساعت در بیوگرافی با فونت ۹\n❌ `.ساعت [اسم/بیو] خاموش` ⇦ غیرفعال‌سازی\n\n📝 **فونت‌های ساعت:**\n`1`: 12:56 | `2`: 𝟏𝟐:𝟓𝟔 | `3`: ¹²:⁵⁶\n`4`: ₁₂:₅₆ | `5`: ۱۲:۵۶ | `6`: ❶❷:❺❻\n`7`: ①②:⑤⑥ | `8`: 𝟙𝟚:𝟝𝟞 | `9`: 𝟭𝟮:𝟱𝟲 | `10`: 𝟷𝟸:𝟻𝟼",
    "p_textmode": "✨ **حالت متن (تغییر استایل چت)**\n\nفونت تمام پیام‌های شما را تغییر می‌دهد:\n🎨 `.حالت بولد` ⇦ **متن ضخیم**\n🎨 `.حالت کج` ⇦ __متن کج__\n🎨 `.حالت مونو` ⇦ `متن کپی‌شونده`\n🎨 `.حالت خط‌خورده` ⇦ ~~متن خط‌خورده~~\n🎨 `.حالت زیرخط` ⇦ --متن زیرخط‌دار--\n🎨 `.حالت اسپویلر` ⇦ ||متن مخفی و تارار||\n🎨 `.حالت نقل‌قول` ⇦ ایجاد بلاک نقل‌قول رسمی (Blockquote)\n🔗 `.حالت لینکدار [لینک]` ⇦ پیام‌های شما را به لینک تبدیل می‌کند\n❌ `.حالت خاموش` ⇦ بازگشت به حالت عادی",
    "p_action": "🎭 **اکشن‌ساز (حالت فیک در حال...)**\n\n🔸 `.اکشن پیوی تایپ` ⇦ typing...\n🔸 `.اکشن گروه عکس` ⇦ sending photo...\n❌ `.اکشن پیوی/گروه خاموش`\n*(حالت‌های مجاز: تایپ، ویس، عکس، ویدیو، گرد، سند، بازی، استیکر)*",
    "p_locks": "🔐 **قفل‌های امنیتی**\n\n🔸 `.قفل پیوی روشن/خاموش` ⇦ پاک کردن پیام‌های دریافتی پیوی\n🔸 `.قفل [لینک/عکس/فوروارد/یوزرنیم/ویدیو] روشن/خاموش`\n🔸 `.انتی اسپم روشن/خاموش`",
    "p_logo": "🎨 **ساخت لوگو اختصاصی**\n\n🔸 `.لوگو [متن]` ⇦ ساخت سریع لوگو\n💡 مثال: `.لوگو Iliya`",
    "p_ping": "🏓 **تست سرعت پینگ**\n\n🔸 `.ping` یا `.پینگ` ⇦ نمایش سرعت پاسخگویی",
    "p_filter": "🚫 **فیلتر هوشمند کلمات**\n\n🔸 `.فیلتر افزودن [کلمه]` ⇦ افزودن به لیست سیاه\n🔸 `.فیلتر حذف [کلمه]`",
    "p_monshi": "🤖 **منشی هوشمند**\n\n🔸 `.منشی روشن/خاموش`\n🔸 `.منشی متن [پیام]`\n🔸 `.منشی زمان 60`",
    "p_forcejoin": "🛑 **عضویت اجباری**\n\n🔸 `.اجباری تنظیم @channel`\n🔸 `.اجباری خاموش`",
    "p_autoreply": "💬 **پاسخ خودکار**\n\n🔸 `.پاسخ افزودن سلام - علیک`\n🔸 `.پاسخ حذف سلام`",
    "p_dl": "📥 **دانلودر مدیا قدرتمند (بدون فوروارد)**\n\n🔸 `.دانلود [لینک]` ⇦ دانلود از اینستاگرام، تیک‌تاک، یوتیوب\n🔸 `.دانلود [لینک تلگرام]` ⇦ دانلود از کانال‌های قفل شده (t.me/c/...)\n*(ربات فایل را مخفیانه دانلود کرده و در چت آپلود می‌کند!)*",
    "p_react": "❤️ **ریکت خودکار**\n\n🔸 `.ریکت تنظیم ❤️`\n🔸 `.ریکت خاموش`",
    "p_spam": "💣 **موتور اسپم**\n\n🔸 `.اسپم [متن] [تعداد] [سرعت/زمان]`\n💡 مثال: `.اسپم سلام 20 0.5`",
    "p_mute": "🔇 **سکوت و آزادی**\n\n🔸 (ریپلای) `.سکوت`\n🔸 (ریپلای) `.ازادی`",
    "p_info": "🆔 **اطلاعات حساب**\n\n🔸 (ریپلای) `.ایدی` ⇦ استخراج آیدی و لینک پروفایل",
    "p_tag": "🎯 **تگ همگانی**\n\n🔸 `.تگ [متن]` ⇦ تگ مخفی تمام اعضا",
    "p_purge": "🧹 **پاکسازی هوشمند چت**\n\n🔸 `.پاکسازی 12` ⇦ پاک کردن خودکار کل چت هر ۱۲ ساعت\n🔸 `.پاکسازی خاموش` ⇦ توقف پاکسازی زمان‌دار\n🔸 `.حذف 50` ⇦ حذف ۵۰ پیام آخر خودتان در لحظه",
    "p_ai": "🧠 **هوش مصنوعی**\n\n🔸 `.هوش [سوال]`",
    "p_translate": "🌍 **مترجم آنلاین**\n\n🔸 (ریپلای) `.ترجمه انگلیسی`\n🔸 (ریپلای) `.ترجمه fa`",
    "p_anim": "💖 **انیمیشن‌های چت**\n\n🔸 `.قلب`",
    "p_cheat": "🎲 **تقلب در بازی‌ها**\n\n🔸 `.تقلب تاس 6`\n🔸 `.تقلب دارت 6`\n🔸 `.تقلب بسکتبال 5`\n🔸 `.تقلب فوتبال 5`\n🔸 `.تقلب بولینگ 6`\n🔸 `.تقلب کازینو 64`",
    "p_tts": "🎤 **تبدیل متن به ویس**\n\n🔸 `.ویس [متن]`",
    "p_music": "🎵 **جستجوی موسیقی**\n\n🔸 `.اهنگ [اسم]`",
    "p_tabchi": "📢 **موتور تبچی**\n\n🔸 `.تبچی متن [متن]`\n🔸 `.تبچی افزودن/حذف`\n🔸 `.تبچی زمان 30`\n🔸 `.تبچی روشن/خاموش`\n📋 `.تبچی لیست` ⇦ نمایش گروه‌های هدف",
    "p_comment": "📝 **کامنت‌گذار خودکار**\n\n🔸 `.کامنت افزودن @channel`\n🔸 `.کامنت متن [متن]`\n🔸 `.کامنت حذف @channel`",
    "p_crypto": "💰 **قیمت ارزهای دیجیتال**\n\n🔸 `.ارز` ⇦ نمایش قیمت تمام ارزهای معروف\n🔸 `.تتر`، `.بیتکوین`، `.اتریوم`، `.ترون`، `.دوج`، `.سولانا`، `.شیبا` و...\n*(دریافت لحظه‌ای قیمت تک‌ارزها به صورت مستقیم)*",
    "p_readall": "👁‍🗨 **سین زدن دسته‌جمعی**\n\n🔸 `.سین پیوی`\n🔸 `.سین گروه`\n🔸 `.سین کانال`\n🔸 `.سین ربات`",
    "p_v2ray": "🌐 **دریافت پروکسی و V2ray**\n\n🔸 `.کانفیگ`\n🔸 `.پروکسی`",
    "p_qr": "⬛️ **مدیریت QR Code**\n\n🔸 `.کیوار ساخت [متن]` یا ریپلای روی عکس\n🔸 (ریپلای روی بارکد) `.کیوار خواندن`",
    "p_profile": "👤 **مدیریت پیشرفته پروفایل**\n\n🔸 `.پروفایل عکس` (ریپلای روی یک عکس)\n🔸 `.پروفایل اسم نام | فامیل`\n🔸 `.پروفایل بیو [متن]`\n🔸 `.پروفایل یوزرنیم ID`\n🔸 `.پروفایل تولد YYYY-MM-DD` (مثال: 2005-04-15)"
}

@bot.on_inline_query()
async def inline_helper_query(client, inline_query):
    if "panel" in inline_query.query.lower():
        result = InlineQueryResultArticle(
            id="panel_main",
            title="پنل مدیریت سلف‌ربات", 
            input_message_content=InputTextMessageContent("🤖 **داشبورد مدیریت سوپر سلف‌ربات VIP** 🤖\n\nبرای دسترسی به امکانات، روی دکمه زیر کلیک کنید 👇"), 
            reply_markup=get_entry_keyboard()
        )
        await inline_query.answer([result], cache_time=1)

@bot.on_callback_query()
async def helper_callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    if data == "close_panel": await callback_query.edit_message_text("✅ **پنل بسته شد.**")
    elif data == "enter_panel": await callback_query.edit_message_text("🗂 **لیست امکانات سلف‌ربات**", reply_markup=get_categories_keyboard(user_id))
    elif data == "back_to_entry": await callback_query.edit_message_text("🤖 **داشبورد مدیریت سوپر سلف‌ربات VIP** 🤖", reply_markup=get_entry_keyboard())
    elif data in PANEL_TEXTS: 
        db = load_db()
        if data not in ["p_ping", "p_info"] and not db.get(str(user_id), {}).get("has_full_package", False) and data not in db.get(str(user_id), {}).get("active_modules", []):
            return await callback_query.answer("🔒 این قابلیت قفل است!", show_alert=True)
        await callback_query.edit_message_text(PANEL_TEXTS[data], reply_markup=get_back_button())

if __name__ == "__main__":
    bot.run()