// App.js
import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import PolicySearch from './pages/PolicySearch';
import ChatAssistant from './pages/ChatAssistant';
import Profile from './pages/Profile';
import Login from './pages/Login';
import Register from './pages/Register';
import { AuthContext, AuthProvider } from './context/AuthContext';
import './App.css';

// 보호된 라우트 컴포넌트 (인증 필요)
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  const location = useLocation();
  
  // 로딩 중이면 로딩 표시
  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }
  
  // 로그인되지 않았으면 로그인 페이지로 리다이렉트
  if (!user) {
    // alert로 경고 표시 (toast 대신)
    alert('로그인이 필요한 서비스입니다.');
    
    // 현재 위치 정보를 포함하여 로그인 페이지로 리다이렉트
    return <Navigate to="/login" state={{ from: location.pathname }} />;
  }
  
  return children;
};

// 공개 라우트 컴포넌트 (이미 로그인한 사용자는 홈으로 리다이렉트)
const PublicRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  
  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }
  
  if (user) {
    return <Navigate to="/" />;
  }
  
  return children;
};

function AppRoutes() {
  const { loading } = useContext(AuthContext);
  
  if (loading) {
    return <div className="loading-container">로딩 중...</div>;
  }
  
  return (
    <Router>
      <div className="App">
        <Navbar />
        <div className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            
            {/* 정책 검색 - 보호된 라우트로 수정 */}
            <Route path="/search" element={
              <ProtectedRoute>
                <PolicySearch />
              </ProtectedRoute>
            } />
            
            {/* 채팅 관련 경로 - 보호된 라우트로 수정 */}
            <Route path="/chat" element={
              <ProtectedRoute>
                <Navigate to="/chat/new" />
              </ProtectedRoute>
            } />
            
            <Route path="/chat/:chatId" element={
              <ProtectedRoute>
                <ChatAssistant />
              </ProtectedRoute>
            } />
            
            {/* 로그인/회원가입 */}
            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />
            
            <Route path="/register" element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            } />
            
            {/* 프로필 */}
            <Route path="/profile" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;