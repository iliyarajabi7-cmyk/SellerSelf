import asyncio
import json
import os
import time
import threading
from datetime import datetime, timezone, timedelta
import urllib.parse
import re
import requests
from pyrogram import Client, filters, raw, enums
from pyrogram.errors import FloodWait, UserNotParticipant, AuthKeyUnregistered, SessionExpired
import edge_tts
from gpytranslate import Translator
from huggingface_hub import HfApi

API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
DB_FILE = "database.json"

HELPER_BOT_USERNAME = "InlineHelper_Bot" 
REPO_ID = "SnowBig/SellerDB" 
HF_TOKEN = os.environ.get("HF_TOKEN")

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))
USER_SETTINGS = {}
translator = Translator()

FONTS = {1: "0123456789"}
FONTS[2] = "0123456789".translate(str.maketrans("0123456789", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"))
FONTS[3] = "0123456789".translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
FONTS[4] = "0123456789".translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))
FONTS[5] = "۰۱۲۳۴۵۶۷۸۹"
FONTS[6] = "0123456789".translate(str.maketrans("0123456789", "⓿❶❷❸❹❺❻❼❽❾"))
FONTS[7] = "0123456789".translate(str.maketrans("0123456789", "⓪①②③④⑤⑥⑦⑧⑨"))
FONTS[8] = "0123456789".translate(str.maketrans("0123456789", "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"))
FONTS[9] = "0123456789".translate(str.maketrans("0123456789", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"))
FONTS[10] = "0123456789".translate(str.maketrans("0123456789", "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿"))

ACTION_MAP = {"تایپ": enums.ChatAction.TYPING, "ویس": enums.ChatAction.RECORD_AUDIO, "عکس": enums.ChatAction.UPLOAD_PHOTO, "ویدیو": enums.ChatAction.UPLOAD_VIDEO, "گرد": enums.ChatAction.RECORD_VIDEO_NOTE, "سند": enums.ChatAction.UPLOAD_DOCUMENT, "بازی": enums.ChatAction.PLAYING, "استیکر": enums.ChatAction.CHOOSE_STICKER}

def get_iran_time(): return datetime.now(IRAN_TZ)

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def upload_to_hf():
    try:
        if HF_TOKEN:
            api = HfApi()
            api.upload_file(path_or_fileobj=DB_FILE, path_in_repo=DB_FILE, repo_id=REPO_ID, repo_type="dataset", token=HF_TOKEN, commit_message="Core DB Update")
    except: pass

def save_db(data):
    try:
        tmp_file = DB_FILE + ".tmp"
        with open(tmp_file, "w") as f: json.dump(data, f, indent=4)
        os.replace(tmp_file, DB_FILE)
        threading.Thread(target=upload_to_hf, daemon=True).start()
    except: pass

def get_hourly_drain(db, uid_str):
    u = db.get(uid_str, {})
    config = db.get("config", {})
    prices = config.get("module_prices", {})
    if u.get("has_full_package", False): return prices.get("full_package", 50)
    total = 0
    for m in u.get("active_modules", []): total += prices.get(m, 0)
    return total

def has_perm(uid, mod_key):
    if mod_key in ["p_ping", "p_info"]: return True 
    db = load_db()
    u = db.get(str(uid), {})
    if u.get("has_full_package", False): return True
    if mod_key in u.get("active_modules", []): return True
    return False

def format_time(time_str, font_id):
    return time_str.translate(str.maketrans("0123456789", FONTS.get(font_id, FONTS[1])))

async def background_tasks(app, uid):
    last_clock_time = ""
    last_bio_time = ""
    while True:
        if uid not in running_clients or running_clients[uid] is not app: break
        if not getattr(app, "is_connected", True):
            await asyncio.sleep(1); continue
            
        try:
            settings = USER_SETTINGS.get(uid, {})
            now = get_iran_time()
            time_str = now.strftime("%H:%M")
            
            if settings.get("clock_status") and has_perm(uid, "p_clock"):
                if time_str != last_clock_time:
                    ft = format_time(time_str, settings.get("font", 1))
                    base_first = settings.get("base_first_name", "User")
                    base_last = settings.get("base_last_name", "")
                    try:
                        if base_last:
                            new_last = f"{base_last} | {ft}"
                            await app.update_profile(first_name=base_first, last_name=new_last)
                        else:
                            new_first = f"{base_first} | {ft}"
                            await app.update_profile(first_name=new_first, last_name="")
                        last_clock_time = time_str
                    except FloodWait as e: await asyncio.sleep(e.value + 2)
                    except: pass

            if settings.get("bio_clock_status") and has_perm(uid, "p_clock"):
                if time_str != last_bio_time:
                    ft = format_time(time_str, settings.get("bio_font", 1))
                    bio = settings.get("base_bio", "")
                    try: await app.update_profile(bio=(f"{bio} | {ft}" if bio else ft)[:70]); last_bio_time = time_str
                    except FloodWait as e: await asyncio.sleep(e.value + 2)
                    except: pass

            if settings.get("tabchi_status") and settings.get("tabchi_text") and has_perm(uid, "p_tabchi"):
                last_t = settings.get("last_tabchi", 0)
                interval = settings.get("tabchi_interval", 30)
                if time.time() - last_t >= (interval * 60):
                    for target in list(settings.get("tabchi_targets", set())):
                        try: await app.send_message(target, settings["tabchi_text"]); await asyncio.sleep(2)
                        except FloodWait as e: await asyncio.sleep(e.value)
                        except: pass
                    USER_SETTINGS[uid]["last_tabchi"] = time.time()

            current_time = time.time()
            if has_perm(uid, "p_purge"):
                for chat_id, hours in list(settings.get("auto_clear_chats", {}).items()):
                    last_clear = settings.get("last_clear_time", {}).get(chat_id, 0)
                    if current_time - last_clear >= (hours * 3600):
                        try: await app.delete_history(chat_id, revoke=True); USER_SETTINGS[uid].setdefault("last_clear_time", {})[chat_id] = current_time
                        except: pass
        except: pass
        await asyncio.sleep(1)

def register_handlers(app, uid):
    if uid not in USER_SETTINGS:
        USER_SETTINGS[uid] = {
            "clock_status": False, "base_first_name": "", "base_last_name": "", "font": 1, "bio_clock_status": False, "base_bio": "", "bio_font": 1,
            "tabchi_status": False, "tabchi_text": "", "tabchi_targets": set(), "tabchi_interval": 30, "last_tabchi": 0,
            "auto_clear_chats": {}, "anti_spam_groups": set(), "spam_tracker": {},
            "guardian": {
                "pv": {"delete": False, "edit": False, "ttl": False},
                "group": {"delete": False, "edit": False, "ttl": False},
                "channel": {"delete": False, "edit": False, "ttl": False}
            },
            "guardian_targets": set(), "message_cache": {},
            "locks": {"pv": False, "groups": {}}, "filters": {}, "force_join": {}, "auto_reply": {}, "auto_react": {},
            "monshi_status": False, "monshi_text": "سلام! در اسرع وقت پاسخ می‌دهم. 🌹", "monshi_delay": 60, "monshi_cache": {},
            "text_mode": None, "text_link": "", "action_pv": None, "action_group": None, "muted_users": {},
            "first_comment_channels": set(), "first_comment_text": "اول! 🚀", "welcome_status": False, "welcome_text": "🌹 کاربر عزیز {name}، به گروه خوش آمدید!", "welcome_media": None
        }

    async def safe_edit(message, text):
        try: await message.edit_text(text, disable_web_page_preview=True)
        except: pass

    async def locked_msg(message):
        await safe_edit(message, "🔒 **این قابلیت قفل است!**\nلطفاً برای استفاده، آن را از بخش 'مدیریت سلف من' در ربات فروشگاه فعال کنید.")

    @app.on_message(filters.me & filters.command(["ping", "پینگ"], prefixes="."))
    async def ping_cmd(client, message):
        start = time.time(); await safe_edit(message, "⏳..."); await safe_edit(message, f"🏓 **پونگ! سلف‌ربات فعال است.**\n⚡ سرعت: `{round((time.time() - start) * 1000)}ms`")

    @app.on_message(filters.me & filters.command(["پنل", "panel"], prefixes="."), group=-1)
    async def trigger_glass_panel(client, message):
        await safe_edit(message, "⏳ در حال ارتباط با پنل شیشه‌ای امکانات...")
        try:
            results = await app.get_inline_bot_results(HELPER_BOT_USERNAME, "panel")
            if not results.results: return await safe_edit(message, f"❌ ربات پنل (`{HELPER_BOT_USERNAME}`) پاسخ نداد!\nمطمئن شوید Inline Mode در BotFather روشن است.")
            await app.send_inline_bot_result(message.chat.id, results.query_id, results.results[0].id); await message.delete()
        except Exception as e: await safe_edit(message, f"⚠️ **خطا:**\n`{e}`\n\n💡 یوزرنیم ربات پنل را بررسی کنید.")

    @app.on_message(filters.me & filters.command("پروفایل", prefixes="."))
    async def profile_manager_cmd(client, message):
        if not has_perm(uid, "p_profile"): return await locked_msg(message)
        parts = message.command
        if len(parts) < 2:
            return await safe_edit(message, "👤 **مدیریت پیشرفته پروفایل**\n\n🔸 `.پروفایل عکس` (ریپلای روی یک عکس)\n🔸 `.پروفایل اسم رضا | محمدی`\n🔸 `.پروفایل بیو [متن]`\n🔸 `.پروفایل یوزرنیم [ID]`\n🔸 `.پروفایل تولد [2005-04-15]`")
        act = parts[1]
        try:
            if act == "عکس":
                if not message.reply_to_message or not message.reply_to_message.photo: return await safe_edit(message, "❌ روی یک عکس ریپلای کنید.")
                await safe_edit(message, "⏳ در حال تنظیم عکس پروفایل...")
                dl = await message.reply_to_message.download()
                await app.set_profile_photo(photo=dl); os.remove(dl)
                await safe_edit(message, "✅ عکس پروفایل شما تغییر کرد.")
            elif act == "اسم":
                full_name = " ".join(parts[2:])
                fname, lname = (full_name.split("|", 1) + [""])[:2]
                await app.update_profile(first_name=fname.strip(), last_name=lname.strip())
                USER_SETTINGS[uid]["base_first_name"] = fname.strip()
                USER_SETTINGS[uid]["base_last_name"] = lname.strip()
                await safe_edit(message, f"✅ نام شما به `{fname.strip()} {lname.strip()}` تغییر یافت.")
            elif act == "بیو":
                bio_text = " ".join(parts[2:])[:70]
                await app.update_profile(bio=bio_text)
                USER_SETTINGS[uid]["base_bio"] = bio_text
                await safe_edit(message, f"✅ بیوگرافی تغییر یافت:\n`{bio_text}`")
            elif act == "یوزرنیم":
                if len(parts) < 3: return await safe_edit(message, "❌ یوزرنیم را وارد کنید.")
                uname = parts[2].replace("@", "")
                await safe_edit(message, f"⏳ تنظیم یوزرنیم `{uname}`...")
                try:
                    await app.set_username(uname)
                    await safe_edit(message, f"✅ یوزرنیم شما به @{uname} تغییر یافت.")
                except Exception as e:
                    err_str = str(e).upper()
                    if "OCCUPIED" in err_str or "TAKEN" in err_str:
                        await safe_edit(message, f"❌ **خطا:** این یوزرنیم توسط شخص دیگری ثبت شده است!\n\n💬 برای پیام به مالک فعلی کلیک کنید: @{uname}")
                    elif "INVALID" in err_str: await safe_edit(message, "❌ **خطا:** یوزرنیم نامعتبر است.")
                    else: await safe_edit(message, f"❌ **خطا در تنظیم:**\n`{e}`")
            elif act == "تولد":
                if len(parts) < 3: return await safe_edit(message, "❌ تاریخ را با فرمت سال-ماه-روز وارد کنید. مثال: 2005-04-15")
                y_str, m_str, d_str = parts[2].split("-")
                try:
                    await app.invoke(raw.functions.account.UpdateBirthday(birthday=raw.types.Birthday(day=int(d_str), month=int(m_str), year=int(y_str))))
                    await safe_edit(message, f"✅ تاریخ تولد شما با موفقیت تنظیم شد.")
                except Exception as e:
                    await safe_edit(message, f"❌ خطا در تنظیم تولد:\n`{e}`")
        except Exception as e: await safe_edit(message, f"❌ خطای سیستمی:\n`{e}`")

    @app.on_message(filters.me & filters.command("زماندار", prefixes="."))
    async def scheduled_msg(client, message):
        if not has_perm(uid, "p_schedule"): return await locked_msg(message)
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3 or not parts[1].isdigit(): 
            return await safe_edit(message, "⏱ **ارسال زمان‌دار**\n\n🔸 `.زماندار [دقیقه] [متن پیام]`")
        mins = int(parts[1])
        text = parts[2]
        await safe_edit(message, f"✅ پیام شما ذخیره شد و `{mins}` دقیقه دیگر در همین چت ارسال می‌شود.")
        await asyncio.sleep(mins * 60)
        try: await app.send_message(message.chat.id, text)
        except: pass

    @app.on_message(filters.me & filters.command("اسکرین", prefixes="."))
    async def screen_msg(client, message):
        if not has_perm(uid, "p_screen"): return await locked_msg(message)
        if not message.reply_to_message: return await safe_edit(message, "❌ لطفاً برای گرفتن اسکرین‌شات روی یک پیام ریپلای کنید.")
        await safe_edit(message, "⏳ در حال ساخت اسکرین‌شات باکیفیت...")
        try:
            bot_id = "QuotLyBot"
            fwd = await message.reply_to_message.forward(bot_id)
            await asyncio.sleep(2)
            async for bot_msg in app.get_chat_history(bot_id, limit=3):
                if bot_msg.sticker or bot_msg.photo or bot_msg.document:
                    dl = await bot_msg.download()
                    await app.send_document(message.chat.id, dl, file_name="Screenshot.webp")
                    os.remove(dl)
                    await message.delete()
                    return
            await safe_edit(message, "❌ سرور ساخت اسکرین‌شات در حال حاضر پاسخگو نیست.")
        except Exception as e:
            await safe_edit(message, f"❌ خطا: {e}")

    @app.on_message(filters.me & filters.command(["سین پیوی", "سین گروه", "سین کانال", "سین ربات"], prefixes="."))
    async def read_all_cmd(client, message):
        if not has_perm(uid, "p_readall"): return await locked_msg(message)
        cmd = message.command[0]; await safe_edit(message, "⏳ در حال پاکسازی تیک‌های نخوانده..."); count = 0
        try:
            async for dialog in app.get_dialogs():
                if dialog.unread_messages_count > 0:
                    ct = dialog.chat.type; should_read = False
                    if "پیوی" in cmd and ct == enums.ChatType.PRIVATE and not dialog.chat.is_bot: should_read = True
                    elif "گروه" in cmd and ct in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]: should_read = True
                    elif "کانال" in cmd and ct == enums.ChatType.CHANNEL: should_read = True
                    elif "ربات" in cmd and ct == enums.ChatType.PRIVATE and dialog.chat.is_bot: should_read = True
                    if should_read:
                        try: await app.read_chat_history(dialog.chat.id); count += 1; await asyncio.sleep(0.5)
                        except FloodWait as e: await asyncio.sleep(e.value)
                        except: pass
            await safe_edit(message, f"✅ تعداد `{count}` گفتگو با موفقیت خوانده شد.")
        except Exception as e: await safe_edit(message, f"❌ خطا: {e}")

    @app.on_message(filters.me & filters.command("کیوار", prefixes="."))
    async def qr_manager_cmd(client, message):
        if not has_perm(uid, "p_qr"): return await locked_msg(message)
        parts = message.command
        if len(parts) < 2: return await safe_edit(message, "⬛️ **مدیریت کیوآر کد**\n\n🔸 `.کیوار ساخت [لینک]`\n🔸 `.کیوار خواندن` (ریپلای)")
        act = parts[1]
        if act == "ساخت":
            text = " ".join(parts[2:])
            if message.reply_to_message and message.reply_to_message.photo:
                await safe_edit(message, "⏳ آپلود عکس..."); dl = await message.reply_to_message.download()
                def ul(): return requests.post("https://uguu.se/upload.php", files={'files[]': open(dl, 'rb')}, timeout=120)
                res = await asyncio.to_thread(ul); os.remove(dl)
                if res.status_code == 200: text = res.json()['files'][0]['url']
                else: return await safe_edit(message, "❌ خطا در آپلود.")
            if not text: return await safe_edit(message, "❌ متنی وارد نشده است.")
            await safe_edit(message, "⏳ ساخت QR Code...")
            try:
                url = f"https://api.qrserver.com/v1/create-qr-code/?size=512x512&data={urllib.parse.quote(text)}"
                res = await asyncio.to_thread(requests.get, url, timeout=10)
                fn = f"qr_{uid}.png"
                with open(fn, "wb") as f: f.write(res.content)
                await app.send_photo(message.chat.id, fn, caption="✅ QR Code ساخته شد."); await message.delete(); os.remove(fn)
            except Exception as e: await safe_edit(message, f"❌ خطا: {e}")
        elif act == "خواندن":
            if not message.reply_to_message or not message.reply_to_message.photo: return await safe_edit(message, "❌ روی یک عکس ریپلای کنید.")
            await safe_edit(message, "⏳ اسکن تصویر..."); dl = await message.reply_to_message.download()
            try:
                def scan(): return requests.post('http://api.qrserver.com/v1/read-qr-code/', files={'file': open(dl, 'rb')}, timeout=10).json()
                data = await asyncio.to_thread(scan); os.remove(dl); extracted = data[0]["symbol"][0]["data"]
                if extracted: await safe_edit(message, f"✅ **متن استخراج شده:**\n\n`{extracted}`")
                else: await safe_edit(message, "❌ هیچ کیوآر کدی یافت نشد.")
            except Exception as e: await safe_edit(message, f"❌ خطا: {e}")

    @app.on_message(filters.me & filters.command(["کانفیگ", "پروکسی"], prefixes="."))
    async def extract_vpn_proxy(client, message):
        if not has_perm(uid, "p_v2ray"): return await locked_msg(message)
        cmd = message.command[0]; is_proxy = (cmd == "پروکسی")
        await safe_edit(message, f"⏳ استخراج {'پروکسی' if is_proxy else 'کانفیگ'}..."); results, doc_files = [], []
        for ch in ["mitivpn", "vasl_bashim", "Zel2oVPN"]:
            try:
                async for msg in app.get_chat_history(ch, limit=20):
                    text = msg.text or msg.caption or ""
                    if is_proxy:
                        links = re.findall(r'(tg://proxy\?[^\s]+|https://t\.me/proxy\?[^\s]+)', text)
                        if links: results.extend(links)
                        if msg.entities:
                            for ent in msg.entities:
                                if ent.type == enums.MessageEntityType.TEXT_LINK and ent.url and 'proxy?' in ent.url: results.append(ent.url)
                    else:
                        clean_text = re.sub(r'(@[a-zA-Z0-9_]+|t\.me/[a-zA-Z0-9_]+)', '', text)
                        links = re.findall(r'(vless://\S+|vmess://\S+|trojan://\S+|ss://\S+)', clean_text)
                        if links: results.extend(links)
                        if msg.document and msg.document.file_name and msg.document.file_name.endswith(('.npvt', '.ovpn', '.conf')): doc_files.append(msg)
            except: pass
        results = list(set(results))
        if is_proxy:
            if results: await safe_edit(message, "🛡 **پروکسی‌های پرسرعت:**\n\n" + "\n\n".join(results[:10]))
            else: await safe_edit(message, "❌ پروکسی جدیدی یافت نشد.")
        else:
            final_text = "🌐 **کانفیگ‌های استخراج شده:**\n\n" + ("\n\n".join(results[:7]) if results else "یافت نشد.")
            await safe_edit(message, final_text)
            for d_msg in doc_files[:3]:
                try: fp = await app.download_media(d_msg); await app.send_document(message.chat.id, fp, caption="✅ فایل کانفیگ اختصاصی"); os.remove(fp)
                except: pass

    @app.on_message(filters.me & filters.command("ساعت", prefixes="."))
    async def clock_cmd(client, message):
        if not has_perm(uid, "p_clock"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]
        if len(parts) < 2: return await safe_edit(message, "⏰ **تنظیمات ساعت**\n\n🔸 `.ساعت اسم روشن 5`\n🔸 `.ساعت بیو روشن 9`\n❌ `.ساعت [اسم/بیو] خاموش`")
        target = parts[1]
        
        if target == "بیو":
            action = parts[2] if len(parts) > 2 else ""
            if action == "روشن":
                if not s["bio_clock_status"]:
                    try: s["base_bio"] = (await app.invoke(raw.functions.users.GetFullUser(id=await app.resolve_peer("me")))).full_user.about.rsplit(" | ", 1)[0]
                    except: s["base_bio"] = ""
                s["bio_clock_status"] = True; s["bio_font"] = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1
                await safe_edit(message, "✅ ساعت بیو فعال شد.")
            elif action == "خاموش": 
                s["bio_clock_status"] = False
                try: await app.update_profile(bio=s["base_bio"])
                except: pass
                await safe_edit(message, "❌ ساعت بیو خاموش شد.")
        elif target == "اسم":
            action = parts[2] if len(parts) > 2 else ""
            if action == "روشن":
                if not s["clock_status"]:
                    try: 
                        me = await app.get_me()
                        s["base_first_name"] = (me.first_name or "User").split(" | ")[0]
                        s["base_last_name"] = (me.last_name or "").split(" | ")[0]
                    except: 
                        s["base_first_name"] = "User"
                        s["base_last_name"] = ""
                s["clock_status"] = True; s["font"] = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1
                await safe_edit(message, "✅ ساعت اسم (روی فامیل) فعال شد.")
            elif action == "خاموش": 
                s["clock_status"] = False
                try: await app.update_profile(first_name=s["base_first_name"], last_name=s["base_last_name"])
                except: pass
                await safe_edit(message, "❌ ساعت اسم خاموش شد.")

    @app.on_message(filters.me & filters.command("اسپم", prefixes="."))
    async def spam_tool(client, message):
        if not has_perm(uid, "p_spam"): return await locked_msg(message)
        parts = message.command
        if len(parts) < 4: return await safe_edit(message, "💣 **موتور اسپم**\n\n🔸 `.اسپم [متن] [تعداد] [سرعت]`")
        speed_str, count_str = parts[-1], parts[-2]; spam_text = " ".join(parts[1:-2])
        if not count_str.isdigit(): return
        try: delay = float(speed_str)
        except ValueError: delay = 0.1 if speed_str == "سریع" else 1.0 if speed_str == "معمولی" else 3.0 if speed_str == "اهسته" else None
        if delay is None or delay < 0: return
        try: await message.delete()
        except: pass
        for _ in range(int(count_str)):
            try: await app.send_message(message.chat.id, spam_text); await asyncio.sleep(delay)
            except: break

    @app.on_message(filters.me & filters.command("نگهبان", prefixes="."))
    async def guardian_cmd(client, message):
        if not has_perm(uid, "p_guard"): return await locked_msg(message)
        s = USER_SETTINGS[uid]
        if "guardian" not in s:
            s["guardian"] = {
                "pv": {"delete": False, "edit": False, "ttl": False},
                "group": {"delete": False, "edit": False, "ttl": False},
                "channel": {"delete": False, "edit": False, "ttl": False}
            }
        parts = message.command
        if len(parts) < 2: 
            return await safe_edit(message, "🛡 **نگهبان چت پیشرفته**\n\n🔸 `.نگهبان پیوی حذف روشن`\n🔸 `.نگهبان گروه ویرایش روشن`\n🔸 `.نگهبان کانال زماندار روشن`\n🎯 `.نگهبان لیست`")
        
        target = parts[1]
        
        if target == "لیست":
            if not s["guardian_targets"]: return await safe_edit(message, "📭 لیست اهداف نگهبان خالی است (روی همه فعال است).")
            msg_str = "📋 **لیست گروه‌های تحت نظارت نگهبان:**\n"
            for t in s["guardian_targets"]: msg_str += f"🔸 `{t}`\n"
            return await safe_edit(message, msg_str)
            
        if target == "گروه" and len(parts) >= 3 and parts[2] in ["افزودن", "حذف"]:
            if parts[2] == "افزودن": s["guardian_targets"].add(message.chat.id); return await safe_edit(message, "✅ گروه فعلی به لیست نگهبان افزوده شد.")
            else: s["guardian_targets"].discard(message.chat.id); return await safe_edit(message, "❌ گروه فعلی از لیست نگهبان خارج شد.")
            
        if len(parts) < 4: return await safe_edit(message, "❌ فرمت اشتباه است. مثال: `.نگهبان پیوی حذف روشن`")
        
        action_type = parts[2] 
        state_bool = parts[3] == "روشن"
        
        if target == "پیوی":
            if action_type == "حذف": s["guardian"]["pv"]["delete"] = state_bool
            elif action_type == "ویرایش": s["guardian"]["pv"]["edit"] = state_bool
            elif action_type == "زماندار": s["guardian"]["pv"]["ttl"] = state_bool
        elif target == "گروه":
            if action_type == "حذف": s["guardian"]["group"]["delete"] = state_bool
            elif action_type == "ویرایش": s["guardian"]["group"]["edit"] = state_bool
            elif action_type == "زماندار": s["guardian"]["group"]["ttl"] = state_bool
        elif target == "کانال":
            if action_type == "حذف": s["guardian"]["channel"]["delete"] = state_bool
            elif action_type == "ویرایش": s["guardian"]["channel"]["edit"] = state_bool
            elif action_type == "زماندار": s["guardian"]["channel"]["ttl"] = state_bool
            
        await safe_edit(message, f"✅ نگهبان `{target}` برای `{action_type}` به حالت **{parts[3]}** تغییر یافت.")

    @app.on_message(filters.me & filters.command("تبچی", prefixes="."))
    async def tabchi_cmd(client, message):
        if not has_perm(uid, "p_tabchi"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]
        if len(parts) < 2: return await safe_edit(message, "📢 **تبچی خودکار**\n\n🔸 `.تبچی متن [متن]`\n🔸 `.تبچی افزودن`\n🔸 `.تبچی روشن`\n🔸 `.تبچی لیست`")
        action = parts[1]
        if action == "روشن": s["tabchi_status"] = True; await safe_edit(message, "✅ تبچی روشن شد.")
        elif action == "خاموش": s["tabchi_status"] = False; await safe_edit(message, "❌ تبچی خاموش شد.")
        elif action == "افزودن": s["tabchi_targets"].add(message.chat.id); await safe_edit(message, "✅ به لیست تبچی افزوده شد.")
        elif action == "حذف": s["tabchi_targets"].discard(message.chat.id); await safe_edit(message, "❌ از لیست تبچی حذف شد.")
        elif action == "متن" and len(parts) >= 3: s["tabchi_text"] = " ".join(parts[2:]); await safe_edit(message, "✅ متن تبلیغ آپدیت شد.")
        elif action == "زمان" and len(parts) >= 3 and parts[2].isdigit(): s["tabchi_interval"] = int(parts[2]); await safe_edit(message, f"✅ زمان به {parts[2]} تغییر یافت.")
        elif action == "لیست":
            if not s["tabchi_targets"]: return await safe_edit(message, "📭 لیست تبچی خالی است.")
            msg_str = "📋 **لیست اهداف تبچی:**\n"
            for t in s["tabchi_targets"]: msg_str += f"🔸 `{t}`\n"
            await safe_edit(message, msg_str)

    @app.on_message(filters.me & filters.command("منشی", prefixes="."))
    async def monshi_cmd(client, message):
        if not has_perm(uid, "p_monshi"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]
        if len(parts) < 2: return await safe_edit(message, "🤖 **منشی هوشمند**\n\n🔸 `.منشی روشن`\n🔸 `.منشی متن [پیام]`")
        act = parts[1]
        if act == "روشن": s["monshi_status"] = True; await safe_edit(message, "✅ منشی روشن شد.")
        elif act == "خاموش": s["monshi_status"], s["monshi_cache"] = False, {}; await safe_edit(message, "❌ منشی خاموش شد.")
        elif act == "متن" and len(parts) >= 3: s["monshi_text"] = " ".join(parts[2:]); await safe_edit(message, "✅ متن منشی آپدیت شد.")
        elif act == "زمان" and len(parts) >= 3 and parts[2].isdigit(): s["monshi_delay"] = int(parts[2]); await safe_edit(message, "✅ زمان منشی آپدیت شد.")

    @app.on_message(filters.me & filters.command("دانلود", prefixes="."))
    async def dl_cmd(client, message):
        if not has_perm(uid, "p_dl"): return await locked_msg(message)
        if len(message.command) < 2: return await safe_edit(message, "📥 **دانلودر مدیا قدرتمند**\n\n🔸 `.دانلود [لینک]`")
        link = message.command[1]
        await safe_edit(message, "⏳ پردازش فایل...")
        
        if "t.me/" in link:
            try:
                if "t.me/c/" in link: chat_id, msg_id = int("-100" + link.split("/")[4]), int(link.split("/")[5])
                else: chat_id, msg_id = link.split("/")[3], int(link.split("/")[4])
                msg = await app.get_messages(chat_id, msg_id)
                dl_path = await msg.download()
                await safe_edit(message, "⬆️ آپلود مدیا در این چت...")
                if msg.photo: await app.send_photo(message.chat.id, dl_path)
                elif msg.video: await app.send_video(message.chat.id, dl_path)
                elif msg.document: await app.send_document(message.chat.id, dl_path)
                elif msg.audio: await app.send_audio(message.chat.id, dl_path)
                elif msg.voice: await app.send_voice(message.chat.id, dl_path)
                else: await app.send_document(message.chat.id, dl_path)
                os.remove(dl_path); await message.delete(); return
            except Exception as e: return await safe_edit(message, f"❌ خطا در تلگرام:\n`{e}`")

        try:
            bot_id = "SaveAsBot"
            sent_msg = await app.send_message(bot_id, link)
            await safe_edit(message, "⏳ ارتباط با سرور ابری (منتظر دریافت مدیا)...")
            downloaded = False
            for _ in range(30):
                await asyncio.sleep(2)
                async for bot_msg in app.get_chat_history(bot_id, limit=3):
                    if bot_msg.id > sent_msg.id:
                        if bot_msg.media:
                            await safe_edit(message, "⬇️ دانلود مدیا از سرور ابری...")
                            dl_path = await bot_msg.download()
                            await safe_edit(message, "⬆️ آپلود در چت فعلی...")
                            if bot_msg.video: await app.send_video(message.chat.id, dl_path)
                            elif bot_msg.photo: await app.send_photo(message.chat.id, dl_path)
                            elif bot_msg.document: await app.send_document(message.chat.id, dl_path)
                            elif bot_msg.audio: await app.send_audio(message.chat.id, dl_path)
                            os.remove(dl_path); await message.delete()
                            downloaded = True; break
                        elif bot_msg.text and "error" in bot_msg.text.lower():
                            await safe_edit(message, "❌ لینک نامعتبر است یا ربات قادر به دانلود آن نیست.")
                            downloaded = True; break
                if downloaded: break
            if not downloaded: await safe_edit(message, "❌ سرور دانلودر پاسخ نداد (تایم‌اوت).")
            try: await app.delete_history(bot_id)
            except: pass
        except Exception as e: await safe_edit(message, f"❌ خطا در دانلودر:\n`{e}`")

    @app.on_message(filters.me & filters.command("هوش", prefixes="."))
    async def ai_cmd(client, message):
        if not has_perm(uid, "p_ai"): return await locked_msg(message)
        query = " ".join(message.command[1:])
        if not query: return await safe_edit(message, "🧠 **هوش مصنوعی**\n\n🔸 `.هوش [سوال]`")
        await safe_edit(message, "🧠 **در حال تفکر...**")
        try:
            url = f"https://text.pollinations.ai/prompt/{urllib.parse.quote(query)}"
            res = await asyncio.to_thread(requests.get, url, headers={'User-Agent': 'Mozilla'}, timeout=20)
            if res.status_code == 200: await safe_edit(message, f"🤖 **پاسخ:**\n\n{res.text}")
            else: await safe_edit(message, "❌ سرور در دسترس نیست.")
        except: await safe_edit(message, "❌ خطا در ارتباط.")

    @app.on_message(filters.me & filters.command("ایدی", prefixes="."))
    async def get_target_id_cmd(client, message):
        if not message.reply_to_message: return await safe_edit(message, "🆔 **اطلاعات حساب**\n\n🔸 ریپلای کنید و بنویسید `.ایدی`")
        target = message.reply_to_message.from_user
        info_text = f"👤 **نام:** {target.first_name}\n🌐 **یوزرنیم:** @{target.username}\n🆔 **آیدی:** `{target.id}`\n🔗 **لینک:** [کلیک کنید](tg://user?id={target.id})"
        try:
            if target.photo:
                dl = await app.download_media(target.photo.big_file_id)
                await app.send_photo(message.chat.id, dl, caption=info_text); await message.delete(); os.remove(dl)
            else: await safe_edit(message, info_text)
        except: await safe_edit(message, info_text)

    @app.on_message(filters.me & filters.command(["تاس", "تقلب"], prefixes="."))
    async def cheat_dice_cmd(client, message):
        if not has_perm(uid, "p_cheat"): return await locked_msg(message)
        parts = message.command
        if len(parts) < 3: return await safe_edit(message, "🎲 **تقلب در بازی‌ها**\n\n🔸 `.تقلب تاس 6`")
        game, target_val = parts[1], int(parts[2])
        emojis = {"تاس": "🎲", "دارت": "🎯", "بسکتبال": "🏀", "فوتبال": "⚽", "بولینگ": "🎳", "کازینو": "🎰"}
        if game not in emojis: return await safe_edit(message, "❌ بازی نامعتبر است.")
        try: await message.delete()
        except: pass
        attempts = 0
        while attempts < 30:
            try:
                msg = await app.send_dice(message.chat.id, emoji=emojis[game])
                if msg.dice.value == target_val: break 
                await msg.delete(); await asyncio.sleep(0.5); attempts += 1
            except FloodWait as e: await asyncio.sleep(e.value)
            except: break

    @app.on_message(filters.me & filters.command(["ارز", "تتر", "بیتکوین", "اتریوم", "دوج", "ترون", "سولانا", "شیبا", "کاردانو", "ریپل"], prefixes="."))
    async def crypto_price(client, message):
        if not has_perm(uid, "p_crypto"): return await locked_msg(message)
        cmd = message.command[0]
        await safe_edit(message, "⏳ در حال دریافت قیمت‌ها...")
        try:
            res = await asyncio.to_thread(requests.get, "https://api.wallex.ir/v1/markets", headers={'User-Agent': 'Mozilla'}, timeout=10)
            data = res.json()['result']['symbols']
            
            coins = {
                "تتر": ("USDT", "💵"), "بیتکوین": ("BTC", "🪙"), "اتریوم": ("ETH", "💎"),
                "ترون": ("TRX", "🔴"), "دوج": ("DOGE", "🐕"), "سولانا": ("SOL", "🌞"),
                "شیبا": ("SHIB", "🐶"), "کاردانو": ("ADA", "💠"), "ریپل": ("XRP", "🌊")
            }
            
            if cmd == "ارز":
                out = "💰 **قیمت لحظه‌ای ارزها:**\n\n"
                for c_name, (sym, emoji) in coins.items():
                    try:
                        p = float(data[f'{sym}TMN']['stats']['lastPrice'])
                        out += f"{emoji} **{c_name}:** `{p:,.0f}` تومان\n"
                    except: pass
                await safe_edit(message, out)
            else:
                if cmd in coins:
                    sym, emoji = coins[cmd]
                    try:
                        p = float(data[f'{sym}TMN']['stats']['lastPrice'])
                        await safe_edit(message, f"{emoji} **قیمت لحظه‌ای {cmd}:**\n`{p:,.0f}` تومان")
                    except: await safe_edit(message, "❌ قیمت در دسترس نیست.")
        except: await safe_edit(message, "❌ خطا در دریافت قیمت‌ها از API.")

    @app.on_message(filters.me & filters.command("ترجمه", prefixes="."))
    async def translate_text(client, message):
        if not has_perm(uid, "p_translate"): return await locked_msg(message)
        if not message.reply_to_message or not message.reply_to_message.text: return await safe_edit(message, "🌍 **مترجم آنلاین**\n\n🔸 ریپلای کنید و بنویسید `.ترجمه انگلیسی`")
        
        LANG_MAP = {"انگلیسی": "en", "فارسی": "fa", "عربی": "ar", "فرانسوی": "fr", "روسی": "ru", "المانی": "de", "ترکی": "tr", "اسپانیایی": "es", "ایتالیایی": "it", "کره": "ko", "ژاپنی": "ja"}
        t_lang = message.command[1] if len(message.command) > 1 else "fa"
        t_lang = LANG_MAP.get(t_lang, t_lang)
        
        if len(t_lang) > 2 and t_lang not in ["zh-cn", "zh-tw"]:
            return await safe_edit(message, "❌ زبان ناشناخته است. لطفاً کد زبان (مثل en) یا نام معتبر وارد کنید.")
            
        await safe_edit(message, "⏳ در حال ترجمه...")
        try:
            tr = await translator.translate(message.reply_to_message.text, targetlang=t_lang)
            await safe_edit(message, f"🌍 **ترجمه ({t_lang}):**\n\n`{tr.text}`")
        except: await safe_edit(message, "❌ خطا در سیستم مترجم.")

    @app.on_message(filters.me & filters.command("ویس", prefixes="."))
    async def tts_voice(client, message):
        if not has_perm(uid, "p_tts"): return await locked_msg(message)
        if len(message.command) < 2: return await safe_edit(message, "🎤 **تبدیل متن به ویس**\n\n🔸 `.ویس [متن]`")
        await safe_edit(message, "⏳ در حال تبدیل...")
        try:
            text, vf = " ".join(message.command[1:]), f"voice_{uid}.mp3"
            await edge_tts.Communicate(text, "fa-IR-FaridNeural").save(vf)
            await app.send_voice(message.chat.id, voice=vf, reply_to_message_id=message.reply_to_message_id)
            try: await message.delete()
            except: pass
            if os.path.exists(vf): os.remove(vf)
        except: pass

    @app.on_message(filters.me & filters.command("لینک", prefixes="."))
    async def file_to_link_cmd(client, message):
        if not has_perm(uid, "p_dl"): return await locked_msg(message)
        if not message.reply_to_message or not message.reply_to_message.media: return await safe_edit(message, "🔗 ریپلای کنید و بنویسید `.لینک`")
        await safe_edit(message, "⏳ در حال ساخت لینک...")
        try:
            fp = await message.reply_to_message.download()
            def ul(): return requests.post("https://uguu.se/upload.php", files={'files[]': open(fp, 'rb')}, timeout=120)
            res = await asyncio.to_thread(ul); os.remove(fp)
            if res.status_code == 200: await safe_edit(message, f"✅ **لینک مستقیم:**\n\n📥 `{res.json()['files'][0]['url']}`")
            else: await safe_edit(message, "❌ خطا.")
        except Exception as e: await safe_edit(message, f"❌ خطا: {e}")

    @app.on_message(filters.me & filters.command("لوگو", prefixes="."))
    async def make_logo_cmd(client, message):
        if not has_perm(uid, "p_logo"): return await locked_msg(message)
        text = " ".join(message.command[1:])
        if not text: return await safe_edit(message, "🎨 **لوگو اختصاصی**\n\n🔸 `.لوگو [متن]`")
        await safe_edit(message, "⏳ طراحی لوگو...")
        try:
            url = f"https://placehold.co/800x400/1e1e1e/00ffaa.png?text={urllib.parse.quote(text)}&font=lobster"
            res = await asyncio.to_thread(requests.get, url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            fn = f"logo_{uid}.png"
            with open(fn, "wb") as f: f.write(res.content)
            await app.send_photo(message.chat.id, fn, reply_to_message_id=message.reply_to_message_id if message.reply_to_message else None)
            await message.delete(); os.remove(fn)
        except: await safe_edit(message, "❌ خطا.")

    @app.on_message(filters.me & filters.command("اهنگ", prefixes="."))
    async def search_music(client, message):
        if not has_perm(uid, "p_music"): return await locked_msg(message)
        parts = message.command
        if len(parts) < 2: return await safe_edit(message, "🎵 **جستجوی موسیقی**\n\n🔸 `.اهنگ [اسم]`")
        query, index = " ".join(parts[1:]), 0
        if parts[-1].isdigit() and len(parts) > 2: index, query = int(parts[-1]) - 1, " ".join(parts[1:-1])
        await safe_edit(message, "🔍 جستجو...")
        try:
            results = await app.get_inline_bot_results("vkmusic_bot", query)
            if results.results:
                await app.send_inline_bot_result(message.chat.id, results.query_id, results.results[index].id)
                await message.delete()
            else: await safe_edit(message, "❌ پیدا نشد.")
        except Exception: await safe_edit(message, f"❌ خطا.")

    @app.on_message(filters.me & filters.command("قلب", prefixes="."))
    async def anim_cmd(client, message):
        if not has_perm(uid, "p_anim"): return await locked_msg(message)
        for h in ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💖"]:
            try: await message.edit_text(h); await asyncio.sleep(0.3)
            except: pass

    @app.on_message(filters.me & filters.command("تگ", prefixes=".") & filters.group)
    async def tag_all_members(client, message):
        if not has_perm(uid, "p_tag"): return await locked_msg(message)
        cid, parts = message.chat.id, message.command
        if len(parts) < 2: return await safe_edit(message, "🎯 **تگ همگانی**\n\n🔸 `.تگ [متن]`")
        txt = " ".join(parts[1:])
        try: await message.delete()
        except: pass
        try:
            batch = []
            async for m in app.get_chat_members(cid):
                if m.user and not m.user.is_bot and not m.user.is_deleted:
                    batch.append(f"[{m.user.first_name}](tg://user?id={m.user.id})")
                    if len(batch) == 5:
                        await app.send_message(cid, f"🔊 **{txt}**\n\n" + " ".join(batch)); batch = []; await asyncio.sleep(1.5)
            if batch: await app.send_message(cid, f"🔊 **{txt}**\n\n" + " ".join(batch))
        except: pass

    @app.on_message(filters.me & filters.command("پاکسازی", prefixes="."))
    async def auto_clear_cmd(client, message):
        if not has_perm(uid, "p_purge"): return await locked_msg(message)
        cid, parts, s = message.chat.id, message.command, USER_SETTINGS[uid]
        if len(parts) < 2: return await safe_edit(message, "🧹 **پاکسازی هوشمند**\n\n🔸 `.پاکسازی 12`\n🔸 `.پاکسازی خاموش`")
        if parts[1] == "خاموش": s["auto_clear_chats"].pop(cid, None); await safe_edit(message, "❌ پاکسازی خودکار متوقف شد.")
        elif parts[1].isdigit(): s["auto_clear_chats"][cid] = int(parts[1]); await safe_edit(message, f"✅ هر `{parts[1]}` ساعت پاکسازی خواهد شد.")

    @app.on_message(filters.me & filters.command("حذف", prefixes="."))
    async def purge_msgs(client, message):
        if not has_perm(uid, "p_purge"): return await locked_msg(message)
        if len(message.command) < 2 or not message.command[1].isdigit(): return await safe_edit(message, "🧹 **حذف پیام‌ها**\n\n🔸 `.حذف 50`")
        count, deleted = int(message.command[1]), 0
        try: await message.delete()
        except: pass
        async for msg in app.get_chat_history(message.chat.id, limit=count):
            if msg.from_user and msg.from_user.id == message.from_user.id:
                try: await msg.delete(); deleted += 1
                except: pass
        r = await app.send_message(message.chat.id, f"✅ `{deleted}` پیام شما پاک شد."); await asyncio.sleep(3)
        try: await r.delete()
        except: pass

    @app.on_message(filters.me & filters.command("قفل", prefixes="."))
    async def locks_cmd(client, message):
        if not has_perm(uid, "p_locks"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]["locks"]
        if len(parts) < 2: return await safe_edit(message, "🔐 **قفل‌های امنیتی**\n\n🔸 `.قفل پیوی روشن/خاموش`\n🔸 `.قفل [لینک/عکس/فوروارد/یوزرنیم/ویدیو] روشن/خاموش`")
        if parts[1] == "پیوی":
            if len(parts) == 3: s["pv"] = (parts[2] == "روشن"); return await safe_edit(message, f"{'✅ قفل پیوی فعال شد.' if s['pv'] else '❌ قفل پیوی غیرفعال شد.'}")
        else:
            tid, tlock, state = message.chat.id, parts[1], parts[2] if len(parts) > 2 else ""
            if tid not in s["groups"]: s["groups"][tid] = set()
            if state == "روشن": s["groups"][tid].add(tlock); await safe_edit(message, f"✅ قفل {tlock} فعال شد.")
            elif state == "خاموش": s["groups"][tid].discard(tlock); await safe_edit(message, f"❌ قفل {tlock} خاموش شد.")

    @app.on_message(filters.me & filters.command("فیلتر", prefixes="."))
    async def filter_cmd(client, message):
        if not has_perm(uid, "p_filter"): return await locked_msg(message)
        content, s = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else "", USER_SETTINGS[uid]["filters"]
        parts = content.split()
        if len(parts) < 2: return await safe_edit(message, "🚫 **فیلتر کلمات**\n\n🔸 `.فیلتر افزودن [کلمه]`\n🔸 `.فیلتر حذف [کلمه]`")
        tid, act, word = message.chat.id, parts[0], content.split(maxsplit=1)[1] if len(content.split(maxsplit=1)) > 1 else ""
        if tid not in s: s[tid] = set()
        if act == "افزودن" and word: s[tid].add(word.lower()); await safe_edit(message, f"✅ کلمه `{word}` فیلتر شد.")
        elif act == "حذف" and word: s[tid].discard(word.lower()); await safe_edit(message, f"❌ کلمه `{word}` از فیلتر خارج شد.")

    @app.on_message(filters.me & filters.command("اجباری", prefixes="."))
    async def forcejoin_cmd(client, message):
        if not has_perm(uid, "p_forcejoin"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]["force_join"]
        if len(parts) < 2: return await safe_edit(message, "🛑 **عضویت اجباری**\n\n🔸 `.اجباری تنظیم @channel`\n🔸 `.اجباری خاموش`")
        tid, act, ch = message.chat.id, parts[1], parts[2] if len(parts) > 2 else ""
        if act == "خاموش": s.pop(tid, None); await safe_edit(message, "❌ عضویت اجباری لغو شد.")
        elif act == "تنظیم" and ch: s[tid] = ch.replace("@", ""); await safe_edit(message, f"✅ عضویت اجباری بر روی کانال {ch} تنظیم شد.")

    @app.on_message(filters.me & filters.command("انتی", prefixes="."))
    async def anti_spam_cmd(client, message):
        if not has_perm(uid, "p_locks"): return await locked_msg(message)
        cid, parts, s = message.chat.id, message.command, USER_SETTINGS[uid]
        if len(parts) < 3 or parts[1] != "اسپم": return await safe_edit(message, "🛡 **آنتی اسپم**\n\n🔸 `.انتی اسپم روشن/خاموش`")
        if parts[2] == "روشن": s["anti_spam_groups"].add(cid); await safe_edit(message, "✅ آنتی اسپم فعال شد.")
        elif parts[2] == "خاموش": s["anti_spam_groups"].discard(cid); await safe_edit(message, "❌ آنتی اسپم خاموش شد.")

    @app.on_message(filters.me & filters.command(["سکوت", "ازادی"], prefixes="."))
    async def mute_user_cmd(client, message):
        if not has_perm(uid, "p_mute"): return await locked_msg(message)
        if not message.reply_to_message: return await safe_edit(message, "🔇 **سکوت کاربران**\n\n🔸 روی کاربر ریپلای کنید و بنویسید `.سکوت`")
        cid, tid, s = message.chat.id, message.reply_to_message.from_user.id, USER_SETTINGS[uid]["muted_users"]
        if message.command[0] == "سکوت":
            if cid not in s: s[cid] = set()
            s[cid].add(tid); await safe_edit(message, "🔇 **به حالت سکوت درآمد!**")
        else:
            if cid in s: s[cid].discard(tid)
            await safe_edit(message, "✅ **آزاد شد.**")

    @app.on_message(filters.me & filters.command("پاسخ", prefixes="."))
    async def autoreply_cmd(client, message):
        if not has_perm(uid, "p_autoreply"): return await locked_msg(message)
        content, s = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else "", USER_SETTINGS[uid]["auto_reply"]
        parts = content.split()
        if len(parts) < 2: return await safe_edit(message, "💬 **پاسخ خودکار**\n\n🔸 `.پاسخ افزودن سلام - علیک`\n🔸 `.پاسخ حذف سلام`")
        tid, act, payload = message.chat.id, parts[0], content.split(maxsplit=1)[1] if len(content.split(maxsplit=1)) > 1 else ""
        if tid not in s: s[tid] = {}
        if act == "افزودن" and "-" in payload:
            t, r = payload.split("-", 1)
            if t.strip() and r.strip(): s[tid][t.strip().lower()] = r.strip(); await safe_edit(message, f"✅ ثبت شد.")
        elif act == "حذف": s[tid].pop(payload.strip().lower(), None); await safe_edit(message, "❌ حذف شد.")

    @app.on_message(filters.me & filters.command("ریکت", prefixes="."))
    async def autoreact_cmd(client, message):
        if not has_perm(uid, "p_react"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]["auto_react"]
        if len(parts) < 2: return await safe_edit(message, "❤️ **ریکت خودکار**\n\n🔸 `.ریکت تنظیم ❤️`\n🔸 `.ریکت خاموش`")
        tid, act, emoji = message.chat.id, parts[1], parts[2] if len(parts) > 2 else ""
        if act == "خاموش": s.pop(tid, None); await safe_edit(message, "❌ لغو شد.")
        elif act == "تنظیم" and emoji: s[tid] = emoji; await safe_edit(message, f"✅ تنظیم شد.")

    @app.on_message(filters.me & filters.command("اکشن", prefixes="."))
    async def action_cmd(client, message):
        if not has_perm(uid, "p_action"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]
        if len(parts) < 3: return await safe_edit(message, "🎭 **اکشن فیک**\n\n🔸 `.اکشن پیوی تایپ`\n🔸 `.اکشن گروه عکس`\n❌ `.اکشن پیوی/گروه خاموش`")
        t, m = parts[1], parts[2]
        if m == "خاموش":
            if t == "پیوی": s["action_pv"] = None
            elif t == "گروه": s["action_group"] = None
            return await safe_edit(message, f"❌ اکشن فیک {t} خاموش شد.")
        if m not in ACTION_MAP: return await safe_edit(message, "❌ حالت نامعتبر است.")
        if t == "پیوی": s["action_pv"] = m
        elif t == "گروه": s["action_group"] = m
        await safe_edit(message, f"✅ اکشن فیک روی {m} تنظیم شد.")

    @app.on_message(filters.me & filters.command("حالت", prefixes="."))
    async def text_mode_cmd(client, message):
        if not has_perm(uid, "p_textmode"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]
        if len(parts) < 2: return await safe_edit(message, "✨ **حالت متن**\n\n🎨 `.حالت بولد`\n🎨 `.حالت کج`\n🎨 `.حالت مونو`\n🎨 `.حالت اسپویلر`\n🎨 `.حالت نقل‌قول`\n🔗 `.حالت لینکدار [لینک]`\n❌ `.حالت خاموش`")
        m = parts[1]
        if m in ["بولد", "کج", "مونو", "خط‌خورده", "زیرخط", "نقل‌قول", "اسپویلر"]: s["text_mode"] = m; await safe_edit(message, f"✅ حالت {m} تنظیم شد.")
        elif m == "لینکدار":
            if len(parts) < 3: return await safe_edit(message, "❌ لینک را وارد کنید.")
            s["text_mode"] = "link"; s["text_link"] = parts[2]; await safe_edit(message, f"✅ حالت لینکدار تنظیم شد.")
        elif m == "خاموش": s["text_mode"] = None; await safe_edit(message, "❌ استایل متن خاموش شد.")

    @app.on_message(filters.me & filters.command("کامنت", prefixes="."))
    async def first_comment_cmd(client, message):
        if not has_perm(uid, "p_comment"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]
        if len(parts) < 3: return await safe_edit(message, "📝 **کامنت‌گذار خودکار**\n\n🔸 `.کامنت افزودن @channel`\n🔸 `.کامنت متن [متن]`\n🔸 `.کامنت حذف @channel`")
        act, target = parts[1], parts[2].replace("@", "")
        if act == "افزودن": s["first_comment_channels"].add(target); await safe_edit(message, f"✅ افزوده شد.")
        elif act == "حذف": s["first_comment_channels"].discard(target); await safe_edit(message, "❌ حذف شد.")
        elif act == "متن": s["first_comment_text"] = " ".join(parts[2:]); await safe_edit(message, "✅ آپدیت شد.")

    @app.on_message(filters.me & filters.command("خوشامد", prefixes="."))
    async def welcome_sys_cmd(client, message):
        if not has_perm(uid, "p_monshi"): return await locked_msg(message)
        parts, s = message.command, USER_SETTINGS[uid]
        if len(parts) < 2: return await safe_edit(message, "👋 **خوشامدگویی گروه**\n\n🔸 `.خوشامد روشن/خاموش`\n🔸 `.خوشامد متن سلام {name}`\n🔸 `.خوشامد مدیا` (ریپلای روی عکس)")
        act = parts[1]
        if act == "روشن": s["welcome_status"] = True; await safe_edit(message, "✅ فعال شد.")
        elif act == "خاموش": s["welcome_status"] = False; await safe_edit(message, "❌ خاموش شد.")
        elif act == "متن" and len(parts) >= 3: s["welcome_text"] = " ".join(parts[2:]); await safe_edit(message, "✅ متن آپدیت شد.")
        elif act == "مدیا":
            if not message.reply_to_message or not (message.reply_to_message.photo or message.reply_to_message.animation): return await safe_edit(message, "❌ روی یک عکس یا گیف ریپلای کنید.")
            s["welcome_media"] = {"type": "photo", "id": message.reply_to_message.photo.file_id} if message.reply_to_message.photo else {"type": "animation", "id": message.reply_to_message.animation.file_id}
            await safe_edit(message, "✅ مدیا ذخیره شد.")

    @app.on_message(~filters.me, group=0)
    async def master_incoming_processor(client, message):
        cid, mtype, sender, s = message.chat.id, message.chat.type, message.from_user.id if message.from_user else None, USER_SETTINGS[uid]
        if has_perm(uid, "p_mute") and cid in s["muted_users"] and sender in s["muted_users"][cid]:
            try: return await message.delete()
            except: pass
        if has_perm(uid, "p_locks"):
            if cid in s["anti_spam_groups"] and sender:
                now = time.time(); u_spam = s["spam_tracker"].setdefault(cid, {}).setdefault(sender, [])
                u_spam.append(now); u_spam = [t for t in u_spam if now - t < 5]; s["spam_tracker"][cid][sender] = u_spam
                if len(u_spam) >= 5:
                    try: return await message.delete()
                    except: pass
            if mtype == enums.ChatType.PRIVATE and s["locks"]["pv"]:
                try: return await message.delete()
                except: pass
        targets = [cid]
        if has_perm(uid, "p_forcejoin"):
            for t in targets:
                if t in s["force_join"] and sender:
                    try: await app.get_chat_member(s["force_join"][t], sender)
                    except UserNotParticipant:
                        try:
                            await message.delete(); warn = await app.send_message(cid, f"⚠️ برای ارسال پیام باید در @{s['force_join'][t]} عضو شوید."); await asyncio.sleep(5); await warn.delete(); return
                        except: pass
                    except: pass; break 
        if has_perm(uid, "p_locks"):
            for t in targets:
                if t in s["locks"]["groups"]:
                    al, sd = s["locks"]["groups"][t], False
                    if "لینک" in al and message.entities and any(e.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK] for e in message.entities): sd = True
                    if "یوزرنیم" in al and message.entities and any(e.type == enums.MessageEntityType.MENTION for e in message.entities): sd = True
                    if "ریپلای" in al and message.reply_to_message: sd = True
                    if "فوروارد" in al and message.forward_date: sd = True
                    if "عکس" in al and message.photo: sd = True
                    if "ویدیو" in al and message.video: sd = True
                    if sd:
                        try: return await message.delete()
                        except: pass
        if getattr(message, "text", None):
            tl = message.text.lower()
            if has_perm(uid, "p_filter"):
                for t in targets:
                    if t in s["filters"] and any(bw in tl for bw in s["filters"][t]):
                        try: return await message.delete()
                        except: pass
            if has_perm(uid, "p_autoreply"):
                for t in targets:
                    if t in s["auto_reply"] and tl in s["auto_reply"][t]:
                        try: await message.reply_text(s["auto_reply"][t][tl])
                        except: pass
        if has_perm(uid, "p_react"):
            for t in targets:
                if t in s["auto_react"]:
                    try: await app.send_reaction(cid, message.id, s["auto_react"][t]); break
                    except: pass

    @app.on_message(filters.channel & ~filters.me, group=-1)
    async def auto_commenter(client, message):
        if not has_perm(uid, "p_comment"): return
        s = USER_SETTINGS[uid]
        if message.chat.username in s["first_comment_channels"] or str(message.chat.id) in s["first_comment_channels"]:
            try: await asyncio.sleep(2); m = await app.get_discussion_message(message.chat.id, message.id); await m.reply_text(s["first_comment_text"])
            except: pass

    @app.on_message(~filters.me, group=2)
    async def action_trigger(client, message):
        if not has_perm(uid, "p_action"): return
        s = USER_SETTINGS[uid]
        try:
            if message.chat.type == enums.ChatType.PRIVATE and s["action_pv"]: await app.send_chat_action(message.chat.id, ACTION_MAP[s["action_pv"]])
            elif message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP] and s["action_group"]: await app.send_chat_action(message.chat.id, ACTION_MAP[s["action_group"]])
        except: pass

    @app.on_message(filters.private & ~filters.me, group=3)
    async def monshi_responder(client, message):
        if not has_perm(uid, "p_monshi"): return
        if not getattr(message, "text", None) and not getattr(message, "photo", None) and not getattr(message, "voice", None) and not getattr(message, "video", None) and not getattr(message, "document", None) and not getattr(message, "audio", None) and not getattr(message, "animation", None) and not getattr(message, "sticker", None):
            return
        s = USER_SETTINGS[uid]
        if not s["monshi_status"] or (message.from_user and message.from_user.is_bot): return
        cid = message.chat.id
        if time.time() - s["monshi_cache"].get(cid, 0) >= s["monshi_delay"]:
            try: await message.reply_text(s["monshi_text"]); s["monshi_cache"][cid] = time.time()
            except: pass

    @app.on_message(~filters.me, group=4)
    async def guardian_cacher_and_ttl(client, message):
        if not has_perm(uid, "p_guard"): return
        s = USER_SETTINGS[uid]
        if "guardian" not in s: return
        s["message_cache"][message.id] = message
        if len(s["message_cache"]) > 500: s["message_cache"].pop(next(iter(s["message_cache"])))
        if message.chat.type == enums.ChatType.PRIVATE and s["guardian"]["pv"]["ttl"]:
            is_ttl = False
            for m_type in ["photo", "video", "voice", "video_note"]:
                if getattr(message, m_type, None) and getattr(getattr(message, m_type), "ttl_seconds", None): is_ttl = True; break
            if is_ttl:
                try:
                    dl = await message.download()
                    await app.send_document("me", dl, caption=f"🔥 **زمان‌دار ذخیره شد!**\n👤 از: `{message.from_user.first_name}`")
                    os.remove(dl)
                except: pass

    @app.on_edited_message(~filters.me)
    async def anti_edit(client, message):
        if not has_perm(uid, "p_guard"): return
        s = USER_SETTINGS[uid]
        if "guardian" not in s: return
        if s["guardian_targets"] and message.chat.id not in s["guardian_targets"]: return
        old = s["message_cache"].get(message.id)
        
        chat_type = message.chat.type
        is_pv = chat_type == enums.ChatType.PRIVATE
        is_group = chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]
        is_channel = chat_type == enums.ChatType.CHANNEL
        
        guard_conf = s["guardian"]
        if is_pv and not guard_conf["pv"]["edit"]: return
        if is_group and not guard_conf["group"]["edit"]: return
        if is_channel and not guard_conf["channel"]["edit"]: return
        
        try: await app.send_message("me", f"✏️ **ویرایش شد!**\n👤 `{message.from_user.first_name}`\n❌ **اصلی:**\n{old.text if old and old.text else '[مدیا]'}\n✅ **جدید:**\n{message.text or '[حذف]'}")
        except: pass

    @app.on_deleted_messages()
    async def anti_delete(client, messages):
        if not has_perm(uid, "p_guard"): return
        s = USER_SETTINGS[uid]
        if "guardian" not in s: return
        for msg in messages:
            if msg.id in s["message_cache"]:
                c = s["message_cache"][msg.id]
                if s["guardian_targets"] and c.chat.id not in s["guardian_targets"]: continue
                
                chat_type = c.chat.type
                is_pv = chat_type == enums.ChatType.PRIVATE
                is_group = chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]
                is_channel = chat_type == enums.ChatType.CHANNEL
                
                guard_conf = s["guardian"]
                if is_pv and not guard_conf["pv"]["delete"]: continue
                if is_group and not guard_conf["group"]["delete"]: continue
                if is_channel and not guard_conf["channel"]["delete"]: continue
                
                try: await app.send_message("me", f"🗑 **حذف شد!**\n👤 `{c.from_user.first_name if c.from_user else 'ناشناس'}`\n💬 **متن:**\n{c.text or '[بدون متن]'}")
                except: pass

    @app.on_message(filters.new_chat_members & filters.group)
    async def welcome_new_member(client, message):
        if not has_perm(uid, "p_monshi") or not USER_SETTINGS[uid]["welcome_status"]: return
        for m in message.new_chat_members:
            if m.is_self: continue 
            msg_text = USER_SETTINGS[uid]["welcome_text"].replace("{name}", f"[{m.first_name or 'کاربر'}](tg://user?id={m.id})")
            try:
                if USER_SETTINGS[uid]["welcome_media"]:
                    med = USER_SETTINGS[uid]["welcome_media"]
                    if med["type"] == "photo": await app.send_photo(message.chat.id, med["id"], caption=msg_text)
                    else: await app.send_animation(message.chat.id, med["id"], caption=msg_text)
                else: await app.send_message(message.chat.id, msg_text)
            except: pass

    @app.on_message(filters.me & filters.text & ~filters.command(["ping", "پینگ", "پنل", "panel", "پروفایل", "هوش", "لینک", "ارز", "تتر", "بیتکوین", "اتریوم", "دوج", "ترون", "سولانا", "شیبا", "کاردانو", "ریپل", "لوگو", "ترجمه", "اهنگ", "ویس", "تگ", "تقلب", "تاس", "ساعت", "تبچی", "اسپم", "پاکسازی", "حذف", "دانلود", "قفل", "فیلتر", "اجباری", "پاسخ", "ریکت", "نگهبان", "انتی", "سکوت", "ازادی", "منشی", "اکشن", "حالت", "ایدی", "قلب", "کامنت", "خوشامد", "سین پیوی", "سین گروه", "سین کانال", "سین ربات", "کیوار", "کانفیگ", "پروکسی", "زماندار", "اسکرین"], prefixes=[".", "/", ""]))
    async def auto_text_formatter(client, message):
        if not has_perm(uid, "p_textmode"): return
        m = USER_SETTINGS[uid]["text_mode"]
        if m and not message.text.startswith((".", "/")):
            txt = message.text
            if m == "بولد": fmt = f"<b>{txt}</b>"
            elif m == "کج": fmt = f"<i>{txt}</i>"
            elif m == "مونو": fmt = f"<code>{txt}</code>"
            elif m == "خط‌خورده": fmt = f"<s>{txt}</s>"
            elif m == "زیرخط": fmt = f"<u>{txt}</u>"
            elif m == "نقل‌قول": fmt = f"<blockquote>{txt}</blockquote>"
            elif m == "اسپویلر": fmt = f"<tg-spoiler>{txt}</tg-spoiler>"
            elif m == "link": fmt = f"<a href='{USER_SETTINGS[uid].get('text_link', '')}'>{txt}</a>"
            else: fmt = txt
            try: await message.edit_text(fmt, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
            except: pass

running_clients = {}

def hide_annoying_errors(loop, context):
    if "Peer id invalid" not in str(context.get("exception")): loop.default_exception_handler(context)

async def main():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(hide_annoying_errors)
    print("=====================================")
    print("🚀 Smart Core SaaS Engine is Starting...")
    print("=====================================")
    while True:
        try:
            db = load_db()
            needs_save = False
            now_ts = int(time.time())
            
            for uid_str, data in list(db.items()):
                if uid_str == "config": continue
                uid = int(uid_str)
                status = data.get("status", "inactive")

                if "mah_balance" not in data:
                    data["mah_balance"] = data.get("coin_balance", data.get("wallet_balance", 0))
                    needs_save = True
                if "active_modules" not in data:
                    data["active_modules"] = []
                    needs_save = True
                if "has_full_package" not in data:
                    data["has_full_package"] = False
                    needs_save = True
                if "last_drain_time" not in data:
                    data["last_drain_time"] = now_ts
                    needs_save = True
                
                last_drain = data["last_drain_time"]
                
                if status == "active":
                    if now_ts - last_drain >= 3600:
                        drain = get_hourly_drain(db, uid_str)
                        data["mah_balance"] -= drain
                        data["last_drain_time"] = now_ts
                        needs_save = True

                    if data["mah_balance"] <= 0:
                        data["status"] = "paused"
                        data["paused_at"] = get_iran_time().replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
                        data["mah_balance"] = 0
                        needs_save = True
                        if uid in running_clients:
                            try: await running_clients[uid].send_message("me", "❌ **باتری سلف‌ربات شما تمام شد!**\nربات خاموش شد. لطفاً شارژ پاوربانک تهیه کنید.")
                            except: pass
                            await running_clients[uid].stop(); del running_clients[uid]
                        continue
                        
                    if uid not in running_clients:
                        try:
                            app = Client(f"user_{uid}", api_id=API_ID, api_hash=API_HASH, session_string=data["session"], in_memory=True)
                            register_handlers(app, uid)
                            await app.start()
                            asyncio.create_task(background_tasks(app, uid))
                            running_clients[uid] = app
                        except (AuthKeyUnregistered, SessionExpired):
                            data["status"] = "inactive"; data["session"] = ""; needs_save = True
                        except Exception as e: print(f"Failed to start user client {uid}: {e}")
                        
                elif status in ["paused", "inactive"]:
                    if uid in running_clients:
                        if status == "paused":
                            try: await running_clients[uid].send_message("me", "⏸ **سلف‌ربات شما متوقف شد و مصرف باتری صفر گردید.**")
                            except: pass
                        await running_clients[uid].stop(); del running_clients[uid]
                        
            if needs_save: save_db(db)
            
        except Exception as e: print(f"Core Global Loop Error: {e}")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
