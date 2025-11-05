import subprocess
import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime

# .env 読み込み
load_dotenv()

# グローバルな requests セッション（接続プールを再利用）
SESSION = requests.Session()

def nowstr() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def check_host(ip: str) -> bool:
    """arpingで生存確認"""
    try:
        result = subprocess.run(
            ["sudo", "arping", "-c", "3", ip],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[{nowstr()}] Error: {e}")
        return False

def post_status(api_url: str, status: bool) -> bool:
    """
    APIへPOST送信。成功なら True を返す。
    """
    payload = {"status": status}
    try:
        resp = SESSION.post(api_url, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"{nowstr()} 📡 API送信成功: {status}")
            return True
        else:
            print(f"{nowstr()} ⚠️ API送信失敗: {resp.status_code} - {resp.text}")
            return False
    except requests.RequestException as e:
        print(f"{nowstr()} ❌ API送信エラー: {e}")
        return False

def main():
    api_url = os.getenv("API_URL")
    target_ip = os.getenv("SWITCH_PORT")

    if not api_url or not target_ip:
        print("⚠️ API_URL または SWITCH_PORT が未設定です（.env を確認してください）")
        return

    check_count = 12
    interval = 10  # 秒

    print(f"{nowstr()} 🎯 監視開始: {target_ip} → {api_url}")
    print(f"{nowstr()}   check_count={check_count}, interval={interval}s")

    last_sent_status = None

    try:
        while True:
            success_count = 0
            for i in range(check_count):
                idx = i + 1
                status = check_host(target_ip)
                print(f"{nowstr()} [{idx}/{check_count}] {'✅ 起動中' if status else '❌ 停止中'} ({target_ip})")

                if status:
                    success_count += 1
                time.sleep(interval)

            # すべて起動中なら True を送信
            if success_count == check_count:
                if last_sent_status is not True:
                    print(f"{nowstr()} ✅ {check_count}回連続で起動中を確認 → True を送信します。")
                    post_status(api_url, True)
                    last_sent_status = True
            else:
                # 1回でも落ちたら False を送信
                if last_sent_status is not False:
                    print(f"{nowstr()} ⚠️ 起動中でない回が存在 → False を送信します。")
                    post_status(api_url, False)
                    last_sent_status = False

    except KeyboardInterrupt:
        print(f"\n{nowstr()} ユーザーによる中断（Ctrl+C）です。終了します。")

if __name__ == "__main__":
    main()
