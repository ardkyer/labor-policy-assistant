// App.js 수정
import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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
  
  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" />;
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
            <Route path="/search" element={<PolicySearch />} />
            
            {/* 채팅 관련 경로 수정 */}
            <Route path="/chat" element={<Navigate to="/chat/new" />} />
            <Route path="/chat/:chatId" element={<ChatAssistant />} />
            
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