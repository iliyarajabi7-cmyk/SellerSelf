# -*- coding: utf-8 -*-
# ============================================================
#  ماژول فروش کانفیگ (3x-ui) - پلاگین مستقل برای master_bot.py
#  نوشته‌شده برای ربات نیترو سلف - واحد پول: میلی‌آمپر (mah_balance)
#  این فایل به ساختار ربات دست نمی‌زند؛ فقط از بیرون وصل می‌شود.
# ============================================================
import asyncio
import json
import time
import uuid
import requests
from datetime import datetime, timezone, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ButtonStyle

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

# ------------------------------------------------------------
# مقادیر پیش‌فرض تنظیمات پنل و قیمت‌ها (داخل db["config"]["xui"])
# admin از داخل ربات این‌ها را ست می‌کند؛ نیازی به دست‌زدن به کد نیست.
# ------------------------------------------------------------
DEFAULT_XUI = {
    "active": False,          # تا وقتی admin پنل را ست نکند، خرید غیرفعال است
    "base_url": "",           # مثال: https://mypanel.up.railway.app یا https://host:2053
    "web_base_path": "",      # اگر پنل مسیر پایه دارد (مثلا abc123) اینجا بگذار، وگرنه خالی
    "username": "",           # یوزرنیم لاگین پنل
    "password": "",           # پسورد لاگین پنل
    "inbound_id": 1,          # آی‌دی اینباند 3x-ui که کلاینت روی آن ساخته می‌شود
    "sub_url_base": "",       # مبنای لینک ساب. مثال: https://mypanel.up.railway.app:2096/sub
    "price_per_gb": 1000,     # میلی‌آمپر به ازای هر گیگ
    "price_per_30d": 5000,    # میلی‌آمپر به ازای هر ۳۰ روز
    "gb_step": 5,             # گام دکمه‌های +/- حجم
    "min_gb": 5,
    "max_gb": 200,
    "day_step": 30,           # گام دکمه‌های +/- مدت
    "min_days": 30,
    "max_days": 90,
    "free_test_gb": 1,        # تست رایگان: حجم
    "free_test_days": 1,      # تست رایگان: مدت
    "free_test_once": True,   # تست رایگان فقط یک‌بار برای هر کاربر
}


def ensure_config(db):
    """مقادیر پیش‌فرض xui را در db[config] تضمین می‌کند (بدون بازنویسی مقادیر ست‌شده)."""
    if "config" not in db:
        db["config"] = {}
    xui = db["config"].get("xui", {})
    for k, v in DEFAULT_XUI.items():
        if k not in xui:
            xui[k] = v
    db["config"]["xui"] = xui
    return xui


def _now_ms():
    return int(time.time() * 1000)


def calc_price(xui, gb, days):
    return int(gb * xui["price_per_gb"] + (days / 30.0) * xui["price_per_30d"])


# ============================================================
#  کلاینت API پنل 3x-ui
# ============================================================
class XUIClient:
    def __init__(self, xui):
        base = (xui.get("base_url") or "").rstrip("/")
        wbp = (xui.get("web_base_path") or "").strip("/")
        if wbp:
            base = f"{base}/{wbp}"
        self.base = base
        self.username = xui.get("username") or ""
        self.password = xui.get("password") or ""
        self.inbound_id = int(xui.get("inbound_id") or 1)
        self.sub_url_base = (xui.get("sub_url_base") or "").rstrip("/")
        self.s = requests.Session()

    def _login(self):
        r = self.s.post(
            f"{self.base}/login",
            data={"username": self.username, "password": self.password},
            timeout=20,
        )
        r.raise_for_status()
        try:
            ok = r.json().get("success", False)
        except Exception:
            ok = False
        if not ok:
            raise RuntimeError("login_failed")

    def create_config(self, email, gb, days):
        """یک کلاینت جدید می‌سازد و لینک ساب + آدرس اتصال را برمی‌گرداند.
        خروجی: dict(sub_link, uuid, email, sub_id)
        """
        if not self.base or not self.username:
            raise RuntimeError("panel_not_configured")
        self._login()

        client_uuid = str(uuid.uuid4())
        sub_id = uuid.uuid4().hex[:16]
        total_bytes = int(gb) * 1024 * 1024 * 1024
        expiry = _now_ms() + int(days) * 24 * 60 * 60 * 1000

        client = {
            "id": client_uuid,
            "email": email,
            "totalGB": total_bytes,
            "expiryTime": expiry,
            "enable": True,
            "tgId": "",
            "subId": sub_id,
            "flow": "",
            "limitIp": 0,
        }
        payload = {
            "id": self.inbound_id,
            "settings": json.dumps({"clients": [client]}),
        }
        r = self.s.post(
            f"{self.base}/panel/api/inbounds/addClient",
            json=payload,
            timeout=25,
        )
        r.raise_for_status()
        try:
            ok = r.json().get("success", False)
        except Exception:
            ok = False
        if not ok:
            raise RuntimeError("add_client_failed")

        sub_link = f"{self.sub_url_base}/{sub_id}" if self.sub_url_base else ""
        return {
            "sub_link": sub_link,
            "uuid": client_uuid,
            "email": email,
            "sub_id": sub_id,
        }


