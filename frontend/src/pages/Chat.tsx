import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, Sparkles, BookOpen, Bot, User, Loader2 } from 'lucide-react';
import { chatApi } from '../api/chat';
import { ChatMessage } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';

const SUGGESTED_PROMPTS = [
  'How to make my resume ATS friendly?',
  'How to answer STAR method behavioral questions?',
  'How to highlight Python machine learning skills?',
  'How to negotiate salary effectively?',
  'How to prepare for a technical coding interview?',
];

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadChatHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const loadChatHistory = async () => {
    try {
      const history = await chatApi.getHistory();
      if (history.length > 0) {
        setMessages(history);
      } else {
        setMessages([
          {
            role: 'ai',
            text: "Hello! I'm your TalentFlow AI Career Coach. Ask me anything about resume optimization, interview preparation, salary negotiation, or career transitions.",
            timestamp: Date.now(),
          },
        ]);
      }
    } catch {
      setMessages([
        {
          role: 'ai',
          text: "Hello! I'm your TalentFlow AI Career Coach. How can I help you accelerate your job search today?",
          timestamp: Date.now(),
        },
      ]);
    }
  };

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isSending) return;

    const userMsg: ChatMessage = {
      role: 'user',
      text: query,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsSending(true);

    try {
      const res = await chatApi.sendMessage(query);
      const aiMsg: ChatMessage = {
        role: 'ai',
        text: res.answer || "I'm sorry, I couldn't generate a response. Please try asking again.",
        timestamp: Date.now(),
        sources: res.sources,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          text: 'A connection issue occurred while contacting the AI Career Coach. Please check your network and try again.',
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-4xl mx-auto">
      {/* Chat Header */}
      <div className="pb-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-100">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-black text-gray-900">AI Career Coach & RAG Assistant</h1>
            <p className="text-xs text-gray-500">Knowledge-grounded answers for your career and ATS queries</p>
          </div>
        </div>
      </div>

      {/* Suggested Prompts */}
      <div className="py-3 flex gap-2 overflow-x-auto">
        {SUGGESTED_PROMPTS.map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSend(prompt)}
            className="px-3 py-1.5 rounded-full text-xs font-semibold bg-white border border-gray-200 text-gray-700 hover:border-indigo-300 hover:bg-indigo-50/50 hover:text-indigo-700 whitespace-nowrap transition-all cursor-pointer shadow-2xs"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Chat Messages Scrollable Area */}
      <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-1">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div key={index} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {!isUser && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-violet-600 text-white flex items-center justify-center flex-shrink-0 text-xs shadow-xs mt-1">
                  <Sparkles className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed shadow-2xs ${
                  isUser
                    ? 'bg-indigo-600 text-white rounded-br-xs'
                    : 'bg-white border border-gray-100 text-gray-800 rounded-bl-xs'
                }`}
              >
                <p className="whitespace-pre-line">{msg.text}</p>

                {/* Sources / Citations */}
                {!isUser && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-[11px] font-bold text-gray-400 uppercase flex items-center gap-1 mb-1.5">
                      <BookOpen className="w-3.5 h-3.5" /> Sources & Reference Material
                    </p>
                    <div className="space-y-1">
                      {msg.sources.map((s, idx) => (
                        <div key={idx} className="p-2 bg-gray-50 rounded-lg text-xs text-gray-600">
                          {s.question && <strong className="block text-gray-800">{s.question}</strong>}
                          <span>{s.content}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center flex-shrink-0 text-xs font-bold mt-1">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {isSending && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 text-xs shadow-xs mt-1">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-xs p-4 flex items-center gap-2 text-xs text-gray-500 shadow-2xs">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              AI Coach is thinking and retrieving context...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="pt-3 border-t border-gray-100">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about resumes, interviews, or career paths..."
            disabled={isSending}
            className="flex-1 bg-white border border-gray-200 rounded-2xl px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-xs"
          />
          <Button
            type="submit"
            variant="primary"
            disabled={!input.trim() || isSending}
            isLoading={isSending}
            className="px-5 rounded-2xl"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
};

