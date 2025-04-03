// File: src/pages/Home.js
import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  return (
    <div className="home-container">
      <div className="hero-section">
        <h1>고용노동 정책 어시스턴트</h1>
        <p>나에게 맞는 고용노동 정책을 쉽고 빠르게 찾아보세요!</p>
        <div className="hero-buttons">
          <Link to="/search" className="btn primary-btn">정책 찾기</Link>
          <Link to="/chat" className="btn secondary-btn">AI 상담사와 대화하기</Link>
        </div>
      </div>

      <div className="features-section">
        <div className="feature-card">
          <div className="feature-icon">🔍</div>
          <h3>맞춤형 정책 매칭</h3>
          <p>나이, 성별, 직업 상태 등 개인 정보를 바탕으로 맞춤형 정책을 추천해드립니다.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">💬</div>
          <h3>AI 챗봇 상담</h3>
          <p>고용노동 정책 전문 AI와 대화하며 궁금한 점을 바로 해결하세요.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🔔</div>
          <h3>정책 알림 서비스</h3>
          <p>관심 있는 정책의 마감일, 변경사항을 실시간으로 알려드립니다.</p>
        </div>
      </div>
    </div>
  );
};

export default Home;