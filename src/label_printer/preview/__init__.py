"""标签预览图生成 — 将模板渲染成 PNG，用于网页展示。

依赖方向（与 docs/ARCHITECTURE.md 一致）：
    preview/ → templates/renderer → tspl/layout
    preview/ → Pillow / python-barcode / qrcode （仅本包依赖，不传染到核心层）

使用方：
    from label_printer.preview.drawer import draw_label_png
    png_bytes = draw_label_png(template, variables)
"""
