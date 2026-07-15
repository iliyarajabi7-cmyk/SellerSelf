# -*- coding: utf-8 -*-
# ============================================================
#  ماژول فروش کانفیگ (3x-ui) - پلاگین مستقل برای master_bot.py
#  واحد پول: میلی‌آمپر (mah_balance)
#  این فایل به ساختار ربات دست نمی‌زند؛ فقط از بیرون وصل می‌شود.
#  قابلیت‌ها:
#   - منوی خرید کانفیگ (حجم متغیر با فلش، مدت ثابت ۳۰ روز)
#   - تست رایگان (۱ گیگ / ۱ روز)
#   - مدیریت کانفیگ من
#   - استخر چندپنله (افزودن/حذف/لیست) با سقف ۷۵ گیگ برای هر پنل
#   - تنظیم قیمت هر گیگ از پنل مدیریت
# ============================================================
import asyncio
import json
import time
import uuid
import requests
try:
    from curl_cffi import requests as cffi_requests
    _HAS_CFFI = True
except Exception:
    cffi_requests = None
    _HAS_CFFI = False
print(f"[config_seller] build=diag-v2 curl_cffi={_HAS_CFFI}", flush=True)
from datetime import datetime, timezone, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ButtonStyle

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

# ------------------------------------------------------------
# مقادیر پیش‌فرض (داخل db["config"]["xui"])
# ------------------------------------------------------------
DEFAULT_XUI = {
    "price_per_gb": 150,       # میلی‌آمپر به ازای هر گیگ
    "gb_step": 1,              # گام دکمه‌های +/- حجم
    "min_gb": 1,
    "max_gb": 75,
    "fixed_days": 30,          # مدت ثابت خرید
    "free_test_gb": 1,         # تست رایگان: حجم
    "free_test_days": 1,       # تست رایگان: مدت
    "free_test_once": True,    # تست رایگان فقط یک‌بار برای هر کاربر
    "cap_per_panel": 75,       # سقف حجم هر پنل (گیگ)
    "panels": [],             # استخر پنل‌ها
}


def ensure_config(db):
    if "config" not in db:
        db["config"] = {}
    xui = db["config"].get("xui", {})
    for k, v in DEFAULT_XUI.items():
        if k not in xui:
            xui[k] = v
    if not isinstance(xui.get("panels"), list):
        xui["panels"] = []
    db["config"]["xui"] = xui
    return xui


def _now_ms():
    return int(time.time() * 1000)


def calc_price(xui, gb):
    # مدت ثابت است، پس مبلغ = حجم × قیمت هر گیگ
    return int(gb * xui["price_per_gb"])


def _panel_remaining(p):
    return int(p.get("cap_gb", 75)) - int(p.get("used_gb", 0))


def _panel_is_full(p):
    return (not p.get("active", True)) or _panel_remaining(p) <= 0


def pick_panel(xui, gb):
    """اولین پنل فعال که جا برای gb دارد را برمی‌گرداند."""
    for p in xui.get("panels", []):
        if not _panel_is_full(p) and _panel_remaining(p) >= gb:
            return p
    return None


