import React, { useState, useRef, useEffect } from 'react';
import { askQuestion, askQuestionAboutFile } from '../services/api';
import './ChatArea.css';

const ChatArea = ({ selectedFileId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = selectedFileId
        ? await askQuestionAboutFile(selectedFileId, input)
        : await askQuestion(input, selectedFileId ? { file_id: selectedFileId } : {});

      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources || [],
        timestamps: response.data.timestamps || [],
        confidence: response.data.confidence,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error asking question:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        error: true,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="chat-area">
      <div className="chat-header">
        <h2>Chat</h2>
        {selectedFileId && (
          <span className="file-indicator">File #{selectedFileId} selected</span>
        )}
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-icon">💬</div>
            <h3>Start a conversation</h3>
            <p>Ask questions about your uploaded documents, audio, or video files.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-header">
                <span className="message-role">
                  {message.role === 'user' ? 'You' : 'Assistant'}
                </span>
                <span className="message-time">{formatTime(message.timestamp)}</span>
              </div>
              <div className="message-content">{message.content}</div>
              {message.sources && message.sources.length > 0 && (
                <div className="message-sources">
                  <strong>Sources:</strong>
                  <ul>
                    {message.sources.slice(0, 3).map((source, idx) => (
                      <li key={idx}>
                        File #{source.file_id}, Chunk #{source.chunk_index}
                        {source.score && ` (${(source.score * 100).toFixed(0)}% match)`}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {message.error && (
                <div className="message-error">Error: {message.error}</div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <span className="typing-indicator">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about your files..."
          rows={3}
          disabled={loading}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatArea;

