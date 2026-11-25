const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface FetchOptions extends RequestInit {
  params?: Record<string, string>;
}

async function request<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    url += `?${qs}`;
  }

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...fetchOptions, headers });

  if (response.status === 401 && token) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      const newToken = localStorage.getItem("access_token");
      headers["Authorization"] = `Bearer ${newToken}`;
      const retryRes = await fetch(url, { ...fetchOptions, headers });
      if (!retryRes.ok) {
        throw new ApiError(retryRes.status, await retryRes.json());
      }
      return retryRes.json();
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    throw new ApiError(401, { detail: "Unauthorized" });
  }

  if (!response.ok) {
    throw new ApiError(response.status, await response.json());
  }

  return response.json();
}

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    return true;
  } catch {
    return false;
  }
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, body: any) {
    super(body?.detail || `HTTP ${status}`);
    this.status = status;
    this.detail = body?.detail || "";
  }
}

export const api = {
  get: <T>(endpoint: string, options?: FetchOptions) => request<T>(endpoint, { ...options, method: "GET" }),
  post: <T>(endpoint: string, body?: unknown, options?: FetchOptions) =>
    request<T>(endpoint, { ...options, method: "POST", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(endpoint: string, options?: FetchOptions) => request<T>(endpoint, { ...options, method: "DELETE" }),
  upload: async <T>(endpoint: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    if (!response.ok) {
      const text = await response.text();
      let detail: string;
      try {
        detail = JSON.parse(text).detail || text;
      } catch {
        detail = text;
      }
      throw new ApiError(response.status, { detail });
    }
    return response.json() as Promise<T>;
  },
};

export { API_BASE };
