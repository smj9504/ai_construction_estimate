"""
이벤트 핸들러 정의
Gradio 인터페이스와 비즈니스 로직을 연결하는 이벤트 핸들러들을 정의합니다.
"""

import gradio as gr
import json
from typing import Tuple, Dict, Any, List
import logging

from services.estimator_service import get_estimator_service
from .components import HTMLGenerators

logger = logging.getLogger(__name__)

class SessionHandlers:
    """세션 관련 이벤트 핸들러"""
    
    def __init__(self):
        self.estimator_service = get_estimator_service()
        self.html_generator = HTMLGenerators()
    
    def handle_new_session(self) -> Tuple[str, str]:
        """새 세션 생성 핸들러"""
        try:
            success, session_id, message = self.estimator_service.create_new_session()
            
            if success:
                # 세션 상태 업데이트
                status = self.estimator_service.get_session_status()
                return status['message'], message
            else:
                return message, message
                
        except Exception as e:
            error_msg = f"❌ 세션 생성 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return error_msg, error_msg
    
    def handle_session_status_update(self) -> str:
        """세션 상태 업데이트 핸들러"""
        try:
            status = self.estimator_service.get_session_status()
            return status['message']
        except Exception as e:
            error_msg = f"❌ 상태 업데이트 실패: {str(e)}"
            logger.error(error_msg)
            return error_msg

class OCRHandlers:
    """OCR 관련 이벤트 핸들러"""
    
    def __init__(self):
        self.estimator_service = get_estimator_service()
        self.html_generator = HTMLGenerators()
    
    def handle_ocr_processing(self, uploaded_files, progress=gr.Progress()) -> Tuple[str, str, str]:
        """OCR 처리 핸들러"""
        try:
            # 진행률 업데이트
            progress(0.1, desc="이미지 저장 중...")
            
            # OCR 처리 실행
            success, ocr_results, status_msg, summary = self.estimator_service.process_images_ocr(uploaded_files)
            
            if success:
                progress(0.9, desc="결과 포맷팅 중...")
                
                # HTML 요약 생성
                summary_html = self.html_generator.create_ocr_summary_html(ocr_results)
                
                # JSON 결과 포맷팅
                formatted_json = json.dumps(ocr_results, indent=2, ensure_ascii=False)
                
                progress(1.0, desc="완료!")
                
                return formatted_json, status_msg, summary_html
            else:
                return "", status_msg, ""
                
        except Exception as e:
            error_msg = f"❌ OCR 처리 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, ""
    
    def handle_ocr_results_visibility(self, json_data: str, status_msg: str, html_data: str) -> Tuple[gr.update, gr.update]:
        """OCR 결과 표시 여부 결정"""
        show_results = bool(json_data and html_data)
        return (
            gr.update(visible=show_results),  # JSON 결과
            gr.update(visible=show_results)   # HTML 요약
        )

class MappingHandlers:
    """데이터 매핑 관련 이벤트 핸들러"""
    
    def __init__(self):
        self.estimator_service = get_estimator_service()
        self.html_generator = HTMLGenerators()
    
    def handle_mapping_processing(self, scope_text: str, progress=gr.Progress()) -> Tuple[str, str, str]:
        """데이터 매핑 처리 핸들러"""
        try:
            # 진행률 업데이트
            progress(0.2, desc="작업 범위 파싱 중...")
            
            # 매핑 처리 실행
            success, mapping_results, status_msg, summary = self.estimator_service.process_scope_mapping(scope_text)
            
            if success:
                progress(0.8, desc="결과 포맷팅 중...")
                
                # HTML 요약 생성
                summary_html = self.html_generator.create_mapping_summary_html(mapping_results)
                
                # JSON 결과 포맷팅
                formatted_json = json.dumps(mapping_results, indent=2, ensure_ascii=False)
                
                progress(1.0, desc="완료!")
                
                return formatted_json, status_msg, summary_html
            else:
                return "", status_msg, ""
                
        except Exception as e:
            error_msg = f"❌ 매핑 처리 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, ""
    
    def handle_mapping_results_visibility(self, json_data: str, status_msg: str, html_data: str) -> Tuple[gr.update, gr.update]:
        """매핑 결과 표시 여부 결정"""
        show_results = bool(json_data and html_data)
        return (
            gr.update(visible=show_results),  # JSON 결과
            gr.update(visible=show_results)   # HTML 요약
        )

