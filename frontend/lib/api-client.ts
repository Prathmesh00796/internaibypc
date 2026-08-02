import axios from "axios";
import Cookies from "js-cookie";

const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
  : "/api/backend";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = Cookies.get("internai_access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear tokens and redirect to login (except for the login/register calls themselves).
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const isAuthEndpoint = error.config?.url?.includes("/auth/login") || error.config?.url?.includes("/auth/register");
      if (!isAuthEndpoint) {
        Cookies.remove("internai_access_token");
        Cookies.remove("internai_refresh_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export function setAuthTokens(accessToken: string, refreshToken: string) {
  Cookies.set("internai_access_token", accessToken, { expires: 1, sameSite: "lax" });
  Cookies.set("internai_refresh_token", refreshToken, { expires: 30, sameSite: "lax" });
}

export function clearAuthTokens() {
  Cookies.remove("internai_access_token");
  Cookies.remove("internai_refresh_token");
}

export function isAuthenticated(): boolean {
  return !!Cookies.get("internai_access_token");
}
