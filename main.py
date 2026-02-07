import subprocess
import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def check_host(ip: str) -> bool:
    """nmapでホストが起動しているか確認"""
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


def post_status(api_url: str, status: bool) -> bool:
    """APIへPOST"""
    try:
        resp = requests.post(
            api_url,
            json={"status": status},
            timeout=10
        )
        return resp.status_code == 200
    except requests.RequestException as e:
        print("❌ API送信エラー:", e)
        return False


def log_status(status: bool):
    """状態切り替わり時のみログ出力"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    if status:
        print(f"🟢 [{now}] 在室を検知（Switch ON）")
    else:
        print(f"🔴 [{now}] 不在を検知（Switch OFF）")


def main():
    api_url = os.getenv("API_URL")
    target_ip = os.getenv("SWITCH_PORT")

    if not api_url or not target_ip:
        print("⚠️ API_URL または SWITCH_PORT が未設定です")
        return

    print(f"🎯 監視開始: {target_ip} → {api_url}")

    check_count = 6   # 1サイクルあたりのチェック回数
    interval = 20     # 秒間隔

    last_sent_status = None  # ← 前回確定した状態

    try:
        while True:
            success_count = 0

            for i in range(check_count):
                if check_host(target_ip):
                    success_count += 1

                if i < check_count - 1:
                    time.sleep(interval)

            # ---- サイクル結果の確定状態 ----
            current_status = (success_count == check_count)

            # ---- 状態が切り替わったときのみ ----
            if current_status != last_sent_status:
                log_status(current_status)
                post_status(api_url, current_status)
                last_sent_status = current_status

    except KeyboardInterrupt:
        print("\n🛑 ユーザー中断（Ctrl+C）。終了します。")


if __name__ == "__main__":
    main()
