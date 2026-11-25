"use client";

import { useState, useEffect, useCallback } from "react";
import { useChat } from "@/hooks/useChat";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { SessionList } from "@/components/SessionList";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";
import type { Session } from "@/hooks/useChat";

export default function ChatPage() {
  const {
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
  } = useChat();

  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const refreshSessions = useCallback(async () => {
    try {
      const list = await getSessions();
      setSessions(list);
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  }, [getSessions]);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  const handleNewSession = async () => {
    try {
      const session = await createSession();
      setCurrentSessionId(session.session_id);
      setSessions((prev) => [
        { id: session.session_id, title: session.title, created_at: new Date().toISOString() },
        ...prev,
      ]);
      setMobileOpen(false);
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  };

  const handleSelectSession = async (id: string) => {
    setCurrentSessionId(id);
    await loadSession(id);
    setMobileOpen(false);
  };

  const handleDeleteSession = async (id: string) => {
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (currentSessionId === id) {
        setCurrentSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  const handleSend = async (question: string) => {
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const session = await createSession();
        sessionId = session.session_id;
        setCurrentSessionId(sessionId);
        setSessions((prev) => [
          { id: sessionId!, title: session.title, created_at: new Date().toISOString() },
          ...prev,
        ]);
      } catch (err) {
        console.error("Failed to create session:", err);
        return;
      }
    }
    await sendMessage(sessionId, question);
  };

  const sidebarContent = (
    <SessionList
      sessions={sessions}
      currentId={currentSessionId ?? undefined}
      onSelect={handleSelectSession}
      onNew={handleNewSession}
      onDelete={handleDeleteSession}
    />
  );

  return (
    <div className="flex h-[calc(100vh-3.5rem)] w-full">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-72 border-r flex-col shrink-0">
        {sidebarContent}
      </aside>

      {/* Mobile sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger className="md:hidden absolute top-1 left-2 z-10 mt-1 inline-flex items-center justify-center rounded-lg p-2 text-muted-foreground hover:bg-muted transition-colors">
          <Menu className="h-5 w-5" />
        </SheetTrigger>
        <SheetContent side="left" className="w-72 p-0">
          {sidebarContent}
        </SheetContent>
      </Sheet>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        <ScrollArea className="flex-1 p-4">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.length === 0 && !streamingContent && (
              <div className="flex flex-col items-center justify-center h-[60vh] text-center">
                <div className="text-6xl mb-4">🏫</div>
                <h2 className="text-xl font-semibold mb-2">校园生活助手</h2>
                <p className="text-muted-foreground max-w-md">
                  关于校园生活的任何问题，都可以问我！<br />
                  宿舍、食堂、图书馆、奖学金...
                </p>
              </div>
            )}

            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}

            {isLoading && !streamingContent && (
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-medium mt-1">
                  AI
                </div>
                <div className="bg-muted rounded-lg px-4 py-3 text-sm">
                  <span className="inline-flex gap-1">
                    <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce [animation-delay:0ms]" />
                    <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce [animation-delay:300ms]" />
                  </span>
                </div>
              </div>
            )}

            {streamingContent && (
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-medium mt-1">
                  AI
                </div>
                <div className="bg-muted rounded-lg px-4 py-2 text-sm prose prose-sm dark:prose-invert max-w-[80%]">
                  {streamingContent}
                  <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <ChatInput onSend={handleSend} onStop={stopGenerating} isLoading={isLoading} />
      </div>
    </div>
  );
}
