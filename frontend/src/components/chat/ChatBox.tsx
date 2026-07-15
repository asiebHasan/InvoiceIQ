'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { ChatSession, ChatSessionDetail, ChatMessage, Document } from '@/lib/types';

export default function ChatBox() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSessionDetail | null>(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [docs, setDocs] = useState<Document[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadSessions = useCallback(async () => {
    const res = await api.listChatSessions();
    setSessions(res);
  }, []);

  const loadSession = useCallback(async (id: string) => {
    const res = await api.getChatSession(id);
    setActiveSession(res);
  }, []);

  useEffect(() => {
    loadSessions();
    api.listDocuments({}).then((res) => {
      setDocs(res.documents.filter((d) => d.status === 'completed'));
    });
  }, [loadSessions]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeSession?.messages]);

  const handleNewChat = async (docId?: string) => {
    const session = await api.createChatSession(docId);
    setActiveSession(session);
    await loadSessions();
  };

  const handleSelectSession = async (id: string) => {
    await loadSession(id);
  };

  const handleDeleteSession = async (id: string) => {
    await api.deleteChatSession(id);
    if (activeSession?.id === id) {
      setActiveSession(null);
    }
    await loadSessions();
  };

  const handleSend = async () => {
    if (!input.trim() || loading || !activeSession) return;
    const message = input.trim();
    setInput('');

    // Add user message optimistically
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    setActiveSession((prev) =>
      prev ? { ...prev, messages: [...prev.messages, userMsg] } : prev
    );
    setLoading(true);

    try {
      const res = await api.sendChatMessage(activeSession.id, message);
      // Reload session to get accurate state
      await loadSession(activeSession.id);
      await loadSessions();
    } catch {
      setActiveSession((prev) =>
        prev
          ? {
              ...prev,
              messages: [
                ...prev.messages,
                {
                  id: `err-${Date.now()}`,
                  role: 'assistant',
                  content: 'Failed to get response. Please try again.',
                  created_at: new Date().toISOString(),
                },
              ],
            }
          : prev
      );
    }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    return d.toLocaleDateString();
  };

  return (
    <div className="flex gap-4 h-[calc(100vh-8rem)]">
      {/* Session sidebar */}
      {showSidebar && (
        <div className="w-64 shrink-0 flex flex-col card overflow-hidden">
          <div className="p-3 border-b border-gray-200">
            <button
              onClick={() => handleNewChat()}
              className="w-full px-3 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700"
            >
              + New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {sessions.length === 0 && (
              <p className="p-4 text-sm text-gray-400 text-center">No conversations yet</p>
            )}
            {sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => handleSelectSession(s.id)}
                className={`group flex items-center gap-2 px-3 py-2.5 cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${
                  activeSession?.id === s.id ? 'bg-brand-50 border-l-2 border-l-brand-600' : ''
                }`}
              >
                <span className="text-lg shrink-0">💬</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{s.title}</p>
                  <p className="text-xs text-gray-400">{s.message_count} messages · {formatTime(s.updated_at)}</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDeleteSession(s.id); }}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 text-xs shrink-0 px-1"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded"
            >
              {showSidebar ? '◀' : '▶'} Sessions
            </button>
            {activeSession && (
              <h2 className="text-sm font-medium text-gray-700 truncate">{activeSession.title}</h2>
            )}
          </div>
          <div className="flex items-center gap-2">
            <select
              onChange={(e) => { if (e.target.value) handleNewChat(e.target.value); e.target.value = ''; }}
              value=""
              className="text-sm border border-gray-300 rounded-lg px-2 py-1"
            >
              <option value="" disabled>New chat with doc...</option>
              {docs.map((d) => (
                <option key={d.id} value={d.id}>{d.filename}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {!activeSession && (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-3">💬</div>
                <p className="text-lg font-medium">Start a new conversation</p>
                <p className="text-sm mt-1">Click "New Chat" or select a session from the sidebar</p>
              </div>
            </div>
          )}
          {activeSession && activeSession.messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-3">💬</div>
                <p className="text-lg font-medium">Ask a question</p>
                <p className="text-sm mt-1">e.g. "What is the total amount?"</p>
              </div>
            </div>
          )}
          {activeSession?.messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    <p className="text-xs text-gray-400">
                      Sources: {msg.sources.map((s) => s.filename).join(', ')}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className="animate-pulse">●</span>
                  <span className="animate-pulse" style={{ animationDelay: '0.2s' }}>●</span>
                  <span className="animate-pulse" style={{ animationDelay: '0.4s' }}>●</span>
                  <span className="ml-1">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="card p-3">
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={activeSession ? "Ask a question..." : "Create a new chat first"}
              rows={1}
              disabled={!activeSession}
              className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent disabled:opacity-50"
              style={{ minHeight: '40px', maxHeight: '120px' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = Math.min(target.scrollHeight, 120) + 'px';
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim() || !activeSession}
              className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50 shrink-0"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
