import threading
import subprocess
import sys
import time
from flask import Flask

app = Flask(__name__)

def run_script(script_name):
    while True:
        print(f"▶️ [System] در حال استارت {script_name}...", flush=True)
        # اجرای اسکریپت و چاپ تمام لاگ‌ها و ارورها در کنسول
        process = subprocess.Popen([sys.executable, "-u", script_name], stdout=sys.stdout, stderr=sys.stderr)
        process.communicate() # منتظر ماندن تا زمانی که اسکریپت بسته شود
        print(f"⚠️ [System] اسکریپت {script_name} متوقف/کرش شد! راه‌اندازی مجدد تا 5 ثانیه دیگر...", flush=True)
        time.sleep(5)

@app.route('/')
def home():
    return "<h1>🚀 Iliya SaaS Bots are Running Successfully!</h1><p>Check the console logs for system status and errors.</p>"

if __name__ == "__main__":
    print("✅ سیستم بیدار شد. در حال بارگذاری ربات‌ها...", flush=True)
    threading.Thread(target=run_script, args=("master_bot.py",), daemon=True).start()
    threading.Thread(target=run_script, args=("core_bot.py",), daemon=True).start()
    threading.Thread(target=run_script, args=("panel_bot.py",), daemon=True).start()
    app.run(host="0.0.0.0", port=7860)
