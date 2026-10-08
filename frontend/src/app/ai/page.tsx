"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Bot, User, Sparkles } from "lucide-react";

export default function AICommandCenter() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<any[]>([
    {
      role: 'ai',
      content: {
        answer: "Hello. I'm DeciFlow. I'm continuously monitoring your campaigns, inventory, and product margins. What would you like to know about your business performance?"
      }
    }
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!query.trim()) return;
    
    const userMsg = query;
    setQuery("");
    
    // Format history for API
    const history = messages
      .filter(m => !m.error && (m.role === 'user' ? m.text : (m.content && m.content.answer)))
      .map(m => ({
        role: m.role,
        content: m.role === 'user' ? m.text : m.content.answer
      }));

    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const response = await api.askAI(userMsg, history);
      setMessages(prev => [...prev, { role: 'ai', content: response }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', error: "Failed to connect to DeciFlow Intelligence." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto">
      <div className="mb-6 text-center">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center justify-center gap-3">
          <Bot className="h-8 w-8 text-indigo-600" /> Ask DeciFlow
        </h1>
        <p className="text-gray-500 mt-2">Ask anything about your business performance, campaigns, or products.</p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden bg-white shadow-lg border-indigo-100">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-indigo-100 ml-3' : 'bg-gradient-to-br from-indigo-600 to-purple-600 mr-3'}`}>
                  {msg.role === 'user' ? <User className="h-5 w-5 text-indigo-600" /> : <Bot className="h-5 w-5 text-white" />}
                </div>
                
                <div className={`p-4 rounded-2xl ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-sm' : 'bg-gray-50 border rounded-tl-sm text-gray-800'}`}>
                  {msg.role === 'user' ? (
                    <p>{msg.text}</p>
                  ) : msg.error ? (
                    <p className="text-red-500">{msg.error}</p>
                  ) : (
                    <div className="space-y-4">
                      {msg.content.answer && <p className="text-lg">{msg.content.answer}</p>}
                      
                      {msg.content.evidence && msg.content.evidence.length > 0 && (
                        <div className="bg-white p-3 rounded-lg border border-gray-100">
                          <p className="text-xs font-bold text-gray-500 uppercase mb-2 flex items-center"><Sparkles className="h-3 w-3 mr-1 text-amber-500"/> Evidence</p>
                          <ul className="space-y-1">
                            {msg.content.evidence.map((ev: string, idx: number) => (
                              <li key={idx} className="text-sm font-medium text-gray-700">• {ev}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {msg.content.impact && (
                        <div className="bg-green-50 p-3 rounded-lg border border-green-100">
                          <p className="text-xs font-bold text-green-700 uppercase mb-1">Estimated Impact</p>
                          <p className="text-sm font-bold text-green-800">{msg.content.impact}</p>
                        </div>
                      )}

                      {msg.content.recommendation && (
                        <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-100">
                          <p className="text-xs font-bold text-indigo-700 uppercase mb-1">Recommendation</p>
                          <p className="text-sm font-bold text-indigo-900">{msg.content.recommendation}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="flex flex-row max-w-[80%]">
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 mr-3 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-white" />
                </div>
                <div className="p-4 rounded-2xl bg-gray-50 border rounded-tl-sm flex space-x-2 items-center">
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t bg-gray-50">
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex gap-2"
          >
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="E.g. Why did my profit drop this week?"
              className="flex-1 bg-white border-gray-300 focus-visible:ring-indigo-500 text-base py-6 rounded-full px-6"
              disabled={loading}
            />
            <Button 
              type="submit" 
              disabled={loading || !query.trim()} 
              className="rounded-full h-14 w-14 p-0 bg-indigo-600 hover:bg-indigo-700 flex-shrink-0"
            >
              <Send className="h-6 w-6" />
            </Button>
          </form>
          <div className="mt-3 flex gap-2 overflow-x-auto pb-1 text-xs justify-center hide-scrollbar">
            {["Which campaigns are actually profitable?", "Which campaigns have strong ROAS but poor profitability?", "What should I review first?", "Which products have the highest gross profit?"].map((suggestion, idx) => (
              <button 
                key={idx}
                type="button"
                onClick={() => setQuery(suggestion)}
                className="whitespace-nowrap px-3 py-1.5 bg-white border rounded-full text-gray-600 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
}
