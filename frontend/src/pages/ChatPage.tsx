import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, Download, Trash2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { postChat } from '../api';
import { useData } from '../DataContext';
import './ChatPage.css';

const ChatPage: React.FC = () => {
  const { dataset, chatHistory, setChatHistory } = useData();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, loading]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input.trim();
    setInput('');
    setChatHistory((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const historyForApi = chatHistory;
      const filename = dataset ? dataset.filename : '';
      let fallbackCtx = '';
      if (dataset) {
        fallbackCtx = `Dataset: ${dataset.filename}\nRows: ${dataset.rows}\nCols: ${dataset.columns}\nCols names: ${dataset.column_names.join(', ')}`;
      }

      const res = await postChat(userMsg, historyForApi, filename, fallbackCtx);
      setChatHistory((prev) => [...prev, { role: 'assistant', content: res.response }]);
    } catch (error) {
      setChatHistory((prev) => [...prev, { role: 'assistant', content: '⚠️ Error connecting to AI. Make sure the backend is running.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => setChatHistory([]);
  const exportChat = () => {
    let md = '# InsightFlow AI — Chat Export\n\n';
    chatHistory.forEach(m => {
      const prefix = m.role === 'user' ? '🧑 **You**' : '🤖 **Nemotron**';
      md += `${prefix}\n\n${m.content}\n\n---\n`;
    });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([md], { type: 'text/markdown' }));
    a.download = 'insightflow_chat.md';
    a.click();
  };

  if (!dataset) {
    return (
      <div className="page-container center-empty">
        <AlertCircle size={48} className="empty-icon warning" />
        <h2>No Dataset Uploaded</h2>
        <p>Please upload a dataset before chatting with the AI.</p>
      </div>
    );
  }

  return (
    <motion.div 
      className="page-container chat-page"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="chat-container glass-panel">
        <div className="chat-header">
          <div className="chat-title">
            <Bot size={28} className="bot-icon" />
            <div>
              <h3>Agentic AI Assistant</h3>
              <p>Powered by Semantic RAG Engine</p>
            </div>
          </div>
          <div className="chat-actions">
            <button className="secondary" onClick={exportChat}><Download size={16} /> Export</button>
            <button className="secondary" onClick={clearChat}><Trash2 size={16} /> Clear</button>
          </div>
        </div>

        <div className="chat-messages-area">
          {chatHistory.length === 0 ? (
            <div className="empty-chat">
              <Bot size={64} className="empty-bot-icon" />
              <h3>How can I help you analyze {dataset.filename}?</h3>
              <p>Ask about distributions, correlations, or clean-up suggestions.</p>
            </div>
          ) : (
            chatHistory.map((msg, idx) => (
              <div key={idx} className={`chat-bubble-wrapper ${msg.role}`}>
                <div className="chat-bubble">
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="chat-bubble-wrapper assistant">
              <div className="chat-bubble loading">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={endOfMessagesRef} />
        </div>

        <div className="chat-input-wrapper">
          <textarea 
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Ask Nemotron about ${dataset.filename}...`}
            rows={1}
          />
          <button className="primary send-btn" onClick={handleSend} disabled={!input.trim() || loading}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default ChatPage;
