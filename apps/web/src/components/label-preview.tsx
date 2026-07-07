"use client";

import { useState } from "react";
import type { LabelPreviewResult } from "@/types/api";

interface Props {
  /** 图片预览结果 */
  imageResult: LabelPreviewResult | null;
  imageLoading: boolean;
  imageError: string | null;
  /** TSPL 文本（可为 null，折叠展示） */
  tspl: string | null;
  tsplLoading: boolean;
  tsplError: string | null;
}

export function LabelPreview({
  imageResult,
  imageLoading,
  imageError,
  tspl,
  tsplLoading,
  tsplError,
}: Props) {
  const [tsplOpen, setTsplOpen] = useState(false);

  const showSkeleton = imageLoading;
  const showImage = !imageLoading && imageResult;

  return (
    <div className="flex flex-col gap-3">
      {/* ---- 图片预览区 ---- */}
      <div className="overflow-hidden rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900">
        {showSkeleton && (
          <div className="flex h-48 items-center justify-center">
            <span className="text-sm text-zinc-400 animate-pulse">生成预览图…</span>
          </div>
        )}

        {showImage && (
          <div className="flex flex-col items-center gap-2 p-4">
            {/* 标签尺寸说明 */}
            <p className="text-xs text-zinc-400">
              {imageResult.width_mm} × {imageResult.height_mm} mm（预览图已放大）
            </p>
            {/* 图片本身：限制最大宽度，保持纵横比 */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`data:image/png;base64,${imageResult.image_b64}`}
              alt={`标签预览 - ${imageResult.template}`}
              className="max-w-full rounded border border-zinc-200 shadow-sm dark:border-zinc-700"
              style={{ imageRendering: "pixelated" }}
            />
          </div>
        )}

        {!imageLoading && !imageResult && !imageError && (
          <div className="flex h-32 items-center justify-center">
            <span className="text-sm text-zinc-400">点击「预览」查看标签效果</span>
          </div>
        )}

        {imageError && (
          <div className="flex items-center gap-2 p-4 text-sm text-red-600 dark:text-red-400">
            <span>⚠</span>
            <span>{imageError}</span>
          </div>
        )}
      </div>

      {/* ---- TSPL 折叠区 ---- */}
      <details
        open={tsplOpen}
        onToggle={(e) => setTsplOpen((e.target as HTMLDetailsElement).open)}
        className="rounded-lg border border-zinc-200 dark:border-zinc-700"
      >
        <summary className="cursor-pointer select-none px-4 py-2 text-xs font-medium text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200">
          {tsplLoading ? "生成 TSPL 指令…" : `TSPL 指令${tspl ? "" : "（点击预览后显示）"}`}
        </summary>

        <div className="border-t border-zinc-200 dark:border-zinc-700">
          {tsplLoading && (
            <p className="px-4 py-3 text-xs text-zinc-400 animate-pulse">加载中…</p>
          )}
          {tsplError && (
            <p className="px-4 py-3 text-xs text-red-500">{tsplError}</p>
          )}
          {tspl && (
            <pre className="overflow-x-auto px-4 py-3 text-[11px] leading-relaxed text-zinc-700 dark:text-zinc-300">
              {tspl}
            </pre>
          )}
          {!tsplLoading && !tspl && !tsplError && (
            <p className="px-4 py-3 text-xs text-zinc-400">暂无指令，点击「预览」后自动获取</p>
          )}
        </div>
      </details>
    </div>
  );
}
