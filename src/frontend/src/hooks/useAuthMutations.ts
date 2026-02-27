import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "../api/apiClient";
import { useAuth } from "./useAuth";
import type { AuthResponseDto } from "../generated/DTOs/Auth/AuthResponseDto";
import type { LoginUserDto } from "../generated/DTOs/Auth/LoginUserDto";
import type { RegisterUserDto } from "../generated/DTOs/Auth/RegisterUserDto";

async function throwResponseError(res: Response, fallback: string): Promise<never> {
  const text = await res.text();
  if (text) {
    // ASP.NET minimal APIs serialize strings as JSON (quoted), try to unwrap
    let message = text;
    try {
      const parsed: unknown = JSON.parse(text);
      if (typeof parsed === "string") message = parsed;
    } catch { /* not JSON, use raw text */ }
    throw new Error(message);
  }
  throw new Error(fallback);
}

export function useLoginMutation() {
  const { setAuth } = useAuth();

  return useMutation({
    mutationFn: async (data: LoginUserDto) => {
      const res = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) await throwResponseError(res, "Login failed");
      return res.json() as Promise<AuthResponseDto>;
    },
    onSuccess: (data) => setAuth(data),
  });
}

export function useRegisterMutation() {
  const { setAuth } = useAuth();

  return useMutation({
    mutationFn: async (data: RegisterUserDto) => {
      const res = await apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) await throwResponseError(res, "Registration failed");
      return res.json() as Promise<AuthResponseDto>;
    },
    onSuccess: (data) => setAuth(data),
  });
}

export function useLogoutMutation() {
  const { clearAuth } = useAuth();

  return useMutation({
    mutationFn: async () => {
      const res = await apiFetch("/api/auth/logout", { method: "POST" });
      if (!res.ok) await throwResponseError(res, "Logout failed");
    },
    onSuccess: () => clearAuth(),
  });
}
