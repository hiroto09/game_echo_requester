# ベースイメージ
FROM python:3.11-slim

# nmap と arping をインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap sudo arping \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# アプリ用ユーザを作成
RUN useradd -m -u 1000 -s /bin/bash app

# sudoでパスワードなしでnmap実行を許可
RUN echo "app ALL=(ALL) NOPASSWD: /usr/bin/nmap" > /etc/sudoers.d/app

# 依存パッケージを直接インストール
RUN pip install --no-cache-dir requests python-dotenv

# アプリコードをコピー
COPY . /app

# 実行ユーザをappに切り替え
USER app

# メインスクリプトを実行
CMD ["python", "main.py"]
