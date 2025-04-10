import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import api, { apiService } from '../services/api';
import './Profile.css';

const Profile = () => {
  const { user } = useContext(AuthContext);
  const [profileData, setProfileData] = useState({
    name: '',
    age: '',
    gender: '',
    employmentStatus: '',
    region: '',
    notifyPolicyUpdates: false,
    notifyDeadlines: false,
    notifyNewPolicies: false
  });
  const [savedPolicies, setSavedPolicies] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('profile');

  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        setLoading(true);

        // 사용자 기본 정보 가져오기
        const userResponse = await api.get('/auth/me');
        console.log('사용자 정보 응답:', userResponse.data);

        // 프로필 데이터 설정
        const userData = userResponse.data;
        const profile = userData.profile || {};

        setProfileData({
          name: userData.full_name || '',
          age: profile.age || '',
          gender: profile.gender || '',
          employmentStatus: profile.employment_status || '',
          region: profile.region || '',
          notifyPolicyUpdates: profile.notify_policy_updates || false,
          notifyDeadlines: profile.notify_deadlines || false,
          notifyNewPolicies: profile.notify_new_policies || false
        });

        try {
          // 저장한 정책 가져오기 (가능한 경우)
          const policiesResponse = await api.get('/profiles/me/saved-policies');
          setSavedPolicies(policiesResponse.data);
        } catch (err) {
          console.warn('저장된 정책을 가져오는데 실패했습니다:', err);
          setSavedPolicies([]);
        }

        try {
          // 알림 가져오기 (가능한 경우)
          const notificationsResponse = await api.get('/profiles/me/notifications');
          setNotifications(notificationsResponse.data);
        } catch (err) {
          console.warn('알림을 가져오는데 실패했습니다:', err);
          setNotifications([]);
        }

      } catch (err) {
        console.error('프로필 정보를 불러오는데 실패했습니다:', err);
        setError('프로필 정보를 불러오는데 실패했습니다.');
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

  const handleRemoveSavedPolicy = async (policyId) => {
    try {
      await api.delete(`/profiles/me/saved-policies/${policyId}`);
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
              <div className="profile-info-message">
                {/* 회원 정보는 회원가입 시에만 설정할 수 있습니다. */}
              </div>
            </div>

            <div className="profile-info">
              <div className="info-item">
                <span className="info-label">이메일</span>
                <span className="info-value">{user?.email || '-'}</span>
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
                <span className="info-value">
                  {profileData.region === 'seoul' && '서울'}
                  {profileData.region === 'busan' && '부산'}
                  {profileData.region === 'incheon' && '인천'}
                  {!profileData.region && '-'}
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'policies' && (
          <div className="policies-section">
            <h3>내 관심 정책</h3>

            {savedPolicies.length === 0 ? (
              <div className="no-policies">
                <p>저장된 정책이 없습니다.</p>
                <a href="/search" className="search-link">정책 추천 보러 가기</a>
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
                      <a href={`/policies/${policy.id}`} className="view-button">상세 보기</a>
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
                      const updated = !profileData.notifyPolicyUpdates;
                      await api.put('/profiles/me/notifications/settings', {
                        notify_policy_updates: updated
                      });
                      setProfileData(prev => ({
                        ...prev,
                        notifyPolicyUpdates: updated
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
                      const updated = !profileData.notifyDeadlines;
                      await api.put('/profiles/me/notifications/settings', {
                        notify_deadlines: updated
                      });
                      setProfileData(prev => ({
                        ...prev,
                        notifyDeadlines: updated
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
                      const updated = !profileData.notifyNewPolicies;
                      await api.put('/profiles/me/notifications/settings', {
                        notify_new_policies: updated
                      });
                      setProfileData(prev => ({
                        ...prev,
                        notifyNewPolicies: updated
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