# ============================================================
#  دکمه‌های منوی اصلی (توسط master_bot فراخوانی می‌شود)
# ============================================================
def config_main_buttons():
    return [
        [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="cfg_menu", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🎁 تست رایگان کانفیگ", callback_data="cfg_free", style=ButtonStyle.SUCCESS)],
    ]


def _buy_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ حجم", callback_data="cfg_gb_inc", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text="➖ حجم", callback_data="cfg_gb_dec", style=ButtonStyle.DANGER),
        ],
        [
            InlineKeyboardButton(text="➕ مدت", callback_data="cfg_day_inc", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text="➖ مدت", callback_data="cfg_day_dec", style=ButtonStyle.DANGER),
        ],
        [InlineKeyboardButton(text="✅ خرید و دریافت کانفیگ", callback_data="cfg_buy", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="📂 کانفیگ‌های من", callback_data="cfg_mine", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main", style=ButtonStyle.DANGER)],
    ])


def _buy_text(db, user_id, xui):
    st = _get_state(user_id)
    gb, days = st["gb"], st["days"]
    price = calc_price(xui, gb, days)
    bal = db[str(user_id)].get("mah_balance", 0)
    return (
        "🛒 *خرید کانفیگ اختصاصی*\n\n"
        f"📦 حجم: *{gb}* گیگ\n"
        f"⏳ مدت: *{days}* روز\n"
        f"💰 قیمت: `{price:,}` میلی‌آمپر\n"
        f"🔋 موجودی شما: `{bal:,}` میلی‌آمپر\n\n"
        "⚙️ با دکمه‌های ➕ و ➖ حجم و مدت را تنظیم کنید."
    )


# state موقت برای انتخاب حجم/مدت (در حافظه، نه دیتابیس)
_BUY_STATE = {}


def _get_state(user_id):
    return _BUY_STATE.setdefault(user_id, {"gb": None, "days": None})


def _init_state(user_id, xui):
    st = _get_state(user_id)
    if st["gb"] is None:
        st["gb"] = xui["min_gb"]
    if st["days"] is None:
        st["days"] = xui["min_days"]
    return st


def _fmt_config_msg(gb, days, res):
    link = res.get("sub_link") or "(لینک ساب تنظیم نشده)"
    return (
        "✅ *کانفیگ شما آماده شد!*\n\n"
        f"📦 حجم: *{gb}* گیگ | ⏳ مدت: *{days}* روز\n\n"
        "🔗 *لینک اشتراک (Subscription):*\n"
        f"`{link}`\n\n"
        "💡 این لینک را در برنامهٔ v2rayNG / v2rayN / Streisand وارد کنید.\n"
        "📂 همیشه از بخش «کانفیگ‌های من» در دسترس است."
    )


async def _make_and_store(bot, db, save_db, user_id, gb, days, xui, is_free, ADMIN_ID):
    """کانفیگ می‌سازد، در دیتابیس ذخیره می‌کند و متن نتیجه را برمی‌گرداند."""
    email = f"u{user_id}_{uuid.uuid4().hex[:6]}"
    client = XUIClient(xui)
    res = await asyncio.to_thread(client.create_config, email, gb, days)

    uid = str(user_id)
    rec = {
        "email": res["email"],
        "uuid": res["uuid"],
        "sub_id": res["sub_id"],
        "sub_link": res["sub_link"],
        "gb": gb,
        "days": days,
        "is_free": is_free,
        "created": datetime.now(IRAN_TZ).strftime("%Y/%m/%d %H:%M"),
        "expiry_ms": _now_ms() + int(days) * 86400000,
    }
    db[uid].setdefault("configs", []).append(rec)
    return res


