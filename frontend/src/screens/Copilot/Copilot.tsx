import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, User, Sparkles, AlertCircle, Loader2, RefreshCw, CheckCircle2, ShieldAlert } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../hooks/useAuth';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  grounded?: boolean;
  isDemo?: boolean;
  timestamp?: string;
}

export default function Copilot() {
  const { user, isDemoMode } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `Hello! I am your KisanCare AI Copilot, dedicated to agricultural decision intelligence.\n\nI can assist you with crop planning, soil test evaluation, irrigation advisories, pest/disease management, and farm economics. How can I help you today?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copilotStatus, setCopilotStatus] = useState<{ status: string; gemini_configured: boolean; message?: string } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkStatus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const checkStatus = async () => {
    try {
      const res = await api.getCopilotStatus();
      setCopilotStatus(res);
    } catch {
      // Backend not yet reachable
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    setError(null);
    setInput('');

    // Append user message
    const userMsg: Message = {
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      // Prepare history for backend
      const history = messages.slice(-6).map(m => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content
      }));

      const res = await api.askCopilot(text, history);

      const aiMsg: Message = {
        role: 'assistant',
        content: res.reply || 'No response returned from the Copilot service.',
        grounded: res.grounded,
        isDemo: res.isDemo,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err: any) {
      console.error('Copilot request error:', err);
      const msg = err.message || String(err);
      setError(msg);
      // Append an error notice in chat as well
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ ${msg.includes('503') ? 'Copilot service is currently unavailable. Please verify the Gemini API key is configured on the backend.' : msg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: `Chat history cleared. How can I assist you with your crops or fields today?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setError(null);
  };

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C] flex items-center gap-2">
              <Bot className="text-[#B6532A]" /> KisanCare AI Copilot
            </h1>
            {isDemoMode ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Demo Mode
              </span>
            ) : copilotStatus?.gemini_configured ? (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <CheckCircle2 size={12} /> Gemini 3.8 Flash Active
              </span>
            ) : (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300 flex items-center gap-1">
                <AlertCircle size={12} /> Gemini Key Unset
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1">Your agricultural decision assistant, grounded in farm data.</p>
        </div>
        <button
          onClick={clearChat}
          className="self-start sm:self-auto text-xs text-[#292B26]/60 hover:text-[#103D2C] border border-[#E5DDCF] bg-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
        >
          <RefreshCw size={12} /> Clear Chat
        </button>
      </div>

      {copilotStatus && !copilotStatus.gemini_configured && !isDemoMode && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-center gap-2 shadow-sm">
          <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>Note:</strong> The Gemini API key is not configured on the backend server. Responses in live mode require <code>GEMINI_API_KEY</code> in the backend environment.
          </span>
        </div>
      )}

      {error && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] flex-1 flex flex-col overflow-hidden">
        {/* Messages Container */}
        <div className="flex-1 p-6 overflow-y-auto space-y-5">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${
                  msg.role === 'user' ? 'bg-[#103D2C] text-white' : 'bg-[#17643E]/10 text-[#17643E]'
                }`}
              >
                {msg.role === 'user' ? <User size={16} /> : <Sparkles size={16} />}
              </div>
              <div className="flex flex-col">
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-[#103D2C] text-white rounded-tr-none'
                      : 'bg-[#FBF7EF] text-[#292B26] rounded-tl-none border border-[#E5DDCF]'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
                <div className={`flex items-center gap-2 mt-1 px-1 text-[11px] text-[#292B26]/50 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.timestamp && <span>{msg.timestamp}</span>}
                  {msg.grounded && (
                    <span className="text-emerald-700 font-medium flex items-center gap-0.5">
                      • Grounded in Farm Data
                    </span>
                  )}
                  {msg.isDemo && (
                    <span className="text-amber-700 font-medium">
                      • Demo Sample
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 max-w-[85%] items-center">
              <div className="w-8 h-8 rounded-full bg-[#17643E]/10 text-[#17643E] flex items-center justify-center shrink-0">
                <Sparkles size={16} />
              </div>
              <div className="bg-[#FBF7EF] border border-[#E5DDCF] px-4 py-3 rounded-2xl rounded-tl-none flex items-center gap-2 text-xs text-[#292B26]/70">
                <Loader2 className="w-4 h-4 animate-spin text-[#17643E]" />
                <span>KisanCare AI is analyzing agricultural context...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Action Suggestions and Input Form */}
        <div className="p-4 bg-[#FBF7EF] border-t border-[#E5DDCF]">
          <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
            <button
              onClick={() => handleSendMessage('What factors should I consider before selecting a crop?')}
              className="bg-white border border-[#E5DDCF] text-xs font-medium text-[#103D2C] px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-[#E5DDCF]/50 transition-colors"
            >
              Crop selection factors
            </button>
            <button
              onClick={() => handleSendMessage('Based on my farm data, what should I do next?')}
              className="bg-white border border-[#E5DDCF] text-xs font-medium text-[#103D2C] px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-[#E5DDCF]/50 transition-colors"
            >
              Analyze my farm records
            </button>
            <button
              onClick={() => handleSendMessage('How much fertilizer should I apply for my field?')}
              className="bg-white border border-[#E5DDCF] text-xs font-medium text-[#103D2C] px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-[#E5DDCF]/50 transition-colors"
            >
              Fertilizer dosage inquiry
            </button>
            <button
              onClick={() => handleSendMessage('What are effective IPM practices for Soybean rust?')}
              className="bg-white border border-[#E5DDCF] text-xs font-medium text-[#103D2C] px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-[#E5DDCF]/50 transition-colors"
            >
              Soybean rust management
            </button>
          </div>

          <div className="relative mt-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your crops, soil, pests, or farm practices..."
              className="w-full bg-white border border-[#E5DDCF] rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:border-[#17643E] shadow-sm"
              disabled={loading}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={loading || !input.trim()}
              className="absolute right-2 top-2 w-8 h-8 bg-[#103D2C] text-white rounded-lg flex items-center justify-center hover:bg-[#17643E] disabled:opacity-40 transition-colors"
            >
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
