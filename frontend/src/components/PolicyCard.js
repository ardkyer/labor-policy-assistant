import React, { useState } from 'react';
import './PolicyCard.css';

const PolicyCard = ({ policy, onSave }) => {
  const [showDetails, setShowDetails] = useState(false);
  
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
      { pattern: /경력설계|노년|중년|신중년/, category: '경력개발' }
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
      default: return '📋';
    }
  };
  
  // 정책 요약 내용 추출 (첫 두 문장 또는 50자)
  const getSummary = (description) => {
    if (!description) return '';
    // 괄호의 번호 패턴과 불필요한 기호 제거
    const cleaned = description.replace(/\(\d+\)/g, '').replace(/\s+/g, ' ').trim();
    // 문장 단위로 나누기
    const sentences = cleaned.split(/(?<=[.!?])\s+/);
    // 첫 2문장 또는 50자 이내로 요약
    if (sentences.length > 0) {
      const firstTwoSentences = sentences.slice(0, 2).join(' ');
      return firstTwoSentences.length > 80 ? firstTwoSentences.substring(0, 80) + '...' : firstTwoSentences;
    }
    return cleaned.length > 80 ? cleaned.substring(0, 80) + '...' : cleaned;
  };
  
  // 정책에서 지원 대상, 지원 내용, 신청 방법 등 추출
  const extractKeyInfo = (description) => {
    const info = {
      target: null, // 지원 대상
      benefits: null, // 지원 내용
      process: null // 신청 방법
    };
    
    if (!description) return info;
    
    // 지원 대상 추출 (패턴 기반)
    const targetPatterns = [
      /대상\s*[:：]?\s*([^.!?]+[.!?])/i,
      /지원대상\s*[:：]?\s*([^.!?]+[.!?])/i,
      /신청자격\s*[:：]?\s*([^.!?]+[.!?])/i,
      /대상[은는이가]\s*([^.!?]+[.!?])/i
    ];
    
    // 지원 내용 추출
    const benefitsPatterns = [
      /내용\s*[:：]?\s*([^.!?]+[.!?])/i,
      /지원내용\s*[:：]?\s*([^.!?]+[.!?])/i,
      /혜택\s*[:：]?\s*([^.!?]+[.!?])/i,
      /지원금\s*[:：]?\s*([^.!?]+[.!?])/i
    ];
    
    // 신청 방법 추출
    const processPatterns = [
      /방법\s*[:：]?\s*([^.!?]+[.!?])/i,
      /신청방법\s*[:：]?\s*([^.!?]+[.!?])/i,
      /신청[은는이가]\s*([^.!?]+[.!?])/i,
      /절차\s*[:：]?\s*([^.!?]+[.!?])/i
    ];
    
    // 패턴 매칭 시도
    for (const pattern of targetPatterns) {
      const match = description.match(pattern);
      if (match && match[1]) {
        info.target = match[1].trim();
        break;
      }
    }
    
    for (const pattern of benefitsPatterns) {
      const match = description.match(pattern);
      if (match && match[1]) {
        info.benefits = match[1].trim();
        break;
      }
    }
    
    for (const pattern of processPatterns) {
      const match = description.match(pattern);
      if (match && match[1]) {
        info.process = match[1].trim();
        break;
      }
    }
    
    return info;
  };
  
  const title = cleanTitle(policy.title);
  const category = extractCategory(title);
  const categoryIcon = getCategoryIcon(category);
  const summary = getSummary(policy.description || policy.content); // policy.content도 체크
  const keyInfo = extractKeyInfo(policy.description || policy.content);
  
  // PDF 페이지 정보
  const pageInfo = policy.source_page || policy.page ? `PDF 페이지: ${policy.source_page || policy.page}` : '';
  
  // 상세 정보 토글
  const toggleDetails = () => {
    setShowDetails(!showDetails);
  };
  
  // 관심 정책 저장 처리
  const handleSave = () => {
    if (onSave) {
      onSave(policy.id, policy.is_saved);
    }
  };
  
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
          {pageInfo && (
            <div className="policy-page-info">
              {pageInfo}
            </div>
          )}
        </div>
      </div>
      <div className="policy-actions">
        <button
          className="btn-toggle-details"
          onClick={toggleDetails}
        >
          {showDetails ? '접기' : '상세 정보'}
        </button>
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