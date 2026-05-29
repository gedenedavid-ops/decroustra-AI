import React, { useState, useRef, useEffect } from "react";
import { ClaudeChatInput } from "./components/ui/claude-style-chat-input";

const API_URL = import.meta.env.VITE_API_URL || "";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "Un enfant a disparu a Yopougon, que faire ?",
  "Montre-moi les disparitions recentes a Abidjan",
  "Y a-t-il des alertes pour des personnes agees ?",
  "Quelles sont les dernieres disparitions signalees ?",
];

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [showWelcome, setShowWelcome] = useState(true);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (data: any) => {
    if (!data.message.trim()) return;
    setShowWelcome(false);

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: data.message,
    };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setIsLoading(true);

    try {
      const history = updatedMessages.map((m) => ({
        role: m.role === "user" ? "user" : "assistant",
        content: m.content,
      }));

      const response = await fetch(`${API_URL}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: data.message,
          history: history.slice(0, -1),
        }),
      });
      const result = await response.json();

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: result.answer,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      const errorMsg: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: "Impossible de contacter le serveur.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto px-4">
      {showWelcome && (
        <div className="flex-1 flex flex-col items-center justify-center">
          <h1
            className="text-6xl sm:text-7xl mb-2 select-none"
            style={{
              fontFamily: "'Caveat', cursive",
              color: "var(--color-accent)",
            }}
          >
            decroustra
          </h1>
          <p className="text-text-300 text-sm mb-10">
            Centralise les alertes. Retrouve les personnes disparues.
          </p>

          <div className="flex flex-wrap justify-center gap-2 max-w-xl">
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage({ message: s, files: [] })}
                className="px-4 py-2 text-sm text-text-300 bg-transparent border border-bg-300 rounded-full hover:bg-bg-200 hover:text-text-200 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {!showWelcome && (
        <div className="flex-1 overflow-y-auto space-y-4 py-4">
          <h2
            className="text-center text-2xl mb-4 select-none"
            style={{
              fontFamily: "'Caveat', cursive",
              color: "var(--color-accent)",
            }}
          >
            decroustra
          </h2>

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`p-4 rounded-2xl max-w-[85%] whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-bg-200 ml-auto text-text-100"
                  : "bg-white border border-bg-300 text-text-100"
              }`}
            >
              {msg.content}
            </div>
          ))}
          {isLoading && (
            <div className="p-4 rounded-2xl bg-white border border-bg-300 max-w-[85%]">
              <span className="inline-flex gap-1">
                <span
                  className="w-2 h-2 bg-text-300 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <span
                  className="w-2 h-2 bg-text-300 rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <span
                  className="w-2 h-2 bg-text-300 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      )}

      <div className="sticky bottom-0 bg-bg-0 pb-4 pt-2">
        <ClaudeChatInput onSendMessage={handleSendMessage} />
      </div>
    </div>
  );
};

export default ChatInterface;