# ============================================================
#  کلاینت API پنل 3x-ui
# ============================================================
class XUIClient:
    def __init__(self, panel):
        origin = (panel.get("base_url") or "").rstrip("/")
        wbp = (panel.get("web_base_path") or "").strip("/")
        # اگر ادمین مسیر پایه را وارد نکرد، پیش‌فرض روی sub می‌گذاریم
        if not wbp:
            wbp = "sub"
        base = f"{origin}/{wbp}"
        self.base = base
        self.origin = origin
        self.username = panel.get("username") or ""
        self.password = panel.get("password") or ""
        self.inbound_id = int(panel.get("inbound_id") or 1)
        self.sub_url_base = (panel.get("sub_url_base") or "").rstrip("/")
        # curl_cffi با اثرانگشت TLS کروم، از سد بات‌دیتکشن کلادفلر/رِیل‌وی رد می‌شود
        if _HAS_CFFI:
            self.s = cffi_requests.Session(impersonate="chrome")
        else:
            self.s = requests.Session()
        # هدرهای مرورگرمانند تا پنل/رِیل‌وی درخواست را 403 نکند
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": origin,
            "Referer": f"{base}/",
        })

    def _csrf(self):
        # پنل‌های جدید 3x-ui برای POST /login توکن CSRF می‌خواهند；
        # اول باید آن را از /csrf-token گرفت و در هدر X-CSRF-Token گذاشت.
        try:
            r = self.s.get(f"{self.base}/csrf-token", timeout=20)
            token = (r.json() or {}).get("obj")
            if token:
                self.s.headers.update({"X-CSRF-Token": token})
                return token
        except Exception:
            pass
        return None

    def _login(self):
        # گام ۱: گرفتن توکن CSRF (و کوکی سشن)
        token = self._csrf()
        # گام ۲: لاگین همراه توکن
        r = self.s.post(
            f"{self.base}/login",
            data={"username": self.username, "password": self.password},
            timeout=20,
        )
        code = getattr(r, "status_code", None)
        if code != 200:
            body = (getattr(r, "text", "") or "")[:150]
            raise RuntimeError(
                f"login_http_{code} | csrf={'ok' if token else 'NONE'} | url={self.base}/login | resp={body}"
            )
        try:
            ok = r.json().get("success", False)
        except Exception:
            ok = False
        if not ok:
            body = (getattr(r, "text", "") or "")[:150]
            raise RuntimeError(f"login_failed | resp={body}")
        # بعد از لاگین سشن عوض می‌شود؛ توکن را برای درخواست‌های بعدی (addClient) تازه می‌کنیم
        self._csrf()

    def create_config(self, email, gb, days):
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
        payload = {"id": self.inbound_id, "settings": json.dumps({"clients": [client]})}
        r = self.s.post(f"{self.base}/panel/api/inbounds/addClient", data=payload, timeout=25)
        r.raise_for_status()
        try:
            ok = r.json().get("success", False)
        except Exception:
            ok = False
        if not ok:
            raise RuntimeError("add_client_failed")
        sub_link = f"{self.sub_url_base}/{sub_id}" if self.sub_url_base else ""
        return {"sub_link": sub_link, "uuid": client_uuid, "email": email, "sub_id": sub_id}


# ============================================================
#  دکمهٔ ورودی منوی اصلی (تک‌دکمه)
# ============================================================
def config_home_row():
    return [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="cfg_home", style=ButtonStyle.SUCCESS)]


def _home_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="cfg_buy_menu", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🎁 تست رایگان", callback_data="cfg_free", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="📂 مدیریت کانفیگ من", callback_data="cfg_mine", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main", style=ButtonStyle.DANGER)],
    ])


def _home_text():
    return (
        "🛒 *بخش کانفیگ*\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:"
    )


def _buy_keyboard(gb):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data="cfg_gb_dec", style=ButtonStyle.DANGER),
            InlineKeyboardButton(text=f"{gb} گیگ", callback_data="cfg_ignore", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="➕", callback_data="cfg_gb_inc", style=ButtonStyle.SUCCESS),
        ],
        [InlineKeyboardButton(text="✅ تایید و خرید", callback_data="cfg_buy", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="cfg_home", style=ButtonStyle.DANGER)],
    ])


_DISABLED_TEXT = (
    "🔧 بخش کانفیگ فعلاً غیرفعال است و به‌زودی فعال خواهد شد.\n\n"
    "🙏 لطفاً کمی بعد دوباره تلاش کنید."
)


def _requester_tag(cq):
    u = cq.from_user
    uname = f"@{u.username}" if getattr(u, "username", None) else "—"
    name = getattr(u, "full_name", "") or ""
    return f"👤 درخواست‌دهنده: {name}\n🆔 آیدی عددی: `{u.id}`\n🔖 یوزرنیم: {uname}"


# state موقت انتخاب حجم (در حافظه)
_BUY_STATE = {}


