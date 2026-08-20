#!/usr/bin/env bash
# 本地开发启动脚本
set -e

cd "$(dirname "$0")/.."

if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在，请先：cp .env.example .env"
    exit 1
fi

echo "🚀 启动开发服务器..."
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
