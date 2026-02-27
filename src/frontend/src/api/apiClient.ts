import { notifyUnauthorized } from "./unauthorizedBus";

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const stored = localStorage.getItem("auth_user");
  if (!stored) return false;

  const { id } = JSON.parse(stored) as { id: string };
  const res = await fetch("/api/auth/refresh-token", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userId: id }),
  });

  return res.ok;
}

function refreshOnce(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = tryRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

function buildInit(options?: RequestInit): RequestInit {
  return {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  };
}

export async function apiFetch(
  url: string,
  options?: RequestInit,
): Promise<Response> {
  const res = await fetch(url, buildInit(options));

  if (res.status === 401) {
    const refreshed = await refreshOnce();
    if (refreshed) {
      return fetch(url, buildInit(options));
    }
    notifyUnauthorized();
  }

  return res;
}