def _get_gb(user_id, xui):
    if user_id not in _BUY_STATE:
        _BUY_STATE[user_id] = xui["min_gb"]
    return _BUY_STATE[user_id]


def _buy_text(db, user_id, xui):
    gb = _get_gb(user_id, xui)
    days = xui["fixed_days"]
    ppg = xui["price_per_gb"]
    price = calc_price(xui, gb)
    bal = db[str(user_id)].get("mah_balance", 0)
    return (
        "🛒 *خرید کانفیگ*\n\n"
        f"📦 حجم: *{gb}* گیگ\n"
        f"⏳ مدت: *{days}* روز\n"
        f"💲 قیمت هر گیگ: `{ppg:,}` میلی‌آمپر\n"
        f"💰 مبلغ نهایی: `{price:,}` میلی‌آمپر\n"
        f"🔋 موجودی شما: `{bal:,}` میلی‌آمپر\n\n"
        "⚙️ با دکمه‌های ➕ و ➖ حجم را تنظیم کنید."
    )


def _fmt_config_msg(gb, days, res):
    link = res.get("sub_link") or "(لینک ساب تنظیم نشده)"
    return (
        "✅ *کانفیگ شما آماده شد!*\n\n"
        f"📦 حجم: *{gb}* گیگ | ⏳ مدت: *{days}* روز\n\n"
        "🔗 *لینک اشتراک (Subscription):*\n"
        f"`{link}`\n\n"
        "💡 این لینک را در v2rayNG / v2rayN / Streisand وارد کنید.\n"
        "📂 همیشه از «مدیریت کانفیگ من» در دسترس است."
    )


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


def _back_home_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت به ��خش کانفیگ", callback_data="cfg_home", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="menu_main", style=ButtonStyle.DANGER)],
    ])


async def _make_and_store(db, user_id, gb, days, xui, is_free, panel):
    email = f"u{user_id}_{uuid.uuid4().hex[:6]}"
    client = XUIClient(panel)
    res = await asyncio.to_thread(client.create_config, email, gb, days)
    uid = str(user_id)
    rec = {
        "email": res["email"], "uuid": res["uuid"], "sub_id": res["sub_id"],
        "sub_link": res["sub_link"], "gb": gb, "days": days, "is_free": is_free,
        "panel_id": panel.get("id"),
        "created": datetime.now(IRAN_TZ).strftime("%Y/%m/%d %H:%M"),
        "expiry_ms": _now_ms() + int(days) * 86400000,
    }
    db[uid].setdefault("configs", []).append(rec)
    # مصرف پنل را بروز کن و در صورت پر شدن، غیرفعال کن
    panel["used_gb"] = int(panel.get("used_gb", 0)) + int(gb)
    if _panel_remaining(panel) <= 0:
        panel["active"] = False
    return res


