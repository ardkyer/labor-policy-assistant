// src/services/api.js
import axios from 'axios';

// 백엔드 API URL
// const API_URL = 'http://localhost:8000/api/v1';
const API_URL = `${process.env.REACT_APP_API_URL}/api/v1`;

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
          region: userData.region,
          is_disabled: userData.isDisabled,
          is_foreign: userData.isForeign,
          family_status: userData.familyStatus
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
      region: profileData.region,
      is_disabled: profileData.isDisabled,
      is_foreign: profileData.isForeign,
      family_status: profileData.familyStatus
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
    // 기본 검색
    search: (params) => api.get('/policies/search/', { params }),
    
    // 정책 상세 정보
    getById: (id) => api.get(`/policies/${id}`),
    
    // 정책 추천 기능
    recommend: () => api.get('/policies/recommend/'),
    
    // 벡터 기반 추천 기능
    recommendVector: (profileData) => api.post('/policies/recommend-vector/', profileData),
    
    // 프로필 기반 추천 정책 가져오기 (DB에 미리 계산된)
    getRecommended: () => api.get('/policies/recommended/'),
    
    // 추천 정책 새로고침
    refreshRecommendations: () => api.post('/policies/refresh-recommendations/'),
    
    // 정책 저장하기
    savePolicy: (policyId) => api.post(`/policies/save/${policyId}`),
    
    // 정책 저장 취소하기
    unsavePolicy: (policyId) => api.delete(`/policies/save/${policyId}`),
    
    // 저장된 정책 목록 가져오기
    getSavedPolicies: () => api.get('/policies/saved/'),
    
    // LLM으로 정책 설명 강화
    enhancePolicyDescription: (policyId, policyContent) => api.post('/policies/enhance', {
      policy_id: policyId,
      policy_content: policyContent
    }),
  },

  // 채팅 어시스턴트 관련
  chat: {
    sendMessage: (query) => api.post('/chat', { query }),
    getHistory: () => api.get('/chat/history')
  }
};