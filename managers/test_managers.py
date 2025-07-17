#!/usr/bin/env python3
"""
Construction Estimator 매니저 테스트 스크립트

실행 방법: python test_managers.py
"""

import os
import sys
import traceback
from datetime import datetime

def test_basic_managers():
    """기본 매니저 테스트 (Phase 1)"""
    print("🧪 기본 매니저 테스트 시작...")
    
    try:
        # 기본 매니저 import 테스트
        from managers import SessionManager, ProcessingManager, UIHelper
        print("✅ 기본 매니저 import 성공")
        
        # SessionManager 테스트
        print("\n📋 SessionManager 테스트:")
        session_manager = SessionManager()
        
        # 새 세션 생성 테스트
        new_session = session_manager.create_new_session("Test Project")
        if new_session.get("status") == "success":
            print("✅ 새 세션 생성 성공")
            print(f"   세션 ID: {new_session['session_id']}")
        else:
            print("❌ 새 세션 생성 실패")
            print(f"   오류: {new_session.get('error')}")
        
        # 세션 드롭다운 테스트
        dropdown_choices = session_manager.get_session_dropdown_choices()
        print(f"✅ 세션 드롭다운 선택지: {len(dropdown_choices)}개")
        
        # ProcessingManager 테스트
        print("\n🔄 ProcessingManager 테스트:")
        processing_manager = ProcessingManager()
        
        # 더미 세션 데이터로 상태 조회
        dummy_session = {"session_id": "test", "service": None}
        status = processing_manager.get_processing_status(dummy_session)
        print(f"✅ 처리 상태 조회: {status}")
        
        # UIHelper 테스트
        print("\n🎨 UIHelper 테스트:")
        ui_helper = UIHelper()
        
        # 더미 데이터로 HTML 생성
        dummy_ocr = {"image1": {"summary": {"total_texts": 5, "measurement_count": 3}}}
        html = ui_helper.create_ocr_summary_html(dummy_ocr, "test_session")
        print(f"✅ OCR 요약 HTML 생성: {len(html)} 문자")
        
        # 알림 HTML 생성
        alert_html = ui_helper.create_alert_html("테스트 메시지", "success")
        print(f"✅ 알림 HTML 생성: {len(alert_html)} 문자")
        
        return True
        
    except Exception as e:
        print(f"❌ 기본 매니저 테스트 실패: {e}")
        print(traceback.format_exc())
        return False

def test_enhanced_managers():
    """Enhanced 매니저 테스트 (Phase 2)"""
    print("\n🚀 Enhanced 매니저 테스트 시작...")
    
    try:
        # Enhanced 매니저 import 테스트
        from managers.logging_manager import LoggingManager
        from managers.error_manager import ErrorManager, ErrorCategory
        from managers.validation_manager import ValidationManager
        print("✅ Enhanced 매니저 import 성공")
        
        # LoggingManager 테스트
        print("\n📊 LoggingManager 테스트:")
        logging_manager = LoggingManager(log_dir="test_logs")
        
        # 로그 기록 테스트
        logging_manager.log_app_activity("테스트 활동", "INFO")
        logging_manager.log_session_activity("test_session", "test_activity")
        print("✅ 로그 기록 성공")
        
        # 시스템 상태 조회
        system_status = logging_manager.get_system_status()
        print(f"✅ 시스템 상태 조회: {len(system_status)} 항목")
        
        # ErrorManager 테스트
        print("\n🛡️ ErrorManager 테스트:")
        error_manager = ErrorManager(logging_manager)
        
        # 에러 처리 테스트
        test_error = ValueError("테스트 에러")
        error_info = error_manager.handle_error(test_error)
        print(f"✅ 에러 처리 성공: {error_info.category.value}")
        
        # 사용자 메시지 생성
        user_message = error_manager.format_error_for_user(error_info)
        print(f"✅ 사용자 메시지 생성: {len(user_message)} 문자")
        
        # 에러 통계 조회
        error_stats = error_manager.get_error_statistics()
        print(f"✅ 에러 통계 조회: {error_stats['total_errors']}개 에러")
        
        # ValidationManager 테스트
        print("\n✅ ValidationManager 테스트:")
        validation_manager = ValidationManager(logging_manager)
        
        # 프로젝트 이름 검증
        project_result = validation_manager.validate_project_name("Test Project")
        print(f"✅ 프로젝트 이름 검증: {'성공' if project_result.is_valid else '실패'}")
        
        # 작업범위 텍스트 검증
        scope_result = validation_manager.validate_scope_text("Kitchen - cabinet replacement")
        print(f"✅ 작업범위 검증: {'성공' if scope_result.is_valid else '실패'}")
        
        # 세션 데이터 검증
        dummy_session = {
            "session_id": "session_20240101_120000_12345678",
            "created_at": datetime.now().isoformat(),
            "service": "dummy_service"
        }
        session_result = validation_manager.validate_session_data(dummy_session)
        print(f"✅ 세션 데이터 검증: {'성공' if session_result.is_valid else '실패'}")
        
        # 검증 통계 조회
        validation_stats = validation_manager.get_validation_statistics()
        print(f"✅ 검증 통계 조회: {validation_stats['total_validations']}개 검증")
        
        # 테스트 로그 정리
        import shutil
        if os.path.exists("test_logs"):
            shutil.rmtree("test_logs")
        
        return True
        
    except ImportError as e:
        print(f"⚠️ Enhanced 매니저 import 실패: {e}")
        print("💡 해결 방법:")
        print("   1. pip install Pillow")
        print("   2. Enhanced 매니저 파일들이 모두 있는지 확인")
        return False
        
    except Exception as e:
        print(f"❌ Enhanced 매니저 테스트 실패: {e}")
        print(traceback.format_exc())
        return False

