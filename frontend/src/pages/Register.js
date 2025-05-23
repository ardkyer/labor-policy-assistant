import React, { useState, useContext, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import './Auth.css';

const Register = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    age: '',
    gender: '',
    employmentStatus: '',
    region: '',
    isDisabled: '',
    isForeign: '',
    familyStatus: ''
  });

  // 필드에 대한 참조 생성
  const formRefs = {
    email: useRef(null),
    password: useRef(null),
    confirmPassword: useRef(null),
    name: useRef(null),
    age: useRef(null),
    gender: useRef(null),
    employmentStatus: useRef(null),
    isDisabled: useRef(null),
    isForeign: useRef(null),
    familyStatus: useRef(null)
  };

  const [formErrors, setFormErrors] = useState({});
  const [showGlobalError, setShowGlobalError] = useState(false); // 전체 오류 메시지 표시 여부
  const { register, error } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // 필드가 변경되면 해당 필드의 오류 메시지 제거
    if (formErrors[name]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
    
    // 전체 오류 메시지 감추기
    setShowGlobalError(false);
  };

  const validate = () => {
    const errors = {};

    if (!formData.email) {
      errors.email = '이메일을 입력해주세요';
    }

    if (!formData.password) {
      errors.password = '비밀번호를 입력해주세요';
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = '비밀번호가 일치하지 않습니다';
    }

    if (!formData.name) {
      errors.name = '이름을 입력해주세요';
    }

    // 프로필 정보 필수 항목 유지
    if (!formData.age) {
      errors.age = '연령대를 선택해주세요';
    }
    if (!formData.gender) {
      errors.gender = '성별을 선택해주세요';
    }
    if (!formData.employmentStatus) {
      errors.employmentStatus = '고용상태를 선택해주세요';
    }
    if (!formData.isDisabled) {
      errors.isDisabled = '장애인 여부를 선택해주세요';
    }
    if (!formData.isForeign) {
      errors.isForeign = '외국인 여부를 선택해주세요';
    }
    if (!formData.familyStatus) {
      errors.familyStatus = '가족 상황을 선택해주세요';
    }

    setFormErrors(errors);
    
    // 첫 번째 오류가 있는 필드로 스크롤
    const errorFields = Object.keys(errors);
    if (errorFields.length > 0) {
      const firstErrorField = errorFields[0];
      if (formRefs[firstErrorField] && formRefs[firstErrorField].current) {
        formRefs[firstErrorField].current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
        formRefs[firstErrorField].current.focus();
      }
      
      // 전체 오류 메시지 표시
      setShowGlobalError(true);
    }
    
    return errorFields.length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validate()) {
      setIsLoading(true); // 로딩 시작
      const success = await register(formData);
      if (success) {
        // 1초 정도 지연을 주면 자연스러움
        setTimeout(() => {
          setIsLoading(false);
          navigate('/login');
        }, 1000);
      } else {
        setIsLoading(false); // 실패 시도 리셋
      }
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card register-card">
        <h2>회원가입</h2>
        {error && <div className="auth-error">{error}</div>}
        
        {/* 모든 필수 항목을 채워야 한다는 안내 메시지 */}
        {showGlobalError && (
          <div className="global-error">
            <p>모든 필수 항목을 채워주세요. 미입력된 항목이 있습니다.</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <h3>기본 정보</h3>
            <div className="form-group">
              <label htmlFor="email">
                이메일 <span className="required">*</span>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                ref={formRefs.email}
                className={formErrors.email ? 'error-field' : ''}
              />
              {formErrors.email && <span className="error-message">{formErrors.email}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="password">
                비밀번호 <span className="required">*</span>
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                ref={formRefs.password}
                className={formErrors.password ? 'error-field' : ''}
              />
              {formErrors.password && <span className="error-message">{formErrors.password}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="confirmPassword">
                비밀번호 확인 <span className="required">*</span>
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                ref={formRefs.confirmPassword}
                className={formErrors.confirmPassword ? 'error-field' : ''}
              />
              {formErrors.confirmPassword && <span className="error-message">{formErrors.confirmPassword}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="name">
                이름 <span className="required">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                ref={formRefs.name}
                className={formErrors.name ? 'error-field' : ''}
              />
              {formErrors.name && <span className="error-message">{formErrors.name}</span>}
            </div>
          </div>

          <div className="form-section">
            <h3>프로필 정보 <span className="required-section">* 모든 항목을 필수로 입력해주세요</span></h3>
            <div className="form-group">
              <label htmlFor="age">
                연령대 <span className="required">*</span>
                <span className="info-tooltip" title="연령대에 따라 추천받는 정책이 달라집니다">ℹ️</span>
              </label>
              <select
                id="age"
                name="age"
                value={formData.age}
                onChange={handleChange}
                ref={formRefs.age}
                className={formErrors.age ? 'error-field' : ''}
              >
                <option value="">선택하세요</option>
                <option value="youth">청년 (만 19-34세)</option>
                <option value="middle">중장년 (만 35-64세)</option>
                <option value="senior">노년 (만 65세 이상)</option>
              </select>
              {formErrors.age && <span className="error-message">{formErrors.age}</span>}
              <div className="option-descriptions">
                <small>
                  • <b>청년</b>: 청년 일자리, 주거지원, 창업지원 등의 지원 정책<br />
                  • <b>중장년</b>: 전직 지원, 경력개발, 퇴직 준비 프로그램 등<br />
                  • <b>노년</b>: 노후 소득 지원, 재취업 지원, 복지 서비스 등의 정책
                </small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="gender">
                성별 <span className="required">*</span>
                <span className="info-tooltip" title="성별에 따라 추천받는 정책이 달라집니다">ℹ️</span>
              </label>
              <select
                id="gender"
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                ref={formRefs.gender}
                className={formErrors.gender ? 'error-field' : ''}
              >
                <option value="">선택하세요</option>
                <option value="male">남성</option>
                <option value="female">여성</option>
                <option value="other">기타</option>
              </select>
              {formErrors.gender && <span className="error-message">{formErrors.gender}</span>}
              <div className="option-descriptions">
                <small>
                  • <b>여성</b>: 경력단절 여성 지원, 여성 창업 지원, 육아 및 일·가정 양립 지원 정책 등<br />
                  • <b>성별</b>에 따른 특정 정책은 정부 지원 프로그램에 반영됩니다
                </small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="employmentStatus">
                고용상태 <span className="required">*</span>
                <span className="info-tooltip" title="고용상태에 따라 추천받는 정책이 달라집니다">ℹ️</span>
              </label>
              <select
                id="employmentStatus"
                name="employmentStatus"
                value={formData.employmentStatus}
                onChange={handleChange}
                ref={formRefs.employmentStatus}
                className={formErrors.employmentStatus ? 'error-field' : ''}
              >
                <option value="">선택하세요</option>
                <option value="employed">재직자</option>
                <option value="unemployed">구직자</option>
                <option value="business">자영업자</option>
                <option value="student">학생</option>
              </select>
              {formErrors.employmentStatus && <span className="error-message">{formErrors.employmentStatus}</span>}
              <div className="option-descriptions">
                <small>
                  • <b>재직자</b>: 직업능력개발, 일자리 안정자금, 근로환경 개선 지원 정책 등<br />
                  • <b>구직자</b>: 취업성공패키지, 취업알선, 구직활동 지원 등<br />
                  • <b>자영업자</b>: 창업 및 경영 지원, 소상공인 지원, 세제 혜택 등<br />
                  • <b>학생</b>: 학자금 지원, 취업준비 프로그램, 직업훈련 프로그램 등
                </small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="isDisabled">
                장애인 여부 <span className="required">*</span>
                <span className="info-tooltip" title="장애인 관련 지원 정책을 확인할 수 있습니다">ℹ️</span>
              </label>
              <select
                id="isDisabled"
                name="isDisabled"
                value={formData.isDisabled}
                onChange={handleChange}
                ref={formRefs.isDisabled}
                className={formErrors.isDisabled ? 'error-field' : ''}
              >
                <option value="">선택하세요</option>
                <option value="true">예</option>
                <option value="false">아니오</option>
              </select>
              {formErrors.isDisabled && <span className="error-message">{formErrors.isDisabled}</span>}
              <div className="option-descriptions">
                <small>
                  • <b>장애인</b>: 장애인 일자리, 근로 지원, 직업재활, 취업 지원, 편의 제공 등의 특화 정책
                </small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="isForeign">
                외국인 여부 <span className="required">*</span>
                <span className="info-tooltip" title="외국인 근로자 관련 정책을 확인할 수 있습니다">ℹ️</span>
              </label>
              <select
                id="isForeign"
                name="isForeign"
                value={formData.isForeign}
                onChange={handleChange}
                ref={formRefs.isForeign}
                className={formErrors.isForeign ? 'error-field' : ''}
              >
                <option value="">선택하세요</option>
                <option value="true">예</option>
                <option value="false">아니오</option>
              </select>
              {formErrors.isForeign && <span className="error-message">{formErrors.isForeign}</span>}
              <div className="option-descriptions">
                <small>
                  • <b>외국인</b>: 체류 지원, 취업 지원, 언어 교육, 생활 적응 프로그램, 다문화 가정 지원 등
                </small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="familyStatus">
                가족 상황 <span className="required">*</span>
                <span className="info-tooltip" title="가족 상황에 따라 추천받는 정책이 달라집니다">ℹ️</span>
              </label>
              <select
                id="familyStatus"
                name="familyStatus"
                value={formData.familyStatus}
                onChange={handleChange}
                ref={formRefs.familyStatus}
                className={formErrors.familyStatus ? 'error-field' : ''}
              >
                <option value="">선택하세요</option>
                <option value="parent">영유아 자녀 있음</option>
                <option value="single_parent">한부모</option>
                <option value="caregiver">주 양육자</option>
                <option value="none">해당 없음</option>
              </select>
              {formErrors.familyStatus && <span className="error-message">{formErrors.familyStatus}</span>}
              <div className="option-descriptions">
                <small>
                  • <b>영유아 자녀 있음</b>: 자녀가 있는 부모님을 위한 일반적인 양육 지원 정책<br />
                  • <b>한부모</b>: 한부모 가정을 위한 특화된 지원 정책<br />
                  • <b>주 양육자</b>: 가정 내 육아를 주로 담당하는 사람을 위한 돌봄 지원 정책
                </small>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="loading-box">
              <div className="spinner"></div>
              <p>사용자 프로필에 맞춰 정책을 추천하고 있습니다...</p>
            </div>
          ) : (
            <button type="submit" className="auth-button">회원가입</button>
          )}
        </form>

        <div className="auth-links">
          <p>
            이미 계정이 있으신가요? <Link to="/login">로그인</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;