def _mine_text(db, user_id):
    cfgs = db[str(user_id)].get("configs", [])
    if not cfgs:
        return "📂 شما هنوز هیچ کانفیگی ندارید."
    lines = ["📂 *کانفیگ‌های من:*\n"]
    for i, c in enumerate(cfgs, 1):
        tag = "🎁 تست" if c.get("is_free") else "💳 خرید"
        lines.append(
            f"*{i}) {tag}* | {c['gb']}گیگ / {c['days']}روز | {c.get('created','')}\n`{c.get('sub_link') or '-'}`\n"
        )
    return "\n".join(lines)


def _back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت به خرید کانفیگ", callback_data="cfg_menu", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="menu_main", style=ButtonStyle.DANGER)],
    ])


# ============================================================
#  هندلر اصلی کالبک‌ها (master_bot تمام cfg_* را به این می‌سپارد)
# ============================================================
async def handle_cfg_callback(callback_query, bot, db, save_db, main_menu_keyboard, ADMIN_ID):
    data = callback_query.data
    user_id = callback_query.from_user.id
    xui = ensure_config(db)
    msg = callback_query.message

    # --- منوی خرید ---
    if data == "cfg_menu":
        _init_state(user_id, xui)
        await _safe_edit(msg, _buy_text(db, user_id, xui), _buy_keyboard())
        return await callback_query.answer()

    # --- تنظیم حجم/مدت با فلش ---
    if data in ("cfg_gb_inc", "cfg_gb_dec", "cfg_day_inc", "cfg_day_dec"):
        st = _init_state(user_id, xui)
        if data == "cfg_gb_inc":
            st["gb"] = min(xui["max_gb"], st["gb"] + xui["gb_step"])
        elif data == "cfg_gb_dec":
            st["gb"] = max(xui["min_gb"], st["gb"] - xui["gb_step"])
        elif data == "cfg_day_inc":
            st["days"] = min(xui["max_days"], st["days"] + xui["day_step"])
        elif data == "cfg_day_dec":
            st["days"] = max(xui["min_days"], st["days"] - xui["day_step"])
        await _safe_edit(msg, _buy_text(db, user_id, xui), _buy_keyboard())
        return await callback_query.answer()

    # --- خرید ---
    if data == "cfg_buy":
        if not xui.get("active") or not xui.get("base_url"):
            await _notify_admin_unconfigured(bot, ADMIN_ID)
            return await callback_query.answer("⚠️ فروش کانفیگ فعلاً غیرفعال است. (پنل تنظیم نشده)", show_alert=True)
        st = _init_state(user_id, xui)
        gb, days = st["gb"], st["days"]
        price = calc_price(xui, gb, days)
        bal = db[str(user_id)].get("mah_balance", 0)
        if bal < price:
            return await callback_query.answer(f"❌ موجودی کافی نیست! نیاز: {price:,} - موجودی: {bal:,}", show_alert=True)
        await _safe_edit(msg, "⏳ در حال ساخت کانفیگ...", None)
        try:
            res = await _make_and_store(bot, db, save_db, user_id, gb, days, xui, False, ADMIN_ID)
        except Exception as e:
            await _notify_admin_error(bot, ADMIN_ID, user_id, e)
            await _safe_edit(msg, "❌ خطا در ساخت کانفیگ. موجودی کسر نشد، با پشتیبانی در تماس باشید.", _back_kb())
            return await callback_query.answer()
        db[str(user_id)]["mah_balance"] = bal - price
        save_db(db)
        await _safe_edit(msg, _fmt_config_msg(gb, days, res), _back_kb())
        return await callback_query.answer("✅ خرید موفق!")

    # --- تست رایگان ---
    if data == "cfg_free":
        uid = str(user_id)
        if xui.get("free_test_once") and db[uid].get("config_test_used"):
            return await callback_query.answer("❌ شما قبلاً تست رایگان کانفیگ خود را دریافت کرده‌اید.", show_alert=True)
        if not xui.get("active") or not xui.get("base_url"):
            await _notify_admin_unconfigured(bot, ADMIN_ID)
            return await callback_query.answer("⚠️ تست رایگان فعلاً غیرفعال است. (پنل تنظیم نشده)", show_alert=True)
        gb, days = xui["free_test_gb"], xui["free_test_days"]
        await _safe_edit(msg, "⏳ در حال ساخت کانفیگ تست...", None)
        try:
            res = await _make_and_store(bot, db, save_db, user_id, gb, days, xui, True, ADMIN_ID)
        except Exception as e:
            await _notify_admin_error(bot, ADMIN_ID, user_id, e)
            await _safe_edit(msg, "❌ خطا در ساخت کانفیگ تست. با پشتیبانی در تماس باشید.", _back_kb())
            return await callback_query.answer()
        db[uid]["config_test_used"] = True
        save_db(db)
        await _safe_edit(msg, _fmt_config_msg(gb, days, res), _back_kb())
        return await callback_query.answer("🎁 کانفیگ تست ساخته شد!")

    # --- کانفیگ‌های من ---
    if data == "cfg_mine":
        await _safe_edit(msg, _mine_text(db, user_id), _back_kb())
        return await callback_query.answer()

    return await callback_query.answer()


