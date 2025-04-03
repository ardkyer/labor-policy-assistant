// File: src/pages/ChatAssistant.js
import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import './ChatAssistant.css';

const ChatAssistant = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Initial greeting from the assistant
  useEffect(() => {
    setMessages([
      {
        sender: 'assistant',
        text: '안녕하세요! 고용노동 정책 어시스턴트입니다. 어떤 정책에 관심이 있으신가요?',
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage = {
      sender: 'user',
      text: input,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Send message to API
      const response = await api.post('/api/v1/chat/', {
        message: input
      });

      // Add assistant response to chat
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: response.data.response,
        timestamp: new Date().toISOString(),
        policies: response.data.policies || []
      }]);
    } catch (err) {
      console.error('Error sending message:', err);
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        timestamp: new Date().toISOString(),
        error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>고용노동 정책 어시스턴트</h1>
        <p>고용노동 정책에 대해 무엇이든 물어보세요!</p>
      </div>

      <div className="chat-messages">
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`message ${message.sender === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div className="message-content">
              <p>{message.text}</p>
              
              {message.policies && message.policies.length > 0 && (
                <div className="suggested-policies">
                  <h4>추천 정책:</h4>
                  <ul>
                    {message.policies.map((policy, idx) => (
                      <li key={idx}>
                        <a href={`/policy/${policy.id}`}>{policy.title}</a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <span className="message-time">
              {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            </span>
          </div>
        ))}
        
        {loading && (
          <div className="message assistant-message">
            <div className="message-content typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder="메시지를 입력하세요..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          전송
        </button>
      </form>
    </div>
  );
};

export default ChatAssistant;