# ============================================================
#  هندلر کالبک‌ها (master_bot تمام cfg_* را به این می‌سپارد)
# ============================================================
async def handle_cfg_callback(callback_query, bot, db, save_db, main_menu_keyboard, ADMIN_ID, user_states):
    data = callback_query.data
    user_id = callback_query.from_user.id
    xui = ensure_config(db)
    msg = callback_query.message

    if data == "cfg_ignore":
        return await callback_query.answer()

    # -------- منوی اصلی بخش کانفیگ --------
    if data == "cfg_home":
        await _safe_edit(msg, _home_text(), _home_keyboard())
        return await callback_query.answer()

    # -------- منوی خرید --------
    if data == "cfg_buy_menu":
        gb0 = _get_gb(user_id, xui)
        await _safe_edit(msg, _buy_text(db, user_id, xui), _buy_keyboard(gb0))
        return await callback_query.answer()

    if data in ("cfg_gb_inc", "cfg_gb_dec"):
        gb = _get_gb(user_id, xui)
        if data == "cfg_gb_inc":
            gb = min(xui["max_gb"], gb + xui["gb_step"])
        else:
            gb = max(xui["min_gb"], gb - xui["gb_step"])
        _BUY_STATE[user_id] = gb
        await _safe_edit(msg, _buy_text(db, user_id, xui), _buy_keyboard(gb))
        return await callback_query.answer()

    if data == "cfg_buy":
        gb = _get_gb(user_id, xui)
        days = xui["fixed_days"]
        price = calc_price(xui, gb)
        bal = db[str(user_id)].get("mah_balance", 0)
        panel = pick_panel(xui, gb)
        if panel is None:
            await _notify_admin(bot, ADMIN_ID, "⚠️ درخواست خرید کانفیگ ثبت شد ولی هیچ پنل فعالی موجود نیست!\n" + _requester_tag(callback_query))
            await _safe_edit(msg, _DISABLED_TEXT, _back_home_kb())
            return await callback_query.answer()
        if bal < price:
            return await callback_query.answer(f"❌ موجودی کافی نیست! نیاز: {price:,} - موجودی: {bal:,}", show_alert=True)
        await _safe_edit(msg, "⏳ در حال ساخت کانفیگ...", None)
        try:
            res = await _make_and_store(db, user_id, gb, days, xui, False, panel)
        except Exception as e:
            await _notify_admin(bot, ADMIN_ID, f"🔥 خطا در ساخت کانفیگ برای {user_id}:\n`{e}`")
            await _safe_edit(msg, "❌ خطا در ساخت کانفیگ. موجودی کسر نشد، با پشتیبانی در تماس باشید.", _back_home_kb())
            return await callback_query.answer()
        db[str(user_id)]["mah_balance"] = bal - price
        save_db(db)
        await _safe_edit(msg, _fmt_config_msg(gb, days, res), _back_home_kb())
        return await callback_query.answer("✅ خرید موفق!")

    # -------- تست رایگان --------
    if data == "cfg_free":
        uid = str(user_id)
        if xui.get("free_test_once") and db[uid].get("config_test_used"):
            return await callback_query.answer("❌ شما قبلاً تست رایگان کانفیگ خود را گرفته‌اید.", show_alert=True)
        gb, days = xui["free_test_gb"], xui["free_test_days"]
        panel = pick_panel(xui, gb)
        if panel is None:
            await _notify_admin(bot, ADMIN_ID, "⚠️ درخواست تست رایگان ثبت شد ولی هیچ پنل فعالی موجود نیست!\n" + _requester_tag(callback_query))
            await _safe_edit(msg, _DISABLED_TEXT, _back_home_kb())
            return await callback_query.answer()
        await _safe_edit(msg, "⏳ در حال ساخت کانفیگ تست...", None)
        try:
            res = await _make_and_store(db, user_id, gb, days, xui, True, panel)
        except Exception as e:
            await _notify_admin(bot, ADMIN_ID, f"🔥 خطا در تست رایگان {user_id}:\n`{e}`")
            await _safe_edit(msg, "❌ خطا در ساخت کانفیگ تست. با پشتیبانی در تماس باشید.", _back_home_kb())
            return await callback_query.answer()
        db[uid]["config_test_used"] = True
        save_db(db)
        await _safe_edit(msg, _fmt_config_msg(gb, days, res), _back_home_kb())
        return await callback_query.answer("🎁 کانفیگ تست ساخته شد!")

    # -------- مدیریت کانفیگ من --------
    if data == "cfg_mine":
        await _safe_edit(msg, _mine_text(db, user_id), _back_home_kb())
        return await callback_query.answer()

    # ========== بخش ادمین ==========
    if data.startswith("cfg_admin") or data in ("cfg_padd", "cfg_pdel", "cfg_plist", "cfg_setprice") or data.startswith("cfg_delp_"):
        if user_id != ADMIN_ID:
            return await callback_query.answer("⛔️ فقط مدیر.", show_alert=True)
        return await _handle_admin_cb(callback_query, bot, db, save_db, xui, user_states, ADMIN_ID)

    return await callback_query.answer()