class ResultsHandlers:
    """결과 관련 이벤트 핸들러"""
    
    def __init__(self):
        self.estimator_service = get_estimator_service()
    
    def handle_refresh_results(self) -> Dict:
        """결과 새로고침 핸들러"""
        try:
            return self.estimator_service.get_all_results()
        except Exception as e:
            logger.error(f"결과 새로고침 실패: {str(e)}")
            return {"error": f"결과 새로고침 실패: {str(e)}"}
    
    def handle_export_results(self) -> Tuple[str, str]:
        """결과 내보내기 핸들러"""
        try:
            success, file_path, message = self.estimator_service.export_results('json')
            
            if success:
                return message, file_path
            else:
                return message, ""
                
        except Exception as e:
            error_msg = f"❌ 결과 내보내기 실패: {str(e)}"
            logger.error(error_msg)
            return error_msg, ""

class ValidationHandlers:
    """입력 검증 관련 핸들러"""
    
    @staticmethod
    def validate_uploaded_files(files) -> Tuple[bool, str]:
        """업로드된 파일 검증"""
        if not files:
            return False, "❌ 업로드할 파일을 선택하세요."
        
        if len(files) > 20:
            return False, "❌ 한 번에 최대 20개 파일까지 처리 가능합니다."
        
        # 파일 형식 검증
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        for file in files:
            if hasattr(file, 'name'):
                filename = file.name.lower()
                if not any(filename.endswith(ext) for ext in allowed_extensions):
                    return False, f"❌ 지원하지 않는 파일 형식: {filename}"
        
        return True, "✅ 파일 검증 통과"
    
    @staticmethod
    def validate_scope_text(scope_text: str) -> Tuple[bool, str]:
        """작업 범위 텍스트 검증"""
        if not scope_text or not scope_text.strip():
            return False, "❌ 작업 범위를 입력하세요."
        
        lines = [line.strip() for line in scope_text.split('\n') if line.strip()]
        if len(lines) == 0:
            return False, "❌ 유효한 작업 범위가 없습니다."
        
        if len(lines) > 50:
            return False, "❌ 작업 범위는 최대 50개까지 입력 가능합니다."
        
        return True, f"✅ 작업 범위 검증 통과 ({len(lines)}개 항목)"

class EventHandlerRegistry:
    """이벤트 핸들러 레지스트리"""
    
    def __init__(self):
        self.session = SessionHandlers()
        self.ocr = OCRHandlers()
        self.mapping = MappingHandlers()
        self.results = ResultsHandlers()
        self.validation = ValidationHandlers()
    
    def get_session_handlers(self) -> SessionHandlers:
        """세션 핸들러 반환"""
        return self.session
    
    def get_ocr_handlers(self) -> OCRHandlers:
        """OCR 핸들러 반환"""
        return self.ocr
    
    def get_mapping_handlers(self) -> MappingHandlers:
        """매핑 핸들러 반환"""
        return self.mapping
    
    def get_results_handlers(self) -> ResultsHandlers:
        """결과 핸들러 반환"""
        return self.results
    
    def get_validation_handlers(self) -> ValidationHandlers:
        """검증 핸들러 반환"""
        return self.validation

# 편의 함수들
def create_combined_ocr_handler(uploaded_files, progress=gr.Progress()):
    """OCR 처리 + 상태 업데이트 결합 핸들러"""
    handler_registry = EventHandlerRegistry()
    
    # 파일 검증
    valid, msg = handler_registry.validation.validate_uploaded_files(uploaded_files)
    if not valid:
        return "", msg, ""
    
    # OCR 처리
    return handler_registry.ocr.handle_ocr_processing(uploaded_files, progress)

def create_combined_mapping_handler(scope_text: str, progress=gr.Progress()):
    """매핑 처리 + 상태 업데이트 결합 핸들러"""
    handler_registry = EventHandlerRegistry()
    
    # 텍스트 검증
    valid, msg = handler_registry.validation.validate_scope_text(scope_text)
    if not valid:
        return "", msg, ""
    
    # 매핑 처리
    return handler_registry.mapping.handle_mapping_processing(scope_text, progress)

def create_session_update_chain():
    """세션 상태 업데이트 체인 생성"""
    handler_registry = EventHandlerRegistry()
    return handler_registry.session.handle_session_status_update

# 전역 핸들러 레지스트리 인스턴스
handler_registry = EventHandlerRegistry()

# 자주 사용되는 핸들러들을 편의 함수로 노출
def get_session_handlers() -> SessionHandlers:
    return handler_registry.session

def get_ocr_handlers() -> OCRHandlers:
    return handler_registry.ocr

def get_mapping_handlers() -> MappingHandlers:
    return handler_registry.mapping

def get_results_handlers() -> ResultsHandlers:
    return handler_registry.results

def get_validation_handlers() -> ValidationHandlers:
    return handler_registry.validation