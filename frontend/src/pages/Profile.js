import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';
import './Profile.css';

const Profile = () => {
  const { user } = useContext(AuthContext);
  const [profileData, setProfileData] = useState(null);
  const [savedPolicies, setSavedPolicies] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('profile');

  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        setLoading(true);
        const profileResponse = await api.get('/api/v1/profiles/me');
        setProfileData(profileResponse.data);
        
        // 저장한 정책 가져오기
        const policiesResponse = await api.get('/api/v1/profiles/me/saved-policies');
        setSavedPolicies(policiesResponse.data);
        
        // 알림 가져오기
        const notificationsResponse = await api.get('/api/v1/profiles/me/notifications');
        setNotifications(notificationsResponse.data);
      } catch (err) {
        setError('프로필 정보를 불러오는데 실패했습니다.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfileData();
  }, []);

  const [editableProfile, setEditableProfile] = useState({
    name: '',
    age: '',
    gender: '',
    employmentStatus: '',
    region: ''
  });
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (profileData) {
      setEditableProfile({
        name: profileData.name || '',
        age: profileData.age || '',
        gender: profileData.gender || '',
        employmentStatus: profileData.employmentStatus || '',
        region: profileData.region || ''
      });
    }
  }, [profileData]);

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
    if (!isEditing) {
      setEditableProfile({
        name: profileData.name || '',
        age: profileData.age || '',
        gender: profileData.gender || '',
        employmentStatus: profileData.employmentStatus || '',
        region: profileData.region || ''
      });
    }
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setEditableProfile(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/api/v1/profiles/', editableProfile);
      setProfileData({
        ...profileData,
        ...editableProfile
      });
      setIsEditing(false);
    } catch (err) {
      setError('프로필 업데이트에 실패했습니다.');
      console.error(err);
    }
  };

  const handleRemoveSavedPolicy = async (policyId) => {
    try {
      await api.delete(`/api/v1/profiles/me/saved-policies/${policyId}`);
      setSavedPolicies(prev => prev.filter(policy => policy.id !== policyId));
    } catch (err) {
      console.error('정책 삭제 실패:', err);
    }
  };

  if (loading) {
    return <div className="loading">프로필 로딩 중...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h1>내 프로필</h1>
        <div className="profile-tabs">
          <button 
            className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            기본 정보
          </button>
          <button 
            className={`tab-button ${activeTab === 'policies' ? 'active' : ''}`}
            onClick={() => setActiveTab('policies')}
          >
            관심 정책
          </button>
          <button 
            className={`tab-button ${activeTab === 'notifications' ? 'active' : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            알림 설정
          </button>
        </div>
      </div>

      <div className="profile-content">
        {activeTab === 'profile' && (
          <div className="profile-section">
            <div className="profile-actions">
              <button 
                className="edit-button"
                onClick={handleEditToggle}
              >
                {isEditing ? '취소' : '정보 수정'}
              </button>
            </div>

            {isEditing ? (
              <form onSubmit={handleProfileSubmit}>
                <div className="profile-form">
                  <div className="form-group">
                    <label>이름</label>
                    <input
                      type="text"
                      name="name"
                      value={editableProfile.name}
                      onChange={handleProfileChange}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>연령대</label>
                    <select
                      name="age"
                      value={editableProfile.age}
                      onChange={handleProfileChange}
                    >
                      <option value="">선택하세요</option>
                      <option value="youth">청년 (만 19-34세)</option>
                      <option value="middle">중장년 (만 35-64세)</option>
                      <option value="senior">노년 (만 65세 이상)</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>성별</label>
                    <select
                      name="gender"
                      value={editableProfile.gender}
                      onChange={handleProfileChange}
                    >
                      <option value="">선택하세요</option>
                      <option value="male">남성</option>
                      <option value="female">여성</option>
                      <option value="other">기타</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>고용상태</label>
                    <select
                      name="employmentStatus"
                      value={editableProfile.employmentStatus}
                      onChange={handleProfileChange}
                    >
                      <option value="">선택하세요</option>
                      <option value="employed">재직자</option>
                      <option value="unemployed">구직자</option>
                      <option value="business">자영업자</option>
                      <option value="student">학생</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>지역</label>
                    <select
                      name="region"
                      value={editableProfile.region}
                      onChange={handleProfileChange}
                    >
                      <option value="">선택하세요</option>
                      <option value="seoul">서울</option>
                      <option value="busan">부산</option>
                      <option value="incheon">인천</option>
                      {/* 다른 지역 추가 */}
                    </select>
                  </div>
                </div>
                
                <div className="form-actions">
                  <button type="submit" className="save-button">저장</button>
                </div>
              </form>
            ) : (
              <div className="profile-info">
                <div className="info-item">
                  <span className="info-label">이메일</span>
                  <span className="info-value">{user.email}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">이름</span>
                  <span className="info-value">{profileData.name || '-'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">연령대</span>
                  <span className="info-value">
                    {profileData.age === 'youth' && '청년 (만 19-34세)'}
                    {profileData.age === 'middle' && '중장년 (만 35-64세)'}
                    {profileData.age === 'senior' && '노년 (만 65세 이상)'}
                    {!profileData.age && '-'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">성별</span>
                  <span className="info-value">
                    {profileData.gender === 'male' && '남성'}
                    {profileData.gender === 'female' && '여성'}
                    {profileData.gender === 'other' && '기타'}
                    {!profileData.gender && '-'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">고용상태</span>
                  <span className="info-value">
                    {profileData.employmentStatus === 'employed' && '재직자'}
                    {profileData.employmentStatus === 'unemployed' && '구직자'}
                    {profileData.employmentStatus === 'business' && '자영업자'}
                    {profileData.employmentStatus === 'student' && '학생'}
                    {!profileData.employmentStatus && '-'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">지역</span>
                  <span className="info-value">{profileData.region || '-'}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'policies' && (
          <div className="policies-section">
            <h3>내 관심 정책</h3>
            
            {savedPolicies.length === 0 ? (
              <div className="no-policies">
                <p>저장된 정책이 없습니다.</p>
                <a href="/search" className="search-link">정책 검색하러 가기</a>
              </div>
            ) : (
              <div className="saved-policies-list">
                {savedPolicies.map(policy => (
                  <div key={policy.id} className="saved-policy-card">
                    <h4 className="policy-title">{policy.title}</h4>
                    <div className="policy-meta">
                      <span className="policy-category">{policy.category}</span>
                      {policy.deadline && (
                        <span className="policy-deadline">마감일: {policy.deadline}</span>
                      )}
                    </div>
                    <div className="policy-actions">
                      <a href={`/policy/${policy.id}`} className="view-button">상세 보기</a>
                      <button 
                        className="remove-button"
                        onClick={() => handleRemoveSavedPolicy(policy.id)}
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'notifications' && (
          <div className="notifications-section">
            <h3>알림 설정</h3>
            
            <div className="notification-options">
              <div className="notification-option">
                <input 
                  type="checkbox" 
                  id="policy-updates" 
                  checked={profileData.notifyPolicyUpdates} 
                  onChange={async () => {
                    try {
                      await api.post('/api/v1/profiles/', {
                        ...profileData,
                        notifyPolicyUpdates: !profileData.notifyPolicyUpdates
                      });
                      setProfileData(prev => ({
                        ...prev,
                        notifyPolicyUpdates: !prev.notifyPolicyUpdates
                      }));
                    } catch (err) {
                      console.error('알림 설정 업데이트 실패:', err);
                    }
                  }}
                />
                <label htmlFor="policy-updates">정책 업데이트 알림</label>
                <p className="option-description">저장한 정책의 내용이 업데이트되면 알림을 받습니다.</p>
              </div>
              
              <div className="notification-option">
                <input 
                  type="checkbox" 
                  id="deadline-alerts" 
                  checked={profileData.notifyDeadlines} 
                  onChange={async () => {
                    try {
                      await api.post('/api/v1/profiles/', {
                        ...profileData,
                        notifyDeadlines: !profileData.notifyDeadlines
                      });
                      setProfileData(prev => ({
                        ...prev,
                        notifyDeadlines: !prev.notifyDeadlines
                      }));
                    } catch (err) {
                      console.error('알림 설정 업데이트 실패:', err);
                    }
                  }}
                />
                <label htmlFor="deadline-alerts">마감일 알림</label>
                <p className="option-description">저장한 정책의 신청 마감일이 다가오면 알림을 받습니다.</p>
              </div>
              
              <div className="notification-option">
                <input 
                  type="checkbox" 
                  id="new-policies" 
                  checked={profileData.notifyNewPolicies} 
                  onChange={async () => {
                    try {
                      await api.post('/api/v1/profiles/', {
                        ...profileData,
                        notifyNewPolicies: !profileData.notifyNewPolicies
                      });
                      setProfileData(prev => ({
                        ...prev,
                        notifyNewPolicies: !prev.notifyNewPolicies
                      }));
                    } catch (err) {
                      console.error('알림 설정 업데이트 실패:', err);
                    }
                  }}
                />
                <label htmlFor="new-policies">새 정책 알림</label>
                <p className="option-description">내 프로필에 맞는 새로운 정책이 추가되면 알림을 받습니다.</p>
              </div>
            </div>
            
            <div className="notification-history">
              <h4>최근 알림</h4>
              
              {notifications.length === 0 ? (
                <p className="no-notifications">최근 알림이 없습니다.</p>
              ) : (
                <ul className="notifications-list">
                  {notifications.map(notification => (
                    <li key={notification.id} className="notification-item">
                      <div className="notification-content">
                        <span className="notification-icon">
                          {notification.type === 'update' && '🔄'}
                          {notification.type === 'deadline' && '⏰'}
                          {notification.type === 'new' && '🆕'}
                        </span>
                        <span className="notification-message">{notification.message}</span>
                      </div>
                      <span className="notification-time">
                        {new Date(notification.createdAt).toLocaleDateString()}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;