import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import {
  HubConnectionBuilder,
  HubConnection,
  HubConnectionState,
  LogLevel,
} from "@microsoft/signalr";

export type HubState = "connecting" | "connected" | "disconnected" | "error";

export function useLiveFeedHub() {
  const [state, setState] = useState<HubState>("connecting");
  const connectionRef = useRef<HubConnection | null>(null);

  useEffect(() => {
    const connection = new HubConnectionBuilder()
      .withUrl("/hub/livefeed")
      .withAutomaticReconnect([0, 1000, 3000])
      .configureLogging(LogLevel.Warning)
      .build();

    connectionRef.current = connection;

    connection.onreconnecting(() => setState("connecting"));
    connection.onreconnected(() => setState("connected"));
    connection.onclose(() => setState("disconnected"));

    // Join is deferred to consumer hooks (after handler registration)
    // to avoid a race where server events arrive before handlers exist.
    connection
      .start()
      .then(() => setState("connected"))
      .catch(() => setState("error"));

    return () => {
      connection.stop();
    };
  }, []);

  const on = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (event: string, handler: (...args: any[]) => void) => {
      connectionRef.current?.on(event, handler);
    },
    [],
  );

  const off = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (event: string, handler: (...args: any[]) => void) => {
      connectionRef.current?.off(event, handler);
    },
    [],
  );

  const invoke = useCallback(
    async (method: string, ...args: unknown[]) => {
      if (connectionRef.current?.state === HubConnectionState.Connected) {
        await connectionRef.current.invoke(method, ...args);
      }
    },
    [],
  );

  return useMemo(
    () => ({ connection: connectionRef.current, state, on, off, invoke }),
    [state, on, off, invoke],
  );
}
