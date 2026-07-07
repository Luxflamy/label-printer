# USB 直连打印 — 详细实施计划

> 打印机：TSC TTP-344M（TSC344）  
> 协议：TSPL2  
> 连接：USB（macOS 表现为串口设备）  
> 方案：路线 A — 程序直发原始指令，不经 QZ Tray / CUPS Raw

---

## 一、技术原理

### 1.1 USB 在 Mac 上的形态

TTP-344M 的 USB 口在 macOS 上通常枚举为 **USB CDC 串口设备**，设备节点类似：

```
/dev/cu.usbserial-XXXX
/dev/cu.usbmodem-XXXX
```

程序通过 **pyserial** 以固定波特率（常见 9600 或 115200，以手册为准）打开该端口，写入 TSPL 文本字节流即可。

### 1.2 TSPL2 打印最小闭环

每张标签的指令序列：

```
SIZE <宽>,<高>          # 标签尺寸（单位 mm 或 inch，见手册）
GAP <间隙>,<偏移>       # 标签间隙
DIRECTION 1             # 打印方向
CLS                     # 清空缓冲区
TEXT ...                # 文字
BARCODE ...             # 一维码（可选）
QRCODE ...              # 二维码（可选）
PRINT 1                 # 打印 1 张
```

行尾使用 `\r\n`（CRLF）。

### 1.3 分辨率与坐标

TTP-344M 标准分辨率为 **203 dpi**（8 dots/mm）。模板中建议用 **毫米** 描述布局，渲染时转换为 dots：

```
dots = mm × 8
```

---

## 二、分阶段实施计划

### 阶段 0：硬件与环境确认（0.5 天）

**目标**：确认 USB 通信可用，不写业务代码。

| 步骤 | 操作 | 验收标准 |
|------|------|----------|
| 0.1 | USB 连接打印机，开机 | Mac 识别设备 |
| 0.2 | 运行 `scripts/discover_printer.sh` | 能看到 `/dev/cu.*` 设备 |
| 0.3 | 用 `screen` 或 minicom 手动发 TSPL | 打印机打出测试标签 |
| 0.4 | 记录：设备路径、波特率、标签纸宽高 | 写入 `config/printer.yaml` |

**手动测试用 TSPL 样例**（保存为 `tests/fixtures/hello.tspl`）：

```tspl
SIZE 40 mm,30 mm
GAP 2 mm,0 mm
DIRECTION 1
CLS
TEXT 20,20,"3",0,1,1,"USB TEST"
PRINT 1
```

---

### 阶段 1：连接层（1 天）

**目标**：封装 USB 串口读写，支持连接、发送、断开。

| 任务 | 文件 | 说明 |
|------|------|------|
| 连接抽象接口 | `src/label_printer/connection/base.py` | `connect()` / `send()` / `close()` |
| USB 串口实现 | `src/label_printer/connection/usb_serial.py` | pyserial 封装 |
| 配置加载 | `src/label_printer/config.py` | 读取 `config/printer.yaml` |
| 单元测试 | `tests/test_connection.py` | Mock 串口，不测真机 |

**`config/printer.yaml` 关键字段**：

```yaml
connection:
  type: usb_serial
  port: /dev/cu.usbserial-XXXX    # 运行 discover 脚本后填写
  baudrate: 9600
  timeout: 5
  write_delay_ms: 50              # 发送后短暂等待，避免缓冲区溢出
```

**验收**：`python -m label_printer ping` 能打开端口且无异常（可不打印）。

---

### 阶段 2：TSPL 指令层（1–2 天）

**目标**：用 Python 构建 TSPL 命令，避免手写字符串拼接错误。

| 任务 | 文件 | 说明 |
|------|------|------|
| 常量 | `src/label_printer/tspl/constants.py` | DPI、行尾符、默认字体 |
| 命令构建器 | `src/label_printer/tspl/commands.py` | `LabelJob` 类：链式 API |
| 单位换算 | `src/label_printer/utils/units.py` | mm ↔ dots |
| 单元测试 | `tests/test_commands.py` | 断言生成的 TSPL 字符串 |

**`LabelJob` 设计示例**（接口规划，非最终实现）：

```python
job = LabelJob(width_mm=40, height_mm=30, gap_mm=2)
job.text(x_mm=5, y_mm=5, content="品名", font="3")
job.barcode(x_mm=5, y_mm=15, code="1234567890", symbology="128")
tspl_bytes = job.build()  # bytes, UTF-8 或指定编码
```

**验收**：`tests/test_commands.py` 全部通过；生成字节流与 `tests/fixtures/` 中样例一致。

---

### 阶段 3：模板系统（1–2 天）

**目标**：标签布局与业务数据分离，改样式不改代码。

