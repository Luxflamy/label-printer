#!/usr/bin/env bash
# 在 macOS 上查找可能的 TSC USB 串口设备

set -e

echo "=== 串口设备 (/dev/cu.*) ==="
ls -1 /dev/cu.* 2>/dev/null || echo "(无)"

echo ""
echo "=== USB 设备（含 TSC 关键字）==="
system_profiler SPUSBDataType 2>/dev/null | grep -i -A6 -E "tsc|344|246" || echo "(未找到 TSC 相关 USB 设备，请确认打印机已连接并开机)"

echo ""
echo "提示：将上方 cu.* 路径填入 config/printer.yaml 的 connection.port"
echo "常见波特率：9600 或 115200"
