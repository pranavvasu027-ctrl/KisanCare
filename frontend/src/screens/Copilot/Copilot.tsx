import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, User, Sparkles, AlertCircle, Loader2, RefreshCw, CheckCircle2, ShieldAlert, Globe, ChevronDown, ChevronUp, Database } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../hooks/useAuth';

interface EvidenceItem {
  tool_name: string;
  arguments: Record<string, any>;
  result: Record<string, any>;
  provenance: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  grounded?: boolean;
  language?: string;
  evidence_references?: EvidenceItem[];
  missing_data_warnings?: string[];
  timestamp?: string;
  failed?: boolean;
  rawText?: string;
}

type LangOption = 'en' | 'mr' | 'hi';

export default function Copilot() {
  const { isDemoMode } = useAuth();
  const [selectedLang, setSelectedLang] = useState<LangOption>('mr');
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `नमस्कार! मी तुमचा किसानकेअर AI कृषी साथीदार (Copilot) आहे.\n\nमी तुम्हाला पीक नियोजन, माती परीक्षण, सिंचन सल्ला, कीड/रोग नियंत्रण आणि बाजारभावाबाबत अचूक मार्गदर्शन करू शकतो. मी तुम्हाला कशी मदत करू?`,
      language: 'mr',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copilotStatus, setCopilotStatus] = useState<{
    status: string;
    gemini_configured: boolean;
    server_reachable?: boolean;
    model?: string;
    message?: string;
  } | null>(null);
  const [expandedEvidence, setExpandedEvidence] = useState<Record<number, boolean>>({});

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

  const toggleEvidence = (idx: number) => {
    setExpandedEvidence(prev => ({ ...prev, [idx]: !prev[idx] }));
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
      // Prepare history for backend (last 6 messages)
      const history = messages.slice(-6).map(m => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content
      }));

      const res = await api.askCopilot(text, history, undefined, selectedLang);

      const aiMsg: Message = {
        role: 'assistant',
        content: res.reply || 'No response returned from the Copilot service.',
        grounded: res.grounded,
        language: res.language || selectedLang,
        evidence_references: res.evidence_references,
        missing_data_warnings: res.missing_data_warnings,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err: any) {
      console.error('Copilot request error:', err);
      const msg = err.message || String(err);
      const isBackendDown = msg.includes('Failed to fetch') || (msg.includes('500') && copilotStatus?.server_reachable === false);
      const friendlyMsg = isBackendDown
        ? 'Cannot connect to the KisanCare backend server (http://localhost:8000). Please ensure the backend service is running.'
        : msg.includes('503')
        ? 'Copilot service is currently unavailable. Please verify backend AI configuration.'
        : msg;
      setError(friendlyMsg);
      // Append an error notice in chat with retry action
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ ${friendlyMsg}`,
          failed: true,
          rawText: text,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = (rawText?: string) => {
    if (!rawText) return;
    handleSendMessage(rawText);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    const defaultGreeting = selectedLang === 'mr'
      ? `संवाद रीसेट केला आहे. मी तुम्हाला शेती, पिके किंवा माती नियोजनात कशी मदत करू शकतो?`
      : selectedLang === 'hi'
      ? `बातचीत रीसेट कर दी गई है। मैं आपकी फसलों या कृषि निर्णयों में कैसे सहायता करूँ?`
      : `Chat history cleared. How can I assist you with your crops or farm decisions today?`;

    setMessages([
      {
        role: 'assistant',
        content: defaultGreeting,
        language: selectedLang,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setError(null);
  };

  const handleLangChange = (lang: LangOption) => {
    setSelectedLang(lang);
  };

  // Language-specific suggestions
  const suggestions: Record<LangOption, string[]> = {
    mr: [
      'माझ्या कापसाच्या पिकाची परिस्थिती कशी आहे? माझ्या शेताची माहिती पाहून सांगा',
      'कापसावरील किडींचे एकात्मिक नियंत्रण (IPM) कसे करावे?',
      'माझ्या शेतासाठी माती परीक्षणाचे काय महत्त्व आहे?',
      'सोयाबीन पिकाचे खत व्यवस्थापन कसे करावे?'
    ],
    hi: [
      'मेरी फसल की वर्तमान स्थिति का विश्लेषण करें',
      'कपास में कीट एवं रोग नियंत्रण के उपाय बताएं',
      'मिट्टी स्वास्थ्य एवं उर्वरक की सही मात्रा क्या है?',
      'फसल चयन करते समय किन बातों का ध्यान रखना चाहिए?'
    ],
    en: [
      'What factors should I consider before selecting a crop?',
      'Based on my farm data, what should I do next?',
      'How much fertilizer should I apply for my field?',
      'What are effective IPM practices for Soybean rust?'
    ]
  };

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      {/* Header Bar */}
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[#103D2C] flex items-center gap-2">
              <Bot className="text-[#B6532A]" /> KisanCare AI Copilot
            </h1>
            {isDemoMode ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Demo Session
              </span>
            ) : copilotStatus?.server_reachable === false ? (
              <span className="bg-rose-100 text-rose-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-rose-300 flex items-center gap-1" title="Backend server offline on localhost:8000">
                <AlertCircle size={12} /> Backend Offline
              </span>
            ) : copilotStatus?.gemini_configured ? (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <CheckCircle2 size={12} /> Gemini Active
              </span>
            ) : (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300 flex items-center gap-1">
                <AlertCircle size={12} /> Gemini Key Unset
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1 text-sm">Grounded agricultural intelligence powered by Google Gemini & KisanCare ML.</p>
        </div>

        {/* Controls: Language Selector and Clear Chat */}
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          <div className="flex items-center bg-white border border-[#E5DDCF] rounded-lg p-0.5 text-xs shadow-sm">
            <Globe size={13} className="text-[#103D2C] ml-2 mr-1" />
            <button
              onClick={() => handleLangChange('mr')}
              className={`px-2 py-1 rounded font-medium transition-colors ${selectedLang === 'mr' ? 'bg-[#103D2C] text-white' : 'text-[#292B26]/70 hover:text-[#103D2C]'}`}
            >
              मराठी
            </button>
            <button
              onClick={() => handleLangChange('hi')}
              className={`px-2 py-1 rounded font-medium transition-colors ${selectedLang === 'hi' ? 'bg-[#103D2C] text-white' : 'text-[#292B26]/70 hover:text-[#103D2C]'}`}
            >
              हिंदी
            </button>
            <button
              onClick={() => handleLangChange('en')}
              className={`px-2 py-1 rounded font-medium transition-colors ${selectedLang === 'en' ? 'bg-[#103D2C] text-white' : 'text-[#292B26]/70 hover:text-[#103D2C]'}`}
            >
              EN
            </button>
          </div>

          <button
            onClick={clearChat}
            className="text-xs text-[#292B26]/60 hover:text-[#103D2C] border border-[#E5DDCF] bg-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <RefreshCw size={12} /> Clear Chat
          </button>
        </div>
      </div>

      {copilotStatus && copilotStatus.server_reachable === false && (
        <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs flex items-center justify-between gap-2 shadow-sm">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
            <span>
              <strong>Backend Offline:</strong> Cannot reach KisanCare backend on <code className="bg-rose-100 px-1 py-0.5 rounded">http://localhost:8000</code>. Please start the backend server: <code className="bg-rose-100 px-1 py-0.5 rounded font-mono">uvicorn backend.app.main:app --port 8000</code>.
            </span>
          </div>
          <button
            onClick={checkStatus}
            className="text-xs bg-white text-rose-800 border border-rose-300 px-2 py-1 rounded hover:bg-rose-100 shrink-0 font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {copilotStatus && copilotStatus.server_reachable !== false && !copilotStatus.gemini_configured && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-center gap-2 shadow-sm">
          <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>Note:</strong> Gemini AI credentials are not configured on the backend server. Configure them in the backend environment (Gemini credentials in backend .env) to enable live Gemini reasoning.
          </span>
        </div>
      )}

      {error && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Chat Messages Panel */}
      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-5">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 max-w-[90%] sm:max-w-[85%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${
                  msg.role === 'user' ? 'bg-[#103D2C] text-white' : 'bg-[#17643E]/10 text-[#17643E]'
                }`}
              >
                {msg.role === 'user' ? <User size={16} /> : <Sparkles size={16} />}
              </div>

              <div className="flex flex-col flex-1 min-w-0">
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-[#103D2C] text-white rounded-tr-none'
                      : msg.failed
                      ? 'bg-red-50 text-red-900 rounded-tl-none border border-red-200'
                      : 'bg-[#FBF7EF] text-[#292B26] rounded-tl-none border border-[#E5DDCF]'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Retry Action for Failed Messages */}
                  {msg.failed && msg.rawText && (
                    <div className="mt-2 pt-2 border-t border-red-200 flex items-center justify-between">
                      <span className="text-xs text-red-700">Request could not be completed.</span>
                      <button
                        onClick={() => handleRetry(msg.rawText)}
                        className="text-xs bg-red-100 hover:bg-red-200 text-red-800 px-2.5 py-1 rounded font-medium transition-colors"
                      >
                        Retry
                      </button>
                    </div>
                  )}

                  {/* Missing Data Warnings */}
                  {msg.missing_data_warnings && msg.missing_data_warnings.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-[#E5DDCF] text-xs text-amber-800 space-y-1">
                      <div className="font-semibold flex items-center gap-1 text-amber-900">
                        <AlertCircle size={12} /> Pending Data Disclosures:
                      </div>
                      {msg.missing_data_warnings.map((w, widx) => (
                        <div key={widx} className="pl-3 border-l-2 border-amber-400">
                          {w}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Evidence & Tool References */}
                  {msg.evidence_references && msg.evidence_references.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-[#E5DDCF]">
                      <button
                        onClick={() => toggleEvidence(i)}
                        className="text-xs text-[#17643E] hover:text-[#103D2C] font-semibold flex items-center gap-1 transition-colors"
                      >
                        <Database size={12} />
                        <span>KisanCare Model Evidence ({msg.evidence_references.length})</span>
                        {expandedEvidence[i] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </button>

                      {expandedEvidence[i] && (
                        <div className="mt-2 space-y-2 text-xs bg-white/80 p-2.5 rounded-lg border border-[#E5DDCF]">
                          {msg.evidence_references.map((ev, evIdx) => (
                            <div key={evIdx} className="p-2 bg-[#FBF7EF] rounded border border-[#E5DDCF]/60">
                              <div className="flex items-center justify-between font-mono text-[11px] text-[#103D2C]">
                                <span>{ev.tool_name}</span>
                                <span className="bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded text-[10px] font-semibold border border-emerald-200">
                                  {ev.provenance}
                                </span>
                              </div>
                              <div className="mt-1 text-[11px] text-[#292B26]/80 font-mono">
                                <strong>Args:</strong> {JSON.stringify(ev.arguments)}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Message Meta: Timestamp and Grounding Badges */}
                <div className={`flex items-center gap-2 mt-1 px-1 text-[11px] text-[#292B26]/50 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.timestamp && <span>{msg.timestamp}</span>}
                  {msg.language && (
                    <span className="uppercase text-[10px] bg-slate-100 text-slate-700 font-semibold px-1.5 py-0.2 rounded">
                      {msg.language}
                    </span>
                  )}
                  {msg.grounded && (
                    <span className="text-emerald-700 font-medium flex items-center gap-0.5">
                      • Grounded in Farm Data
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
                <span>KisanCare AI is analyzing agricultural context and models...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Action Suggestions and Input Form */}
        <div className="p-4 bg-[#FBF7EF] border-t border-[#E5DDCF]">
          <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
            {suggestions[selectedLang].map((sug, sidx) => (
              <button
                key={sidx}
                onClick={() => handleSendMessage(sug)}
                className="bg-white border border-[#E5DDCF] text-xs font-medium text-[#103D2C] px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-[#E5DDCF]/50 transition-colors shadow-xs"
              >
                {sug.length > 45 ? `${sug.slice(0, 45)}...` : sug}
              </button>
            ))}
          </div>

          <div className="relative mt-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                selectedLang === 'mr'
                  ? 'तुमची पिके, माती, कीड, सिंचन किंवा बाजाराबाबत विचारा...'
                  : selectedLang === 'hi'
                  ? 'अपनी फसल, मिट्टी, कीट, सिंचाई या मंडी भाव के बारे में पूछें...'
                  : 'Ask anything about your crops, soil, pests, or farm practices...'
              }
              className="w-full bg-white border border-[#E5DDCF] rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:border-[#17643E] shadow-sm"
              disabled={loading}
              aria-label="Farmer message input"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={loading || !input.trim()}
              aria-label="Send message"
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
