// File: src/components/ProtectedRoute.js
import React, { useContext, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';
import { AuthContext } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  const location = useLocation();

  // 사용자가 로그인하지 않은 상태에서 보호된 페이지에 접근할 때 알림 표시
  useEffect(() => {
    if (!loading && !user) {
      toast.info('로그인이 필요한 서비스입니다.', {
        position: "top-center",
        autoClose: 3000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true
      });
    }
  }, [loading, user]);

  // 로딩 중일 때 표시할 컴포넌트
  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  // 로그인하지 않은 경우 현재 페이지 정보와 함께 로그인 페이지로 리다이렉트
  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // 로그인한 경우 자식 컴포넌트 표시
  return children;
};

export default ProtectedRoute;