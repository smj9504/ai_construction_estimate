"""
UI 컴포넌트 정의
Gradio 인터페이스의 재사용 가능한 컴포넌트들을 정의합니다.
"""

import gradio as gr
from typing import Dict, List, Optional
from .styles import get_component_class

class HeaderComponents:
    """헤더 관련 컴포넌트들"""
    
    @staticmethod
    def create_main_header():
        """메인 헤더 생성"""
        return gr.Markdown(
            """
            # 🏗️ Construction Estimator - Phase 1 MVP
            
            **작업 범위 입력 + 측량 사진 업로드 → 데이터 매핑 시스템**
            
            이 시스템은 작업범위 텍스트와 측량 사진을 분석하여 자동으로 데이터를 매핑합니다.
            
            ---
            """,
            elem_classes=["container"]
        )
    
    @staticmethod
    def create_session_status():
        """세션 상태 표시 컴포넌트"""
        return gr.Textbox(
            label="📊 세션 상태",
            value="❌ 활성 세션 없음\n새 세션을 시작하세요.",
            interactive=False,
            max_lines=6,
            elem_classes=[get_component_class('status_box')]
        )
    
    @staticmethod
    def create_new_session_button():
        """새 세션 버튼"""
        return gr.Button(
            "🆕 새 세션 시작", 
            variant="primary",
            size="lg",
            elem_classes=[get_component_class('primary_button')]
        )

class OCRComponents:
    """OCR 관련 컴포넌트들"""
    
    @staticmethod
    def create_image_upload():
        """이미지 업로드 컴포넌트"""
        return gr.File(
            label="📁 측량 사진들 업로드 (여러 파일 가능)",
            file_count="multiple",
            file_types=["image"],
            elem_classes=[get_component_class('upload_area')]
        )
    
    @staticmethod
    def create_upload_instructions():
        """업로드 안내 텍스트"""
        return gr.Markdown(
            """
            **지원 형식:** PNG, JPG, JPEG, BMP, TIFF  
            **최대 크기:** 10MB per file  
            **권장:** 측량 도면, 스케치, 측정값이 적힌 사진들
            """
        )
    
    @staticmethod
    def create_process_button():
        """OCR 처리 버튼"""
        return gr.Button(
            "🔍 OCR 처리 시작", 
            variant="primary",
            size="lg",
            elem_classes=[get_component_class('primary_button')]
        )
    
    @staticmethod
    def create_status_display():
        """OCR 상태 표시"""
        return gr.Textbox(
            label="처리 상태",
            placeholder="이미지를 업로드하고 OCR 처리를 시작하세요...",
            max_lines=8,
            interactive=False
        )
    
    @staticmethod
    def create_results_display():
        """OCR 결과 표시"""
        summary_html = gr.HTML(
            label="📊 OCR 결과 요약",
            visible=False,
            elem_classes=[get_component_class('summary_card')]
        )
        
        detailed_json = gr.JSON(
            label="OCR 결과 데이터",
            visible=False
        )
        
        return summary_html, detailed_json

class MappingComponents:
    """데이터 매핑 관련 컴포넌트들"""
    
    @staticmethod
    def create_scope_input():
        """작업 범위 입력 컴포넌트"""
        return gr.Textbox(
            label="📝 작업 범위 입력",
            placeholder="""예시:
Kitchen - cabinet replacement and countertop
Bathroom - tile work and vanity
Living room - hardwood flooring
Bedroom 1 - carpet and paint
Bedroom 2 - flooring upgrade""",
            lines=10,
            max_lines=20
        )
    
    @staticmethod
    def create_scope_instructions():
        """작업 범위 입력 안내"""
        return gr.Markdown(
            """
            **입력 형식:**  
            `방 이름 - 작업 내용`  
            각 줄에 하나씩 입력하세요.
            """
        )
    
    @staticmethod
    def create_mapping_button():
        """매핑 처리 버튼"""
        return gr.Button(
            "🔗 데이터 매핑 시작",
            variant="primary",
            size="lg",
            elem_classes=[get_component_class('primary_button')]
        )
    
    @staticmethod
    def create_mapping_status():
        """매핑 상태 표시"""
        return gr.Textbox(
            label="매핑 상태",
            placeholder="작업 범위를 입력하고 데이터 매핑을 시작하세요...",
            max_lines=10,
            interactive=False
        )
    
    @staticmethod
    def create_mapping_results():
        """매핑 결과 표시"""
        summary_html = gr.HTML(
            label="📊 매핑 결과 요약",
            visible=False,
            elem_classes=[get_component_class('summary_card')]
        )
        
        detailed_json = gr.JSON(
            label="매핑 결과 데이터",
            visible=False
        )
        
        return summary_html, detailed_json

