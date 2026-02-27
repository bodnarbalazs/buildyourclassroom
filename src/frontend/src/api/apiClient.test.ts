import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiFetch } from "./apiClient";
import * as bus from "./unauthorizedBus";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.spyOn(bus, "notifyUnauthorized");
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

function okResponse(body?: unknown): Response {
  return new Response(body ? JSON.stringify(body) : null, { status: 200 });
}

function unauthorizedResponse(): Response {
  return new Response(null, { status: 401 });
}

describe("apiFetch", () => {
  it("passes through successful responses", async () => {
    fetchMock.mockResolvedValueOnce(okResponse({ ok: true }));

    const res = await apiFetch("/api/test");
    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("sets credentials and content-type headers", async () => {
    fetchMock.mockResolvedValueOnce(okResponse());

    await apiFetch("/api/test");
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.credentials).toBe("include");
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe(
      "application/json",
    );
  });

  it("retries once after 401 if refresh succeeds", async () => {
    localStorage.setItem("auth_user", JSON.stringify({ id: "u1" }));

    // First call: 401
    fetchMock.mockResolvedValueOnce(unauthorizedResponse());
    // Refresh call: 200
    fetchMock.mockResolvedValueOnce(okResponse());
    // Retry of original call: 200
    fetchMock.mockResolvedValueOnce(okResponse({ retried: true }));

    const res = await apiFetch("/api/protected");

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(res.status).toBe(200);
    expect(bus.notifyUnauthorized).not.toHaveBeenCalled();
  });

  it("notifies unauthorized bus when refresh fails", async () => {
    localStorage.setItem("auth_user", JSON.stringify({ id: "u1" }));

    fetchMock.mockResolvedValueOnce(unauthorizedResponse());
    // Refresh fails
    fetchMock.mockResolvedValueOnce(unauthorizedResponse());

    const res = await apiFetch("/api/protected");

    expect(res.status).toBe(401);
    expect(bus.notifyUnauthorized).toHaveBeenCalledOnce();
  });

  it("notifies unauthorized bus when no stored user (skip refresh)", async () => {
    fetchMock.mockResolvedValueOnce(unauthorizedResponse());

    const res = await apiFetch("/api/protected");

    expect(res.status).toBe(401);
    expect(bus.notifyUnauthorized).toHaveBeenCalledOnce();
  });
});
