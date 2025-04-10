import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import './Navbar.css';

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  // 챗봇 상담 클릭 핸들러 - 임시 채팅으로 이동
  const handleChatClick = (e) => {
    e.preventDefault(); // 기본 동작 방지
    // 임시 채팅 페이지로 이동 (DB에 저장하지 않음)
    navigate('/chat/temp');
  };
  
  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <Link to="/">고용노동 정책 어시스턴트</Link>
      </div>
      <ul className="navbar-links">
        <li>
          <Link to="/">홈</Link>
        </li>
        <li>
          <Link to="/search">정책 추천</Link>
        </li>
        <li>
          {/* 임시 채팅 페이지로 이동 */}
          <a href="#" onClick={handleChatClick} className="nav-link">챗봇 상담</a>
        </li>
        {user ? (
          <>
            <li>
              <Link to="/profile">내 프로필</Link>
            </li>
            <li>
              <button onClick={handleLogout} className="logout-btn">로그아웃</button>
            </li>
          </>
        ) : (
          <>
            <li>
              <Link to="/login">로그인</Link>
            </li>
            <li>
              <Link to="/register">회원가입</Link>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
};

export default Navbar;