import { useEffect, useRef, useState, useCallback } from "react";
import {
  HubConnectionBuilder,
  HubConnection,
  HubConnectionState,
  LogLevel,
} from "@microsoft/signalr";

export type HubState = "connecting" | "connected" | "disconnected" | "error";

export function useLiveFeedHub(role: "display" | "camera") {
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

    connection
      .start()
      .then(() => {
        setState("connected");
        return connection.invoke(
          role === "display" ? "JoinAsDisplay" : "JoinAsCamera",
        );
      })
      .catch(() => setState("error"));

    return () => {
      connection.stop();
    };
  }, [role]);

  const on = useCallback(
    (event: string, handler: (...args: unknown[]) => void) => {
      connectionRef.current?.on(event, handler);
    },
    [],
  );

  const off = useCallback(
    (event: string, handler: (...args: unknown[]) => void) => {
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

  return { connection: connectionRef.current, state, on, off, invoke };
}
