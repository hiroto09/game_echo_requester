import subprocess
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

def check_host(ip: str) -> bool:
    """nmapでホストが起動しているか確認"""
    try:
        result = subprocess.run(
            ["sudo", "nmap", "-sn", ip],
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
    """APIへPOST。成功したら True を返す"""
    payload = {"status": status}
    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"📡 API送信成功: {status}")
            return True
        else:
            print(f"⚠️ API送信失敗: {resp.status_code} - {resp.text}")
            return False
    except requests.RequestException as e:
        print("❌ API送信エラー:", e)
        return False

def main():
    api_url = os.getenv("API_URL")
    target_ip = os.getenv("SWITCH_PORT")

    if not api_url or not target_ip:
        print("⚠️ API_URL または SWITCH_PORT が未設定です")
        return

    print(f"🎯 監視開始: {target_ip} → {api_url}")

    check_count = 12      # 1サイクルあたりのチェック回数
    interval = 10          # 秒間隔（60秒で6回 => 10秒）
    last_sent_status = None  # 直近で API に送ったステータス（True/False/None）

    try:
        while True:
            success_count = 0
            # 1サイクル（最大 check_count 回）
            for i in range(check_count):
                idx = i + 1
                status = check_host(target_ip)
                # print(f"[{idx}/{check_count}] {'✅ 起動中' if status else '❌ 停止中'} ({target_ip})")

                if not status:
                    # 停止が見つかった時点で即座に False を送る（前回と異なれば送信）
                    if last_sent_status is not False:
                        print("⚠️ 停止検出 → すぐに False を送信してサイクルをリセットします。")
                        post_status(api_url, False)
                        last_sent_status = False
                    # サイクルをリセット（breakして次サイクルへ）
                    break
                else:
                    success_count += 1

                # 最後のチェックでは sleep しない
                if i < check_count - 1:
                    time.sleep(interval)

            else:
                # for が break されずに最後まで回った（＝success_count == check_count）
                if success_count == check_count:
                    if last_sent_status is not True:
                        post_status(api_url, True)
                        last_sent_status = True

            # 1サイクル終了 → 次サイクルに移る（即座に開始）

    except KeyboardInterrupt:
        print("\nユーザーによる中断（Ctrl+C）。終了します。")

if __name__ == "__main__":
    main()
