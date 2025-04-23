import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';
import PolicyCard from '../components/PolicyCard';
import './PolicySearch.css';

const PolicySearch = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [savedPolicies, setSavedPolicies] = useState([]);

  // 저장된 추천 정책 불러오기
  useEffect(() => {
    const fetchRecommendedPolicies = async () => {
      try {
        setLoading(true);
        // 새로운 엔드포인트로 사전 계산된 추천 정책 가져오기
        const response = await api.get('/policies/recommended/');
        
        if (response.data && response.data.length > 0) {
          setPolicies(response.data.map(policy => ({
            id: policy.id,
            title: policy.title,
            description: policy.content,
            category: policy.category || '기타',
            source_page: policy.page || '',
            is_saved: policy.is_saved
          })));
        } else {
          setPolicies([]);
        }
        
        // 저장된 정책도 함께 가져오기
        const savedResponse = await api.get('/policies/saved/');
        if (savedResponse.data) {
          setSavedPolicies(savedResponse.data);
        }
      } catch (err) {
        setError('추천 정책을 불러오는데 실패했습니다.');
        console.error('정책 추천 API 오류:', err);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchRecommendedPolicies();
    }
  }, [user]);

  // 정책 저장 처리
  const handleSavePolicy = async (policyId, isSaved) => {
    try {
      if (isSaved) {
        await api.delete(`/policies/save/${policyId}`);
        // 저장 상태 업데이트
        setPolicies(policies.map(policy => 
          policy.id === policyId ? {...policy, is_saved: false} : policy
        ));
      } else {
        await api.post(`/policies/save/${policyId}`);
        // 저장 상태 업데이트
        setPolicies(policies.map(policy => 
          policy.id === policyId ? {...policy, is_saved: true} : policy
        ));
      }
    } catch (err) {
      console.error('정책 저장/삭제 오류:', err);
    }
  };

  // 추천 정책 강제 갱신
  const refreshRecommendations = async () => {
    try {
      setLoading(true);
      await api.post('/policies/refresh-recommendations/');
      
      // 갱신된 추천 정책 다시 불러오기
      const response = await api.get('/policies/recommended/');
      if (response.data) {
        setPolicies(response.data.map(policy => ({
          id: policy.id,
          title: policy.title,
          description: policy.content,
          category: policy.category || '기타',
          source_page: policy.page || '',
          is_saved: policy.is_saved
        })));
      }
    } catch (err) {
      setError('추천 정책 갱신에 실패했습니다.');
      console.error('정책 갱신 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  // 챗봇 상담으로 이동
  const navigateToChatbot = () => {
    navigate('/chat/temp');
  };

  // PDF 다운로드 함수
  const downloadPdf = () => {
    window.open('https://www.moel.go.kr/info/publicdata/majorpublish/majorPublishView.do?bbs_seq=20250200573', '_blank');
  };

  return (
    <div className="policy-search-container">
      <h1>맞춤 정책 추천</h1>

      <div className="recommendation-info">
        <p>회원님의 프로필에 맞춰 저장된 맞춤 정책을 확인하세요.</p>
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
                  <PolicyCard 
                    policy={policy} 
                    onSave={() => handleSavePolicy(policy.id, policy.is_saved)}
                  />
                </div>
              ))
            ) : (
              <div className="no-results">
                <p>추천 정책이 없습니다.</p>
                <p>프로필 정보를 업데이트하거나 '추천 정책 갱신하기' 버튼을 클릭해보세요.</p>
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

      {/* 저장된 정책 섹션 */}
      {savedPolicies.length > 0 && (
        <div className="saved-policies-section">
          <h2>내가 저장한 정책</h2>
          <div className="saved-policies-grid">
            {savedPolicies.map((policy, index) => (
              <div className="policy-card-wrapper" key={`saved-${policy.id}-${index}`}>
                <PolicyCard 
                  policy={{...policy, is_saved: true}} 
                  onSave={() => handleSavePolicy(policy.id, true)}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicySearch;