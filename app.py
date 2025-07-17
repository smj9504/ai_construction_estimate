#!/usr/bin/env python3
"""
Construction Estimator - 업무용 버전
여러 사용자가 동시에 사용할 수 있는 세션 기반 시스템

사용법: python app.py
"""

import gradio as gr
import json
import traceback
import logging
import os
from typing import Tuple, Dict, List, Optional
from datetime import datetime

# 기본 매니저 import
from managers import SessionManager, ProcessingManager, UIHelper

# 고급 매니저 import (사용 가능한 경우)
try:
    from managers.logging_manager import LoggingManager
    from managers.error_manager import ErrorManager, ErrorCategory
    from managers.validation_manager import ValidationManager
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False

# 로컬 모듈 import
try:
    from config import config
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("필요한 파일들이 모두 존재하는지 확인하세요.")
    exit(1)

# 기본 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class BusinessEstimatorApp:
    """업무용 건축 견적서 생성기 애플리케이션"""
    
    def __init__(self):
        """앱 초기화"""
        logger.info("BusinessEstimatorApp 초기화 시작")
        
        # 고급 매니저 초기화 (사용 가능한 경우)
        if ADVANCED_FEATURES:
            self.logging_manager = LoggingManager(debug_mode=False)
            self.error_manager = ErrorManager(self.logging_manager)
            self.validation_manager = ValidationManager(self.logging_manager)
        else:
            self.logging_manager = None
            self.error_manager = None
            self.validation_manager = None
        
        # 기본 매니저 초기화
        self.session_manager = SessionManager()
        self.processing_manager = ProcessingManager()
        self.ui_helper = UIHelper()
        
        # 전역 설정 확인
        if not config.ANTHROPIC_API_KEY:
            self.config_warning = "⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
        else:
            self.config_warning = None
        
        # 시스템 통계 초기화
        self.system_stats = {
            "total_sessions": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "start_time": datetime.now().isoformat()
        }
        
        if self.logging_manager:
            self.logging_manager.log_app_activity("BusinessEstimatorApp 초기화 완료")
        
        logger.info("BusinessEstimatorApp 초기화 완료")
    
    def _handle_with_monitoring(self, operation_name: str, operation_func, *args, **kwargs):
        """모니터링을 포함한 작업 실행"""
        if not ADVANCED_FEATURES:
            return operation_func(*args, **kwargs)
        
        # 성능 추적 시작
        operation_id = f"{operation_name}_{datetime.now().strftime('%H%M%S')}"
        self.logging_manager.start_performance_tracking(operation_id)
        
        try:
            # 작업 실행
            result = operation_func(*args, **kwargs)
            
            # 성공 기록
            self.logging_manager.end_performance_tracking(operation_id, success=True)
            self.system_stats["successful_operations"] += 1
            
            return result
            
        except Exception as e:
            # 에러 처리
            error_info = self.error_manager.handle_error(
                error=e,
                context={"operation": operation_name, "args": str(args)[:200]}
            )
            
            # 성능 추적 종료
            self.logging_manager.end_performance_tracking(operation_id, success=False)
            self.system_stats["failed_operations"] += 1
            
            # 사용자 친화적 에러 메시지 반환
            error_message = self.error_manager.format_error_for_user(error_info)
            
            # 작업 유형에 따른 기본 반환값
            if operation_name in ["new_session", "load_session"]:
                return {}, error_message, "", []
            elif operation_name in ["image_processing", "mapping_processing"]:
                return "", error_message, "", {}
            else:
                return error_message
    
    def handle_new_session(self, project_name: str, session_state: Dict) -> Tuple[Dict, str, str, List]:
        """새 세션 생성 핸들러"""
        def _create_session():
            if self.logging_manager:
                self.logging_manager.log_session_activity("system", "new_session_request", {
                    "project_name": project_name
                })
            
            # 프로젝트 이름 검증
            if ADVANCED_FEATURES and self.validation_manager:
                validation_result = self.validation_manager.validate_project_name(project_name)
                if not validation_result.is_valid:
                    error_msg = "❌ 프로젝트 이름 검증 실패:\n" + "\n".join(validation_result.errors)
                    return session_state, error_msg, "", []
            
            # 새 세션 생성
            new_session = self.session_manager.create_new_session(project_name)
            
            if new_session.get("status") == "success":
                self.system_stats["total_sessions"] += 1
                
                if self.logging_manager:
                    self.logging_manager.log_session_activity(
                        new_session["session_id"], 
                        "created", 
                        {"project_name": project_name}
                    )
                
                status_msg = self.session_manager.get_session_status_message(new_session, "create")
                session_dropdown = self.session_manager.get_session_dropdown_choices()
                
                return new_session, status_msg, new_session['session_id'], session_dropdown
            else:
                error_msg = f"❌ 세션 생성 실패: {new_session.get('error', 'Unknown error')}"
                return session_state, error_msg, "", []
        
        return self._handle_with_monitoring("new_session", _create_session)
    
    def handle_load_session(self, selected_session_id: str, session_state: Dict) -> Tuple[Dict, str, str, str, str]:
        """기존 세션 로드 핸들러"""
        def _load_session():
            if not selected_session_id:
                return session_state, "❌ 세션을 선택하세요.", "", "", ""
            
            if self.logging_manager:
                self.logging_manager.log_session_activity(
                    selected_session_id, 
                    "load_request"
                )
            
            loaded_session = self.session_manager.load_existing_session(selected_session_id)
            
            if loaded_session.get("status") == "success":
                # 세션 데이터 검증
                if ADVANCED_FEATURES and self.validation_manager:
                    validation_result = self.validation_manager.validate_session_data(loaded_session)
                    if not validation_result.is_valid:
                        if self.logging_manager:
                            self.logging_manager.log_app_activity(
                                "세션 데이터 검증 경고",
                                level="WARNING",
                                extra_data={"session_id": selected_session_id}
                            )
                
                if self.logging_manager:
                    self.logging_manager.log_session_activity(
                        selected_session_id, 
                        "loaded"
                    )
                
                status_msg = self.session_manager.get_session_status_message(loaded_session, "load")
                
                # 기존 결과가 있으면 복원
                ocr_json = ""
                mapping_json = ""
                scope_text = ""
                
                if loaded_session["ocr_results"]:
                    ocr_json = json.dumps(loaded_session["ocr_results"], indent=2, ensure_ascii=False)
                
                if loaded_session["mapping_results"]:
                    mapping_json = json.dumps(loaded_session["mapping_results"], indent=2, ensure_ascii=False)
                    scope_text = loaded_session["service"].current_results.get("scope_text", "")
                
                return loaded_session, status_msg, ocr_json, mapping_json, scope_text
            else:
                error_msg = f"❌ 세션 로드 실패: {loaded_session.get('error', 'Unknown error')}"
                return session_state, error_msg, "", "", ""
        
        return self._handle_with_monitoring("load_session", _load_session)
    
    def handle_image_processing(self, uploaded_files, session_state: Dict, progress=gr.Progress()) -> Tuple[str, str, str, Dict]:
        """이미지 처리 핸들러"""
        def _process_images():
            session_id = session_state.get("session_id", "unknown")
            
            if self.logging_manager:
                self.logging_manager.log_processing_activity(
                    session_id, 
                    "ocr", 
                    "started", 
                    details={"file_count": len(uploaded_files) if uploaded_files else 0}
                )
            
            # 파일 검증
            if ADVANCED_FEATURES and self.validation_manager:
                validation_result = self.validation_manager.validate_multiple_files(uploaded_files)
                if not validation_result.is_valid:
                    error_msg = "❌ 파일 검증 실패:\n" + "\n".join(validation_result.errors)
                    return "", error_msg, "", session_state
                
                # 검증 경고가 있으면 로그에 기록
                if validation_result.warnings:
                    if self.logging_manager:
                        self.logging_manager.log_app_activity(
                            "파일 검증 경고",
                            level="WARNING",
                            extra_data={"warnings": validation_result.warnings}
                        )
            
            # 진행률 콜백 함수 정의
            def progress_callback(value, desc=""):
                if progress:
                    progress(value, desc=desc)
            
            # OCR 처리
            success, json_result, status_msg, updated_session = self.processing_manager.process_images_ocr(
                uploaded_files, session_state, progress_callback
            )
            
            if success:
                # HTML 요약 생성
                html_summary = self.ui_helper.create_ocr_summary_html(
                    updated_session["ocr_results"], 
                    updated_session["session_id"]
                )
                
                if self.logging_manager:
                    self.logging_manager.log_processing_activity(
                        session_id, 
                        "ocr", 
                        "completed", 
                        details={
                            "result_count": len(updated_session["ocr_results"]),
                            "success": True
                        }
                    )
                
                return json_result, status_msg, html_summary, updated_session
            else:
                if self.logging_manager:
                    self.logging_manager.log_processing_activity(
                        session_id, 
                        "ocr", 
                        "failed", 
                        details={"error": status_msg}
                    )
                
                return "", status_msg, "", updated_session
        
        return self._handle_with_monitoring("image_processing", _process_images)
    
    def handle_mapping_processing(self, scope_text: str, session_state: Dict, progress=gr.Progress()) -> Tuple[str, str, str, Dict]:
        """매핑 처리 핸들러"""
        def _process_mapping():
            session_id = session_state.get("session_id", "unknown")
            
            if self.logging_manager:
                self.logging_manager.log_processing_activity(
                    session_id, 
                    "mapping", 
                    "started", 
                    details={"scope_text_length": len(scope_text)}
                )
            
            # 작업범위 텍스트 검증
            if ADVANCED_FEATURES and self.validation_manager:
                validation_result = self.validation_manager.validate_scope_text(scope_text)
                if not validation_result.is_valid:
                    error_msg = "❌ 작업범위 검증 실패:\n" + "\n".join(validation_result.errors)
                    return "", error_msg, "", session_state
            
            # 진행률 콜백 함수 정의
            def progress_callback(value, desc=""):
                if progress:
                    progress(value, desc=desc)
            
            # 매핑 처리
            success, json_result, status_msg, updated_session = self.processing_manager.process_scope_mapping(
                scope_text, session_state, progress_callback
            )
            
            if success:
                # HTML 요약 생성
                html_summary = self.ui_helper.create_mapping_summary_html(
                    updated_session["mapping_results"], 
                    updated_session["session_id"]
                )
                
                if self.logging_manager:
                    self.logging_manager.log_processing_activity(
                        session_id, 
                        "mapping", 
                        "completed", 
                        details={
                            "mapping_count": len(updated_session["mapping_results"]),
                            "success": True
                        }
                    )
                
                return json_result, status_msg, html_summary, updated_session
            else:
                if self.logging_manager:
                    self.logging_manager.log_processing_activity(
                        session_id, 
                        "mapping", 
                        "failed", 
                        details={"error": status_msg}
                    )
                
                return "", status_msg, "", updated_session
        
        return self._handle_with_monitoring("mapping_processing", _process_mapping)
    
    def handle_clear_session(self, session_state: Dict) -> Tuple[str, str, str, str, str, Dict]:
        """세션 데이터 초기화 핸들러"""
        def _clear_session():
            session_id = session_state.get("session_id", "unknown")
            
            if self.logging_manager:
                self.logging_manager.log_session_activity(session_id, "clear_request")
            
            updated_session = self.session_manager.clear_session_data(session_state)
            
            if updated_session and updated_session.get("service"):
                if self.logging_manager:
                    self.logging_manager.log_session_activity(session_id, "cleared")
                
                status_msg = self.session_manager.get_session_status_message(updated_session, "clear")
                return "", status_msg, "", "", "", updated_session
            else:
                return "", "❌ 활성 세션이 없습니다.", "", "", "", session_state
        
        return self._handle_with_monitoring("clear_session", _clear_session)
    
    def handle_get_all_results(self, session_state: Dict) -> Dict:
        """전체 결과 조회 핸들러"""
        def _get_results():
            session_id = session_state.get("session_id", "unknown")
            
            if self.logging_manager:
                self.logging_manager.log_session_activity(session_id, "get_all_results")
            
            return self.processing_manager.get_all_results(session_state)
        
        return self._handle_with_monitoring("get_all_results", _get_results)
    
    def handle_refresh_sessions(self) -> List:
        """세션 목록 새로고침 핸들러"""
        def _refresh_sessions():
            if self.logging_manager:
                self.logging_manager.log_app_activity("세션 목록 새로고침")
            
            return self.session_manager.get_session_dropdown_choices()
        
        return self._handle_with_monitoring("refresh_sessions", _refresh_sessions)
    
    # 고급 기능 핸들러들
    def handle_get_system_status(self) -> Dict:
        """시스템 상태 조회 핸들러"""
        if not ADVANCED_FEATURES:
            return {"status": "고급 기능 사용 불가", "basic_stats": self.system_stats}
        
        try:
            system_status = {
                "advanced_features": True,
                "system_stats": self.system_stats,
                "logging_status": self.logging_manager.get_system_status(),
                "error_statistics": self.error_manager.get_error_statistics(),
                "validation_statistics": self.validation_manager.get_validation_statistics(),
                "timestamp": datetime.now().isoformat()
            }
            
            return system_status
            
        except Exception as e:
            if self.error_manager:
                error_info = self.error_manager.handle_error(e, {"context": "system_status"})
                return {"error": self.error_manager.format_error_for_user(error_info)}
            else:
                return {"error": f"시스템 상태 조회 실패: {str(e)}"}
    
    def handle_toggle_debug_mode(self) -> str:
        """디버그 모드 토글 핸들러"""
        if not ADVANCED_FEATURES or not self.logging_manager:
            return "❌ 고급 기능을 사용할 수 없습니다."
        
        try:
            new_debug_mode = self.logging_manager.toggle_debug_mode()
            return f"✅ 디버그 모드: {'ON' if new_debug_mode else 'OFF'}"
        except Exception as e:
            if self.error_manager:
                error_info = self.error_manager.handle_error(e, {"context": "toggle_debug"})
                return self.error_manager.format_error_for_user(error_info)
            else:
                return f"❌ 디버그 모드 토글 실패: {str(e)}"
    
    def handle_get_recent_logs(self, logger_name: str = "app", lines: int = 50) -> str:
        """최근 로그 조회 핸들러"""
        if not ADVANCED_FEATURES or not self.logging_manager:
            return "❌ 고급 기능을 사용할 수 없습니다."
        
        try:
            recent_logs = self.logging_manager.get_recent_logs(logger_name, lines)
            if recent_logs:
                return f"📋 최근 로그 ({logger_name}):\n\n" + "".join(recent_logs[-lines:])
            else:
                return f"📋 {logger_name} 로그 파일이 없거나 비어있습니다."
        except Exception as e:
            if self.error_manager:
                error_info = self.error_manager.handle_error(e, {"context": "get_recent_logs"})
                return self.error_manager.format_error_for_user(error_info)
            else:
                return f"❌ 로그 조회 실패: {str(e)}"
    
    def create_interface(self):
        """Gradio 인터페이스 생성"""
        
        # CSS 스타일
        css = """
        .container { max-width: 1400px; margin: auto; padding: 20px; }
        .session-card { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .advanced-card {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .upload-area { 
            border: 2px dashed #007bff; 
            border-radius: 12px; 
            padding: 30px; 
            text-align: center;
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            transition: all 0.3s ease;
        }
        .upload-area:hover {
            border-color: #0056b3;
            background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,123,255,0.2);
        }
        .primary-btn { 
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            font-weight: 600;
        }
        .secondary-btn {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
            color: white;
        }
        .advanced-btn {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            font-weight: 600;
        }
        .system-info {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        """
        
        # 기능 상태 메시지
        features_status = "✅ 고급 기능 활성화" if ADVANCED_FEATURES else "⚠️ 고급 기능 비활성화 (기본 기능만 사용)"
        
        with gr.Blocks(
            title="🏗️ Construction Estimator - 업무용",
            theme=gr.themes.Soft(),
            css=css
        ) as interface:
            
            # 세션 상태
            session_state = gr.State({})
            
            # 헤더
            gr.Markdown(
                f"""
                # 🏗️ Construction Estimator - 업무용 버전
                
                **다중 사용자 지원 | 세션 기반 데이터 관리 | 프로젝트별 작업**
                
                🔧 **기능 상태:** {features_status}
                
                🚀 **업무용 기능:**
                - 👥 여러 사용자 동시 사용 가능
                - 💾 세션별 자동 저장/복구
                - 📁 프로젝트별 데이터 관리
                - 🔄 브라우저 새로고침해도 데이터 보존
                - 🎯 **SessionManager**: 세션 생성/로드/관리
                - 🔄 **ProcessingManager**: OCR/매핑 데이터 처리
                - 🎨 **UIHelper**: HTML 생성/UI 헬퍼
                """ + ("""
                - 📊 **LoggingManager**: 구조화된 로깅 시스템
                - 🛡️ **ErrorManager**: 지능형 에러 처리
                - ✅ **ValidationManager**: 포괄적 검증 시스템
                - 📈 **실시간 모니터링**: 성능 및 상태 추적
                """ if ADVANCED_FEATURES else "") + """
                
                ---
                """,
                elem_classes=["container"]
            )
            
            # 설정 경고
            if self.config_warning:
                gr.Markdown(f"⚠️ **{self.config_warning}**")
            
            # 고급 시스템 정보 (상단)
            if ADVANCED_FEATURES:
                with gr.Row():
                    with gr.Column(scale=1, elem_classes=["advanced-card"]):
                        gr.Markdown("### 🛠️ 시스템 제어")
                        
                        with gr.Row():
                            debug_toggle_btn = gr.Button("🔧 디버그 모드", variant="secondary", size="sm")
                            system_status_btn = gr.Button("📊 시스템 상태", variant="secondary", size="sm")
                            logs_btn = gr.Button("📋 로그 조회", variant="secondary", size="sm")
                        
                        system_info_display = gr.Textbox(
                            label="시스템 정보",
                            placeholder="시스템 상태 버튼을 클릭하여 정보를 확인하세요...",
                            lines=4,
                            interactive=False,
                            elem_classes=["system-info"]
                        )
            
            # 세션 관리 섹션
            with gr.Row():
                with gr.Column(scale=2, elem_classes=["session-card"]):
                    gr.Markdown("### 🎯 세션 관리")
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            project_name_input = gr.Textbox(
                                label="프로젝트 이름",
                                placeholder="예: Johnson House Renovation",
                                value=f"Project {datetime.now().strftime('%m%d_%H%M')}"
                            )
                            new_session_btn = gr.Button(
                                "🆕 새 세션 시작",
                                variant="primary",
                                elem_classes=["primary-btn"]
                            )
                        
                        with gr.Column(scale=1):
                            session_dropdown = gr.Dropdown(
                                label="기존 세션 로드",
                                choices=self.session_manager.get_session_dropdown_choices(),
                                value=None,
                                interactive=True
                            )
                            load_session_btn = gr.Button(
                                "📂 세션 로드",
                                variant="secondary",
                                elem_classes=["secondary-btn"]
                            )
                    
                    session_status = gr.Textbox(
                        label="세션 상태",
                        value="🔄 새 세션을 시작하거나 기존 세션을 로드하세요.",
                        interactive=False,
                        max_lines=6
                    )
            
            # 메인 작업 영역
            with gr.Row():
                # 왼쪽: 입력 영역
                with gr.Column(scale=1):
                    
                    # 1. 이미지 업로드 섹션
                    validation_text = "고급 검증 기능" if ADVANCED_FEATURES else "기본 검증"
                    gr.Markdown(f"## 1️⃣ 측량 사진 업로드 ({validation_text})")
                    
                    image_upload = gr.File(
                        label="📁 측량 사진들 (여러 파일 가능)",
                        file_count="multiple",
                        file_types=["image"],
                        elem_classes=["upload-area"]
                    )
                    
                    if ADVANCED_FEATURES:
                        gr.Markdown(
                            """
                            **고급 검증 기능:**
                            - 파일 형식 및 크기 검증
                            - 이미지 해상도 및 품질 검증
                            - 보안 검사 및 무결성 확인
                            - 지원 형식: PNG, JPG, JPEG, BMP, TIFF
                            """
                        )
                    else:
                        gr.Markdown(
                            """
                            **지원 형식:** PNG, JPG, JPEG, BMP, TIFF  
                            **최대 크기:** 10MB per file  
                            **권장:** 측량 도면, 스케치, 측정값이 적힌 사진들
                            """
                        )
                    
                    process_images_btn = gr.Button(
                        "🔍 OCR 처리 시작", 
                        variant="primary", 
                        size="lg",
                        elem_classes=["primary-btn"]
                    )
                    
                    gr.Markdown("---")
                    
                    # 2. 작업 범위 입력 섹션
                    gr.Markdown(f"## 2️⃣ 작업 범위 입력 ({validation_text})")
                    
                    scope_input = gr.Textbox(
                        label="📝 작업 범위",
                        placeholder="""예시:
Kitchen - cabinet replacement and countertop installation
Master Bathroom - tile replacement and vanity upgrade  
Living Room - hardwood flooring installation
Bedroom 1 - carpet replacement and paint
Bedroom 2 - flooring upgrade""",
                        lines=8,
                        max_lines=15
                    )
                    
                    if ADVANCED_FEATURES:
                        gr.Markdown(
                            """
                            **고급 검증 기능:**
                            - 텍스트 길이 및 형식 검증
                            - 작업 범위 구조 분석
                            - 중복 항목 감지
                            - 비즈니스 룰 적용
                            """
                        )
                    else:
                        gr.Markdown(
                            """
                            **입력 형식:** `방 이름 - 작업 내용`  
                            각 줄에 하나씩 입력하세요.
                            """
                        )
                    
                    process_mapping_btn = gr.Button(
                        "🔗 데이터 매핑 시작",
                        variant="primary",
                        size="lg",
                        elem_classes=["primary-btn"]
                    )
                
                # 오른쪽: 결과 영역
                with gr.Column(scale=1):
                    
                    # 처리 상태
                    monitoring_text = "실시간 모니터링" if ADVANCED_FEATURES else "기본 상태"
                    gr.Markdown(f"## 📊 처리 상태 ({monitoring_text})")
                    
                    ocr_status = gr.Textbox(
                        label="1️⃣ OCR 처리 상태",
                        placeholder="이미지를 업로드하고 OCR 처리를 시작하세요...",
                        max_lines=8,
                        interactive=False
                    )
                    
                    mapping_status = gr.Textbox(
                        label="2️⃣ 매핑 처리 상태", 
                        placeholder="작업 범위를 입력하고 매핑을 시작하세요...",
                        max_lines=8,
                        interactive=False
                    )
                    
                    # 세션 관리 버튼들
                    with gr.Row():
                        clear_session_btn = gr.Button(
                            "🗑️ 세션 초기화",
                            variant="secondary",
                            size="sm"
                        )
                        refresh_sessions_btn = gr.Button(
                            "🔄 세션 목록 새로고침",
                            variant="secondary", 
                            size="sm"
                        )
            
            # 결과 요약 (전체 폭)
            ui_text = "고급 UI" if ADVANCED_FEATURES else "기본 UI"
            gr.Markdown(f"## 📈 처리 결과 ({ui_text})")
            
            with gr.Row():
                with gr.Column():
                    ocr_summary_html = gr.HTML(
                        label="📊 OCR 결과 요약",
                        visible=False
                    )
                    
                    mapping_summary_html = gr.HTML(
                        label="🔗 매핑 결과 요약", 
                        visible=False
                    )
            
            # 상세 결과 (접을 수 있는 섹션들)
            with gr.Accordion("📄 상세 OCR 결과 (JSON)", open=False):
                ocr_results_json = gr.JSON(
                    label="OCR 상세 데이터",
                    visible=False
                )
            
            with gr.Accordion("🔗 상세 매핑 결과 (JSON)", open=False):
                mapping_results_json = gr.JSON(
                    label="매핑 상세 데이터",
                    visible=False
                )
            
            # 전체 결과
            with gr.Accordion("📊 전체 결과 데이터", open=False):
                refresh_all_btn = gr.Button("🔄 전체 결과 새로고침", variant="secondary")
                all_results_json = gr.JSON(label="전체 결과 데이터")
            
            # 고급 시스템 정보 (하단)
            if ADVANCED_FEATURES:
                with gr.Accordion("🛠️ 고급 시스템 정보", open=False):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### 📊 로깅 시스템")
                            log_type_dropdown = gr.Dropdown(
                                choices=["app", "session", "processing", "error", "debug"],
                                value="app",
                                label="로그 타입"
                            )
                            log_lines_slider = gr.Slider(
                                minimum=10,
                                maximum=200,
                                value=50,
                                step=10,
                                label="로그 라인 수"
                            )
                            view_logs_btn = gr.Button("📋 로그 보기", elem_classes=["advanced-btn"])
                        
                        with gr.Column():
                            gr.Markdown("### 🛡️ 에러 관리")
                            error_stats_btn = gr.Button("📈 에러 통계", elem_classes=["advanced-btn"])
                            validation_stats_btn = gr.Button("✅ 검증 통계", elem_classes=["advanced-btn"])
                            clear_history_btn = gr.Button("🗑️ 히스토리 초기화", variant="secondary")
                    
                    system_logs_display = gr.Textbox(
                        label="시스템 로그",
                        lines=10,
                        interactive=False,
                        visible=False
                    )
            
            # 향후 기능 안내
            gr.Markdown(
                """
                ---
                ### 🚀 Phase 3+ 예정 기능
                - **AI 견적서 생성** (Claude API 연동)
                - **PDF 견적서 출력** 
                - **팀 협업 기능** (공유 및 댓글)
                - **프로젝트 템플릿**
                - **자동 백업 및 버전 관리**
                """ + ("""
                - **ConfigManager**: 설정 관리 전담
                - **CacheManager**: 캐싱 시스템
                - **SecurityManager**: 보안 관리
                - **MetricsManager**: 성능 메트릭
                - **NotificationManager**: 알림 시스템
                """ if ADVANCED_FEATURES else """
                
                **고급 기능 활성화 방법:**
                1. pip install Pillow
                2. 고급 매니저 파일들 추가
                3. logs/ 디렉토리 생성
                """) + """
                """,
                elem_classes=["container"]
            )
            
            # 이벤트 핸들러 연결
            
            # 기본 세션 관리
            new_session_btn.click(
                fn=self.handle_new_session,
                inputs=[project_name_input, session_state],
                outputs=[session_state, session_status, project_name_input, session_dropdown]
            )
            
            load_session_btn.click(
                fn=self.handle_load_session,
                inputs=[session_dropdown, session_state],
                outputs=[session_state, session_status, ocr_results_json, mapping_results_json, scope_input]
            ).then(
                fn=lambda x, y, z: (gr.update(visible=bool(x)), gr.update(visible=bool(y))),
                inputs=[ocr_results_json, mapping_results_json, session_state],
                outputs=[ocr_results_json, mapping_results_json]
            )
            
            # 처리 작업
            process_images_btn.click(
                fn=self.handle_image_processing,
                inputs=[image_upload, session_state],
                outputs=[ocr_results_json, ocr_status, ocr_summary_html, session_state]
            ).then(
                fn=lambda x, y, z: (gr.update(visible=bool(x)), gr.update(visible=bool(z))),
                inputs=[ocr_results_json, ocr_status, ocr_summary_html],
                outputs=[ocr_results_json, ocr_summary_html]
            )
            
            process_mapping_btn.click(
                fn=self.handle_mapping_processing,
                inputs=[scope_input, session_state],
                outputs=[mapping_results_json, mapping_status, mapping_summary_html, session_state]
            ).then(
                fn=lambda x, y, z: (gr.update(visible=bool(x)), gr.update(visible=bool(z))),
                inputs=[mapping_results_json, mapping_status, mapping_summary_html],
                outputs=[mapping_results_json, mapping_summary_html]
            )
            
            # 세션 관리
            clear_session_btn.click(
                fn=self.handle_clear_session,
                inputs=[session_state],
                outputs=[ocr_results_json, ocr_status, ocr_summary_html, 
                        mapping_results_json, mapping_status, mapping_summary_html, session_state]
            )
            
            refresh_sessions_btn.click(
                fn=self.handle_refresh_sessions,
                outputs=session_dropdown
            )
            
            refresh_all_btn.click(
                fn=self.handle_get_all_results,
                inputs=[session_state],
                outputs=all_results_json
            )
            
            # 고급 기능 핸들러
            if ADVANCED_FEATURES:
                # 시스템 제어
                debug_toggle_btn.click(
                    fn=self.handle_toggle_debug_mode,
                    outputs=system_info_display
                )
                
                system_status_btn.click(
                    fn=self.handle_get_system_status,
                    outputs=system_info_display
                ).then(
                    fn=lambda x: json.dumps(x, indent=2, ensure_ascii=False),
                    inputs=[system_info_display],
                    outputs=system_info_display
                )
                
                logs_btn.click(
                    fn=lambda: self.handle_get_recent_logs("app", 20),
                    outputs=system_info_display
                )
                
                # 로그 보기
                view_logs_btn.click(
                    fn=self.handle_get_recent_logs,
                    inputs=[log_type_dropdown, log_lines_slider],
                    outputs=system_logs_display
                ).then(
                    fn=lambda: gr.update(visible=True),
                    outputs=system_logs_display
                )
                
                # 통계 보기
                error_stats_btn.click(
                    fn=lambda: json.dumps(self.error_manager.get_error_statistics(), indent=2, ensure_ascii=False),
                    outputs=system_info_display
                )
                
                validation_stats_btn.click(
                    fn=lambda: json.dumps(self.validation_manager.get_validation_statistics(), indent=2, ensure_ascii=False),
                    outputs=system_info_display
                )
                
                # 히스토리 초기화
                clear_history_btn.click(
                    fn=lambda: [
                        self.error_manager.clear_error_history(),
                        self.validation_manager.clear_validation_history(),
                        "✅ 히스토리가 초기화되었습니다."
                    ][-1],
                    outputs=system_info_display
                )
        
        return interface

