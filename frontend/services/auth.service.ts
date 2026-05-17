import { api } from "@/lib/api";
import type { CurrentUser, TokenPair } from "@/types/api";

export const authService = {
  async login(email: string, password: string): Promise<TokenPair> {
    const { data } = await api.post<TokenPair>("/auth/login", { email, password });
    return data;
  },
  async register(payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }): Promise<TokenPair> {
    const { data } = await api.post<TokenPair>("/auth/register", payload);
    return data;
  },
  async me(): Promise<CurrentUser> {
    const { data } = await api.get<CurrentUser>("/auth/me");
    return data;
  },
  async changePassword(current_password: string, new_password: string): Promise<void> {
    await api.post("/auth/change-password", { current_password, new_password });
  },
  async logout(): Promise<void> {
    try {
      await api.post("/auth/logout");
    } catch {
      /* ignore — JWT is stateless */
    }
  },
};
