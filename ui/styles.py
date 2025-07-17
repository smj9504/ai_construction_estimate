"""
UI 스타일 정의
Gradio 인터페이스용 CSS 스타일들을 관리합니다.
"""

# 메인 CSS 스타일
MAIN_CSS = """
/* 전체 컨테이너 */
.container { 
    max-width: 1400px; 
    margin: auto; 
    padding: 20px;
}

/* 상태 박스 스타일 */
.status-box { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    color: white; 
    padding: 20px; 
    border-radius: 12px; 
    margin: 15px 0; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 성공 메시지 */
.success { 
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
    color: white; 
    padding: 15px; 
    border-radius: 8px; 
    margin: 10px 0;
    border-left: 4px solid #2e7d32;
}

/* 에러 메시지 */
.error { 
    background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%); 
    color: white; 
    padding: 15px; 
    border-radius: 8px; 
    margin: 10px 0;
    border-left: 4px solid #c62828;
}

/* 경고 메시지 */
.warning {
    background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
    color: white;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid #ef6c00;
}

/* 탭 네비게이션 */
.tab-nav { 
    background: #f8f9fa; 
    border-radius: 8px;
    padding: 5px;
}

/* 업로드 영역 */
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

/* 버튼 스타일 */
.primary-button {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    color: white;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,123,255,0.2);
}

.primary-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,123,255,0.3);
}

.secondary-button {
    background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    color: white;
    font-weight: 600;
    transition: all 0.3s ease;
}

/* 카드 스타일 */
.card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border: 1px solid #e9ecef;
}

.card-header {
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 15px;
    margin-bottom: 20px;
    font-weight: 600;
    color: #495057;
}

/* 진행률 표시 */
.progress-container {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}

/* 결과 요약 스타일 */
.summary-card {
    background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
    border-left: 4px solid #4caf50;
    border-radius: 8px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 2px 6px rgba(76,175,80,0.1);
}

.summary-item {
    background: white;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid #dee2e6;
    transition: all 0.3s ease;
}

.summary-item:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transform: translateY(-1px);
}

/* 매핑 결과 스타일 */
.mapping-success {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    border-left: 4px solid #28a745;
    border-radius: 8px;
    padding: 15px;
    margin: 8px 0;
}

.mapping-warning {
    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    border-left: 4px solid #ffc107;
    border-radius: 8px;
    padding: 15px;
    margin: 8px 0;
}

.mapping-error {
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    border-left: 4px solid #dc3545;
    border-radius: 8px;
    padding: 15px;
    margin: 8px 0;
}

/* 신뢰도 배지 */
.confidence-high {
    background: #28a745;
    color: white;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: 600;
}

.confidence-medium {
    background: #ffc107;
    color: #212529;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: 600;
}

.confidence-low {
    background: #dc3545;
    color: white;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: 600;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    .upload-area {
        padding: 20px;
    }
    
    .card {
        padding: 15px;
        margin: 10px 0;
    }
}

/* 애니메이션 */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeIn 0.5s ease-out;
}

@keyframes slideIn {
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
}

.slide-in {
    animation: slideIn 0.3s ease-out;
}

/* 로딩 스피너 */
.loading-spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #007bff;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    animation: spin 1s linear infinite;
    display: inline-block;
    margin-right: 10px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 텍스트 스타일 */
.text-success { color: #28a745; font-weight: 600; }
.text-warning { color: #ffc107; font-weight: 600; }
.text-danger { color: #dc3545; font-weight: 600; }
.text-info { color: #17a2b8; font-weight: 600; }
.text-muted { color: #6c757d; }

/* 아이콘 스타일 */
.icon-lg { font-size: 1.5em; margin-right: 8px; }
.icon-md { font-size: 1.2em; margin-right: 6px; }
.icon-sm { font-size: 1em; margin-right: 4px; }

/* 데이터 테이블 스타일 */
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.data-table th {
    background: linear-gradient(135deg, #495057 0%, #343a40 100%);
    color: white;
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
}

.data-table td {
    padding: 12px 15px;
    border-bottom: 1px solid #dee2e6;
}

.data-table tr:hover {
    background: #f8f9fa;
}

/* JSON 뷰어 스타일 */
.json-viewer {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
    max-height: 400px;
    overflow-y: auto;
}
"""

# 테마별 스타일
DARK_THEME_CSS = """
/* 다크 테마 */
.dark-theme {
    background-color: #2c3e50;
    color: #ecf0f1;
}

.dark-theme .card {
    background: #34495e;
    border-color: #4a5568;
    color: #ecf0f1;
}

.dark-theme .status-box {
    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
}
"""

# 컴포넌트별 스타일
COMPONENT_STYLES = {
    'upload_area': 'upload-area',
    'status_box': 'status-box',
    'primary_button': 'primary-button',
    'secondary_button': 'secondary-button',
    'card': 'card',
    'success_message': 'success',
    'error_message': 'error',
    'warning_message': 'warning',
    'summary_card': 'summary-card',
    'mapping_success': 'mapping-success',
    'mapping_warning': 'mapping-warning',
    'confidence_high': 'confidence-high',
    'confidence_medium': 'confidence-medium',
    'confidence_low': 'confidence-low',
}

def get_main_css() -> str:
    """메인 CSS 스타일 반환"""
    return MAIN_CSS

def get_dark_theme_css() -> str:
    """다크 테마 CSS 반환"""
    return DARK_THEME_CSS

def get_component_class(component_name: str) -> str:
    """컴포넌트별 CSS 클래스명 반환"""
    return COMPONENT_STYLES.get(component_name, '')

def get_full_css() -> str:
    """전체 CSS 스타일 반환"""
    return MAIN_CSS + DARK_THEME_CSS