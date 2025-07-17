import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """앱 설정 관리"""
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # 파일 저장 경로
    UPLOAD_FOLDER = 'uploads'
    DATA_FOLDER = 'data'
    TEMPLATES_FOLDER = 'templates'
    
    # OCR 설정
    OCR_LANGUAGES = ['en']  # English
    OCR_CONFIDENCE_THRESHOLD = 0.3
    
    # Gradio 설정
    GRADIO_SHARE = False  # 개발 중에는 False
    GRADIO_DEBUG = True
    
    # 지원하는 이미지 포맷
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    # 최대 파일 크기 (MB)
    MAX_FILE_SIZE = 10
    
    @classmethod
    def validate_config(cls):
        """설정 검증"""
        issues = []
        
        if not cls.ANTHROPIC_API_KEY:
            issues.append("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        
        # 필요한 폴더 생성
        for folder in [cls.UPLOAD_FOLDER, cls.DATA_FOLDER, cls.TEMPLATES_FOLDER]:
            os.makedirs(folder, exist_ok=True)
        
        return issues

# 전역 설정 인스턴스
config = Config()