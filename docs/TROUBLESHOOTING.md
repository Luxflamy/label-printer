# 排障指南（macOS + USB）

## 1. 找不到打印机设备

```bash
# 列出所有串口
ls -la /dev/cu.*

# 查看 USB 设备树
system_profiler SPUSBDataType | grep -A5 -i tsc
```

**处理**：
- 确认打印机已开机、USB 线插牢
- 先开打印机再插 USB，或重新插拔
- 运行 `./scripts/discover_printer.sh`

## 2. 权限被拒绝

```bash
# 查看当前用户是否在 dialout/wheel 组（Mac 通常不需要）
ls -l /dev/cu.usbserial-*
```

Mac 上 `/dev/cu.*` 一般可直接访问。若失败，检查是否有其他程序占用端口（如 CUPS、screen 会话）。

```bash
# 查看谁占用了端口
lsof /dev/cu.usbserial-XXXX
```

## 3. 打印机无反应

- 确认波特率：TTP-344M 常见为 **9600**，部分配置为 115200，查阅机身手册或试用两者
- 确认发送的是 **TSPL** 而非 ZPL
- 用 `screen` 手动测试：

```bash
screen /dev/cu.usbserial-XXXX 9600
# 粘贴 TSPL 后 Ctrl+A, K 退出
```

## 4. 打出乱码或 TSPL 源码文本

说明字节被当作普通文本打印，而非指令执行。可能原因：
- 连接到了错误的设备节点（选 `cu.` 而非 `tty.`）
- 波特率不匹配
- 误通过 CUPS 打印队列发送（本项目应直连串口，不走 CUPS）

## 5. 标签位置偏移 / 多张连打

- 检查 `SIZE` 是否与实际标签纸一致
- 检查 `GAP`：有间隙标签用 `GAP 2 mm,0`；连续纸用 `GAP 0,0`
- 检查 `DIRECTION` 是否设反
- 黑标纸改用 `BLINE` 而非 `GAP`

## 6. 条码扫不出来

- 增大条码高度（建议 ≥ 8mm）
- 检查静区：条码左右留空
- 确认 symbology 与数据匹配（如 EAN13 需 12/13 位）
- 避免条码区域被文字覆盖

## 7. 中文显示问题

TTP-344M 内置字体不支持中文。必须使用 **位图 BITMAP** 方案（见 PLAN.md 阶段 5）。

## 8. 批量打印漏打

- 增大 `config/printer.yaml` 中 `write_delay_ms`（如 50 → 200）
- 每张标签单独 `PRINT 1`，不要一次 `PRINT 100`
- 检查 USB 线质量，换短线或带屏蔽线

## 9. 日志位置

实施后日志输出至 `data/logs/label_printer.log`（阶段 6）。
