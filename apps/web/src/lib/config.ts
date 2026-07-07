/** 本地 API 地址；开发环境可用 apps/web/.env.local 覆盖。 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8765";
