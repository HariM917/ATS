import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../services/api';
import { Card } from '../components/ui';
import { 
  Brain, Sparkles, Copy, Loader2, ChevronRight 
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Helmet } from 'react-helmet-async';

interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  timestamp?: number;
}

export const ChatPage = ({ messages, setMessages }: { messages: ChatMessage[]; setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>> }) => {
  const { user } = useAuth();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input;
    setMessages(prev => [...prev, { role: "user", text: userMsg, timestamp: Date.now() }]);
    setInput("");
    setLoading(true);

    const SMART_FALLBACK = "I'm here to support your career journey! I can provide guidance on resume optimization, interview strategies, technical skill roadmaps, and career strategy. What specific area can I help you with right now?";

    try {
      const res = await apiClient.post('/chat', { message: userMsg });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      let aiText = "";
      if (typeof data.answer === "string" && data.answer.trim().length > 5) {
        aiText = data.answer.trim();
      } else if (typeof data.response === "string" && data.response.trim().length > 5) {
        aiText = data.response.trim();
      } else {
        aiText = SMART_FALLBACK;
      }
      setMessages(prev => [...prev, { role: "ai", text: aiText, timestamp: Date.now() }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: "ai", text: SMART_FALLBACK, timestamp: Date.now() }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestedQueries = [
    "How to improve my resume?",
    "Data Science career roadmap",
    "Interview preparation tips",
    "Salary negotiation strategies"
  ];

  return (
    <div className="h-full flex flex-col page-enter">
      <Helmet>
        <title>AI Coach | FlowATS</title>
        <meta name="description" content="Get AI-powered career guidance and interview prep." />
      </Helmet>
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-100 rounded-xl"><Brain className="w-6 h-6 text-indigo-600" /></div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Career Intelligence</h2>
            <p className="text-gray-500 text-sm">Real-time coaching powered by FlowATS RAG</p>
          </div>
        </div>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden shadow-2xl border-gray-100 bg-white">
        <div className="p-4 bg-gradient-to-r from-indigo-600 to-indigo-800 flex justify-between items-center text-white shadow-md">
          <div className="flex items-center gap-2 font-bold tracking-tight"><Sparkles className="w-5 h-5 text-indigo-200" /> AI STRATEGIST</div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            <span className="text-[10px] font-black uppercase opacity-80">Live Pipeline</span>
          </div>
        </div>

        <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-50/50 scroll-smooth">
          {messages.length <= 1 && !loading && (
            <div className="flex flex-wrap gap-2 justify-center pt-4">
              {suggestedQueries.map((q, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => { setInput(q); }}
                  className="px-4 py-2 bg-white border border-indigo-100 text-indigo-700 rounded-xl text-xs font-semibold hover:bg-indigo-50 hover:border-indigo-300 transition-all cursor-pointer"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}>
              <div className={`flex gap-3 max-w-[85%] ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${m.role === 'user' ? 'bg-indigo-100 text-indigo-600' : 'bg-indigo-600 text-white'}`}>
                  {m.role === 'user' ? 'ME' : 'AI'}
                </div>
                <div className={`relative group p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-white border border-gray-100 text-gray-700 rounded-tl-none'}`}>
                  {m.role === 'user' ? (
                    <div className="whitespace-pre-wrap">{m.text}</div>
                  ) : (
                    <>
                      <div className="markdown-content"><ReactMarkdown>{m.text}</ReactMarkdown></div>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(m.text)}
                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-100 rounded cursor-pointer"
                        title="Copy"
                      >
                        <Copy className="w-3 h-3 text-gray-400" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start animate-in fade-in duration-300">
              <div className="flex gap-3 max-w-[85%]">
                <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center">
                  <Loader2 className="w-4 h-4 animate-spin" />
                </div>
                <div className="p-4 bg-white border border-gray-100 rounded-2xl rounded-tl-none">
                  <div className="typing-indicator">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 bg-white border-t border-gray-100">
          <div className="flex gap-3">
            <input
              className="flex-1 border border-gray-200 rounded-xl px-5 py-4 text-sm focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition-all bg-gray-50 focus:bg-white"
              placeholder="Ask about resume tips, interview prep, or job matches..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              disabled={loading}
            />
            <button
              type="button"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 disabled:opacity-50 disabled:shadow-none hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          </div>
          <p className="text-[10px] text-gray-400 text-center mt-3 font-medium uppercase tracking-widest">Powered by FlowATS Intelligence v3.0</p>
        </div>
      </Card>
    </div>
  );
};
