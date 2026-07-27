import subprocess
import os
import time
import threading

from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI()

# =========================
# 現在のSwitch起動状態
# =========================
packet_status = False


# =========================
# nmapでホスト確認
# =========================
def check_host(ip: str) -> bool:
    try:
        result = subprocess.run(
            ["nmap", "-sn", ip],
            capture_output=True,
            text=True,
            timeout=20
        )

        return "Host is up" in result.stdout

    except subprocess.TimeoutExpired:
        print("❌ nmap タイムアウト")
        return False

    except Exception as e:
        print("❌ nmap実行エラー:", e)
        return False


# =========================
# バックグラウンド監視
# =========================
def monitor():

    global packet_status

    target_ip = os.getenv("SWITCH_PORT")

    if not target_ip:
        print("⚠️ SWITCH_PORT が設定されていません")
        return

    print(f"🎯 監視開始 : {target_ip}")

    check_count = 6
    interval = 20

    while True:

        success_count = 0

        for i in range(check_count):

            if check_host(target_ip):
                success_count += 1

            if i < check_count - 1:
                time.sleep(interval)

        packet_status = (success_count == check_count)

        print("Switch:", "ON" if packet_status else "OFF")


# =========================
# GET API
# =========================
@app.get("/packet")
async def get_packet():
    return {
        "packet": packet_status
    }


# =========================
# メイン
# =========================
if __name__ == "__main__":

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )