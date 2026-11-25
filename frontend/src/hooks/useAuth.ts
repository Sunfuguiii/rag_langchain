"use client";

import { useState, useEffect, useCallback } from "react";
import { api, ApiError } from "@/lib/api";

export interface User {
  id: string;
  email: string;
  role: "student" | "admin";
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setState({ user: null, loading: false, error: null });
      return;
    }
    try {
      const user = await api.get<User>("/auth/me");
      setState({ user, loading: false, error: null });
    } catch (err) {
      // 只在 401 时清除 token，其他错误保留（如后端暂未启动）
      if (err instanceof ApiError && err.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        setState({ user: null, loading: false, error: null });
      } else {
        // 非 401 错误（网络问题等），保留登录状态，稍后重试
        setState((prev) => ({ ...prev, loading: false }));
      }
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    const data = await api.post<{ access_token: string; refresh_token: string }>("/auth/login", {
      email,
      password,
    });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    await fetchUser();
  };

  const register = async (email: string, password: string) => {
    await api.post("/auth/register", { email, password });
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setState({ user: null, loading: false, error: null });
    window.location.href = "/login";
  };

  return { ...state, login, register, logout, refresh: fetchUser };
}
