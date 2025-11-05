# ベースイメージ
FROM python:3.11-slim

# nmap と arping をインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap arping \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# 依存パッケージをインストール
RUN pip install --no-cache-dir requests python-dotenv

# アプリコードをコピー
COPY . /app

# （USER切り替えなし → rootのまま実行）
CMD ["python", "main.py"]
