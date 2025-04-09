// src/context/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

// 백엔드 서버 URL
const API_URL = 'http://localhost:8000/api/v1';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true); // 로딩 상태 추가

  // 앱 시작 시 자동으로 사용자 정보 불러오기
  useEffect(() => {
    const loadUserFromToken = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          await fetchUserInfo(token);
        } catch (err) {
          console.error('토큰에서 사용자 정보 로드 실패:', err);
          localStorage.removeItem('token'); // 유효하지 않은 토큰 제거
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };

    loadUserFromToken();
  }, []);

  // 로그인 함수
  const login = async (email, password) => {
    try {
      setError(null);
      
      // FormData로 변환 (OAuth2PasswordRequestForm 호환)
      const formData = new FormData();
      formData.append('username', email); // 백엔드는 username으로 email을 받음
      formData.append('password', password);
      
      // 로그인 요청
      console.log('로그인 요청 URL:', `${API_URL}/auth/login`);
      const response = await axios.post(`${API_URL}/auth/login`, formData);
      console.log('로그인 응답:', response.data);
      
      // 토큰 저장 및 사용자 정보 설정
      const token = response.data.access_token;
      localStorage.setItem('token', token);
      
      // 사용자 정보 가져오기
      await fetchUserInfo(token);
      return true;
    } catch (err) {
      console.error('로그인 오류:', err.response?.data || err.message);
      setError(err.response?.data?.detail || '로그인 중 오류가 발생했습니다');
      return false;
    }
  };

  // 회원가입 함수
  const register = async (userData) => {
    try {
      setError(null);
      
      // 백엔드 API에 맞게 데이터 변환
      const registerData = {
        email: userData.email,
        password: userData.password,
        full_name: userData.name, // name을 full_name으로 변환
        profile: {  // profile 정보 추가
          age: userData.age,
          gender: userData.gender,
          employment_status: userData.employmentStatus,
          region: userData.region
        }
      };
      
      // 회원가입 요청 - 디버깅 추가
      console.log('회원가입 요청 URL:', `${API_URL}/auth/register`);
      console.log('회원가입 데이터:', registerData);
      
      // 요청 전송
      const response = await axios.post(`${API_URL}/auth/register`, registerData);
      console.log('회원가입 응답:', response.data);
      return true;
    } catch (err) {
      console.error('회원가입 오류:', err.response?.data || err.message);
      setError(err.response?.data?.detail || '회원가입 중 오류가 발생했습니다');
      return false;
    }
  };

  // 사용자 정보 가져오기
  const fetchUserInfo = async (token) => {
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (err) {
      console.error('사용자 정보 조회 실패:', err.response?.data || err.message);
      throw err; // 에러를 다시 던져서 호출자가 처리할 수 있게 함
    }
  };

  // 로그아웃 함수
  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, error, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};