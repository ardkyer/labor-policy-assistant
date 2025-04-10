// src/pages/ChatAssistant.js
import React, { useState, useEffect, useRef, useContext } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';
import './ChatAssistant.css';

const ChatAssistant = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);

  // 상태 관리
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isTemporaryChat, setIsTemporaryChat] = useState(false);

  const messagesEndRef = useRef(null);

  // 채팅 목록 불러오기
  const fetchChats = async () => {
    try {
      const response = await api.get('/chat/list');
      console.log('불러온 채팅 목록:', response.data);
      setChats(response.data);
    } catch (error) {
      console.error('채팅 목록 불러오기 실패:', error);
    }
  };

  // 특정 채팅의 메시지 불러오기
  const fetchMessages = async (id) => {
    if (id === 'temp') {
      // 임시 채팅인 경우 기본 인사말만 표시
      setMessages([
        {
          sender: 'assistant',
          text: '안녕하세요! 고용노동 정책 어시스턴트입니다. 어떤 정책에 관심이 있으신가요?',
          timestamp: new Date().toISOString()
        }
      ]);
      return;
    }

    try {
      setLoading(true);
      const response = await api.get(`/chat/${id}/messages`);

      if (response.data.length === 0) {
        // 메시지가 없으면 초기 인사말 설정
        setMessages([
          {
            sender: 'assistant',
            text: '안녕하세요! 고용노동 정책 어시스턴트입니다. 어떤 정책에 관심이 있으신가요?',
            timestamp: new Date().toISOString()
          }
        ]);
      } else {
        // 서버에서 받은 메시지 형식 변환
        const formattedMessages = response.data.map(msg => ({
          id: msg.id,
          sender: msg.is_user ? 'user' : 'assistant',
          text: msg.content,
          timestamp: msg.created_at,
          sources: msg.sources
        }));

        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('메시지 불러오기 실패:', error);
      setMessages([
        {
          sender: 'assistant',
          text: '메시지를 불러오는 데 문제가 발생했습니다.',
          timestamp: new Date().toISOString(),
          error: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // 채팅 삭제
  const deleteChat = async (e, id) => {
    e.stopPropagation(); // 이벤트 버블링 방지

    try {
      await api.delete(`/chat/${id}`);

      // 목록에서 삭제된 채팅 제거
      setChats(prev => prev.filter(chat => chat.id !== id));

      // 현재 보고 있는 채팅이 삭제된 경우
      if (id === activeChatId) {
        // 임시 채팅으로 이동
        navigate('/chat/temp', { replace: true });
      }
    } catch (error) {
      console.error('채팅 삭제 실패:', error);
      alert('채팅을 삭제하는 데 문제가 발생했습니다.');
    }
  };

  // 새 채팅 생성 함수
  const createNewChat = async (initialMessage) => {
    try {
      setLoading(true);
      // 백엔드 API 호출하여 새 채팅 생성
      const response = await api.post('/chat/create');
      const newChatId = response.data.id;

      // 새 채팅을 목록에 추가
      setChats(prev => [response.data, ...prev]);

      // 활성 채팅 ID 설정
      setActiveChatId(newChatId);

      // URL 변경
      navigate(`/chat/${newChatId}`, { replace: true });

      // 임시 채팅 모드 해제
      setIsTemporaryChat(false);

      // 초기 메시지가 있는 경우, 그 메시지로 채팅 시작
      if (initialMessage) {
        return newChatId;
      } else {
        // 초기 메시지가 없으면 기본 인사말만 설정
        setMessages([
          {
            sender: 'assistant',
            text: '안녕하세요! 고용노동 정책 어시스턴트입니다. 어떤 정책에 관심이 있으신가요?',
            timestamp: new Date().toISOString()
          }
        ]);
      }
      
      return newChatId;
    } catch (error) {
      console.error('새 채팅 생성 실패:', error);
      alert('새 채팅을 생성하는 데 문제가 발생했습니다.');
      return null;
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트시 채팅 목록 로드
  useEffect(() => {
    if (user) {
      fetchChats();
    }
  }, [user]);

  // chatId 변경 감지 및 메시지 로드
  useEffect(() => {
    if (chatId === 'temp') {
      // 임시 채팅 모드 설정
      setIsTemporaryChat(true);
      setActiveChatId(null);
      
      // 임시 채팅의 초기 인사말 설정
      setMessages([
        {
          sender: 'assistant',
          text: '안녕하세요! 고용노동 정책 어시스턴트입니다. 어떤 정책에 관심이 있으신가요?',
          timestamp: new Date().toISOString()
        }
      ]);
    } else if (chatId && chatId !== 'new') {
      // 일반 채팅인 경우
      setIsTemporaryChat(false);
      setActiveChatId(parseInt(chatId));
      fetchMessages(parseInt(chatId))
        .catch(error => {
          console.error('채팅 메시지 로드 실패:', error);
          // 메시지 로드 실패 시 임시 채팅으로 리다이렉트
          if (error.response && error.response.status === 404) {
            console.log('존재하지 않는 채팅입니다. 임시 채팅으로 이동합니다.');
            navigate('/chat/temp', { replace: true });
          }
        });
    } else if (chatId === 'new') {
      // 새 채팅 생성 요청인 경우
      setIsTemporaryChat(false);
      createNewChat();
    } else if (!chatId && chats.length > 0) {
      // 채팅 ID가 없고 채팅 목록이 있으면 임시 채팅으로 이동
      navigate('/chat/temp', { replace: true });
    }
  }, [chatId, chats.length]);

  // 메시지 스크롤 처리
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // 사용자 메시지 추가
    const userMessage = {
      sender: 'user',
      text: input,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    const userInput = input;
    setInput('');
    setLoading(true);

    try {
      let chatIdToUse = activeChatId;
      
      // 임시 채팅이면 새 채팅 생성
      if (isTemporaryChat) {
        chatIdToUse = await createNewChat(userInput);
        if (!chatIdToUse) {
          throw new Error('채팅 생성 실패');
        }
      }

      // 백엔드 API 호출
      const response = await api.post(`/chat/${chatIdToUse}/message`, {
        query: userInput
      });

      // 응답 추가
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: response.data.answer,
        timestamp: new Date().toISOString(),
        sources: response.data.sources
      }]);

      // 채팅 목록 업데이트 (제목이 변경됐을 수 있음)
      fetchChats();
    } catch (error) {
      console.error('메시지 전송 오류:', error);
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

  // 채팅 선택
  const selectChat = (id) => {
    navigate(`/chat/${id}`);
  };

  // 사이드바 토글
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="chat-page">
      {/* 채팅 사이드바 */}
      <div className={`chat-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>대화 목록</h2>
          <button className="new-chat-btn" onClick={() => navigate('/chat/temp')}>새 대화</button>
        </div>
        <div className="chat-list">
          {chats.length > 0 ? (
            chats.map(chat => (
              <div
                key={chat.id}
                className={`chat-item ${chat.id === activeChatId ? 'active' : ''}`}
                onClick={() => selectChat(chat.id)}
              >
                <div className="chat-title">
                  {chat.title || '새 대화'}
                </div>
                <div className="chat-time">
                  {new Date(chat.created_at).toLocaleDateString()}
                </div>
                <button
                  className="delete-chat-btn"
                  onClick={(e) => deleteChat(e, chat.id)}
                >×</button>
              </div>
            ))
          ) : (
            <div className="no-chats">
              대화 내역이 없습니다.<br />
              새 대화를 시작해보세요.
            </div>
          )}
        </div>
      </div>

      {/* 사이드바 토글 버튼 - 사이드바 밖으로 이동 */}
      <button
        className={`sidebar-toggle ${sidebarOpen ? 'open' : 'closed'}`}
        onClick={toggleSidebar}
        aria-label={sidebarOpen ? "닫기" : "열기"}
      >
        {sidebarOpen ? '◀' : '▶'}
      </button>

      {/* 채팅 메인 영역 */}
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
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <h4>참고 자료:</h4>
                    <ul>
                      {message.sources.map((source, idx) => (
                        <li key={idx}>
                          <div className="source-page">페이지: {source.page}</div>
                          <div className="source-text">{source.text}</div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <span className="message-time">
                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
    </div>
  );
};

export default ChatAssistant;