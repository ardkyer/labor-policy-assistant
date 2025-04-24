// File: src/components/ProtectedRoute.js
import React, { useContext, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  const location = useLocation();

  // 사용자가 로그인하지 않은 상태에서 보호된 페이지에 접근할 때 알림 표시
  useEffect(() => {
    if (!loading && !user) {
      // Toast 대신 alert 사용
      alert('로그인이 필요한 서비스입니다.');
    }
  }, [loading, user]);

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return children;
};

export default ProtectedRoute;