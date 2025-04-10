// src/services/api.js
import axios from 'axios';

// 백엔드 API URL
const API_URL = 'http://localhost:8000/api/v1';

// axios 인스턴스 생성
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 인증 토큰 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 오류 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API 오류:', error.response?.status, error.response?.data);

    // 401 오류 처리 (인증 만료)
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 기본 API 사용
export default api;

// API 요청 함수들
export const apiService = {
  // 인증 관련
  auth: {
    login: (email, password) => {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      return axios.post(`${API_URL}/auth/login`, formData);
    },
    register: (userData) => {
      return api.post('/auth/register', {
        email: userData.email,
        password: userData.password,
        full_name: userData.name,
        profile: {
          age: userData.age,
          gender: userData.gender,
          employment_status: userData.employmentStatus,
          region: userData.region
        }
      });
    },
    me: () => api.get('/auth/me'),
  },

  // 프로필 관련
  profiles: {
    // 내 프로필 정보 가져오기
    getMyProfile: () => api.get('/profiles/me'),

    // 프로필 정보 업데이트
    updateProfile: (profileData) => api.put('/profiles/me', {
      name: profileData.name,
      age: profileData.age,
      gender: profileData.gender,
      employment_status: profileData.employmentStatus,
      region: profileData.region
    }),

    // 저장한 정책 가져오기
    getSavedPolicies: () => api.get('/profiles/me/saved-policies'),

    // 정책 저장/삭제
    savePolicy: (policyId) => api.post(`/profiles/me/saved-policies/${policyId}`),
    removePolicy: (policyId) => api.delete(`/profiles/me/saved-policies/${policyId}`),

    // 알림 가져오기/설정
    getNotifications: () => api.get('/profiles/me/notifications'),
    updateNotificationSettings: (settings) => api.put('/profiles/me/notifications/settings', settings)
  },

  // 정책 검색 관련 
  policies: {
    search: (params) => api.get('/policies/search/', { params }),
    getById: (id) => api.get(`/policies/${id}`),
    // 정책 추천 기능 추가
    recommend: () => api.get('/policies/recommend/'),
    // 벡터 기반 추천 기능 추가
    recommendVector: (profileData) => api.post('/policies/recommend-vector/', profileData),
  },

  // 채팅 어시스턴트 관련
  chat: {
    sendMessage: (query) => api.post('/chat', { query }),
    getHistory: () => api.get('/chat/history')
  }
};