def test_file_structure():
    """파일 구조 테스트"""
    print("\n📁 파일 구조 테스트:")
    
    required_files = [
        "managers/__init__.py",
        "managers/session_manager.py",
        "managers/processing_manager.py",
        "managers/ui_helper.py"
    ]
    
    enhanced_files = [
        "managers/logging_manager.py",
        "managers/error_manager.py",
        "managers/validation_manager.py"
    ]
    
    app_files = [
        "app_refactored.py",
        "app_enhanced.py"
    ]
    
    # 필수 파일 확인
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (누락)")
            missing_files.append(file)
    
    # Enhanced 파일 확인
    enhanced_available = True
    for file in enhanced_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"⚠️ {file} (Enhanced 기능 사용 불가)")
            enhanced_available = False
    
    # 앱 파일 확인
    for file in app_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (누락)")
            missing_files.append(file)
    
    # 디렉토리 확인
    directories = ["data", "data/sessions"]
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ {directory}/")
        else:
            print(f"⚠️ {directory}/ (없음 - 자동 생성됨)")
    
    if enhanced_available:
        if os.path.exists("logs"):
            print("✅ logs/")
        else:
            print("⚠️ logs/ (없음 - 자동 생성됨)")
    
    return len(missing_files) == 0, enhanced_available

def test_dependencies():
    """의존성 테스트"""
    print("\n📦 의존성 테스트:")
    
    required_deps = [
        ("gradio", "Gradio 웹 프레임워크"),
        ("json", "JSON 처리 (내장)"),
        ("datetime", "날짜/시간 처리 (내장)"),
        ("typing", "타입 힌트 (내장)"),
        ("os", "운영체제 인터페이스 (내장)"),
        ("logging", "로깅 (내장)")
    ]
    
    enhanced_deps = [
        ("PIL", "이미지 처리 (Pillow)"),
        ("mimetypes", "MIME 타입 (내장)"),
        ("re", "정규식 (내장)"),
        ("traceback", "트레이스백 (내장)")
    ]
    
    # 필수 의존성 확인
    missing_deps = []
    for dep_name, desc in required_deps:
        try:
            __import__(dep_name)
            print(f"✅ {dep_name} - {desc}")
        except ImportError:
            print(f"❌ {dep_name} - {desc} (누락)")
            missing_deps.append(dep_name)
    
    # Enhanced 의존성 확인
    enhanced_available = True
    for dep_name, desc in enhanced_deps:
        try:
            __import__(dep_name)
            print(f"✅ {dep_name} - {desc}")
        except ImportError:
            print(f"⚠️ {dep_name} - {desc} (Enhanced 기능 제한)")
            if dep_name == "PIL":
                enhanced_available = False
    
    return len(missing_deps) == 0, enhanced_available

def main():
    """메인 테스트 실행"""
    print("🏗️ Construction Estimator 매니저 테스트")
    print("="*60)
    
    # 파일 구조 테스트
    files_ok, enhanced_files_ok = test_file_structure()
    
    # 의존성 테스트
    deps_ok, enhanced_deps_ok = test_dependencies()
    
    if not files_ok or not deps_ok:
        print("\n❌ 기본 요구사항이 충족되지 않았습니다.")
        print("   설치 가이드를 참고하여 누락된 파일/의존성을 확인하세요.")
        return False
    
    # 기본 매니저 테스트
    basic_test_ok = test_basic_managers()
    
    # Enhanced 매니저 테스트 (가능한 경우)
    enhanced_test_ok = True
    if enhanced_files_ok and enhanced_deps_ok:
        enhanced_test_ok = test_enhanced_managers()
    else:
        print("\n⚠️ Enhanced 매니저 테스트 생략 (의존성 또는 파일 부족)")
    
    # 최종 결과
    print("\n" + "="*60)
    print("📊 테스트 결과 요약:")
    print(f"   파일 구조: {'✅ 통과' if files_ok else '❌ 실패'}")
    print(f"   의존성: {'✅ 통과' if deps_ok else '❌ 실패'}")
    print(f"   기본 매니저: {'✅ 통과' if basic_test_ok else '❌ 실패'}")
    print(f"   Enhanced 매니저: {'✅ 통과' if enhanced_test_ok else '❌ 실패' if enhanced_files_ok and enhanced_deps_ok else '⚠️ 생략'}")
    
    if basic_test_ok:
        print(f"\n🎉 테스트 완료!")
        print(f"   Phase 1 (기본): {'✅ 사용 가능' if basic_test_ok else '❌ 사용 불가'}")
        print(f"   Phase 2 (Enhanced): {'✅ 사용 가능' if enhanced_test_ok and enhanced_files_ok and enhanced_deps_ok else '❌ 사용 불가'}")
        
        if basic_test_ok and not (enhanced_test_ok and enhanced_files_ok and enhanced_deps_ok):
            print("\n💡 Enhanced 기능을 사용하려면:")
            print("   1. pip install Pillow")
            print("   2. Enhanced 매니저 파일들 추가")
            print("   3. logs/ 디렉토리 생성")
        
        return True
    else:
        print("\n❌ 테스트 실패. 설치 가이드를 참고하세요.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)