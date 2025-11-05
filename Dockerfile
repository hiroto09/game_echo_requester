# ベースイメージ
FROM python:3.11-slim

# nmapインストールに必要なツールを追加
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# 依存パッケージを直接インストール
RUN pip install --no-cache-dir requests python-dotenv

# アプリコードをコピー
COPY . /app

# rootユーザーでそのまま実行
CMD ["python", "main.py"]
