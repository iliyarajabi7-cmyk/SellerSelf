import threading
import subprocess
import sys
import time
import traceback
from flask import Flask

app = Flask(__name__)

def run_script(script_name):
    while True:
        try:
            print(f"▶️ [System] Starting {script_name}...", flush=True)
            subprocess.run([sys.executable, "-u", script_name], check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ [Error] {script_name} stopped with error: {e}", flush=True)
        except Exception as e:
            print(f"🔥 [Crash] CRITICAL CRASH IN {script_name}:\n{traceback.format_exc()}", flush=True)
        
        print(f"🔄 [Restart] Restarting {script_name} in 5 seconds...", flush=True)
        time.sleep(5)

def run_master():
    run_script("master_bot.py")

def run_core():
    run_script("core_bot.py")

def run_panel():
    run_script("panel_bot.py")

@app.route('/')
def home():
    return "<h1>🚀 Iliya SaaS Bots are Running Successfully!</h1>"

if __name__ == "__main__":
    print("✅ System Awake. Loading robust auto-healing bots...", flush=True)
    threading.Thread(target=run_master, daemon=True).start()
    threading.Thread(target=run_core, daemon=True).start()
    threading.Thread(target=run_panel, daemon=True).start()
    app.run(host="0.0.0.0", port=7860)
