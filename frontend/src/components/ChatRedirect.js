// src/components/ChatRedirect.js
import { useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';

const ChatRedirect = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);

  useEffect(() => {
    const redirectToChat = async () => {
      try {
        // 기존 채팅 목록 가져오기
        const response = await api.get('/chat/list');
        
        if (response.data.length > 0) {
          // 기존 채팅이 있으면 가장 최근 채팅으로 이동
          navigate(`/chat/${response.data[0].id}`);
        } else {
          // 채팅이 없으면 /chat/new로 리다이렉트 (새 채팅 생성)
          navigate('/chat/new');
        }
      } catch (error) {
        console.error('채팅 목록 불러오기 실패:', error);
        // 오류 발생 시 새 채팅 생성 페이지로 이동
        navigate('/chat/new');
      }
    };

    if (user) {
      redirectToChat();
    } else {
      // 로그인하지 않은 경우 로그인 페이지로 이동 (선택 사항)
      navigate('/login');
    }
  }, [user, navigate]);

  // 리다이렉트 중 로딩 상태 표시
  return <div className="loading">채팅 페이지로 이동 중...</div>;
};

export default ChatRedirect;