// File: src/pages/Login.js
import React, { useState, useContext } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import './Auth.css';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [formErrors, setFormErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const { login, error } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  
  // 이전 페이지 경로 가져오기 (없으면 홈으로)
  const from = location.state?.from || '/';
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const validate = () => {
    const errors = {};
    if (!formData.email) {
      errors.email = '이메일을 입력해주세요';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = '유효한 이메일 주소를 입력해주세요';
    }
    if (!formData.password) {
      errors.password = '비밀번호를 입력해주세요';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validate()) {
      setIsLoading(true); // 로딩 시작
      
      const success = await login(formData.email, formData.password);
      
      if (success) {
        // 로그인 성공 시 1초 후에 이전 페이지로 리다이렉트 (스피너 효과를 위해)
        setTimeout(() => {
          setIsLoading(false);
          navigate(from);
        }, 1000);
      } else {
        setIsLoading(false); // 실패 시 로딩 중단
      }
    }
  };
  
  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>로그인</h2>
        
        {/* 이전 페이지 정보가 있으면 안내 메시지 표시 */}
        {location.state?.from && location.state.from !== '/' && (
          <div className="auth-message">
            서비스 이용을 위해 로그인이 필요합니다.
          </div>
        )}
        
        {error && <div className="auth-error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">이메일</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="example@email.com"
              disabled={isLoading}
            />
            {formErrors.email && <span className="error-message">{formErrors.email}</span>}
          </div>
          
          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="비밀번호를 입력하세요"
              disabled={isLoading}
            />
            {formErrors.password && <span className="error-message">{formErrors.password}</span>}
          </div>
          
          {isLoading ? (
            <div className="loading-box">
              <div className="spinner"></div>
              <p>로그인 중입니다...</p>
            </div>
          ) : (
            <button type="submit" className="auth-button">로그인</button>
          )}
        </form>
        
        <div className="auth-links">
          <p>
            계정이 없으신가요? <Link to="/register">회원가입</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;