import subprocess
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

def check_host(ip: str) -> bool:
    """nmapでホストが起動しているか確認し、結果をログに出力"""
    try:
        result = subprocess.run(
            ["nmap", "-sn", ip],
            capture_output=True,
            text=True,
            timeout=20
        )

        # --- ここで nmap の出力をログとして表示 ---
        # print("📄 nmap 出力 --------------------------")
        # print(result.stdout.strip())
        # print("--------------------------------------")

        # "Host is up" が含まれているかで判定
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
            return True
        else:
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

    check_count = 6      # 1サイクルあたりのチェック回数
    interval = 20        # 秒間隔
    last_sent_status = None

    try:
        while True:
            success_count = 0
            any_failure = False

            for i in range(check_count):
                idx = i + 1
                status = check_host(target_ip)

                if not status:
                    any_failure = True

                else:
                    success_count += 1

                # サイクル内の最後のチェックでなければ待機
                if i < check_count - 1:
                    time.sleep(interval)

            # サイクル終了後にまとめて送信判定
            if success_count == check_count:
                # 全成功 → True を送る
                if last_sent_status is not True:
                    post_status(api_url, True)
                    last_sent_status = True
            else:
                # 1回でも失敗あり → False を送る
                if last_sent_status is not False:
                    post_status(api_url, False)
                    last_sent_status = False
    except KeyboardInterrupt:
        print("\n🛑 ユーザー中断（Ctrl+C）。終了します。")


if __name__ == "__main__":
    main()
