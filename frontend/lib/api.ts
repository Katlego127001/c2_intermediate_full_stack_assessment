/**
 * Axios client with auth interceptor.
 * - Reads access token from Zustand auth store
 * - On 401, clears auth and redirects to /login (in browser only)
 */
import axios, { AxiosError } from "axios";

import { useAuthStore } from "@/store/auth";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err: AxiosError) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      const here = window.location.pathname;
      useAuthStore.getState().logout();
      if (!here.startsWith("/login") && !here.startsWith("/register")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  },
);

export function apiErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { detail?: string | Array<{ msg?: string }> } | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d) => d?.msg).filter(Boolean).join(", ") || fallback;
    }
    return err.message || fallback;
  }
  return fallback;
}
