import threading
import subprocess
import sys
from flask import Flask

app = Flask(__name__)

def run_master():
    print("▶️ [System] در حال استارت ربات فروشگاه...", flush=True)
    subprocess.run([sys.executable, "-u", "master_bot.py"])

def run_core():
    print("▶️ [System] در حال استارت هسته سلف‌ربات...", flush=True)
    subprocess.run([sys.executable, "-u", "core_bot.py"])

def run_panel():
    print("▶️ [System] در حال استارت ربات اختصاصی پنل شیشه‌ای...", flush=True)
    subprocess.run([sys.executable, "-u", "panel_bot.py"])

@app.route('/')
def home():
    return "<h1>🚀 Iliya SaaS Bots are Running Successfully!</h1>"

if __name__ == "__main__":
    print("✅ سیستم بیدار شد. در حال بارگذاری ربات‌ها...", flush=True)
    threading.Thread(target=run_master, daemon=True).start()
    threading.Thread(target=run_core, daemon=True).start()
    threading.Thread(target=run_panel, daemon=True).start()
    app.run(host="0.0.0.0", port=7860)