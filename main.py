
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
    """
    nmap -sn -Pn を使ってホストが起動しているか確認する。
    戻り値: True == Host is up, False == Host down or error
    """
    try:
        # -sn : host discovery only
        # -Pn : skip host discovery ping probes (we rely on ARP/other LAN-level checks)
        # -n option could be added to skip DNS resolution if desired.
        cmd = ["nmap", "-sn", "-Pn", ip]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=25  # nmapの実行が長引かないようにタイムアウト
        )
        out = result.stdout or ""
        # デバッグ出力（必要なら有効に）
        # print(out)
        up = "Host is up" in out
        return up
    except subprocess.TimeoutExpired:
        print(f"{nowstr()} ❌ nmap タイムアウト")
        return False
    except FileNotFoundError:
        print(f"{nowstr()} ❌ nmap が見つかりません。nmap をインストールしてください。")
        return False
    except Exception as e:
        print(f"{nowstr()} ❌ nmap 実行エラー: {e}")
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

    # オプションの環境変数（未指定時はデフォルト値を使う）
    try:
        check_count = int(os.getenv("CHECK_COUNT", "20"))
    except ValueError:
        check_count = 20

    try:
        interval = float(os.getenv("INTERVAL", "3"))
    except ValueError:
        interval = 3.0

    print(f"{nowstr()} 🎯 監視開始: {target_ip} → {api_url}")
    print(f"{nowstr()}   check_count={check_count}, interval={interval}s")

    last_sent_status = None  # 直近でAPIに送信したステータスを保持（True/False/None）

    try:
        while True:
            success_count = 0
            # 1サイクル（最大 check_count 回）
            for i in range(check_count):
                idx = i + 1
                status = check_host(target_ip)
                print(f"{nowstr()} [{idx}/{check_count}] {'✅ 起動中' if status else '❌ 停止中'} ({target_ip})")

                if not status:
                    # 停止が見つかった時点で即座に False を送る（前回と異なれば送信）
                    if last_sent_status is not False:
                        print(f"{nowstr()} ⚠️ 停止検出 → すぐに False を送信しサイクルをリセットします。")
                        post_status(api_url, False)
                        last_sent_status = False
                    else:
                        print(f"{nowstr()} （既に False を送信済みのため再送しません）")
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
                        print(f"{nowstr()} ✅ {check_count}回連続で起動中を確認 → True を送信します。")
                        post_status(api_url, True)
                        last_sent_status = True
                    else:
                        print(f"{nowstr()} （既に True を送信済みのため再送信しません）")

            # 次サイクルへ（即座に開始）
            print(f"{nowstr()} ----- 次サイクルへ -----\n")

    except KeyboardInterrupt:
        print(f"\n{nowstr()} ユーザーによる中断（Ctrl+C）です。終了します。")

if __name__ == "__main__":
    main()