class ResultComponents:
    """결과 관련 컴포넌트들"""
    
    @staticmethod
    def create_action_buttons():
        """결과 탭 액션 버튼들"""
        refresh_btn = gr.Button(
            "🔄 결과 새로고침", 
            variant="secondary",
            size="lg",
            elem_classes=[get_component_class('secondary_button')]
        )
        
        export_btn = gr.Button(
            "📁 결과 내보내기", 
            variant="secondary",
            size="lg",
            elem_classes=[get_component_class('secondary_button')]
        )
        
        return refresh_btn, export_btn
    
    @staticmethod
    def create_final_results_display():
        """최종 결과 표시"""
        return gr.JSON(
            label="📊 전체 처리 결과",
            visible=True
        )
    
    @staticmethod
    def create_future_features():
        """향후 기능 안내"""
        return gr.Markdown(
            """
            ---
            ### 🚀 향후 기능 (Phase 2+)
            - **AI 견적서 생성** (Claude API 연동)
            - **PDF 견적서 출력**
            - **Kitchen Cabinet 특화 분석**
            - **시장 가격 자동 조회**
            - **프로젝트 타임라인 생성**
            """,
            elem_classes=[get_component_class('card')]
        )

class UtilityComponents:
    """유틸리티 컴포넌트들"""
    
    @staticmethod
    def create_progress_bar():
        """진행률 표시 바"""
        return gr.Progress()
    
    @staticmethod
    def create_error_display():
        """에러 메시지 표시"""
        return gr.HTML(
            visible=False,
            elem_classes=[get_component_class('error_message')]
        )
    
    @staticmethod
    def create_success_display():
        """성공 메시지 표시"""
        return gr.HTML(
            visible=False,
            elem_classes=[get_component_class('success_message')]
        )
    
    @staticmethod
    def create_accordion(title: str, open: bool = False):
        """접을 수 있는 섹션"""
        return gr.Accordion(title, open=open)
    
    @staticmethod
    def create_tab(title: str):
        """탭 생성"""
        return gr.Tab(title)

