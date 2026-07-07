#!/usr/bin/env bash
# 一键启动本地开发环境：FastAPI（8765）+ Next.js（3000）
# 用法：./scripts/dev.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV_PY="$ROOT_DIR/.venv/bin/python"
WEB_DIR="$ROOT_DIR/apps/web"

if [ ! -x "$VENV_PY" ]; then
  echo "未找到 .venv，请先执行："
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -e \".[dev,api]\""
  exit 1
fi

if [ ! -d "$WEB_DIR/node_modules" ]; then
  echo "未安装前端依赖，请先执行："
  echo "  cd apps/web && npm install"
  exit 1
fi

# 释放常用端口（避免重复启动导致 Turbopack 状态损坏）
for port in 8765 3000; do
  pid=$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo "端口 $port 已被占用 (PID $pid)，正在释放…"
    kill "$pid" 2>/dev/null || true
    sleep 0.5
  fi
done

# 目录改名后 .next 内缓存的绝对路径会失效，触发 Turbopack panic：
# "Next.js package not found"。对比项目根路径，变化时自动清理。
NEXT_STAMP="$WEB_DIR/.next-project-root"
if [ -f "$NEXT_STAMP" ] && [ "$(cat "$NEXT_STAMP")" != "$ROOT_DIR" ]; then
  echo "检测到项目路径变化，清理前端缓存 .next …"
  rm -rf "$WEB_DIR/.next"
fi
echo "$ROOT_DIR" > "$NEXT_STAMP"

echo "启动 API  http://127.0.0.1:8765"
"$VENV_PY" -m uvicorn services.api.main:app --port 8765 --host 127.0.0.1 --reload &
API_PID=$!

echo "启动 Web  http://localhost:3000"
(cd "$WEB_DIR" && npm run dev) &
WEB_PID=$!

cleanup() {
  echo ""
  echo "正在停止服务…"
  kill "$API_PID" "$WEB_PID" 2>/dev/null || true
  wait "$API_PID" "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# 注意：系统自带 bash（3.2）不支持 `wait -n`，这里等待任意一个子进程退出
while kill -0 "$API_PID" 2>/dev/null && kill -0 "$WEB_PID" 2>/dev/null; do
  sleep 1
done
