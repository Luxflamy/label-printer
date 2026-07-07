# TSC 标签打印机 — USB 直连打印

基于 **TSPL2 原始指令** 驱动 TSC TTP-344M（TSC344）系列标签机，通过 **USB 串口直连**，不依赖 QZ Tray 或浏览器。

## 目标

- Mac 上通过 USB 直接发送 TSPL2 命令到打印机
- 标签布局用 YAML 模板描述，业务数据与布局分离
- 提供 CLI 工具：发现设备、测试打印、按模板批量打印

## 快速开始（CLI）

```bash
# 1. 创建虚拟环境并安装依赖（含本地 API 所需的 fastapi/uvicorn）
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,api]"

# 2. 复制并编辑打印机配置
cp config/printer.example.yaml config/printer.yaml
# macOS 上若打印机已在"系统设置 → 打印机与扫描仪"添加，用 cups_raw + 队列名即可，
# 无需 /dev/cu.* 串口；运行 `lpstat -p` 查看队列名。

# 3.（可选，仅 usb_serial 方式需要）查找 USB 串口设备路径
./scripts/discover_printer.sh
```

## 快速开始（本地网页）

```bash
# 1. 安装后端依赖（同上）与前端依赖
.venv/bin/pip install -e ".[dev,api]"
cd apps/web && npm install && cd ../..

# 2. 一键启动 API（:8765）+ 网页（:3000）
./scripts/dev.sh
```

打开 [http://localhost:3000](http://localhost:3000)：选择模板 → 填写品名/SKU/条码 → 预览 TSPL → 点击打印。

**架构**：网页（Next.js，`apps/web/`）→ 本地 HTTP API（FastAPI，`services/api/`）→ 核心组件（`src/label_printer/`）。
核心组件的 `LabelPrinterService`（`src/label_printer/api/service.py`）是唯一编排入口，CLI、Web、脚本、测试都调用同一套逻辑，互不重复实现。

## 文档

| 文档 | 说明 |
|------|------|
| [docs/PLAN.md](docs/PLAN.md) | 分阶段实施计划（主文档） |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 模块架构与数据流 |
| [docs/TSPL_REFERENCE.md](docs/TSPL_REFERENCE.md) | TSPL2 常用命令速查 |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | USB / Mac 排障指南 |

## 目录结构

```
打印标签/
├── README.md                 # 本文件
├── requirements.txt          # Python 依赖
├── config/                   # 运行配置（printer.yaml 不入库）
├── docs/                     # 设计与参考文档
├── src/label_printer/        # 主程序包
├── tests/                    # 单元测试
├── scripts/                  # Shell 辅助脚本
└── data/                     # 示例数据与输出
```

## 环境要求

- macOS（已验证目标平台）
- Python 3.10+
- TSC TTP-344M，USB 数据线连接
- 标签纸规格需在 `config/labels/` 中配置

## 当前状态

✅ **可用 MVP** — CLI、本地 API、网页界面与单元测试已就绪；支持 CUPS Raw 与 USB 串口两种连接方式。商品库默认使用 `BT_store`（本机需有 `data/stores/BT_store.json`），示例库见 `example_store.json`（已入库）。

## 商品库

在 `data/stores/` 下放置 `<id>.json` 并在 `manifest.yaml` 中注册即可新增商品库：

```yaml
# data/stores/manifest.yaml
default: my_store
stores:
  my_store:
    name: my_store
```

参考示例：`data/stores/example_store.json`。
