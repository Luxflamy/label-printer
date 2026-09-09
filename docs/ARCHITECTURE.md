# 架构设计

## 整体数据流

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  CSV / CLI   │────▶│   Template   │────▶│   LabelJob   │
│  业务数据     │     │   Renderer   │     │  (TSPL 构建)  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │ bytes
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Printer    │◀────│  USB Serial  │◀────│   TSPL       │
│  TTP-344M    │     │  Connection  │     │   bytes      │
└──────────────┘     └──────────────┘     └──────────────┘
```

## 模块职责

### `connection/` — 传输层

只负责字节流的打开、写入、关闭。不包含 TSPL 业务逻辑。

```
PrinterConnection (抽象)
    └── UsbSerialConnection
            - port, baudrate, timeout
            - connect() / send(data: bytes) / close()
            - 可选: context manager (__enter__/__exit__)
```

未来扩展：`TcpConnection`（网口 9100）实现同一接口。

### `tspl/` — 指令层

将标签描述转换为 TSPL2 文本字节流。

```
constants.py   DPI、EOL、字体映射
commands.py    LabelJob 构建器
bitmap.py      中文/图片 → BITMAP 命令（阶段 5）
```

**设计原则**：
- 输出为 `bytes`，默认 UTF-8；条码/二维码内容注意编码
- 每个 `PRINT` 前必须有完整的 `SIZE`…`CLS`…内容 序列

### `templates/` — 模板层

```
loader.py      读取 config/labels/*.yaml
renderer.py    {{ variable }} 替换 + 调用 LabelJob
```

模板只描述「画什么」，不描述「怎么连打印机」。

### `history/` — 打印历史层

```
sku_history.py   已打印 SKU 的记录与查询（data/sku_history.json）
```

只做存储与查询，不依赖 `templates/` / `tspl/` / `connection/`，因此 Service、CLI、
测试都能独立复用。写入用「临时文件 + 原子替换」，文件损坏时降级为空历史，
不会阻断打印主流程。

### `printer.py` — 编排层

高层 API，供 CLI 和后续 Web 服务复用：

```python
print_label(template_name, variables, config) -> None
print_batch(template_name, rows: list[dict], config) -> int
send_raw_file(path, config) -> None
```

### `main.py` — CLI 入口

解析命令行参数，加载配置，调用 `printer.py`。

### `config.py` — 配置

统一加载：
- `config/printer.yaml` — 连接参数
- `config/labels/*.yaml` — 模板（由 templates.loader 使用）

## 依赖关系（禁止反向依赖）

```
main.py
  → printer.py
      → templates/
      → connection/
      → tspl/
  → config.py

templates/ → tspl/
connection/ → （无内部依赖）
history/ → config.py（仅取数据目录）
tspl/ → utils/units.py
```

## 配置文件约定

| 文件 | 入库 | 说明 |
|------|------|------|
| `config/printer.example.yaml` | ✅ | 示例配置 |
| `config/printer.yaml` | ❌ | 本机实际端口，加入 .gitignore |
| `config/labels/*.yaml` | ✅ | 标签模板 |
| `data/sku_history.json` | ❌ | 已打印 SKU 历史，本机数据，加入 .gitignore |

## 错误处理策略

| 场景 | 行为 |
|------|------|
| 端口不存在 | 明确报错 + 提示运行 `discover` |
| 发送超时 | 记录日志，可选重试 |
| 模板变量缺失 | 渲染前校验，列出缺失字段 |
| 模板文件不存在 | 列出 `config/labels/` 下可用模板 |

## 测试策略

| 层级 | 方式 |
|------|------|
| `tspl/` | 纯单元测试，对比 fixture 文件 |
| `templates/` | 用固定 CSV 行渲染，快照比对 |
| `connection/` | Mock serial，不测真机 |
| 集成 | 手动 `label_printer test` 在真机验证 |