async def _safe_edit(message, text, kb):
    try:
        await message.edit_text(text, reply_markup=kb)
    except Exception:
        try:
            await message.answer(text, reply_markup=kb)
        except Exception:
            pass


async def _notify_admin_unconfigured(bot, ADMIN_ID):
    try:
        await bot.send_message(ADMIN_ID, "⚠️ یک کاربر خواست کانفیگ بسازد اما پنل 3x-ui هنوز تنظیم نشده.\nبا دستور /panel تنظیمات پنل را کامل کن.")
    except Exception:
        pass


async def _notify_admin_error(bot, ADMIN_ID, user_id, e):
    try:
        await bot.send_message(ADMIN_ID, f"🔥 خطا در ساخت کانفیگ برای کاربر {user_id}:\n`{e}`")
    except Exception:
        pass


# ============================================================
#  تنظیمات پنل توسط ادمین (دستور /panelset در ربات)
#  master_bot این را در message_handler صدا می‌زند.
# ============================================================
_ADMIN_STEPS = [
    ("base_url", "🌐 آدرس پنل را بفرست (مثلاً https://mypanel.up.railway.app):", str),
    ("web_base_path", "📁 مسیر پایهٔ پنل (web base path) را بفرست. اگر ندارد بنویس: -", str),
    ("username", "👤 یوزرنیم لاگین پنل:", str),
    ("password", "🔑 پسورد لاگین پنل:", str),
    ("inbound_id", "🔢 آیدی اینباند (inbound id) — معمولاً 1:", int),
    ("sub_url_base", "🔗 مبنای لینک ساب (مثلاً https://mypanel.up.railway.app:2096/sub):", str),
    ("price_per_gb", "💰 قیمت هر گیگ (میلی‌آمپر):", int),
    ("price_per_30d", "📅 قیمت هر ۳۰ روز (میلی‌آمپر):", int),
]


def admin_start_state():
    return "cfg_set_0"


async def handle_cfg_admin_message(message, bot, db, save_db, user_states, main_menu_keyboard, state):
    """مراحل ست‌کردن تنظیمات پنل. اگر state مربوط به cfg نباشد False برمی‌گرداند."""
    if not state.startswith("cfg_set_"):
        return False
    user_id = message.chat.id
    xui = ensure_config(db)
    idx = int(state.split("_")[-1])
    key, _prompt, caster = _ADMIN_STEPS[idx]
    val = (message.text or "").strip()

    if key == "web_base_path" and val in ("-", "—", ""):
        val = ""
    else:
        try:
            val = caster(val)
        except Exception:
            await message.answer("❌ مقدار نامعتبر است، دوباره بفرست.")
            return True
    xui[key] = val
    db["config"]["xui"] = xui
    save_db(db)

    nxt = idx + 1
    if nxt < len(_ADMIN_STEPS):
        user_states[user_id] = f"cfg_set_{nxt}"
        await message.answer(_ADMIN_STEPS[nxt][1])
    else:
        xui["active"] = True
        db["config"]["xui"] = xui
        save_db(db)
        if user_id in user_states:
            del user_states[user_id]
        await message.answer(
            "✅ تنظیمات پنل ذخیره شد و فروش کانفیگ فعال شد! 🚀",
            reply_markup=main_menu_keyboard(db, user_id),
        )
    return True
