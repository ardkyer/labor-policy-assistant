import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import api, { apiService } from '../services/api';
import './Profile.css';
import PolicyCard from '../components/PolicyCard';

const Profile = () => {
  const { user } = useContext(AuthContext);
  const [profileData, setProfileData] = useState({
    name: '',
    age: '',
    gender: '',
    employmentStatus: '',
    // region: '',
    isDisabled: false,
    isForeign: false,
    familyStatus: '',
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
    console.log("savedPolicies 확인", savedPolicies);
  }, [savedPolicies]);


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
          familyStatus: profile.family_status || '',
          isDisabled: profile.is_disabled || false,
          isForeign: profile.is_foreign || false,
          notifyPolicyUpdates: profile.notify_policy_updates || false,
          notifyDeadlines: profile.notify_deadlines || false,
          notifyNewPolicies: profile.notify_new_policies || false
        });


        try {
          // 저장한 정책 가져오기 (가능한 경우)
          const policiesResponse = await api.get('/policies/saved/');
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
    // region: ''
  });
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (profileData) {
      setEditableProfile({
        name: profileData.name || '',
        age: profileData.age || '',
        gender: profileData.gender || '',
        employmentStatus: profileData.employmentStatus || '',
        // region: profileData.region || ''
      });
    }
  }, [profileData]);

  const handleRemoveSavedPolicy = async (policyId) => {
    try {
      await api.delete(`/policies/save/${policyId}`); // 🔥 이게 맞는 주소야
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
                <span className="info-label">장애인 여부</span>
                <span className="info-value">
                  {profileData.isDisabled ? '예' : '아니오'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">외국인 여부</span>
                <span className="info-value">
                  {profileData.isForeign ? '예' : '아니오'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">가족 상황</span>
                <span className="info-value">
                  {profileData.familyStatus === 'parent' && '영유아 자녀 있음'}
                  {profileData.familyStatus === 'single_parent' && '한부모'}
                  {profileData.familyStatus === 'caregiver' && '주 양육자'}
                  {!profileData.familyStatus && '-'}
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
              <div className="saved-policies-grid">
                {savedPolicies.map((policy, index) => (
                  <div className="policy-card-wrapper" key={`saved-${policy.id}-${index}`}>
                    <PolicyCard
                      policy={{ ...policy, is_saved: true }}
                      onSave={() => handleRemoveSavedPolicy(policy.id)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
};

export default Profile;