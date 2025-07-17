"""
메인 Gradio 인터페이스
모든 UI 컴포넌트와 이벤트 핸들러를 결합하여 완전한 인터페이스를 구성합니다.
"""

import gradio as gr
from typing import Dict, Any
import logging

from .styles import get_full_css
from .components import component_factory
from .handlers import (
    get_session_handlers, 
    get_ocr_handlers, 
    get_mapping_handlers, 
    get_results_handlers,
    create_combined_ocr_handler,
    create_combined_mapping_handler,
    create_session_update_chain
)
from services.estimator_service import get_estimator_service

logger = logging.getLogger(__name__)

class ConstructionEstimatorInterface:
    """건축 견적서 생성기 메인 인터페이스"""
    
    def __init__(self):
        """인터페이스 초기화"""
        logger.info("ConstructionEstimatorInterface 초기화 시작")
        
        # 서비스 및 핸들러 초기화
        self.estimator_service = get_estimator_service()
        self.session_handlers = get_session_handlers()
        self.ocr_handlers = get_ocr_handlers()
        self.mapping_handlers = get_mapping_handlers()
        self.results_handlers = get_results_handlers()
        
        # 컴포넌트들
        self.components = {}
        
        logger.info("ConstructionEstimatorInterface 초기화 완료")
    
    def create_interface(self) -> gr.Blocks:
        """완전한 Gradio 인터페이스 생성"""
        logger.info("Gradio 인터페이스 생성 시작")
        
        with gr.Blocks(
            title="🏗️ Construction Estimator - Phase 1 MVP",
            theme=gr.themes.Soft(),
            css=get_full_css()
        ) as interface:
            
            # 설정 문제 경고 (있는 경우)
            self._create_config_warning()
            
            # 헤더 섹션
            self._create_header_section()
            
            # 메인 탭들
            self._create_main_tabs()
            
            # 이벤트 핸들러 연결
            self._connect_event_handlers()
        
        logger.info("Gradio 인터페이스 생성 완료")
        return interface
    
    def _create_config_warning(self):
        """설정 문제 경고 표시"""
        if self.estimator_service.has_config_issues():
            issues = self.estimator_service.get_config_issues()
            warning_html = component_factory.html.create_config_warning_html(issues)
            gr.HTML(warning_html)
    
    def _create_header_section(self):
        """헤더 섹션 생성"""
        # 메인 헤더
        self.components['main_header'] = component_factory.header.create_main_header()
        
        # 세션 상태 및 새 세션 버튼
        with gr.Row():
            with gr.Column(scale=3):
                self.components['session_status'] = component_factory.header.create_session_status()
            with gr.Column(scale=1):
                self.components['new_session_btn'] = component_factory.header.create_new_session_button()
    
    def _create_main_tabs(self):
        """메인 탭들 생성"""
        with gr.Tabs() as tabs:
            self.components['tabs'] = tabs
            
            # Tab 1: OCR 처리
            self._create_ocr_tab()
            
            # Tab 2: 데이터 매핑
            self._create_mapping_tab()
            
            # Tab 3: 결과 확인
            self._create_results_tab()
    
    def _create_ocr_tab(self):
        """OCR 처리 탭 생성"""
        with gr.Tab("1️⃣ 이미지 업로드 & OCR") as ocr_tab:
            self.components['ocr_tab'] = ocr_tab
            
            gr.Markdown("### 📸 측량 사진 업로드 및 OCR 처리")
            
            with gr.Row():
                # 왼쪽: 업로드 영역
                with gr.Column(scale=1):
                    self.components['image_upload'] = component_factory.ocr.create_image_upload()
                    self.components['upload_instructions'] = component_factory.ocr.create_upload_instructions()
                    self.components['process_ocr_btn'] = component_factory.ocr.create_process_button()
                
                # 오른쪽: 상태 표시
                with gr.Column(scale=1):
                    self.components['ocr_status'] = component_factory.ocr.create_status_display()
            
            # OCR 결과 표시
            with gr.Row():
                with gr.Column():
                    self.components['ocr_summary_html'], self.components['ocr_detailed_json'] = component_factory.ocr.create_results_display()
            
            # 상세 결과 (접을 수 있는 섹션)
            with gr.Accordion("📄 상세 OCR 결과 (JSON)", open=False):
                # ocr_detailed_json은 이미 위에서 생성됨
                pass
    
    def _create_mapping_tab(self):
        """데이터 매핑 탭 생성"""
        with gr.Tab("2️⃣ 작업 범위 & 데이터 매핑") as mapping_tab:
            self.components['mapping_tab'] = mapping_tab
            
            gr.Markdown("### 📋 작업 범위 입력 및 측정 데이터 매핑")
            
            with gr.Row():
                # 왼쪽: 작업 범위 입력
                with gr.Column(scale=1):
                    self.components['scope_input'] = component_factory.mapping.create_scope_input()
                    self.components['scope_instructions'] = component_factory.mapping.create_scope_instructions()
                    self.components['process_mapping_btn'] = component_factory.mapping.create_mapping_button()
                
                # 오른쪽: 상태 표시
                with gr.Column(scale=1):
                    self.components['mapping_status'] = component_factory.mapping.create_mapping_status()
            
            # 매핑 결과 표시
            with gr.Row():
                with gr.Column():
                    self.components['mapping_summary_html'], self.components['mapping_detailed_json'] = component_factory.mapping.create_mapping_results()
            
            # 상세 결과 (접을 수 있는 섹션)
            with gr.Accordion("🔗 상세 매핑 결과 (JSON)", open=False):
                # mapping_detailed_json은 이미 위에서 생성됨
                pass
    
    def _create_results_tab(self):
        """결과 확인 탭 생성"""
        with gr.Tab("3️⃣ 결과 확인") as results_tab:
            self.components['results_tab'] = results_tab
            
            gr.Markdown("### 📈 전체 처리 결과 확인")
            
            # 액션 버튼들
            with gr.Row():
                self.components['refresh_btn'], self.components['export_btn'] = component_factory.results.create_action_buttons()
            
            # 최종 결과 표시
            self.components['final_results'] = component_factory.results.create_final_results_display()
            
            # 향후 기능 안내
            self.components['future_features'] = component_factory.results.create_future_features()
    
    def _connect_event_handlers(self):
        """이벤트 핸들러들을 UI 컴포넌트에 연결"""
        logger.info("이벤트 핸들러 연결 시작")
        
        # 세션 관련 이벤트
        self._connect_session_events()
        
        # OCR 관련 이벤트
        self._connect_ocr_events()
        
        # 매핑 관련 이벤트
        self._connect_mapping_events()
        
        # 결과 관련 이벤트
        self._connect_results_events()
        
        logger.info("이벤트 핸들러 연결 완료")
    
    def _connect_session_events(self):
        """세션 관련 이벤트 연결"""
        # 새 세션 생성
        self.components['new_session_btn'].click(
            fn=self.session_handlers.handle_new_session,
            outputs=[
                self.components['session_status'],
                gr.Textbox(visible=False)  # 더미 출력
            ]
        ).then(
            fn=self.session_handlers.handle_session_status_update,
            outputs=self.components['session_status']
        )
    
    def _connect_ocr_events(self):
        """OCR 관련 이벤트 연결"""
        # OCR 처리
        self.components['process_ocr_btn'].click(
            fn=create_combined_ocr_handler,
            inputs=self.components['image_upload'],
            outputs=[
                self.components['ocr_detailed_json'],
                self.components['ocr_status'],
                self.components['ocr_summary_html']
            ]
        ).then(
            # 결과 표시 여부 결정
            fn=self.ocr_handlers.handle_ocr_results_visibility,
            inputs=[
                self.components['ocr_detailed_json'],
                self.components['ocr_status'],
                self.components['ocr_summary_html']
            ],
            outputs=[
                self.components['ocr_detailed_json'],
                self.components['ocr_summary_html']
            ]
        ).then(
            # 세션 상태 업데이트
            fn=self.session_handlers.handle_session_status_update,
            outputs=self.components['session_status']
        )
    
    def _connect_mapping_events(self):
        """매핑 관련 이벤트 연결"""
        # 데이터 매핑 처리
        self.components['process_mapping_btn'].click(
            fn=create_combined_mapping_handler,
            inputs=self.components['scope_input'],
            outputs=[
                self.components['mapping_detailed_json'],
                self.components['mapping_status'],
                self.components['mapping_summary_html']
            ]
        ).then(
            # 결과 표시 여부 결정
            fn=self.mapping_handlers.handle_mapping_results_visibility,
            inputs=[
                self.components['mapping_detailed_json'],
                self.components['mapping_status'],
                self.components['mapping_summary_html']
            ],
            outputs=[
                self.components['mapping_detailed_json'],
                self.components['mapping_summary_html']
            ]
        ).then(
            # 세션 상태 업데이트
            fn=self.session_handlers.handle_session_status_update,
            outputs=self.components['session_status']
        )
    
    def _connect_results_events(self):
        """결과 관련 이벤트 연결"""
        # 결과 새로고침
        self.components['refresh_btn'].click(
            fn=self.results_handlers.handle_refresh_results,
            outputs=self.components['final_results']
        )
        
        # 결과 내보내기 (향후 구현)
        self.components['export_btn'].click(
            fn=self.results_handlers.handle_export_results,
            outputs=[
                gr.Textbox(visible=False),  # 메시지 (현재는 표시 안함)
                gr.Textbox(visible=False)   # 파일 경로 (현재는 표시 안함)
            ]
        )
    
    def get_components(self) -> Dict[str, Any]:
        """생성된 컴포넌트들 반환"""
        return self.components.copy()

# 편의 함수들
def create_interface() -> gr.Blocks:
    """인터페이스 생성 편의 함수"""
    interface_manager = ConstructionEstimatorInterface()
    return interface_manager.create_interface()

def create_interface_with_components() -> tuple[gr.Blocks, Dict[str, Any]]:
    """인터페이스와 컴포넌트들을 함께 반환"""
    interface_manager = ConstructionEstimatorInterface()
    interface = interface_manager.create_interface()
    components = interface_manager.get_components()
    return interface, components

# 전역 인터페이스 관리자 (필요한 경우)
_interface_manager = None

def get_interface_manager() -> ConstructionEstimatorInterface:
    """전역 인터페이스 관리자 반환"""
    global _interface_manager
    if _interface_manager is None:
        _interface_manager = ConstructionEstimatorInterface()
    return _interface_manager

def reset_interface_manager():
    """인터페이스 관리자 재설정"""
    global _interface_manager
    _interface_manager = None