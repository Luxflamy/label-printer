"""本地 HTTP API — Next.js 前端与 label_printer 核心组件之间的薄适配层。

设计约束（保持低耦合）：
- 本包不实现任何 TSPL / 模板 / 打印业务逻辑，全部转发给
  label_printer.api.service.LabelPrinterService。
- Web 前端只认 HTTP JSON，不直接依赖 Python；未来若替换为其他前端
  技术栈，这一层无需改动。
"""
