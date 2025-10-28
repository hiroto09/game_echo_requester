# ベース（適宜バージョン変更可）
FROM python:3.11-slim

# 非対話で apt を動かすための設定
ENV DEBIAN_FRONTEND=noninteractive

# 必要パッケージを入れる（nmap, sudo, build-essential は pip ビルド用保険）
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    nmap \
    sudo \
    ca-certificates \
    gcc \
    libffi-dev \
    build-essential \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# 非rootユーザーを作成（UIDは任意）
ARG USER=app
ARG UID=1000
RUN useradd -m -u ${UID} -s /bin/bash ${USER}

# app ユーザーがパスワード無しで nmap を sudo できるように設定
# /etc/sudoers.d/nmap-runner に権限を書き込む
RUN echo "${USER} ALL=(ALL) NOPASSWD: /usr/bin/nmap" > /etc/sudoers.d/nmap-runner \
 && chmod 0440 /etc/sudoers.d/nmap-runner

# 依存ファイル（requirements）をコピーしてインストール
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# アプリケーションコードをコピー（ローカルの main.py 等を想定）
COPY . /app

# 実行ユーザーを app に切り替え（sudo が必要なnmap呼び出しは可能）
USER ${USER}

# デフォルト起動コマンド
CMD ["python3", "main.py"]
