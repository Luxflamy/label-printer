#!/usr/bin/env bash
# 使用 screen 手动发送测试 TSPL（需先配置端口）
# 用法: PORT=/dev/cu.usbserial-XXX ./scripts/test_print.sh

set -e

PORT="${PORT:-}"
BAUD="${BAUD:-9600}"
FIXTURE="$(dirname "$0")/../tests/fixtures/hello.tspl"

if [[ -z "$PORT" ]]; then
  echo "请指定端口: PORT=/dev/cu.usbserial-XXXX ./scripts/test_print.sh"
  exit 1
fi

if [[ ! -f "$FIXTURE" ]]; then
  echo "找不到测试文件: $FIXTURE"
  exit 1
fi

echo "将向 $PORT @ $BAUD 发送 $FIXTURE"
echo "（需要安装 screen: brew install screen）"

# 通过 cat 管道发送（比 screen 更适合脚本）
stty -f "$PORT" "$BAUD" 2>/dev/null || true
cat "$FIXTURE" > "$PORT"
echo "已发送，请检查打印机输出"
