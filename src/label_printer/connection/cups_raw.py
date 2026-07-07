"""CUPS Raw 连接 — 通过系统 `lp -o raw` 发送 TSPL 原始字节。

适用场景：打印机在 macOS 上未暴露 /dev/cu.* 虚拟串口，但已通过
"系统设置 → 打印机与扫描仪" 添加为 USB 打印机（即有 CUPS 队列）。
`-o raw` 绕过驱动/PPD 转换，直接把字节流发给打印机，等价于串口直写。
"""

from __future__ import annotations

import shutil
import subprocess

from label_printer.connection.base import PrinterConnection

# macOS 的 lpstat 消息按系统语言本地化（例如中文），且不受 LANG/LC_ALL 影响，
# 因此状态检测采用多语言关键字匹配，匹配不到则归为 "unknown"（不影响可用性判断）。
_STATUS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "idle": ("idle", "闲置", "空闲"),
    "printing": ("printing", "正在打印", "打印中"),
    "disabled": ("disabled", "已停用", "停用"),
}


def _detect_status(line: str) -> str:
    lowered = line.lower()
    for status, keywords in _STATUS_KEYWORDS.items():
        if any(kw in line or kw in lowered for kw in keywords):
            return status
    return "unknown"


class CupsRawConnection(PrinterConnection):
    """实现 PrinterConnection 接口；上层无需关心底层是 CUPS 还是串口。"""

    def __init__(self, queue: str, timeout: float = 10.0) -> None:
        self.queue = queue
        self.timeout = timeout
        self._connected = False

    def connect(self) -> None:
        if shutil.which("lp") is None:
            raise RuntimeError(
                "未找到系统命令 `lp`，请确认在 macOS/Linux 且已安装 CUPS 客户端"
            )
        self._connected = True

    def send(self, data: bytes) -> None:
        if not self._connected:
            raise RuntimeError("连接未打开，请先调用 connect()")
        result = subprocess.run(
            ["lp", "-d", self.queue, "-o", "raw"],
            input=data,
            capture_output=True,
            timeout=self.timeout,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"lp 发送失败 (queue={self.queue}): {stderr or '未知错误'}"
            )

    def close(self) -> None:
        self._connected = False


def list_cups_printers() -> list[dict[str, str]]:
    """返回本机已配置的 CUPS 打印机列表，供上层实现"打印机发现"功能使用。

    - 名称来自 `lpstat -e`：输出为纯队列名，不受系统语言影响，最可靠。
    - 状态来自 `lpstat -p`：按行做多语言关键字匹配，仅供参考展示。
    """
    if shutil.which("lpstat") is None:
        return []

    names_result = subprocess.run(
        ["lpstat", "-e"], capture_output=True, text=True, timeout=5
    )
    names = [line.strip() for line in names_result.stdout.splitlines() if line.strip()]
    if not names:
        return []

    status_result = subprocess.run(
        ["lpstat", "-p"], capture_output=True, text=True, timeout=5
    )
    status_lines = status_result.stdout.splitlines()

    printers: list[dict[str, str]] = []
    for name in names:
        line = next((l for l in status_lines if name in l), "")
        printers.append({"name": name, "status": _detect_status(line)})
    return printers
