"use client";

import { useEffect, useState } from "react";
import { PrinterPicker } from "@/components/printer-picker";
import { StatusBanner } from "@/components/status-banner";
import { useCalibration, type NudgeDirection } from "@/hooks/use-calibration";
import { usePrinters } from "@/hooks/use-printers";
import type { CalibrationProfile, FeedStrategy, MediaType } from "@/types/api";

function Stepper({
  label,
  hint,
  value,
  unit,
  step,
  onChange,
  disabled,
}: {
  label: string;
  hint: string;
  value: number;
  unit: string;
  step: number;
  onChange: (next: number) => void;
  disabled?: boolean;
}) {
  const dec = () => onChange(Math.round((value - step) * 1000) / 1000);
  const inc = () => onChange(Math.round((value + step) * 1000) / 1000);

  return (
    <div className="flex flex-col gap-1 rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-700 dark:bg-zinc-900">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-700 dark:text-zinc-200">{label}</span>
        <span className="font-mono text-xs text-zinc-500">
          {value}
          {unit}
        </span>
      </div>
      <p className="text-[10px] text-zinc-400">{hint}</p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={dec}
          className="h-8 w-8 rounded border border-zinc-300 text-sm hover:bg-zinc-50 disabled:opacity-40 dark:border-zinc-600 dark:hover:bg-zinc-800"
        >
          −
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={inc}
          className="h-8 w-8 rounded border border-zinc-300 text-sm hover:bg-zinc-50 disabled:opacity-40 dark:border-zinc-600 dark:hover:bg-zinc-800"
        >
          +
        </button>
      </div>
    </div>
  );
}

function DirectionPad({
  disabled,
  onNudge,
}: {
  disabled?: boolean;
  onNudge: (dir: NudgeDirection) => void;
}) {
  const btn =
    "h-9 rounded border border-zinc-300 text-xs hover:bg-zinc-50 disabled:opacity-40 dark:border-zinc-600 dark:hover:bg-zinc-800";

  return (
    <div className="flex flex-col gap-1 rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-700 dark:bg-zinc-900">
      <span className="text-xs font-medium text-zinc-700 dark:text-zinc-200">内容偏移微调</span>
      <p className="text-[10px] text-zinc-400">试打后若内容偏了，点对应方向（每次 1 dot）</p>
      <div className="grid grid-cols-3 gap-1">
        <div />
        <button type="button" disabled={disabled} className={btn} onClick={() => onNudge("up")}>
          偏上 ↑
        </button>
        <div />
        <button type="button" disabled={disabled} className={btn} onClick={() => onNudge("left")}>
          偏左 ←
        </button>
        <div className="flex items-center justify-center text-[10px] text-zinc-400">内容</div>
        <button type="button" disabled={disabled} className={btn} onClick={() => onNudge("right")}>
          偏右 →
        </button>
        <div />
        <button type="button" disabled={disabled} className={btn} onClick={() => onNudge("down")}>
          偏下 ↓
        </button>
        <div />
      </div>
    </div>
  );
}