| 任务 | 文件 | 说明 |
|------|------|------|
| 模板格式定义 | `config/labels/default.yaml` | 尺寸 + 元素列表 |
| 模板加载 | `src/label_printer/templates/loader.py` | 解析 YAML |
| 模板渲染 | `src/label_printer/templates/renderer.py` | 变量替换 → `LabelJob` |
| 示例数据 | `data/samples/products.csv` | 测试用 |

**模板 YAML 结构规划**：

```yaml
name: default
label:
  width_mm: 40
  height_mm: 30
  gap_mm: 2
  direction: 1
elements:
  - type: text
    x_mm: 3
    y_mm: 3
    font: "3"
    content: "{{ product_name }}"
  - type: barcode
    x_mm: 3
    y_mm: 12
    symbology: "128"
    content: "{{ barcode }}"
    height_mm: 8
```

**验收**：`python -m label_printer render --template default --row 1` 输出可读的 TSPL 文本到 stdout。

---

### 阶段 4：CLI 与打印流程（1 天）

**目标**：提供命令行入口，串联连接层 + 模板 + 发送。

| 命令 | 说明 |
|------|------|
| `label_printer discover` | 列出可用串口及推荐配置 |
| `label_printer ping` | 测试端口是否可打开 |
| `label_printer test` | 发送 `hello.tspl` 固定测试页 |
| `label_printer render` | 预览 TSPL（不打印） |
| `label_printer print` | 按模板 + 数据文件打印 |
| `label_printer raw` | 直接发送 `.tspl` / `.prn` 文件 |

| 文件 | 说明 |
|------|------|
| `src/label_printer/main.py` | argparse CLI |
| `src/label_printer/printer.py` | 高层 `print_label()` / `print_batch()` |

**验收**：`python -m label_printer test` 在真机上打出测试标签。

---

### 阶段 5：中文与图片（按需，1–2 天）

TTP-344M 内置字体对中文支持有限，可选方案：

| 方案 | 实现位置 | 适用 |
|------|----------|------|
| A. 位图贴图 | `src/label_printer/tspl/bitmap.py` | 中文、Logo，推荐 |
| B. 下载字体到打印机 | `src/label_printer/tspl/font.py` | 固定字号、量产场景 |
| C. 仅用英文/数字 | 无需额外模块 | 条码标签为主 |

位图流程：Pillow 渲染文字/图片 → 单色 BMP → `BITMAP` 命令。

**验收**：含中文的模板能正确打印（边缘清晰、位置正确）。

---

### 阶段 6：健壮性与生产化（按需）

| 任务 | 说明 |
|------|------|
| 重试机制 | 发送失败自动重连 1–3 次 |
| 打印队列 | 批量打印时逐张发送，间隔 `write_delay_ms` |
| 日志 | `logging` 输出到 `data/logs/` |
| 预览 | 可选：将 TSPL 渲染为 PNG 预览（后期） |

---

## 三、实施时间线（参考）

```
第 1 天   阶段 0 + 阶段 1   USB 连通 + 连接层
第 2 天   阶段 2           TSPL 构建器 + 测试
第 3 天   阶段 3           模板系统
第 4 天   阶段 4           CLI + 真机联调
第 5 天+  阶段 5/6         中文、批量、打磨
```

---

## 四、风险与对策

| 风险 | 对策 |
|------|------|
| Mac 找不到 USB 设备 | 检查线缆、开机顺序；运行 `system_profiler SPUSBDataType` |
| 打出 TSPL 源码而非标签 | 说明数据发到了错误端点；确认用串口而非 CUPS 队列 |
| 中文乱码/方块 | 改用位图方案（阶段 5） |
| 条码扫不出 | 检查 symbology、静区、高度；参考 TSPL 手册 BARCODE 参数 |
| 位置偏移 | 校准 `GAP`、检查 `DIRECTION`、用 mm→dots 换算 |
| 连续打印卡纸/漏打 | 增大 `write_delay_ms`；批量时逐张 `PRINT 1` |

---

## 五、后续扩展（本期不做）

- Web 前端 + 本地 API 服务（FastAPI）
- 如需多机 Web 打印，再评估 QZ Tray
- 网口打印：新增 `connection/tcp.py`，连接 `IP:9100`
- 标签设计器 GUI

---

## 六、开发顺序检查清单

- [ ] 阶段 0：USB 手动 TSPL 测试成功
- [ ] 阶段 1：`ping` 命令通过
- [ ] 阶段 2：TSPL 单元测试通过
- [ ] 阶段 3：模板渲染输出正确
- [ ] 阶段 4：`test` 真机打印成功
- [ ] 阶段 5：中文标签（如需要）
- [ ] 阶段 6：批量打印稳定
