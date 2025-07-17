import os
import shutil
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import logging

from config import config

logger = logging.getLogger(__name__)

class FileHandler:
    """파일 업로드 및 관리를 담당하는 서비스"""
    
    def __init__(self):
        # 필요한 디렉토리 생성
        self.upload_folder = Path(config.UPLOAD_FOLDER)
        self.data_folder = Path(config.DATA_FOLDER)
        
        self.upload_folder.mkdir(exist_ok=True)
        self.data_folder.mkdir(exist_ok=True)
        
        # 세션별 디렉토리
        self.current_session = None
        self.session_folder = None
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """새 세션 생성"""
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.current_session = session_id
        self.session_folder = self.upload_folder / session_id
        self.session_folder.mkdir(exist_ok=True)
        
        # 세션 폴더 내부 구조 생성
        (self.session_folder / "images").mkdir(exist_ok=True)
        (self.session_folder / "results").mkdir(exist_ok=True)
        
        logger.info(f"새 세션 생성: {session_id}")
        return session_id
    
    def load_session(self, session_id: str) -> bool:
        """기존 세션 로드"""
        session_folder = self.upload_folder / session_id
        if session_folder.exists():
            self.current_session = session_id
            self.session_folder = session_folder
            logger.info(f"세션 로드: {session_id}")
            return True
        else:
            logger.warning(f"세션을 찾을 수 없음: {session_id}")
            return False
    
    def save_uploaded_images(self, uploaded_files) -> List[str]:
        """업로드된 이미지 파일들 저장"""
        if not self.current_session:
            raise ValueError("세션이 설정되지 않았습니다. create_session()을 먼저 호출하세요.")
        
        saved_paths = []
        images_folder = self.session_folder / "images"
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # 파일 유효성 검사
                if not self._is_valid_image_file(uploaded_file):
                    logger.warning(f"유효하지 않은 이미지 파일 건너뛰기: {uploaded_file}")
                    continue
                
                # 안전한 파일명 생성
                original_name = getattr(uploaded_file, 'name', f'image_{i+1}')
                safe_filename = self._make_safe_filename(original_name)
                file_path = images_folder / safe_filename
                
                # 파일 저장
                if hasattr(uploaded_file, 'name') and os.path.exists(uploaded_file.name):
                    # Gradio file object - 임시 파일 경로가 있는 경우
                    shutil.copy2(uploaded_file.name, file_path)
                elif hasattr(uploaded_file, 'save'):
                    # 다른 형태의 파일 객체
                    uploaded_file.save(file_path)
                else:
                    # 바이트 데이터인 경우
                    with open(file_path, 'wb') as f:
                        if hasattr(uploaded_file, 'read'):
                            f.write(uploaded_file.read())
                        else:
                            f.write(uploaded_file)
                
                saved_paths.append(str(file_path))
                logger.info(f"이미지 저장: {file_path}")
                
            except Exception as e:
                logger.error(f"이미지 저장 실패: {uploaded_file} - {e}")
        
        logger.info(f"총 {len(saved_paths)}개 이미지 저장 완료")
        return saved_paths
    
    def _is_valid_image_file(self, file) -> bool:
        """이미지 파일 유효성 검사"""
        try:
            # 파일명 확인
            filename = getattr(file, 'name', str(file))
            if not filename:
                return False
            
            # 파일명이 실제 파일 경로인 경우 (Gradio)
            if isinstance(filename, str) and os.path.exists(filename):
                filename = os.path.basename(filename)
            
            # 확장자 확인
            ext = Path(filename).suffix.lower()
            if ext not in config.ALLOWED_EXTENSIONS:
                logger.warning(f"지원하지 않는 확장자: {ext}")
                return False
            
            # 파일 크기 확인 (가능한 경우)
            if hasattr(file, 'size'):
                if file.size > config.MAX_FILE_SIZE * 1024 * 1024:  # MB to bytes
                    logger.warning(f"파일 크기 초과: {file.size} bytes")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"파일 유효성 검사 실패: {e}")
            return False
    
    def _make_safe_filename(self, filename: str) -> str:
        """안전한 파일명 생성"""
        # 파일명이 전체 경로인 경우 파일명만 추출
        if os.path.sep in filename or '/' in filename:
            filename = os.path.basename(filename)
        
        # 기본 정리
        safe_name = "".join(c for c in filename if c.isalnum() or c in '._-')
        
        # 길이 제한
        if len(safe_name) > 100:
            name_part = safe_name[:90]
            ext_part = safe_name[-10:] if '.' in safe_name[-10:] else ''
            safe_name = name_part + ext_part
        
        # 빈 이름 처리
        if not safe_name:
            safe_name = f"image_{uuid.uuid4().hex[:8]}.jpg"
        
        return safe_name
    
    def save_processing_results(self, data: Dict, filename: str = "processing_results.json") -> str:
        """처리 결과 저장"""
        if not self.current_session:
            raise ValueError("세션이 설정되지 않았습니다.")
        
        results_folder = self.session_folder / "results"
        file_path = results_folder / filename
        
        try:
            # 메타데이터 추가
            data_with_meta = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.current_session,
                "version": "1.0",
                "data": data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_with_meta, f, ensure_ascii=False, indent=2)
            
            logger.info(f"처리 결과 저장: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
            raise
    
    def load_processing_results(self, filename: str = "processing_results.json") -> Optional[Dict]:
        """저장된 처리 결과 로드"""
        if not self.current_session:
            return None
        
        results_folder = self.session_folder / "results"
        file_path = results_folder / filename
        
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"처리 결과 로드: {file_path}")
                return data.get('data', data)  # 메타데이터가 있으면 data 부분만, 없으면 전체
            else:
                return None
                
        except Exception as e:
            logger.error(f"결과 로드 실패: {e}")
            return None
    
    def get_session_info(self) -> Dict:
        """현재 세션 정보 반환"""
        if not self.current_session:
            return {"error": "활성 세션 없음"}
        
        images_folder = self.session_folder / "images"
        results_folder = self.session_folder / "results"
        
        info = {
            "session_id": self.current_session,
            "session_folder": str(self.session_folder),
            "images_count": len(list(images_folder.glob("*"))) if images_folder.exists() else 0,
            "results_files": [f.name for f in results_folder.glob("*.json")] if results_folder.exists() else [],
            "created_time": datetime.fromtimestamp(self.session_folder.stat().st_ctime).isoformat() if self.session_folder.exists() else None
        }
        
        return info
    
    def list_sessions(self) -> List[Dict]:
        """모든 세션 목록 반환"""
        sessions = []
        
        for session_dir in self.upload_folder.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith("session_"):
                images_folder = session_dir / "images"
                results_folder = session_dir / "results"
                
                session_info = {
                    "session_id": session_dir.name,
                    "created_time": datetime.fromtimestamp(session_dir.stat().st_ctime).isoformat(),
                    "images_count": len(list(images_folder.glob("*"))) if images_folder.exists() else 0,
                    "has_results": (results_folder / "processing_results.json").exists() if results_folder.exists() else False
                }
                sessions.append(session_info)
        
        # 최신 순으로 정렬
        sessions.sort(key=lambda x: x["created_time"], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        try:
            session_folder = self.upload_folder / session_id
            if session_folder.exists():
                shutil.rmtree(session_folder)
                logger.info(f"세션 삭제: {session_id}")
                
                # 현재 세션이 삭제된 세션이면 초기화
                if self.current_session == session_id:
                    self.current_session = None
                    self.session_folder = None
                
                return True
            else:
                logger.warning(f"삭제할 세션을 찾을 수 없음: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"세션 삭제 실패: {session_id} - {e}")
            return False
    
    def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """오래된 세션들 정리"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        for session_dir in self.upload_folder.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith("session_"):
                created_time = datetime.fromtimestamp(session_dir.stat().st_ctime)
                if created_time < cutoff_time:
                    if self.delete_session(session_dir.name):
                        deleted_count += 1
        
        logger.info(f"{deleted_count}개의 오래된 세션 정리 완료")
        return deleted_count

# 편의 함수들
def create_file_handler() -> FileHandler:
    """파일 핸들러 인스턴스 생성"""
    return FileHandler()

def quick_file_processing(uploaded_files) -> Tuple[FileHandler, List[str]]:
    """빠른 파일 처리 (편의 함수)"""
    file_handler = create_file_handler()
    session_id = file_handler.create_session()
    saved_paths = file_handler.save_uploaded_images(uploaded_files)
    return file_handler, saved_paths