export default function CalibratePage() {
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

  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [mediaType, setMediaType] = useState<MediaType>("gap");
  const [strategy, setStrategy] = useState<FeedStrategy>("gapdetect");

  const {
    stocks,
    profile,
    preview,
    loading,
    previewing,
    saving,
    printing,
    autoFeeding,
    feedResult,
    error,
    saved,
    adjustProfile,
    nudge,
    save,
    printTest,
    autoFeedCalibrate,
    clearFeedResult,
  } = useCalibration(selectedQueue, selectedStock);

  useEffect(() => {
    if (!selectedStock && stocks.length > 0) {
      setSelectedStock(stocks[0].stock_code);
    }
  }, [stocks, selectedStock]);

  const patch = (partial: Partial<CalibrationProfile>) => adjustProfile(partial);

  const busy = loading || previewing || saving || printing || autoFeeding;

  const handleAutoFeed = (withTestPrint: boolean) => {
    autoFeedCalibrate(mediaType, strategy, withTestPrint);
  };

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4">
      <div>
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">标签校准</h1>
        <p className="mt-1 text-sm text-zinc-500">
          换新纸卷先走纸校准，再打印测试页；内容偏移用方向键或 REFERENCE 微调。
        </p>
      </div>

      {error && <StatusBanner kind="error" message={error} />}
      {saved && <StatusBanner kind="success" message="软件偏移已保存到 calibration.yaml" />}
      {feedResult && (
        <div className="flex flex-col gap-2">
          <StatusBanner kind="warning" message={feedResult.message} />
          <div className="flex flex-wrap gap-2">
            {!feedResult.test_printed && (
              <button
                type="button"
                disabled={busy}
                onClick={() => {
                  printTest();
                  clearFeedResult();
                }}
                className="rounded-md bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-500 disabled:opacity-40"
              >
                打印测试页，检查内容位置
              </button>
            )}
            <button
              type="button"
              onClick={clearFeedResult}
              className="text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            >
              知道了
            </button>
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="flex flex-col gap-3">
          <section className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
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

          <section className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
            <span className="text-xs font-medium text-zinc-500">纸张规格</span>
            <div className="mt-2 flex flex-col gap-1">
              {stocks.map((stock) => {
                const active = stock.stock_code === selectedStock;
                return (
                  <button
                    key={stock.stock_code}
                    type="button"
                    onClick={() => setSelectedStock(stock.stock_code)}
                    className={`rounded-md border px-2 py-1.5 text-left text-xs transition-colors ${
                      active
                        ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                        : "border-zinc-200 hover:border-zinc-400 dark:border-zinc-700 dark:hover:border-zinc-500"
                    }`}
                  >
                    <div className="font-medium">{stock.stock_code}</div>
                    <div className={active ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-400"}>
                      {stock.width_mm}×{stock.height_mm} mm
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="flex flex-col gap-2 rounded-lg border border-blue-200 bg-blue-50/50 p-3 dark:border-blue-900 dark:bg-blue-950/30">
            <span className="text-xs font-medium text-blue-800 dark:text-blue-200">
              ① 走纸传感器校准
            </span>
            <p className="text-[10px] text-blue-700/80 dark:text-blue-300/80">
            打印机将自动走纸学习间隙（约数秒），然后停止。若红灯闪，请检查纸张规格或换 AUTODETECT。请关好上盖。
            </p>
            <div className="flex gap-1">
              {(["gap", "blackmark"] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  disabled={busy}
                  onClick={() => setMediaType(t)}
                  className={`flex-1 rounded border px-2 py-1 text-[10px] ${
                    mediaType === t
                      ? "border-blue-600 bg-blue-600 text-white"
                      : "border-zinc-300 dark:border-zinc-600"
                  }`}
                >
                  {t === "gap" ? "间隙纸" : "黑标纸"}
                </button>
              ))}
            </div>
            {mediaType === "gap" && (
              <div className="flex gap-1">
                {(["gapdetect", "autodetect"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    disabled={busy}
                    onClick={() => setStrategy(s)}
                    className={`flex-1 rounded border px-2 py-1 text-[10px] ${
                      strategy === s
                        ? "border-blue-600 bg-blue-600 text-white"
                        : "border-zinc-300 dark:border-zinc-600"
                    }`}
                  >
                    {s === "gapdetect" ? "GAPDETECT" : "AUTODETECT"}
                  </button>
                ))}
              </div>
            )}
            <button
              type="button"
              disabled={busy || !selectedQueue || !selectedStock}
              onClick={() => handleAutoFeed(false)}
              className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-40"
            >
              {autoFeeding ? "走纸校准中…" : "自动走纸校准"}
            </button>
            <button
              type="button"
              disabled={busy || !selectedQueue || !selectedStock}
              onClick={() => handleAutoFeed(true)}
              className="rounded-lg border border-blue-400 px-3 py-1.5 text-xs text-blue-700 hover:bg-blue-100 disabled:opacity-40 dark:text-blue-300 dark:hover:bg-blue-900/40"
            >
              走纸校准 + 打印测试页
            </button>
          </section>

          <section className="flex flex-col gap-2">
            <span className="text-xs font-medium text-zinc-500">② 软件偏移（REFERENCE）</span>
            <DirectionPad disabled={busy} onNudge={nudge} />
            <Stepper
              label="水平 REFERENCE X"
              hint="1 dot ≈ 0.125 mm"
              value={profile.reference_x_dots}
              unit=" dot"
              step={1}
              disabled={busy}
              onChange={(v) => patch({ reference_x_dots: v })}
            />
            <Stepper
              label="垂直 REFERENCE Y"
              hint="内容整体上下"
              value={profile.reference_y_dots}
              unit=" dot"
              step={1}
              disabled={busy}
              onChange={(v) => patch({ reference_y_dots: v })}
            />
            <Stepper
              label="走纸 GAP offset"
              hint="走纸垂直定位"
              value={profile.gap_offset_mm}
              unit=" mm"
              step={0.1}
              disabled={busy}
              onChange={(v) => patch({ gap_offset_mm: v })}
            />
          </section>

          <div className="flex flex-col gap-2">
            <button
              type="button"
              disabled={busy || !selectedQueue || !selectedStock}
              onClick={printTest}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
            >
              {printing ? "打印中…" : "打印测试页"}
            </button>
            <button
              type="button"
              disabled={busy || !selectedQueue || !selectedStock}
              onClick={save}
              className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50 disabled:opacity-40 dark:border-zinc-600 dark:hover:bg-zinc-800"
            >
              {saving ? "保存中…" : "保存软件偏移"}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                adjustProfile({
                  reference_x_dots: 0,
                  reference_y_dots: 0,
                  gap_offset_mm: 0,
                })
              }
              className="text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            >
              重置偏移为零
            </button>
          </div>
        </aside>

        <section className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-200">校准页预览</h2>
            {previewing && <span className="text-xs text-zinc-400">更新中…</span>}
          </div>
          {preview ? (
            <div className="flex flex-col gap-3">
              <p className="text-xs text-zinc-400">
                {preview.width_mm} × {preview.height_mm} mm（固定预览框内缩放显示）
              </p>
              <div className="flex h-[360px] w-[280px] shrink-0 items-center justify-center overflow-hidden rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-950">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`data:image/png;base64,${preview.image_b64}`}
                  alt="校准页预览"
                  className="max-h-full max-w-full object-contain"
                  style={{ imageRendering: "pixelated" }}
                />
              </div>
              <details className="rounded-lg border border-zinc-200 dark:border-zinc-700">
                <summary className="cursor-pointer px-4 py-2 text-xs font-medium text-zinc-500">
                  TSPL 指令
                </summary>
                <pre className="overflow-x-auto border-t border-zinc-200 px-4 py-3 text-[11px] leading-relaxed text-zinc-700 dark:border-zinc-700 dark:text-zinc-300">
                  {preview.tspl}
                </pre>
              </details>
            </div>
          ) : (
            <div className="flex h-[360px] w-[280px] items-center justify-center rounded-lg border border-dashed border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-950">
              <p className="px-4 text-center text-sm text-zinc-400">
                {loading ? "加载中…" : "选择打印机和纸张规格后显示预览"}
              </p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
