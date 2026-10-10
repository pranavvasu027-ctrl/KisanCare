import React, { useState } from 'react';
import { Bot, Send, User, Sparkles } from 'lucide-react';

export default function Copilot() {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Hello Ramesh! I am your KisanCare AI Copilot. How can I help you with your farm today?' },
    { role: 'user', content: 'What crop should I plant in Field 1 next season?' },
    { role: 'ai', content: 'Based on Field 1\'s black cotton soil, your current soil test (pH 7.2), and the upcoming Kharif season, I strongly recommend **Soybean (JS 335)**. \n\nOur models predict a yield of 2.8 t/ac and a profit of ₹42,000/ac. Would you like to run a What-If simulation to see how different irrigation levels might affect this?' }
  ]);

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      <div className="mb-4">
        <h1 className="text-3xl font-serif font-bold text-[#103D2C] flex items-center gap-2"><Bot className="text-[#B6532A]" /> KisanCare AI Copilot</h1>
        <p className="text-[#292B26]/70 mt-1">Your personal agricultural assistant, powered by farm data.</p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-4 max-w-[80%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-[#103D2C] text-white' : 'bg-[#17643E]/10 text-[#17643E]'}`}>
                {msg.role === 'user' ? <User size={16} /> : <Sparkles size={16} />}
              </div>
              <div className={`p-4 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-[#103D2C] text-white rounded-tr-none' : 'bg-[#FBF7EF] text-[#292B26] rounded-tl-none border border-[#E5DDCF]'}`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 bg-[#FBF7EF] border-t border-[#E5DDCF]">
          <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
            <button className="bg-white border border-[#E5DDCF] text-xs font-medium text-[#103D2C] px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-[#E5DDCF]/50">Analyze soil report</button>
            <button className="bg-white border border-[#E5DDCF] text-xs font-medium text-[#103D2C] px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-[#E5DDCF]/50">Check weather risks</button>
            <button className="bg-white border border-[#E5DDCF] text-xs font-medium text-[#103D2C] px-3 py-1.5 rounded-full whitespace-nowrap hover:bg-[#E5DDCF]/50">Compare fertilizer costs</button>
          </div>
          <div className="relative mt-2">
            <input type="text" placeholder="Ask anything about your farm..." className="w-full bg-white border border-[#E5DDCF] rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:border-[#17643E] shadow-sm" />
            <button className="absolute right-2 top-2 w-8 h-8 bg-[#103D2C] text-white rounded-lg flex items-center justify-center hover:bg-[#17643E]">
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
