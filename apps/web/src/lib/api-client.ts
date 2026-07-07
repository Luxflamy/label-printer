/**
 * 所有对本地 API 的 HTTP 调用的唯一出口。
 *
 * 页面 / 组件 / hooks 只应通过 apiClient 访问后端，不直接使用 fetch，
 * 这样未来更换后端实现或调整错误处理方式时只需改这一个文件。
 */

import { API_BASE_URL } from "./config";
import type {
  BatchPrintData,
  BatchPrintPayload,
  Envelope,
  HealthData,
  LabelPreviewResult,
  PrinterInfo,
  PrintPayload,
  PrintResult,
  ProductItem,
  ProductStoresData,
  RenderResult,
  TemplateDetail,
  TemplateSummary,
} from "@/types/api";

export class ApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "NETWORK_ERROR",
      "无法连接本地打印服务，请确认已运行 scripts/dev.sh 启动后端"
    );
  }

  const body = (await response.json().catch(() => null)) as Envelope<T> | null;

  if (!body) {
    throw new ApiError(
      "BAD_RESPONSE",
      `服务器返回了无法解析的响应（状态码 ${response.status}）`
    );
  }

  if (!body.ok || body.data === null || body.data === undefined) {
    throw new ApiError(
      body.error?.code ?? "UNKNOWN_ERROR",
      body.error?.message ?? "未知错误"
    );
  }

  return body.data;
}

export const apiClient = {
  health: () => request<HealthData>("/health"),

  listPrinters: () => request<PrinterInfo[]>("/printers"),

  listTemplates: () => request<TemplateSummary[]>("/templates"),

  getTemplate: (name: string) =>
    request<TemplateDetail>(`/templates/${encodeURIComponent(name)}`),

  render: (payload: PrintPayload) =>
    request<RenderResult>("/render", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  renderPreview: (payload: Omit<PrintPayload, "copies">) =>
    request<LabelPreviewResult>("/render/preview", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  printOne: (payload: PrintPayload) =>
    request<PrintResult>("/print", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listProducts: (store?: string) =>
    request<ProductItem[]>(
      store ? `/products?store=${encodeURIComponent(store)}` : "/products"
    ),

  listProductStores: () => request<ProductStoresData>("/products/stores"),

  batchPrint: (payload: BatchPrintPayload) =>
    request<BatchPrintData>("/batch/print", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
