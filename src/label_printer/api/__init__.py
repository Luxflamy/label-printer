"""Service 层 — 供 CLI / HTTP API / 测试等所有客户端共用的统一入口。

命名说明：这里的 "api" 指"Python 组件对外暴露的编程接口"，
与 services/api（FastAPI HTTP 服务）是两个不同层级，不要混淆：

    services/api (FastAPI)  --import-->  label_printer.api.service.LabelPrinterService

FastAPI 只做 HTTP <-> 本模块的薄转换，不重复实现任何业务逻辑。
"""
