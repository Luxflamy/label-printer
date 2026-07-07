"use client";

import { PdfDropZone } from "@/components/pdf-drop-zone";
import { PrinterPicker } from "@/components/printer-picker";
import { PrintButton } from "@/components/print-button";
import { StatusBanner } from "@/components/status-banner";
import { usePdfShipping } from "@/hooks/use-pdf-shipping";
import { usePrinters } from "@/hooks/use-printers";
import type { FitMode } from "@/types/api";

export default function ShippingLabelPage() {
  const {
    printers,
    selectedQueue,
    loading: printersLoading,
    selecting: printerSelecting,
    error: printersError,
    lastUpdated,
    selectPrinter,
    refresh: refreshPrinters,
  } = usePrinters();

  const {
    file,
    preview,
    page,
    copies,
    rotation,
    fitMode,
    scale,
    printAllPages,
    previewing,
    printing,
    error,
    printSuccess,
    setFile,
    clearFile,
    setPage,
    setCopies,
    setRotation,
    setFitMode,
    setScale,
    setPrintAllPages,
    print,
  } = usePdfShipping(selectedQueue);

  const busy = previewing || printing;

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-5 px-6 py-8">
      <header>
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">运货标签</h1>
        <p className="mt-1 text-sm text-zinc-500">
          拖入 PDF 箱标，自动适配 100×150mm（250P）并打印到 TSC 标签机
        </p>
      </header>

      {error && <StatusBanner kind="error" message={error} />}
      {printSuccess && <StatusBanner kind="success" message={printSuccess} />}

      <section className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <PrinterPicker
          printers={printers}
          selectedQueue={selectedQueue}
          loading={printersLoading}
          selecting={printerSelecting}
          error={printersError}
          lastUpdated={lastUpdated}
          onSelect={selectPrinter}
          onRefresh={refreshPrinters}
        />
      </section>

      <section className="relative flex flex-col gap-3">
        <PdfDropZone file={file} disabled={busy} onFile={setFile} onClear={clearFile} />
      </section>

      {preview && (
        <section className="grid gap-4 md:grid-cols-[280px_1fr]">
          <div className="flex flex-col gap-3 text-sm">
            <div className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-700">
              <p className="text-xs text-zinc-500">PDF 尺寸</p>
              <p className="font-medium">
                {preview.pdf_width_mm} × {preview.pdf_height_mm} mm
              </p>
              <p className="mt-2 text-xs text-zinc-500">目标纸张</p>
              <p className="font-medium">
                {preview.target_width_mm}×{preview.target_height_mm} mm ({preview.target_stock})
              </p>
            </div>

            {preview.page_count > 1 && (
              <label className="flex flex-col gap-1 text-xs">
                <span className="text-zinc-500">页码</span>
                <select
                  value={page}
                  disabled={busy || printAllPages}
                  onChange={(e) => setPage(Number(e.target.value))}
                  className="rounded border border-zinc-300 bg-white px-2 py-1 dark:border-zinc-600 dark:bg-zinc-900"
                >
                  {Array.from({ length: preview.page_count }, (_, i) => (
                    <option key={i} value={i}>
                      第 {i + 1} 页 / {preview.page_count}
                    </option>
                  ))}
                </select>
                <label className="mt-1 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={printAllPages}
                    disabled={busy}
                    onChange={(e) => setPrintAllPages(e.target.checked)}
                  />
                  打印全部页
                </label>
              </label>
            )}

            <label className="flex flex-col gap-1 text-xs">
              <span className="text-zinc-500">适应方式</span>
              <select
                value={fitMode}
                disabled={busy}
                onChange={(e) => setFitMode(e.target.value as FitMode)}
                className="rounded border border-zinc-300 bg-white px-2 py-1 dark:border-zinc-600 dark:bg-zinc-900"
              >
                <option value="contain">等比完整（推荐）</option>
                <option value="cover">铺满裁切</option>
                <option value="fill">拉伸填满</option>
              </select>
            </label>

            <label className="flex flex-col gap-1 text-xs">
              <span className="text-zinc-500">打印放大</span>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={50}
                  max={150}
                  step={1}
                  value={Math.round(scale * 100)}
                  disabled={busy}
                  onChange={(e) => setScale(Number(e.target.value) / 100)}
                  className="flex-1"
                />
                <span className="w-10 text-right font-medium tabular-nums">
                  {Math.round(scale * 100)}%
                </span>
              </div>
            </label>

            <label className="flex flex-col gap-1 text-xs">
              <span className="text-zinc-500">旋转</span>
              <select
                value={rotation}
                disabled={busy}
                onChange={(e) => setRotation(Number(e.target.value))}
                className="rounded border border-zinc-300 bg-white px-2 py-1 dark:border-zinc-600 dark:bg-zinc-900"
              >
                <option value={0}>0°</option>
                <option value={90}>90°</option>
                <option value={180}>180°</option>
                <option value={270}>270°</option>
              </select>
            </label>

            <label className="flex flex-col gap-1 text-xs">
              <span className="text-zinc-500">份数</span>
              <input
                type="number"
                min={1}
                max={99}
                value={copies}
                disabled={busy || printAllPages}
                onChange={(e) => setCopies(Number(e.target.value))}
                className="rounded border border-zinc-300 bg-white px-2 py-1 dark:border-zinc-600 dark:bg-zinc-900"
              />
            </label>

            {preview.warnings.map((w) => (
              <p key={w} className="text-xs text-amber-600 dark:text-amber-400">
                {w}
              </p>
            ))}
          </div>

          <div className="flex flex-col gap-2">
            <p className="text-xs text-zinc-400">预览（固定框内缩放）</p>
            <div className="flex h-[420px] w-[280px] items-center justify-center overflow-hidden rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-950">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`data:image/png;base64,${preview.image_b64}`}
                alt="PDF 标签预览"
                className="max-h-full max-w-full object-contain"
              />
            </div>
            <PrintButton
              loading={printing}
              disabled={!file || !selectedQueue || previewing}
              onClick={print}
            />
          </div>
        </section>
      )}

      {previewing && <p className="text-sm text-zinc-400">正在解析 PDF…</p>}
    </main>
  );
}
