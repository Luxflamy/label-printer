"use client";

import { useCallback, useState } from "react";

interface PdfDropZoneProps {
  file: File | null;
  disabled?: boolean;
  onFile: (file: File) => void;
  onClear: () => void;
}

export function PdfDropZone({ file, disabled, onFile, onClear }: PdfDropZoneProps) {
  const [dragOver, setDragOver] = useState(false);

  const pick = useCallback(
    (f: File | undefined) => {
      if (!f || disabled) return;
      if (f.type !== "application/pdf" && !f.name.toLowerCase().endsWith(".pdf")) {
        return;
      }
      onFile(f);
    },
    [disabled, onFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        pick(e.dataTransfer.files[0]);
      }}
      className={`flex min-h-[140px] flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-6 transition-colors ${
        dragOver
          ? "border-blue-500 bg-blue-50 dark:bg-blue-950/30"
          : "border-zinc-300 dark:border-zinc-600"
      } ${disabled ? "opacity-50" : "cursor-pointer hover:border-zinc-400"}`}
    >
      {file ? (
        <div className="flex flex-col items-center gap-2 text-center">
          <span className="text-sm font-medium text-zinc-800 dark:text-zinc-100">{file.name}</span>
          <span className="text-xs text-zinc-500">{(file.size / 1024).toFixed(0)} KB</span>
          <button
            type="button"
            disabled={disabled}
            onClick={(e) => {
              e.stopPropagation();
              onClear();
            }}
            className="text-xs text-zinc-500 hover:text-red-500"
          >
            移除
          </button>
        </div>
      ) : (
        <>
          <p className="text-sm text-zinc-600 dark:text-zinc-300">将 PDF 运货标签拖入此处</p>
          <p className="mt-1 text-xs text-zinc-400">或点击选择文件（最大 20MB）</p>
        </>
      )}
      <input
        type="file"
        accept="application/pdf,.pdf"
        disabled={disabled}
        className="absolute h-0 w-0 opacity-0"
        id="pdf-upload-input"
        onChange={(e) => pick(e.target.files?.[0])}
      />
      {!file && (
        <label
          htmlFor="pdf-upload-input"
          className="mt-3 rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          选择 PDF
        </label>
      )}
    </div>
  );
}
