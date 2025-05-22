import { useEffect, useRef, useState } from "react";

interface IUseWebSocketConnectionProps {
  clientId: string;
  endpoint: string;
  token: string;
  handleWSOpen?: (event: Event) => void;
  handleWSMessage?: (event: MessageEvent<any>) => void;
  handleWSClose?: (event: CloseEvent) => void;
  handleWSError?: (event: Event) => void;
}

const useWebSocketConnection = ({
  clientId,
  endpoint,
  token,
  handleWSOpen,
  handleWSMessage,
  handleWSClose,
  handleWSError,
}: IUseWebSocketConnectionProps) => {
  const ws = useRef<WebSocket | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false); // loading state to indicate if the websocket connection is loading or not
  const [isError, setIsError] = useState(false); // error state to indicate if there is an error in websocket connection
  const [lockChat, setLockChat] = useState(false);

  function getWebSocketURL(): string {
    const isSecureProtocol =
      window.location.protocol === "https:" || window.location.port === "443";
    const webSocketProtocol = isSecureProtocol ? "wss" : "ws";
    // const host = process.env.VITE_OPENAGI_BACKEND_URL.replace(
    //   /^https?:\/\//,
    //   ""
    // );

    const host = "";

    /**
     * Ex: endpoint = `/api/v1/private/applications/${agentId}/interact/clarification`;
     */
    return `${
      process.env.DEV ? "ws" : webSocketProtocol
    }://${host}${endpoint}?token=${encodeURIComponent(token!)}`;
  }

  function connectWS(): void {
    try {
      setLoading(true);
      const urlWs = getWebSocketURL();
      const newWs = new WebSocket(urlWs);
      console.log("New ws connection attempt");
      newWs.onopen = (event) => {
        if (typeof handleWSOpen !== "undefined") {
          handleWSOpen(event);
        } else {
          console.log("WebSocket connection established!");
        }
        setIsOpen(true);
        setLoading(false);
        setIsError(false);
      };
      newWs.onmessage = (event) => {
        // Check if backend is notifying the frontend via the message before closing the connection
        if (
          JSON.parse(event.data)?.message ===
          "WEBSOCKET_CONNECTION_CLOSED_UNGRACEFULLY_AT_BACKEND"
        ) {
          setIsError(true);
          return;
        }

        if (typeof handleWSMessage !== "undefined") {
          handleWSMessage(event);
        } else {
          console.log("onmessage :", event.data);
        }
      };
      newWs.onclose = (event) => {
        // Check if the event was closed cleanly or not
        if (!event.wasClean) {
          setIsError(true);
        }

        if (typeof handleWSClose !== "undefined") {
          handleWSClose(event);
        } else {
          console.log("WebSocket connection closed!");
          console.log(event);
        }
        setIsOpen(false);
        setLoading(false);
      };
      newWs.onerror = (event) => {
        if (typeof handleWSError !== "undefined") {
          handleWSError(event);
        } else {
          console.log("onerror :", event);
        }
        setLoading(false);
        setIsError(true);
      };
      ws.current = newWs;
    } catch (error) {
      setLoading(false);
      setIsError(true);
      if (!!clientId) {
        connectWS();
      } else {
        console.log("Error :", error);
      }
    }
  }

  useEffect(() => {
    connectWS();
    return () => {
      if (ws.current) {
        setIsOpen(false);
        setLoading(false);
        setIsError(false);
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (
      ws.current &&
      (ws.current.readyState === ws.current.CLOSED ||
        ws.current.readyState === ws.current.CLOSING)
    ) {
      connectWS();
      setLockChat(false);
    }
  }, [lockChat]);

  return { ws, connectWS, lockChat, setLockChat, isOpen, loading, isError };
};

export default useWebSocketConnection;