def main():
    """메인 실행 함수"""
    print("🏗️ Construction Estimator - 업무용 버전 시작...")
    
    try:
        # 환경 설정 확인
        if not os.path.exists('.env'):
            print("⚠️ .env 파일이 없습니다.")
            print("💡 .env.template을 참고하여 .env 파일을 생성하고 ANTHROPIC_API_KEY를 설정하세요.")
        
        # 필수 디렉토리 생성
        os.makedirs("data/sessions", exist_ok=True)
        if ADVANCED_FEATURES:
            os.makedirs("logs", exist_ok=True)
        
        # 앱 인스턴스 생성
        print("📦 애플리케이션 초기화 중...")
        app = BusinessEstimatorApp()
        
        # 인터페이스 생성
        print("🎨 인터페이스 생성 중...")
        interface = app.create_interface()
        
        # 서버 시작 안내
        print("\n" + "="*70)
        print("✅ 업무용 서버가 성공적으로 시작되었습니다!")
        print("")
        print("📱 브라우저에서 다음 주소를 열어주세요:")
        print("   http://127.0.0.1:7860")
        print("   http://localhost:7860")
        print("")
        print("🚀 기능 상태:")
        print("   ✅ SessionManager: 세션 생성/로드/관리")
        print("   ✅ ProcessingManager: OCR/매핑 처리")
        print("   ✅ UIHelper: HTML 생성/UI 헬퍼")
        if ADVANCED_FEATURES:
            print("   ✅ LoggingManager: 구조화된 로깅 시스템")
            print("   ✅ ErrorManager: 지능형 에러 처리")
            print("   ✅ ValidationManager: 포괄적 검증 시스템")
            print("   ✅ 실시간 성능 모니터링")
            print("   ✅ 자동 에러 복구 제안")
            print("   ✅ 시스템 상태 실시간 조회")
        else:
            print("   ⚠️ 고급 매니저 로드 실패 - 기본 기능만 사용")
            print("   💡 고급 기능 활성화: pip install Pillow")
        print("")
        print("💼 업무용 기능:")
        print("   ✅ 다중 사용자 동시 접속 가능")
        print("   ✅ 세션별 독립적인 데이터 관리")
        print("   ✅ 프로젝트별 자동 저장/복구")
        print("   ✅ 브라우저 새로고침해도 데이터 보존")
        print("")
        print("🔧 시스템 아키텍처:")
        print("   📁 managers/session_manager.py")
        print("   📁 managers/processing_manager.py")
        print("   📁 managers/ui_helper.py")
        if ADVANCED_FEATURES:
            print("   📁 managers/logging_manager.py")
            print("   📁 managers/error_manager.py")
            print("   📁 managers/validation_manager.py")
        print("   📁 app.py (현재 파일)")
        print("")
        print("💡 사용법:")
        print("   1. 프로젝트 이름 입력 → 새 세션 시작")
        print("   2. 측량 사진 업로드 → OCR 처리")
        print("   3. 작업 범위 입력 → 데이터 매핑")
        print("   4. 기존 세션 로드로 이전 작업 이어서 하기")
        print("")
        print("🛑 서버 종료: Ctrl+C")
        print("="*70)
        
        # 서버 시작
        interface.launch(
            share=config.GRADIO_SHARE,
            debug=config.GRADIO_DEBUG,
            server_name="0.0.0.0",
            server_port=7860,
            show_error=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 업무용 서버가 종료되었습니다.")
        if ADVANCED_FEATURES:
            try:
                # 로그 정리
                print("📊 서버 종료 로그 기록 중...")
                app.logging_manager.log_app_activity("서버 정상 종료")
                app.logging_manager.cleanup_old_logs()
            except:
                pass
        logger.info("서버가 정상적으로 종료되었습니다.")
        
    except ImportError as e:
        print(f"\n❌ 모듈 import 실패: {e}")
        print("\n해결 방법:")
        print("1. 기본 매니저 파일들이 존재하는지 확인:")
        print("   - managers/__init__.py")
        print("   - managers/session_manager.py")
        print("   - managers/processing_manager.py")
        print("   - managers/ui_helper.py")
        print("2. 고급 기능 사용을 위해 Pillow 라이브러리 설치: pip install Pillow")
        print("3. managers/__init__.py 파일 업데이트")
        print("4. 가상환경이 활성화되었는지 확인")
        print("5. 의존성이 설치되었는지 확인: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        print("\n🔍 상세 오류 정보:")
        print(traceback.format_exc())
        print("\n해결 방법:")
        if ADVANCED_FEATURES:
            print("1. logs/ 디렉토리에서 상세 로그 확인")
        else:
            print("1. app.log 파일에서 상세 로그 확인")
        print("2. 매니저 클래스들이 올바르게 구현되었는지 확인")
        print("3. 필요한 의존성들이 모두 설치되었는지 확인")
        print("4. 권한 문제가 없는지 확인")
        logger.error(f"애플리케이션 시작 실패: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()