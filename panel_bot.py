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
            
            # رنگ‌بندی یکی‌در‌میان ردیف‌ها برای جذابیت بصری
            if row_idx % 2 == 0:
                row_color = ButtonStyle.PRIMARY
            else:
                row_color = ButtonStyle.SUCCESS

            for btn_key in row:
                btn_name = names.get(btn_key, btn_key)
                is_locked = False
                
                if btn_key not in free_modules and not has_full_package and btn_key not in active_modules: 
                    btn_name = f"🔒 {btn_name}"
                    is_locked = True
                
                # اعمال استایل دکمه (اگر قفل باشه استایل خاکستری به خود میگیره)
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
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"enter|{owner_id}", style=ButtonStyle.DANGER)]
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
    "p_guard": "🛡 <b>نگهبان چت تفکیک‌شده</b>\n🔸 <code>.نگهبان پیوی حذف روشن</code>\n🎯 <code>.نگهبان گروه افزودن</code>",
    "p_clock": "⏰ <b>تنظیمات ساعت جامع</b>\n🔸 <code>.ساعت اسم روشن 5</code>\n🔸 <code>.ساعت بیو روشن 9</code>",
    "p_textmode": "✨ <b>حالت متن (تغییر استایل چت)</b>\n🎨 <code>.حالت اسپویلر</code>\n🎨 <code>.حالت نقل‌قول</code>",
    "p_action": "🎭 <b>اکشن‌ساز (حالت فیک)</b>\n🔸 <code>.اکشن پیوی تایپ</code>\n🔸 <code>.اکشن گروه عکس</code>",
    "p_locks": "🔐 <b>قفل‌های امنیتی</b>\n🔸 <code>.قفل پیوی روشن/خاموش</code>",
    "p_logo": "🎨 <b>ساخت لوگو اختصاصی</b>\n🔸 <code>.لوگو [متن]</code>",
    "p_ping": "🏓 <b>تست سرعت پینگ</b>\n🔸 <code>.ping</code>",
    "p_filter": "🚫 <b>فیلتر هوشمند کلمات</b>\n🔸 <code>.فیلتر افزودن [کلمه]</code>",
    "p_monshi": "🤖 <b>منشی هوشمند</b>\n🔸 <code>.منشی روشن/خاموش</code>",
    "p_forcejoin": "🛑 <b>عضویت اجباری</b>\n🔸 <code>.اجباری تنظیم @channel</code>",
    "p_autoreply": "💬 <b>پاسخ خودکار</b>\n🔸 <code>.پاسخ افزودن سلام - علیک</code>",
    "p_dl": "📥 <b>دانلودر مدیا قدرتمند (بدون فوروارد)</b>\n🔸 <code>.دانلود [لینک]</code>",
    "p_react": "❤️ <b>ریکت خودکار</b>\n🔸 <code>.ریکت تنظیم ❤️</code>",
    "p_spam": "💣 <b>موتور اسپم</b>\n🔸 <code>.اسپم [متن] [تعداد] [سرعت]</code>",
    "p_mute": "🔇 <b>سکوت و آزادی</b>\n🔸 (ریپلای) <code>.سکوت</code>",
    "p_info": "🆔 <b>اطلاعات حساب</b>\n🔸 (ریپلای) <code>.ایدی</code>",
    "p_tag": "🎯 <b>تگ همگانی</b>\n🔸 <code>.تگ [متن]</code>",
    "p_purge": "🧹 <b>پاکسازی هوشمند چت</b>\n🔸 <code>.پاکسازی 12</code>",
    "p_ai": "🧠 <b>هوش مصنوعی</b>\n🔸 <code>.هوش [سوال]</code>",
    "p_translate": "🌍 <b>مترجم آنلاین</b>\n🔸 (ریپلای) <code>.ترجمه انگلیسی</code>",
    "p_anim": "💖 <b>انیمیشن‌های چت</b>\n🔸 <code>.قلب</code>",
    "p_cheat": "🎲 <b>تقلب در بازی‌ها</b>\n🔸 <code>.تقلب تاس 6</code>",
    "p_tts": "🎤 <b>تبدیل متن به ویس</b>\n🔸 <code>.ویس [متن]</code>",
    "p_music": "🎵 <b>جستجوی موسیقی</b>\n🔸 <code>.اهنگ [اسم]</code>",
    "p_tabchi": "📢 <b>موتور تبچی</b>\n🔸 <code>.تبچی متن [متن]</code>",
    "p_comment": "📝 <b>کامنت‌گذار خودکار</b>\n🔸 <code>.کامنت افزودن @channel</code>",
    "p_crypto": "💰 <b>قیمت ارزهای دیجیتال</b>\n🔸 <code>.ارز</code>",
    "p_readall": "👁‍🗨 <b>سین زدن دسته‌جمعی</b>\n🔸 <code>.سین پیوی</code>",
    "p_v2ray": "🌐 <b>دریافت پروکسی و V2ray</b>\n🔸 <code>.کانفیگ</code>",
    "p_qr": "⬛️ <b>مدیریت QR Code</b>\n🔸 <code>.کیوار ساخت [متن]</code>",
    "p_profile": "👤 <b>مدیریت پیشرفته پروفایل</b>\n🔸 <code>.پروفایل عکس</code> (ریپلای)"
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
            
        elif action in PANEL_TEXTS: 
            db = load_db()
            if action not in ["p_ping", "p_info"] and not db.get(str(owner_id), {}).get("has_full_package", False) and action not in db.get(str(owner_id), {}).get("active_modules", []):
                return await callback_query.answer("🔒 این قابلیت قفل است!", show_alert=True)
            await bot.edit_message_text(inline_message_id=callback_query.inline_message_id, text=PANEL_TEXTS[action], reply_markup=get_back_button(owner_id), parse_mode=ParseMode.HTML)
            
    await callback_query.answer()

async def main():
    print("🚀 Panel Bot is starting (Styled Buttons Included)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
