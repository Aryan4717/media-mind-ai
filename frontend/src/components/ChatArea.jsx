import React, { useState, useRef, useEffect } from 'react';
import { askQuestion, askQuestionAboutFile, askQuestionStreaming, askQuestionAboutFileStreaming } from '../services/api';
import './ChatArea.css';

const ChatArea = ({ selectedFileId, onPlayTimestamp }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef(null);
  const streamingMessageRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  const handleSend = async (useStreaming = true) => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const question = input;
    setInput('');
    setLoading(true);
    setStreaming(useStreaming);

    // Create placeholder for assistant message
    const assistantMessageId = Date.now() + 1;
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      sources: [],
      timestamps: [],
      confidence: null,
      timestamp: new Date(),
      streaming: useStreaming,
    };

    setMessages((prev) => [...prev, assistantMessage]);
    streamingMessageRef.current = assistantMessageId;

    try {
      if (useStreaming) {
        // Use streaming endpoint
        const onChunk = (data) => {
          if (data.answer_chunk) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + data.answer_chunk }
                  : msg
              )
            );
          }

          if (data.final_response) {
            const final = data.final_response;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      content: final.answer,
                      sources: final.sources || [],
                      timestamps: final.timestamps || [],
                      confidence: final.confidence,
                      streaming: false,
                    }
                  : msg
              )
            );
            setStreaming(false);
            setLoading(false);
          }
        };

        if (selectedFileId) {
          await askQuestionAboutFileStreaming(selectedFileId, question, {}, onChunk);
        } else {
          await askQuestionStreaming(question, {}, onChunk);
        }
      } else {
        // Use regular endpoint
        const response = selectedFileId
          ? await askQuestionAboutFile(selectedFileId, question)
          : await askQuestion(question, selectedFileId ? { file_id: selectedFileId } : {});

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: response.data.answer,
                  sources: response.data.sources || [],
                  timestamps: response.data.timestamps || [],
                  confidence: response.data.confidence,
                  streaming: false,
                }
              : msg
          )
        );
        setLoading(false);
      }
    } catch (error) {
      console.error('Error asking question:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: 'Sorry, I encountered an error. Please try again.',
                error: true,
                streaming: false,
              }
            : msg
        )
      );
      setLoading(false);
      setStreaming(false);
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
          messages.map((message) => (
            <div key={message.id} className={`message-bubble ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content-wrapper">
                <div className="message-header">
                  <span className="message-role">
                    {message.role === 'user' ? 'You' : 'Assistant'}
                  </span>
                  <span className="message-time">{formatTime(message.timestamp)}</span>
                </div>
                <div className="message-content">
                  {message.content || (message.streaming && <span className="typing-indicator">Thinking...</span>)}
                  {message.streaming && message.content && (
                    <span className="streaming-cursor">▋</span>
                  )}
                </div>
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-header">
                      <strong>📚 Sources</strong>
                      {message.confidence && (
                        <span className="confidence-badge">
                          {Math.round(message.confidence * 100)}% confidence
                        </span>
                      )}
                    </div>
                    <div className="sources-list">
                      {message.sources.slice(0, 3).map((source, idx) => (
                        <div key={idx} className="source-item">
                          <div className="source-header">
                            <span className="source-label">File #{source.file_id}</span>
                            {source.score && (
                              <span className="source-score">
                                {(source.score * 100).toFixed(0)}% match
                              </span>
                            )}
                          </div>
                          {source.text_preview && (
                            <div className="source-preview">{source.text_preview}</div>
                          )}
                          {source.timestamps && source.timestamps.length > 0 && (
                            <div className="source-timestamps">
                              {source.timestamps.map((ts, tsIdx) => (
                                <span key={tsIdx} className="timestamp-tag">
                                  {ts.formatted_start} - {ts.formatted_end}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {message.timestamps && message.timestamps.length > 0 && (
                  <div className="message-timestamps">
                    <strong>⏱️ Timestamps:</strong>
                    <div className="timestamps-list">
                      {message.timestamps.map((ts, idx) => (
                        <button
                          key={idx}
                          className="timestamp-badge play-segment-button"
                          onClick={() => {
                            if (onPlayTimestamp) {
                              onPlayTimestamp(ts.start);
                            }
                          }}
                          title="Play relevant segment"
                        >
                          ▶️ {ts.formatted_start} - {ts.formatted_end}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {message.sources && message.sources.some(s => s.timestamps && s.timestamps.length > 0) && (
                  <div className="message-source-timestamps">
                    {message.sources
                      .filter(s => s.timestamps && s.timestamps.length > 0)
                      .map((source, sourceIdx) => (
                        <div key={sourceIdx} className="source-timestamps-group">
                          <strong>Source {sourceIdx + 1} segments:</strong>
                          <div className="timestamps-list">
                            {source.timestamps.map((ts, tsIdx) => (
                              <button
                                key={tsIdx}
                                className="timestamp-badge play-segment-button"
                                onClick={() => {
                                  if (onPlayTimestamp) {
                                    onPlayTimestamp(ts.start);
                                  }
                                }}
                                title="Play relevant segment"
                              >
                                ▶️ {ts.formatted_start} - {ts.formatted_end}
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}
                  </div>
                )}
                {message.error && (
                  <div className="message-error">
                    ⚠️ {message.error || 'An error occurred'}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && !streaming && (
          <div className="message-bubble assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content-wrapper">
              <div className="message-content">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="input-wrapper">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your files..."
            rows={1}
            disabled={loading}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
          <button
            className="send-button"
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            title="Send message (Enter)"
          >
            {loading ? (
              <span className="send-button-loading">⏳</span>
            ) : (
              <span>➤</span>
            )}
          </button>
        </div>
        <div className="input-footer">
          <span className="input-hint">Press Enter to send, Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;
