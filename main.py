import subprocess
import time
import os
from dotenv import load_dotenv
from datetime import datetime
import requests

# .env 読み込み
load_dotenv()

API_URL = os.getenv("API_URL")
TARGET_IP = os.getenv("TARGET_IP")

SESSION = requests.Session()

def nowstr():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def post_status(status: bool):
    """APIへ状態をPOST送信"""
    if not API_URL:
        print(f"{nowstr()} ⚠️ API_URLが設定されていません")
        return False

    payload = {"status": status}
    try:
        resp = SESSION.post(API_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"{nowstr()} 📡 API送信成功: {status}")
            return True
        else:
            print(f"{nowstr()} ⚠️ API送信失敗: {resp.status_code} - {resp.text}")
            return False
    except requests.RequestException as e:
        print(f"{nowstr()} ❌ API送信エラー: {e}")
        return False

def check_host(ip: str) -> bool:
    """arpingで応答確認"""
    try:
        result = subprocess.run(
            ["arping", "-c", "3", ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"{nowstr()} arpingエラー: {e}")
        return False

def main():
    print(f"{nowstr()} 🛰️ 監視開始 ({TARGET_IP}) → {API_URL}")
    check_count = 12
    interval = 10  # 秒（12回 × 10秒 = 120秒 = 2分）

    last_status = None

    while True:
        success_count = 0

        for i in range(check_count):
            status = check_host(TARGET_IP)
            print(f"{nowstr()} [{i+1}/{check_count}] {'✅ 起動中' if status else '❌ 停止中'} ({TARGET_IP})")

            if status:
                success_count += 1

            time.sleep(interval)

        # 12回すべて成功
        if success_count == check_count:
            current_status = True
            print(f"{nowstr()} ✅ {check_count}回すべて成功 → 起動中")
        else:
            current_status = False
            print(f"{nowstr()} ⚠️ {check_count}回中 {success_count}回のみ成功 → 停止中")

        # 状態が変化したときのみAPI送信
        if current_status != last_status:
            post_status(current_status)
            last_status = current_status
        else:
            print(f"{nowstr()} 🔁 状態に変化なし → API送信スキップ")

        print(f"{nowstr()} ----- 次サイクルへ -----\n")

if __name__ == "__main__":
    main()
