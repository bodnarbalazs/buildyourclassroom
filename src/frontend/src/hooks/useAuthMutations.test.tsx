import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { AuthContext } from "../contexts/authState";
import type { AuthState } from "../contexts/authState";
import {
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
} from "./useAuthMutations";

const fetchMock = vi.fn();

function createAuthState(overrides?: Partial<AuthState>): AuthState {
  return {
    user: null,
    isAuthenticated: false,
    setAuth: vi.fn(),
    clearAuth: vi.fn(),
    ...overrides,
  };
}

function createWrapper(authState: AuthState) {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false } },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <AuthContext value={authState}>{children}</AuthContext>
      </QueryClientProvider>
    );
  };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useLoginMutation", () => {
  it("calls setAuth on successful login", async () => {
    const authResponse = {
      expiresAt: "2026-01-01",
      user: { id: "1", email: "a@b.c", username: "u", roles: [], createdAt: "2026-01-01", lastLoginAt: null },
    };
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(authResponse), { status: 200 }),
    );

    const auth = createAuthState();
    const { result } = renderHook(() => useLoginMutation(), {
      wrapper: createWrapper(auth),
    });

    result.current.mutate({ emailOrUsername: "u", password: "p" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(auth.setAuth).toHaveBeenCalledWith(authResponse);
  });

  it("throws with backend error message on failure", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify("Invalid credentials"), { status: 401 }),
    );

    const auth = createAuthState();
    const { result } = renderHook(() => useLoginMutation(), {
      wrapper: createWrapper(auth),
    });

    result.current.mutate({ emailOrUsername: "u", password: "wrong" });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Invalid credentials");
  });

  it("uses raw text when backend returns plain-text error", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response("Internal Server Error", { status: 500 }),
    );

    const auth = createAuthState();
    const { result } = renderHook(() => useLoginMutation(), {
      wrapper: createWrapper(auth),
    });

    result.current.mutate({ emailOrUsername: "u", password: "p" });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Internal Server Error");
  });
});

describe("useRegisterMutation", () => {
  it("calls setAuth on successful registration", async () => {
    const authResponse = {
      expiresAt: "2026-01-01",
      user: { id: "2", email: "b@c.d", username: "v", roles: [], createdAt: "2026-01-01", lastLoginAt: null },
    };
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(authResponse), { status: 200 }),
    );

    const auth = createAuthState();
    const { result } = renderHook(() => useRegisterMutation(), {
      wrapper: createWrapper(auth),
    });

    result.current.mutate({ email: "b@c.d", username: "v", password: "p" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(auth.setAuth).toHaveBeenCalledWith(authResponse);
  });

  it("throws with backend error on failure", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify("Email already taken"), { status: 400 }),
    );

    const auth = createAuthState();
    const { result } = renderHook(() => useRegisterMutation(), {
      wrapper: createWrapper(auth),
    });

    result.current.mutate({ email: "b@c.d", username: "v", password: "p" });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Email already taken");
  });
});

describe("useLogoutMutation", () => {
  it("calls clearAuth on successful logout", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ message: "ok" }), { status: 200 }),
    );

    const auth = createAuthState();
    const { result } = renderHook(() => useLogoutMutation(), {
      wrapper: createWrapper(auth),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(auth.clearAuth).toHaveBeenCalledOnce();
  });
});
