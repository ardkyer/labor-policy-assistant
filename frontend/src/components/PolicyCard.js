import React, { useState, useEffect } from 'react';
import './PolicyCard.css';

// const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const PolicyCard = ({ policy, onSave }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [enhancedInfo, setEnhancedInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(false);
  const [loadingDots, setLoadingDots] = useState('.');
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    if (!isLoading) return;

    const interval = setInterval(() => {
      setLoadingDots(prev => (prev.length >= 3 ? '.' : prev + '.'));
    }, 500);

    return () => clearInterval(interval);
  }, [isLoading]);

  // 컴포넌트 마운트 시 또는 policy가 변경될 때 실행
  useEffect(() => {
    // 이미 향상된 정보가 있는 경우 설정
    if (policy.enhanced_summary ||
      (policy.enhanced_eligibility && policy.enhanced_eligibility.length > 0) ||
      (policy.enhanced_benefits && policy.enhanced_benefits.length > 0) ||
      policy.enhanced_application) {

      setEnhancedInfo({
        summary: policy.enhanced_summary,
        eligibility: policy.enhanced_eligibility || [],
        benefits: policy.enhanced_benefits || [],
        application: policy.enhanced_application
      });
    }
  }, [policy]);

  // 정책 제목 정리: 번호와 같은 괄호 내용 제거
  const cleanTitle = (title) => {
    if (!title) return '';
    // 연속된 번호 (숫자) 패턴 제거
    return title.replace(/\(\d+\)\s*\(\d+\)\s*/g, '').replace(/\(\d+\)/g, '').trim();
  };

  // 카테고리 추출 (제목에서 주요 키워드 추출)
  const extractCategory = (title) => {
    const keywords = [
      { pattern: /특화과정|폴리텍/, category: '교육훈련' },
      { pattern: /장애인/, category: '장애인 지원' },
      { pattern: /청년/, category: '청년 지원' },
      { pattern: /고용장려금|지원금/, category: '고용장려금' },
      { pattern: /창업/, category: '창업 지원' },
      { pattern: /취업|재취업/, category: '취업 지원' },
      { pattern: /경력설계|노년|중년|신중년/, category: '경력개발' },
      { pattern: /육아|출산/, category: '육아지원' },
      { pattern: /여성/, category: '여성지원' }
    ];

    for (const keyword of keywords) {
      if (keyword.pattern.test(title)) {
        return keyword.category;
      }
    }
    return policy.category || '고용정책';
  };

  // 카테고리에 맞는 아이콘 선택
  const getCategoryIcon = (category) => {
    switch (category) {
      case '교육훈련': return '🎓';
      case '장애인 지원': return '♿';
      case '청년 지원': return '👨‍🎓';
      case '고용장려금': return '💰';
      case '창업 지원': return '🏢';
      case '취업 지원': return '👔';
      case '경력개발': return '📈';
      case '육아지원': return '👶';
      case '여성지원': return '👩';
      default: return '📋';
    }
  };

  // 정책 요약 내용 추출 (첫 두 문장 또는 80자)
  const getSummary = (description) => {
    if (!description) return '';
    // 괄호의 번호 패턴과 불필요한 기호 제거
    const cleaned = description.replace(/\(\d+\)/g, '').replace(/\s+/g, ' ').trim();
    // 문장 단위로 나누기
    const sentences = cleaned.split(/(?<=[.!?])\s+/);
    // 첫 2문장 또는 80자 이내로 요약
    if (sentences.length > 0) {
      const firstTwoSentences = sentences.slice(0, 2).join(' ');
      return firstTwoSentences.length > 80 ? firstTwoSentences.substring(0, 80) + '...' : firstTwoSentences;
    }
    return cleaned.length > 80 ? cleaned.substring(0, 80) + '...' : cleaned;
  };

  // 정책 내용에서 표 형식인지 확인
  const isTableFormat = (description) => {
    if (!description) return false;
    // 표 형식을 나타내는 패턴 (구분, 지원 대상, 지원 내용 등의 행과 열 구조)
    return /구\s*분.*지원\s*대상.*지원\s*내용/.test(description) ||
      /프로그램.*개요/.test(description) ||
      /프로세스.*과정목표/.test(description);
  };

  // LLM으로 정책에 대한 향상된 정보 요청
  const getEnhancedPolicyInfo = async (policyId, policyContent) => {
    setIsLoading(true);
    setApiError(false);
    try {
      if (enhancedInfo) {
        setIsLoading(false);
        return;
      }

      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/v1/policies/enhance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          policy_id: policyId,
          policy_content: policyContent
        }),
      });

      if (!response.ok) {
        throw new Error('정책 정보 향상 실패');
      }

      const data = await response.json();
      setEnhancedInfo(data);

    } catch (error) {
      console.error('정책 정보 향상 오류:', error);
      setApiError(true);
    } finally {
      setIsLoading(false);
    }
  };

  // 상세 정보 토글 시 LLM 정보 가져오기
  const toggleDetails = () => {
    // 상세 정보가 표시되고 아직 향상된 정보가 없는 경우 정보 가져오기
    if (!showDetails && !enhancedInfo && !apiError && !isLoading) {
      getEnhancedPolicyInfo(policy.id, policy.description || policy.content);
    }
    setShowDetails(!showDetails);
  };

  // 정책에서 지원 대상, 지원 내용, 신청 방법 등 추출
  const extractKeyInfo = (description) => {
    const info = {
      target: null, // 지원 대상
      benefits: null, // 지원 내용
      process: null, // 신청 방법
      hasContent: false // 정보 추출 여부
    };

    if (!description) return info;

    // 지원 대상 추출 (패턴 기반)
    const targetPatterns = [
      /대상\s*[:：]?\s*([^.!?]+[.!?])/i,
      /지원대상\s*[:：]?\s*([^.!?]+[.!?])/i,
      /신청자격\s*[:：]?\s*([^.!?]+[.!?])/i,
      /대상[은는이가]\s*([^.!?]+[.!?])/i,
      /지원\s*대상[은는과와]\s*([^.!?]+[.!?])/i,
      /프로그램\s*기초과정\s*심화과정\s*선택과정/i
    ];

    // 지원 내용 추출
    const benefitsPatterns = [
      /내용\s*[:：]?\s*([^.!?]+[.!?])/i,
      /지원내용\s*[:：]?\s*([^.!?]+[.!?])/i,
      /혜택\s*[:：]?\s*([^.!?]+[.!?])/i,
      /지원금\s*[:：]?\s*([^.!?]+[.!?])/i,
      /사업내용\s*[:：]?\s*([^.!?]+[.!?])/i,
      /지원\s*내용[은는이가]\s*([^.!?]+[.!?])/i
    ];

    // 신청 방법 추출
    const processPatterns = [
      /방법\s*[:：]?\s*([^.!?]+[.!?])/i,
      /신청방법\s*[:：]?\s*([^.!?]+[.!?])/i,
      /신청[은는이가]\s*([^.!?]+[.!?])/i,
      /절차\s*[:：]?\s*([^.!?]+[.!?])/i,
      /사업추진체계\s*([^.!?]+[.!?])/i,
      /운영\s*기관\s*[:：]?\s*([^.!?]+[.!?])/i
    ];

    // 프로그램 목적 추출 (신중년/고령자 정책에서 유용)
    const purposePatterns = [
      /사업목적\s*[:：]?\s*([^.!?]+[.!?])/i,
      /프로그램\s*개요\s*([^.!?]+[.!?])/i,
      /과정목표\s*([^.!?]+[.!?])/i
    ];

    // 패턴 매칭 시도
    for (const pattern of targetPatterns) {
      const match = description.match(pattern);
      if (match && match[1]) {
        info.target = match[1].trim();
        info.hasContent = true;
        break;
      } else if (pattern.test(description)) {
        // 패턴은 매치되지만 캡처 그룹이 없는 경우 (예: 프로그램 기초과정 심화과정)
        info.target = "해당 정책 카테고리 대상자";
        info.hasContent = true;
        break;
      }
    }

    for (const pattern of benefitsPatterns) {
      const match = description.match(pattern);
      if (match && match[1]) {
        info.benefits = match[1].trim();
        info.hasContent = true;
        break;
      }
    }

    for (const pattern of processPatterns) {
      const match = description.match(pattern);
      if (match && match[1]) {
        info.process = match[1].trim();
        info.hasContent = true;
        break;
      }
    }

    // 어떤 정보도 추출되지 않았고, 텍스트가 있는 경우 목적을 추출
    if (!info.hasContent && description.length > 20) {
      for (const pattern of purposePatterns) {
        const match = description.match(pattern);
        if (match && match[1]) {
          info.benefits = `프로그램 목적: ${match[1].trim()}`;
          info.hasContent = true;
          break;
        }
      }

      // 여전히 정보가 없으면 표 형식인지 확인
      if (!info.hasContent && isTableFormat(description)) {
        info.target = "표 형식의 정보는 PDF 원문을 참조하세요.";
        info.hasContent = true;
      }
    }

    return info;
  };

  // 관심 정책 저장 처리
  const handleSave = () => {
    if (onSave) {
      onSave(policy.id, policy.is_saved);
    }
  };

  const title = cleanTitle(policy.title);
  const category = extractCategory(title);
  const categoryIcon = getCategoryIcon(category);
  const policyText = policy.description || policy.content || "";
  const summary = getSummary(policyText);
  const keyInfo = extractKeyInfo(policyText);

  // PDF 페이지 정보
  const pageInfo = policy.source_page || policy.page ? `PDF 페이지: ${policy.source_page || policy.page}` : '';

  return (
    <div className="policy-card" data-category={category}>
      <div className="policy-header">
        <div className="category-icon">{categoryIcon}</div>
        <span className="policy-category">{category}</span>
      </div>
      <div className="policy-content">
        <h3 className="policy-title">{title}</h3>
        {/* 요약 정보 */}
        <p className="policy-summary">{summary}</p>
        {/* 상세 정보 (키 정보) */}
        <div className={`policy-details ${showDetails ? 'expanded' : ''}`}>
          {isLoading && (
            <div className="loading-indicator">
              <p>정책 정보를 분석 중입니다{loadingDots}</p>
              <p className="loading-time-note">AI 정책 분석은 약 10초 정도 소요됩니다.</p>
            </div>
          )}


          {/* LLM으로 향상된 정보가 있으면 표시 */}
          {!isLoading && enhancedInfo && (
            <>
              {enhancedInfo.summary && (
                <div className="enhanced-summary">
                  <h4>🔍 정책 요약</h4>
                  <p>{enhancedInfo.summary}</p>
                </div>
              )}

              {enhancedInfo.eligibility && enhancedInfo.eligibility.length > 0 && (
                <div className="key-info">
                  <span className="key-info-icon">👥</span>
                  <div className="key-info-content">
                    <h4>지원 대상</h4>
                    <ul>
                      {enhancedInfo.eligibility.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {enhancedInfo.benefits && enhancedInfo.benefits.length > 0 && (
                <div className="key-info">
                  <span className="key-info-icon">💰</span>
                  <div className="key-info-content">
                    <h4>지원 내용</h4>
                    <ul>
                      {enhancedInfo.benefits.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {enhancedInfo.application && (
                <div className="key-info">
                  <span className="key-info-icon">📝</span>
                  <div className="key-info-content">
                    <h4>신청 방법</h4>
                    <p>{enhancedInfo.application}</p>
                  </div>
                </div>
              )}
            </>
          )}

          {/* LLM 정보 없거나 오류 시 기존 추출 정보 표시 */}
          {!isLoading && (!enhancedInfo || apiError) && (
            <>
              {keyInfo.target && (
                <div className="key-info">
                  <span className="key-info-icon">👥</span>
                  <div className="key-info-content">
                    <h4>지원 대상</h4>
                    <p>{keyInfo.target}</p>
                  </div>
                </div>
              )}
              {keyInfo.benefits && (
                <div className="key-info">
                  <span className="key-info-icon">💰</span>
                  <div className="key-info-content">
                    <h4>지원 내용</h4>
                    <p>{keyInfo.benefits}</p>
                  </div>
                </div>
              )}
              {keyInfo.process && (
                <div className="key-info">
                  <span className="key-info-icon">📝</span>
                  <div className="key-info-content">
                    <h4>신청 방법</h4>
                    <p>{keyInfo.process}</p>
                  </div>
                </div>
              )}

              {/* 아무 정보도 추출되지 않았을 때 기본 내용 표시 */}
              {!keyInfo.hasContent && policyText.length > 0 && (
                <div className="key-info">
                  <span className="key-info-icon">📋</span>
                  <div className="key-info-content">
                    <h4>정책 안내</h4>
                    <p>이 정책에 대한 상세 정보는 PDF 원문을 참조하시기 바랍니다. 요약된 정보는 주요 내용만 추출한 것이며, 실제 정책과 차이가 있을 수 있습니다.</p>
                  </div>
                </div>
              )}
            </>
          )}

          {pageInfo && (
            <div className="policy-page-info">
              {pageInfo}
            </div>
          )}
        </div>
      </div>
      <div className="policy-actions">
        <div className="btn-analysis-wrapper" 
             onMouseEnter={() => setShowTooltip(true)}
             onMouseLeave={() => setShowTooltip(false)}>
          <button
            className="btn-toggle-details"
            onClick={toggleDetails}
          >
            {showDetails ? '접기' : 'AI 정책 분석'}
          </button>
          {!showDetails && showTooltip && (
            <div className="btn-tooltip">
              AI 분석은 10초 정도 소요됩니다. 조금만 기다려주세요!
            </div>
          )}
        </div>
        <button
          className={`btn-save ${policy.is_saved ? 'saved' : ''}`}
          onClick={handleSave}
        >
          {policy.is_saved ? '관심 정책 해제' : '관심 정책 등록'}
        </button>
      </div>
    </div>
  );
};

export default PolicyCard;