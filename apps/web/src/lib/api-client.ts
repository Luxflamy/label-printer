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
  CalibrationData,
  CalibrationPreviewData,
  CalibrationProfile,
  AutoFeedData,
  FeedStrategy,
  MediaType,
  Envelope,
  HealthData,
  LabelPreviewResult,
  PrinterListData,
  PrintPayload,
  PrintResult,
  ProductItem,
  ProductStoresData,
  RenderPayload,
  RenderResult,
  FitMode,
  ShippingLabelPreviewData,
  ShippingLabelPrintData,
  StockSpec,
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

async function fetchWithTimeout(
  input: string,
  init?: RequestInit,
  timeoutMs = 8000
): Promise<Response> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(
        "TIMEOUT",
        "连接本地打印服务超时，请确认已运行 scripts/dev.sh 启动后端"
      );
    }
    throw err;
  } finally {
    window.clearTimeout(timer);
  }
}

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  let response: Response;
  try {
    response = await fetchWithTimeout(`${API_BASE_URL}${path}`, {
      method: "POST",
      body: formData,
      cache: "no-store",
    });
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "NETWORK_ERROR",
      "无法连接本地打印服务，请确认已运行 scripts/dev.sh 启动后端"
    );
  }

  const body = (await response.json().catch(() => null)) as Envelope<T> | null;

  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : null;
    throw new ApiError(
      "HTTP_ERROR",
      detail ?? body?.error?.message ?? `请求失败（状态码 ${response.status}）`
    );
  }

  if (!body) {
    throw new ApiError("BAD_RESPONSE", `服务器返回了无法解析的响应（状态码 ${response.status}）`);
  }

  if (!body.ok || body.data === null || body.data === undefined) {
    throw new ApiError(
      body.error?.code ?? "UNKNOWN_ERROR",
      body.error?.message ?? "未知错误"
    );
  }

  return body.data;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetchWithTimeout(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "NETWORK_ERROR",
      "无法连接本地打印服务，请确认已运行 scripts/dev.sh 启动后端"
    );
  }

  const body = (await response.json().catch(() => null)) as Envelope<T> | null;

  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : null;
    throw new ApiError(
      "HTTP_ERROR",
      detail ?? body?.error?.message ?? `请求失败（状态码 ${response.status}）`
    );
  }

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

  listPrinters: () => request<PrinterListData>("/printers"),

  selectPrinter: (queue: string) =>
    request<PrinterListData>("/printers/select", {
      method: "POST",
      body: JSON.stringify({ queue }),
    }),

  listTemplates: () => request<TemplateSummary[]>("/templates"),

  getTemplate: (name: string) =>
    request<TemplateDetail>(`/templates/${encodeURIComponent(name)}`),

  render: (payload: RenderPayload) =>
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

  listCalibrationStocks: () =>
    request<{ stocks: StockSpec[] }>("/calibration/stocks"),

  getCalibration: (printer: string, stockCode: string) =>
    request<CalibrationData>(
      `/calibration?printer=${encodeURIComponent(printer)}&stock=${encodeURIComponent(stockCode)}`
    ),

  saveCalibration: (printer: string, stockCode: string, profile: CalibrationProfile) =>
    request<CalibrationData>("/calibration", {
      method: "PUT",
      body: JSON.stringify({ printer, stock_code: stockCode, profile }),
    }),

  previewCalibration: (
    printer: string,
    stockCode: string,
    profile: CalibrationProfile
  ) =>
    request<CalibrationPreviewData>("/calibration/preview", {
      method: "POST",
      body: JSON.stringify({ printer, stock_code: stockCode, profile }),
    }),

  printCalibration: (
    printer: string,
    stockCode: string,
    profile: CalibrationProfile
  ) =>
    request<PrintResult>("/calibration/print", {
      method: "POST",
      body: JSON.stringify({ printer, stock_code: stockCode, profile }),
    }),

  autoFeedCalibrate: (
    printer: string,
    stockCode: string,
    options?: {
      media_type?: MediaType;
      strategy?: FeedStrategy;
      print_test_after?: boolean;
    }
  ) =>
    request<AutoFeedData>("/calibration/auto-feed", {
      method: "POST",
      body: JSON.stringify({
        printer,
        stock_code: stockCode,
        media_type: options?.media_type ?? "gap",
        strategy: options?.strategy ?? "gapdetect",
        print_test_after: options?.print_test_after ?? false,
      }),
    }),

  previewShippingLabel: (
    file: File,
    options: {
      page?: number;
      fit_mode?: FitMode;
      rotation?: number;
      scale?: number;
      printer?: string | null;
    }
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("page", String(options.page ?? 0));
    form.append("fit_mode", options.fit_mode ?? "contain");
    form.append("rotation", String(options.rotation ?? 0));
    form.append("scale", String(options.scale ?? 1.08));
    if (options.printer) form.append("printer", options.printer);
    return uploadRequest<ShippingLabelPreviewData>("/shipping-label/preview", form);
  },

  printShippingLabel: (
    file: File,
    options: {
      page?: number;
      copies?: number;
      fit_mode?: FitMode;
      rotation?: number;
      scale?: number;
      printer?: string | null;
      print_all_pages?: boolean;
    }
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("page", String(options.page ?? 0));
    form.append("copies", String(options.copies ?? 1));
    form.append("fit_mode", options.fit_mode ?? "contain");
    form.append("rotation", String(options.rotation ?? 0));
    form.append("scale", String(options.scale ?? 1.08));
    form.append("print_all_pages", String(options.print_all_pages ?? false));
    if (options.printer) form.append("printer", options.printer);
    return uploadRequest<ShippingLabelPrintData>("/shipping-label/print", form);
  },
};
