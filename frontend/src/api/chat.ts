/**
 * TalentFlow AI — AI Career Coach & RAG Chat API Client
 */
import client from './client';
import { ChatMessage } from '../types';

export interface ChatResponse {
  answer: string;
  sources: Array<{
    id?: string;
    category?: string;
    question?: string;
    content?: string;
    similarity?: number;
  }>;
  session_id?: string;
}

export const chatApi = {
  sendMessage: async (message: string, sessionId?: string): Promise<ChatResponse> => {
    const res = await client.post<{ status: string; data?: ChatResponse; answer?: string; sources?: any[] }>(
      '/chat/message',
      { message, session_id: sessionId }
    );
    if (res.data) {
      return res.data;
    }
    return {
      answer: res.answer || '',
      sources: res.sources || [],
    };
  },

  getHistory: async (): Promise<ChatMessage[]> => {
    const res = await client.get<{ status: string; data?: any[]; history?: any[] }>('/chat/history');
    const items = res.data || res.history || [];
    return items.map((item) => ({
      id: item.id,
      role: 'ai',
      text: item.ai,
      timestamp: item.timestamp,
      sources: item.sources,
    }));
  },
};