class HTMLGenerators:
    """HTML 생성 유틸리티"""
    
    @staticmethod
    def create_ocr_summary_html(ocr_results: Dict) -> str:
        """OCR 결과 요약 HTML 생성"""
        html = "<div class='summary-card'>"
        html += "<h3 style='color: #2e8b57; margin-top: 0;'>📊 OCR 처리 결과 요약</h3>"
        
        for image_key, result in ocr_results.items():
            if 'error' in result:
                html += f"<div class='mapping-error'>"
                html += f"<strong>❌ {image_key}</strong><br>"
                html += f"<span>오류: {result['error']}</span>"
                html += "</div>"
            else:
                summary = result.get('summary', {})
                measurements = result.get('measurements', [])
                
                # 측정값 유형별 개수 계산
                measurement_types = {}
                for m in measurements:
                    if m.get('pattern_type') != 'text':
                        pattern_type = m.get('pattern_type', 'unknown')
                        measurement_types[pattern_type] = measurement_types.get(pattern_type, 0) + 1
                
                html += f"<div class='mapping-success'>"
                html += f"<strong>✅ {image_key}</strong><br>"
                html += f"📄 추출된 텍스트: {summary.get('total_texts', 0)}개<br>"
                html += f"📏 측정값: {summary.get('measurement_count', 0)}개<br>"
                html += f"📝 일반 텍스트: {summary.get('text_count', 0)}개"
                
                if measurement_types:
                    html += "<br><small>측정값 유형: "
                    html += ", ".join([f"{k}({v})" for k, v in measurement_types.items()])
                    html += "</small>"
                
                html += "</div>"
        
        html += "</div>"
        return html
    
    @staticmethod
    def create_mapping_summary_html(mapping_result: Dict) -> str:
        """매핑 결과 요약 HTML 생성"""
        html = "<div class='summary-card'>"
        html += "<h3 style='color: #2e8b57; margin-top: 0;'>🔗 데이터 매핑 결과</h3>"
        
        # 성공적인 매핑들
        mappings = mapping_result.get('mappings', [])
        if mappings:
            html += "<h4 style='color: #28a745; margin-bottom: 10px;'>✅ 성공적인 매핑</h4>"
            for i, mapping in enumerate(mappings, 1):
                work_scope = mapping['work_scope']
                measurements = mapping['measurements']
                confidence = mapping['match_confidence']
                
                confidence_class = "confidence-high" if confidence > 0.7 else "confidence-medium" if confidence > 0.4 else "confidence-low"
                confidence_text = "높음" if confidence > 0.7 else "보통" if confidence > 0.4 else "낮음"
                
                html += f"<div class='summary-item'>"
                html += f"<strong>{i}. {work_scope['room_name']}</strong> "
                html += f"<span style='color: #6c757d; font-size: 0.9em;'>({work_scope['room_type']})</span><br>"
                html += f"<span style='color: #6c757d;'>📋 작업: {work_scope['work_description']}</span><br>"
                html += f"<span style='color: #6c757d;'>📏 측정값: {len(measurements)}개</span> "
                html += f"<span class='{confidence_class}'>"
                html += f"신뢰도: {confidence_text} ({confidence:.0%})</span>"
                html += "</div>"
        
        # 미매핑 측정값들
        unmatched = mapping_result.get('unmatched_measurements', [])
        if unmatched:
            html += "<h4 style='color: #ffc107; margin: 20px 0 10px 0;'>⚠️ 매핑되지 않은 측정값</h4>"
            for unmatch in unmatched:
                room_id = unmatch['room_identifier']
                measurements = unmatch['measurements']
                html += f"<div class='mapping-warning'>"
                html += f"<strong>📍 {room_id}</strong><br>"
                html += f"📏 측정값: {len(measurements)}개"
                html += "</div>"
        
        # 전체 요약
        summary = mapping_result.get('summary', {})
        html += "<div class='summary-item' style='background: #e9ecef;'>"
        html += "<strong>📊 전체 요약</strong><br>"
        html += f"작업 범위: {summary.get('total_work_scopes', 0)}개 | "
        html += f"측정 데이터: {summary.get('total_measurements', 0)}개 | "
        html += f"성공 매핑: {summary.get('successful_mappings', 0)}개 | "
        html += f"미매핑: {summary.get('unmatched_measurements', 0)}개"
        html += "</div>"
        
        html += "</div>"
        return html
    
    @staticmethod
    def create_config_warning_html(config_issues: List[str]) -> str:
        """설정 문제 경고 HTML"""
        if not config_issues:
            return ""
        
        html = "<div class='warning'>"
        html += "<h4>⚠️ 설정 문제 발견</h4>"
        html += "<ul>"
        for issue in config_issues:
            html += f"<li>{issue}</li>"
        html += "</ul>"
        html += "<p>정상 동작을 위해 설정을 확인해주세요.</p>"
        html += "</div>"
        return html

# 컴포넌트 팩토리 클래스
class ComponentFactory:
    """컴포넌트 생성을 위한 팩토리 클래스"""
    
    def __init__(self):
        self.header = HeaderComponents()
        self.ocr = OCRComponents()
        self.mapping = MappingComponents()
        self.results = ResultComponents()
        self.utils = UtilityComponents()
        self.html = HTMLGenerators()
    
    def create_all_components(self) -> Dict:
        """모든 필요한 컴포넌트들을 생성하여 딕셔너리로 반환"""
        components = {}
        
        # 헤더 컴포넌트들
        components['main_header'] = self.header.create_main_header()
        components['session_status'] = self.header.create_session_status()
        components['new_session_btn'] = self.header.create_new_session_button()
        
        # OCR 컴포넌트들
        components['image_upload'] = self.ocr.create_image_upload()
        components['upload_instructions'] = self.ocr.create_upload_instructions()
        components['process_ocr_btn'] = self.ocr.create_process_button()
        components['ocr_status'] = self.ocr.create_status_display()
        components['ocr_summary_html'], components['ocr_detailed_json'] = self.ocr.create_results_display()
        
        # 매핑 컴포넌트들
        components['scope_input'] = self.mapping.create_scope_input()
        components['scope_instructions'] = self.mapping.create_scope_instructions()
        components['process_mapping_btn'] = self.mapping.create_mapping_button()
        components['mapping_status'] = self.mapping.create_mapping_status()
        components['mapping_summary_html'], components['mapping_detailed_json'] = self.mapping.create_mapping_results()
        
        # 결과 컴포넌트들
        components['refresh_btn'], components['export_btn'] = self.results.create_action_buttons()
        components['final_results'] = self.results.create_final_results_display()
        components['future_features'] = self.results.create_future_features()
        
        return components

# 전역 컴포넌트 팩토리 인스턴스
component_factory = ComponentFactory()