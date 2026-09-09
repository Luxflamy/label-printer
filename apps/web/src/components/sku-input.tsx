"use client";

import { useState } from "react";
import type { SkuRecord } from "@/types/api";

interface SkuInputProps {
  value: string;
  suggestions: SkuRecord[];
  disabled?: boolean;
  onChange: (value: string) => void;
  onPick: (sku: string) => void;
  onSubmit: () => void;
}

/** SKU 手工输入框 — 输入时从打印历史给出建议，回车直接打印。 */
export function SkuInput({
  value,
  suggestions,
  disabled,
  onChange,
  onPick,
  onSubmit,
}: SkuInputProps) {
  const [focused, setFocused] = useState(false);
  const showSuggestions =
    focused && value.trim().length > 0 && suggestions.length > 0;

  return (
    <div className="relative flex flex-col gap-1">
      <label htmlFor="sku-input" className="text-xs font-medium text-zinc-500">
        SKU
      </label>
      <input
        id="sku-input"
        type="text"
        value={value}
        disabled={disabled}
        autoComplete="off"
        spellCheck={false}
        placeholder="手动输入 SKU，回车即打印"
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            onSubmit();
          } else if (e.key === "Escape") {
            setFocused(false);
          }
        }}
        className="rounded-md border border-zinc-300 px-3 py-2 font-mono text-sm outline-none focus:border-zinc-900 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:focus:border-zinc-100"
      />

      {showSuggestions && (
        <ul className="absolute top-full z-20 mt-1 max-h-56 w-full overflow-y-auto rounded-md border border-zinc-200 bg-white py-1 shadow-lg dark:border-zinc-700 dark:bg-zinc-900">
          {suggestions.map((record) => (
            <li key={record.sku}>
              <button
                type="button"
                // onMouseDown 早于 onBlur，避免下拉在点击生效前先关闭
                onMouseDown={(e) => {
                  e.preventDefault();
                  onPick(record.sku);
                  setFocused(false);
                }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left hover:bg-zinc-100 dark:hover:bg-zinc-800"
              >
                <span className="min-w-0 flex-1 truncate font-mono text-xs text-zinc-800 dark:text-zinc-100">
                  {record.sku}
                </span>
                <span className="shrink-0 text-[10px] text-zinc-400">
                  已打 {record.print_count} 次
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
