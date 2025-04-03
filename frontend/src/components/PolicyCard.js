import React from 'react';
import './PolicyCard.css';

const PolicyCard = ({ policy }) => {
  return (
    <div className="policy-card">
      <div className="policy-header">
        <h3 className="policy-title">{policy.title}</h3>
        <span className="policy-category">{policy.category}</span>
      </div>
      <div className="policy-body">
        <p className="policy-description">{policy.description}</p>
        <div className="policy-details">
          <div className="policy-detail">
            <span className="detail-label">지원대상:</span>
            <span className="detail-value">{policy.eligibility}</span>
          </div>
          <div className="policy-detail">
            <span className="detail-label">지원내용:</span>
            <span className="detail-value">{policy.benefits}</span>
          </div>
          {policy.deadline && (
            <div className="policy-detail">
              <span className="detail-label">신청기한:</span>
              <span className="detail-value deadline">{policy.deadline}</span>
            </div>
          )}
        </div>
      </div>
      <div className="policy-footer">
        <button className="btn-detail">상세 보기</button>
        <button className="btn-save">관심 정책 등록</button>
      </div>
    </div>
  );
};

export default PolicyCard;