def _admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن پنل", callback_data="cfg_padd", style=ButtonStyle.SUCCESS)],
        [InlineKeyboardButton(text="➖ حذف پنل", callback_data="cfg_pdel", style=ButtonStyle.DANGER)],
        [InlineKeyboardButton(text="📋 لیست پنل‌ها", callback_data="cfg_plist", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="💲 تنظیم قیمت هر گیگ", callback_data="cfg_setprice", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(text="🔙 بازگشت به پنل مدیریت", callback_data="menu_admin", style=ButtonStyle.DANGER)],
    ])


def _admin_menu_text(xui):
    panels = xui.get("panels", [])
    active = [p for p in panels if not _panel_is_full(p)]
    full = [p for p in panels if _panel_is_full(p)]
    return (
        "🛰 *تنظیم پنل کانفیگ*\n\n"
        f"💲 قیمت هر گیگ: `{xui['price_per_gb']:,}` میلی‌آمپر\n"
        f"📦 سقف هر پنل: `{xui['cap_per_panel']}` گیگ\n"
        f"🟢 پنل فعال: `{len(active)}` | 🔴 پرشده: `{len(full)}`"
    )


def _plist_text(xui):
    panels = xui.get("panels", [])
    if not panels:
        return "📋 هنوز هیچ پنلی اضافه نشده. با «➕ افزودن پنل» شروع کن."
    active = [p for p in panels if not _panel_is_full(p)]
    full = [p for p in panels if _panel_is_full(p)]
    out = ["📋 *لیست پنل‌ها*\n"]
    out.append("🟢 *پنل‌های فعال:*")
    if active:
        for p in active:
            out.append(f"• `{p['id']}` | {p.get('used_gb',0)}/{p.get('cap_gb',75)} گیگ | {p.get('base_url','')}")
    else:
        out.append("‌— هیچ‌کدام")
    out.append("\n🔴 *پنل‌های پرشده:*")
    if full:
        for p in full:
            out.append(f"• `{p['id']}` | {p.get('used_gb',0)}/{p.get('cap_gb',75)} گیگ | {p.get('base_url','')}")
    else:
        out.append("‌— هیچ‌کدام")
    return "\n".join(out)


def _pdel_kb(xui):
    kb = []
    for p in xui.get("panels", []):
        flag = "🔴" if _panel_is_full(p) else "🟢"
        kb.append([InlineKeyboardButton(
            text=f"🗑 {flag} {p['id']} ({p.get('used_gb',0)}/{p.get('cap_gb',75)})",
            callback_data=f"cfg_delp_{p['id']}", style=ButtonStyle.DANGER)])
    kb.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="cfg_admin_menu", style=ButtonStyle.PRIMARY)])
    return InlineKeyboardMarkup(inline_keyboard=kb)


async def _handle_admin_cb(callback_query, bot, db, save_db, xui, user_states, ADMIN_ID):
    data = callback_query.data
    user_id = callback_query.from_user.id
    msg = callback_query.message

    if data in ("cfg_admin_menu",):
        await _safe_edit(msg, _admin_menu_text(xui), _admin_menu_kb())
        return await callback_query.answer()

    if data == "cfg_plist":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data="cfg_admin_menu", style=ButtonStyle.PRIMARY)]])
        await _safe_edit(msg, _plist_text(xui), kb)
        return await callback_query.answer()

    if data == "cfg_pdel":
        await _safe_edit(msg, "🗑 پنلی که می‌خواهی حذف شود را انتخاب کن:", _pdel_kb(xui))
        return await callback_query.answer()

    if data.startswith("cfg_delp_"):
        pid = data[len("cfg_delp_"):]
        xui["panels"] = [p for p in xui.get("panels", []) if p.get("id") != pid]
        db["config"]["xui"] = xui
        save_db(db)
        await _safe_edit(msg, f"✅ پنل `{pid}` حذف شد.", _pdel_kb(xui))
        return await callback_query.answer("حذف شد")

    if data == "cfg_padd":
        _PADD_TMP[user_id] = {}
        user_states[user_id] = "cfg_padd_0"
        await _safe_edit(msg, _PANEL_STEPS[0][1], None)
        return await callback_query.answer()

    if data == "cfg_setprice":
        user_states[user_id] = "cfg_setprice_wait"
        await _safe_edit(msg, "💲 قیمت جدید هر گیگ (میلی‌آمپر) را بفرست:", None)
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


