import { createContext } from "react";
import type { UserDto } from "../generated/DTOs/Auth/UserDto";
import type { AuthResponseDto } from "../generated/DTOs/Auth/AuthResponseDto";

export interface AuthState {
  user: UserDto | null;
  isAuthenticated: boolean;
  setAuth: (response: AuthResponseDto) => void;
  clearAuth: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);
