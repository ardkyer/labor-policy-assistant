// File: src/pages/PolicySearch.js
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import PolicyCard from '../components/PolicyCard';
import './PolicySearch.css';

const PolicySearch = () => {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    age: '',
    gender: '',
    employment: '',
    region: ''
  });

  useEffect(() => {
    const fetchPolicies = async () => {
      try {
        setLoading(true);
        const response = await api.get('/api/v1/policies/search/', {
          params: { 
            q: searchTerm,
            ...filters
          }
        });
        setPolicies(response.data);
      } catch (err) {
        setError('정책을 불러오는데 실패했습니다.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPolicies();
  }, [searchTerm, filters]);

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="policy-search-container">
      <h1>정책 검색</h1>
      
      <div className="search-bar">
        <input 
          type="text" 
          placeholder="정책명, 키워드로 검색..." 
          value={searchTerm}
          onChange={handleSearchChange}
        />
        <button type="button">검색</button>
      </div>
      
      <div className="filters-section">
        <h3>상세 필터</h3>
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
          <div className="loading">정책을 불러오는 중...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : policies.length > 0 ? (
          policies.map(policy => (
            <PolicyCard key={policy.id} policy={policy} />
          ))
        ) : (
          <div className="no-results">검색 결과가 없습니다.</div>
        )}
      </div>
    </div>
  );
};

export default PolicySearch;