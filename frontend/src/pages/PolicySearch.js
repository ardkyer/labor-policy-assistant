import React, { useState, useEffect, useContext, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';
import PolicyCard from '../components/PolicyCard';
import './PolicySearch.css';

const PolicySearch = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
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
  
  // API 요청이 중복으로 발생하는 것을 방지하기 위한 ref
  const fetchInProgress = useRef(false);
  const isMounted = useRef(false);

  // 프로필 정보 가져오기
  useEffect(() => {
    if (isMounted.current) return;
    isMounted.current = true;

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
        setProfileLoaded(true);
      }
    };

    fetchUserProfile();

    return () => {
      isMounted.current = false;
    };
  }, [user]);

  // 정책 불러오기
  useEffect(() => {
    if (!profileLoaded || fetchInProgress.current) return;

    const fetchPolicies = async () => {
      fetchInProgress.current = true;
      try {
        setLoading(true);

        const profileData = {
          age: filters.age ? (filters.age === 'youth' ? 25 : filters.age === 'middle' ? 45 : filters.age === 'senior' ? 65 : null) : null,
          gender: filters.gender,
          employment_status: filters.employment,
          region: filters.region
        };

        const response = await api.post('/policies/recommend-vector/', profileData);

        if (response.data && response.data.recommendations) {
          // 목차 페이지(1-20페이지) 제외 및 중복 제거
          const uniquePolicies = [];
          const policyIds = new Set();
          
          response.data.recommendations.forEach(recommendation => {
            const policyId = recommendation.policy_id || `${recommendation.title}-${recommendation.page}`;
            const pageNumber = parseInt(recommendation.page) || 0;
            
            // 목차 페이지(1-20페이지) 제외 및 중복 제거
            if (pageNumber > 20 && !policyIds.has(policyId)) {
              policyIds.add(policyId);
              uniquePolicies.push({
                id: policyId,
                title: recommendation.title || '맞춤 정책 추천',
                description: recommendation.text || '',
                category: '',
                source_page: recommendation.page || '',
                score: recommendation.score
              });
            }
          });
          
          // 최대 4개만 표시
          setPolicies(uniquePolicies.slice(0, 4));
        } else {
          setPolicies([]);
        }
      } catch (err) {
        setError('맞춤 정책을 불러오는데 실패했습니다.');
        console.error('정책 추천 API 오류:', err);
      } finally {
        setLoading(false);
        fetchInProgress.current = false;
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

  // 챗봇 상담으로 이동
  const navigateToChatbot = () => {
    navigate('/chat/temp');
  };

  // PDF 다운로드 함수
  const downloadPdf = () => {
    // PDF 다운로드 링크 (고용노동부 사이트)
    window.open('https://www.moel.go.kr/info/publicdata/majorpublish/majorPublishView.do?bbs_seq=20250200573', '_blank');
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

      {/* 정책 카드 그리드 */}
      <div className="policies-grid">
        {loading ? (
          <div className="loading">맞춤 정책을 불러오는 중...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : (
          <>
            {/* 정책 카드 영역 */}
            {policies.length > 0 ? (
              policies.map((policy, index) => (
                <div className="policy-card-wrapper" key={`policy-${policy.id}-${index}`}>
                  <PolicyCard policy={policy} />
                </div>
              ))
            ) : (
              <div className="no-results">
                <p>현재 조건에 맞는 추천 정책이 없습니다.</p>
                <p>필터 조건을 변경하여 다른 정책을 확인해보세요.</p>
              </div>
            )}
            
            {/* 챗봇 상담 카드 */}
            <div className="policy-card-wrapper chatbot-card-wrapper">
              <div className="chatbot-card" onClick={navigateToChatbot}>
                <div className="chatbot-icon">💬</div>
                <h3>AI 챗봇 상담</h3>
                <p>고용노동 정책 전문 AI와 대화하며 궁금한 점을 바로 해결하세요.</p>
                <button className="chatbot-btn">상담 시작하기</button>
              </div>
            </div>
            
            {/* PDF 다운로드 카드 */}
            <div className="policy-card-wrapper pdf-card-wrapper">
              <div className="pdf-card" onClick={downloadPdf}>
                <div className="pdf-icon">📄</div>
                <h3>정책 자료 다운로드</h3>
                <p>고용노동 정책 종합 안내서를 PDF로 다운받아 상세 내용을 확인하세요.</p>
                <button className="pdf-btn">PDF 다운로드</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PolicySearch;