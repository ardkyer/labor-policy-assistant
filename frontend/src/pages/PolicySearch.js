import React, { useState, useEffect, useContext } from 'react';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';
import PolicyCard from '../components/PolicyCard';
import './PolicySearch.css';

const PolicySearch = () => {
  const { user } = useContext(AuthContext);
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [filters, setFilters] = useState({
    age: '',
    gender: '',
    employment: '',
    region: ''
  });

  // 프로필 정보 가져오기
  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        if (user) {
          const response = await api.get('/auth/me');
          const userData = response.data;
          const profile = userData.profile || {};

          // 프로필 정보로 필터 초기화
          setFilters({
            age: profile.age || '',
            gender: profile.gender || '',
            employment: profile.employment_status || '',
            region: profile.region || ''
          });

          setProfileLoaded(true);
        }
      } catch (err) {
        console.error('프로필 정보 로딩 실패:', err);
        setProfileLoaded(true); // 오류 발생해도 로딩 완료로 처리
      }
    };

    fetchUserProfile();
  }, [user]);

  // 정책 불러오기
  useEffect(() => {
    const fetchPolicies = async () => {
      if (!profileLoaded) return;

      try {
        setLoading(true);

        // ProfileModel에 맞는 형식으로 데이터 변환
        // 주의: age는 문자열이 아닌 숫자로 변환해야 함
        const profileData = {
          age: filters.age ? (filters.age === 'youth' ? 25 : filters.age === 'middle' ? 45 : filters.age === 'senior' ? 65 : null) : null,
          gender: filters.gender,
          employment_status: filters.employment,
          region: filters.region
        };

        console.log('정책 추천 요청 데이터:', profileData); // 디버깅용

        // POST 요청으로 변경
        const response = await api.post('/policies/recommend-vector/', profileData);

        console.log('정책 추천 응답:', response.data); // 디버깅용

        // 응답 데이터 구조에 맞게 처리
        if (response.data && response.data.recommendations) {
          const formattedPolicies = response.data.recommendations.map(recommendation => ({
            id: recommendation.policy_id || Date.now(), // 고유 ID 필요
            title: recommendation.title || '맞춤 정책 추천',
            description: recommendation.text || '',
            category: '',
            source_page: recommendation.page || '',
            score: recommendation.score
          }));
          setPolicies(formattedPolicies);
        } else {
          setPolicies([]);
        }
      } catch (err) {
        setError('맞춤 정책을 불러오는데 실패했습니다.');
        console.error('정책 추천 API 오류:', err);
        console.error('상세 오류:', err.response?.data);
      } finally {
        setLoading(false);
      }
    };

    fetchPolicies();
  }, [filters, profileLoaded]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="policy-search-container">
      <h1>맞춤 정책 추천</h1>

      <div className="recommendation-info">
        <p>회원님의 프로필 정보를 바탕으로 맞춤 정책을 추천해 드립니다.</p>
      </div>

      <div className="filters-section">
        <h3>추천 필터</h3>
        <div className="filter-controls">
          <div className="filter-group">
            <label>연령대</label>
            <select name="age" value={filters.age} onChange={handleFilterChange}>
              <option value="">전체</option>
              <option value="youth">청년 (만 19-34세)</option>
              <option value="middle">중장년 (만 35-64세)</option>
              <option value="senior">노년 (만 65세 이상)</option>
            </select>
          </div>
          <div className="filter-group">
            <label>성별</label>
            <select name="gender" value={filters.gender} onChange={handleFilterChange}>
              <option value="">전체</option>
              <option value="male">남성</option>
              <option value="female">여성</option>
            </select>
          </div>
          <div className="filter-group">
            <label>고용상태</label>
            <select name="employment" value={filters.employment} onChange={handleFilterChange}>
              <option value="">전체</option>
              <option value="employed">재직자</option>
              <option value="unemployed">구직자</option>
              <option value="business">자영업자</option>
              <option value="student">학생</option>
            </select>
          </div>
          <div className="filter-group">
            <label>지역</label>
            <select name="region" value={filters.region} onChange={handleFilterChange}>
              <option value="">전국</option>
              <option value="seoul">서울</option>
              <option value="busan">부산</option>
              <option value="incheon">인천</option>
              {/* 다른 지역 추가 */}
            </select>
          </div>
        </div>
      </div>

      <div className="policies-list">
        {loading ? (
          <div className="loading">맞춤 정책을 불러오는 중...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : policies.length > 0 ? (
          policies.map((policy, index) => (
            <PolicyCard
              key={policy.id ? `policy-${policy.id}` : `policy-${index}`}
              policy={policy}
            />
          ))
        ) : (
          <div className="no-results">
            <p>현재 조건에 맞는 추천 정책이 없습니다.</p>
            <p>필터 조건을 변경하여 다른 정책을 확인해보세요.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PolicySearch;