async def _notify_admin(bot, ADMIN_ID, text):
    try:
        await bot.send_message(ADMIN_ID, text)
    except Exception:
        pass


# ============================================================
#  مراحل افزودن پنل + تنظیم قیمت (ورودی متنی ادمین)
# ============================================================
_PANEL_STEPS = [
    ("base_url", "🌐 آدرس پنل را بفرست (مثلاً https://mypanel.up.railway.app):", str),
    ("web_base_path", "📁 مسیر پایهٔ پنل (web base path). اگر نداری یا مطمئن نیستی بنویس: -  (پیش‌فرض روی sub تنظیم می‌شود)", str),
    ("username", "👤 یوزرنیم لاگین پنل:", str),
    ("password", "🔑 پسورد لاگین پنل:", str),
    ("inbound_id", "🔢 آیدی اینباند (inbound id) — معمولاً 1:", int),
    ("sub_url_base", "🔗 مبنای لینک ساب (مثلاً https://mypanel.up.railway.app:2096/sub):", str),
]
_ADMIN_STEPS = _PANEL_STEPS  # سازگاری با دستور /panelset
_PADD_TMP = {}


def admin_start_state():
    return "cfg_padd_0"


async def handle_cfg_admin_message(message, bot, db, save_db, user_states, main_menu_keyboard, state):
    """ورودی‌های متنی ادمین برای افزودن پنل و تنظیم قیمت. اگر مربوط نباشد False."""
    user_id = message.chat.id
    xui = ensure_config(db)
    val = (message.text or "").strip()

    # --- تنظیم قیمت هر گیگ ---
    if state == "cfg_setprice_wait":
        if not val.isdigit():
            await message.answer("❌ فقط عدد بفرست.")
            return True
        xui["price_per_gb"] = int(val)
        db["config"]["xui"] = xui
        save_db(db)
        if user_id in user_states:
            del user_states[user_id]
        await message.answer(f"✅ قیمت هر گیگ روی `{int(val):,}` میلی‌آمپر تنظیم شد.", reply_markup=main_menu_keyboard(db, user_id))
        return True

    # --- افزودن پنل (مرحله‌ای) ---
    if state.startswith("cfg_padd_"):
        idx = int(state.split("_")[-1])
        if idx == 0:
            _PADD_TMP[user_id] = {}
        key, _prompt, caster = _PANEL_STEPS[idx]
        if key == "web_base_path" and val in ("-", "—", ""):
            val = ""
        else:
            try:
                val = caster(val)
            except Exception:
                await message.answer("❌ مقدار نامعتبر است، دوباره بفرست.")
                return True
        _PADD_TMP.setdefault(user_id, {})[key] = val
        nxt = idx + 1
        if nxt < len(_PANEL_STEPS):
            user_states[user_id] = f"cfg_padd_{nxt}"
            await message.answer(_PANEL_STEPS[nxt][1])
        else:
            p = _PADD_TMP.pop(user_id, {})
            p["id"] = "p" + uuid.uuid4().hex[:6]
            p["cap_gb"] = int(xui.get("cap_per_panel", 75))
            p["used_gb"] = 0
            p["active"] = True
            xui.setdefault("panels", []).append(p)
            db["config"]["xui"] = xui
            save_db(db)
            if user_id in user_states:
                del user_states[user_id]
            await message.answer(
                f"✅ پنل جدید با آیدی `{p['id']}` اضافه شد (سقف {p['cap_gb']} گیگ). فروش از این پنل فعال شد! 🚀",
                reply_markup=main_menu_keyboard(db, user_id),
            )
        return True

    return False
