import { describe, it, expect, vi } from "vitest";
import { subscribeUnauthorized, notifyUnauthorized } from "./unauthorizedBus";

describe("unauthorizedBus", () => {
  it("notifies subscribers when unauthorized", () => {
    const cb = vi.fn();
    subscribeUnauthorized(cb);
    notifyUnauthorized();
    expect(cb).toHaveBeenCalledOnce();
  });

  it("does not call unsubscribed callbacks", () => {
    const cb = vi.fn();
    const unsub = subscribeUnauthorized(cb);
    unsub();
    notifyUnauthorized();
    expect(cb).not.toHaveBeenCalled();
  });

  it("supports multiple subscribers", () => {
    const cb1 = vi.fn();
    const cb2 = vi.fn();
    const unsub1 = subscribeUnauthorized(cb1);
    const unsub2 = subscribeUnauthorized(cb2);

    notifyUnauthorized();
    expect(cb1).toHaveBeenCalledOnce();
    expect(cb2).toHaveBeenCalledOnce();

    unsub1();
    unsub2();
  });
});
