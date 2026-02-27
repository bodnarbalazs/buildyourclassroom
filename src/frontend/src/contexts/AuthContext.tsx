import { useState, useEffect } from "react";
import type { ReactNode } from "react";
import type { UserDto } from "../generated/DTOs/Auth/UserDto";
import type { AuthResponseDto } from "../generated/DTOs/Auth/AuthResponseDto";
import { AuthContext } from "./authState";

const STORAGE_KEY = "auth_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserDto | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? (JSON.parse(stored) as UserDto) : null;
  });

  useEffect(() => {
    // Validate session on mount using raw fetch to avoid triggering the unauthorized bus
    fetch("/api/auth/me", { credentials: "include" })
      .then((res) => {
        if (!res.ok) {
          setUser(null);
          localStorage.removeItem(STORAGE_KEY);
        }
      })
      .catch(() => {
        setUser(null);
        localStorage.removeItem(STORAGE_KEY);
      });
  }, []);

  function setAuth(response: AuthResponseDto) {
    setUser(response.user);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(response.user));
  }

  function clearAuth() {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  }

  return (
    <AuthContext value={{ user, isAuthenticated: user !== null, setAuth, clearAuth }}>
      {children}
    </AuthContext>
  );
}
