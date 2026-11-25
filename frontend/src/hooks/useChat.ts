"use client";

import { useState, useRef, useCallback } from "react";
import { api, API_BASE } from "@/lib/api";

const STREAM_API = "http://localhost:8000/api/v1";

export interface Source {
  content: string;
  chapter: string;
  section: string;
  score: number;
}

export interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (sessionId: string, question: string) => {
      setIsLoading(true);
      const userMsg: Message = { role: "user", content: question };
      setMessages((prev) => [...prev, userMsg]);
      setStreamingContent("");

      try {
        const token = localStorage.getItem("access_token");
        const response = await fetch(`${STREAM_API}/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ session_id: sessionId, question }),
        });

        if (!response.ok) {
          throw new Error("Stream request failed");
        }

        const reader = response.body?.getReader();
        if (!reader) return;

        const decoder = new TextDecoder();
        let buffer = "";
        let fullAnswer = "";
        let finalSources: Source[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = JSON.parse(line.slice(6));

            if (data.type === "token") {
              fullAnswer += data.content;
              setStreamingContent(fullAnswer);
            } else if (data.type === "sources") {
              finalSources = data.content;
            } else if (data.type === "done") {
              // done
            }
          }
        }

        const assistantMsg: Message = {
          role: "assistant",
          content: fullAnswer,
          sources: finalSources,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setStreamingContent("");
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error("Chat error:", err);
        }
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const loadSession = useCallback(async (sessionId: string) => {
    try {
      const data = await api.get<{ messages: Message[] }>(`/chat/sessions/${sessionId}`);
      setMessages(data.messages);
    } catch (err) {
      console.error("Load session error:", err);
    }
  }, []);

  const createSession = useCallback(async () => {
    const data = await api.post<{ session_id: string; title: string }>("/chat/sessions");
    return data;
  }, []);

  const getSessions = useCallback(async () => {
    const data = await api.get<{ sessions: Session[] }>("/chat/sessions");
    return data.sessions;
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    await api.delete(`/chat/sessions/${sessionId}`);
  }, []);

  const stopGenerating = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return {
    messages,
    setMessages,
    isLoading,
    streamingContent,
    sendMessage,
    loadSession,
    createSession,
    getSessions,
    deleteSession,
    stopGenerating,
  };
}
