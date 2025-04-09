import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import './Auth.css';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    age: '',
    gender: '',
    employmentStatus: '',
    region: ''
  });
  const [formErrors, setFormErrors] = useState({});
  const { register, error } = useContext(AuthContext);
  const navigate = useNavigate();

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
    } else if (formData.password.length < 8) {
      errors.password = '비밀번호는 8자 이상이어야 합니다';
    }
    
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = '비밀번호가 일치하지 않습니다';
    }
    
    if (!formData.name) {
      errors.name = '이름을 입력해주세요';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (validate()) {
      console.log('회원가입 데이터:', formData);
      
      const success = await register(formData);
      if (success) {
        navigate('/login');
      }
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card register-card">
        <h2>회원가입</h2>
        
        {error && <div className="auth-error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <h3>기본 정보</h3>
            
            <div className="form-group">
              <label htmlFor="email">이메일</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
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
              />
              {formErrors.password && <span className="error-message">{formErrors.password}</span>}
            </div>
            
            <div className="form-group">
              <label htmlFor="confirmPassword">비밀번호 확인</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
              />
              {formErrors.confirmPassword && <span className="error-message">{formErrors.confirmPassword}</span>}
            </div>
            
            <div className="form-group">
              <label htmlFor="name">이름</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
              />
              {formErrors.name && <span className="error-message">{formErrors.name}</span>}
            </div>
          </div>
          
          <div className="form-section">
            <h3>프로필 정보 (선택사항)</h3>
            
            <div className="form-group">
              <label htmlFor="age">연령대</label>
              <select
                id="age"
                name="age"
                value={formData.age}
                onChange={handleChange}
              >
                <option value="">선택하세요</option>
                <option value="youth">청년 (만 19-34세)</option>
                <option value="middle">중장년 (만 35-64세)</option>
                <option value="senior">노년 (만 65세 이상)</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="gender">성별</label>
              <select
                id="gender"
                name="gender"
                value={formData.gender}
                onChange={handleChange}
              >
                <option value="">선택하세요</option>
                <option value="male">남성</option>
                <option value="female">여성</option>
                <option value="other">기타</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="employmentStatus">고용상태</label>
              <select
                id="employmentStatus"
                name="employmentStatus"
                value={formData.employmentStatus}
                onChange={handleChange}
              >
                <option value="">선택하세요</option>
                <option value="employed">재직자</option>
                <option value="unemployed">구직자</option>
                <option value="business">자영업자</option>
                <option value="student">학생</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="region">지역</label>
              <select
                id="region"
                name="region"
                value={formData.region}
                onChange={handleChange}
              >
                <option value="">선택하세요</option>
                <option value="seoul">서울</option>
                <option value="busan">부산</option>
                <option value="incheon">인천</option>
                {/* 다른 지역 추가 */}
              </select>
            </div>
          </div>
          
          <button type="submit" className="auth-button">회원가입</button>
        </form>
        
        <div className="auth-links">
          <p>
            이미 계정이 있으신가요? <Link to="/login">로그인</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;