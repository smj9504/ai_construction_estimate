"""
세션 관리자 (SessionManager)

세션 생성, 로드, 관리 등의 책임을 전담합니다.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, List

try:
    from services.estimator_service import create_estimator_service, list_all_sessions
except ImportError:
    # 서비스 모듈이 없을 경우 더미 함수
    def create_estimator_service(session_id):
        return None
    def list_all_sessions():
        return []

logger = logging.getLogger(__name__)

class SessionManager:
    """세션 생성, 로드, 관리를 담당하는 매니저"""
    
    def __init__(self):
        """SessionManager 초기화"""
        logger.info("SessionManager 초기화")
    
    def create_new_session(self, project_name: str = None) -> Dict:
        """새 세션 생성
        
        Args:
            project_name: 프로젝트 이름 (옵션)
            
        Returns:
            Dict: 세션 정보 (session_id, service, created_at 등)
        """
        try:
            # 새 세션 ID 생성
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # EstimatorService 인스턴스 생성
            service = create_estimator_service(session_id)
            
            # 프로젝트 이름 설정
            if project_name and project_name.strip():
                service.update_project_name(project_name.strip())
            
            logger.info(f"새 세션 생성: {session_id}")
            
            return {
                "session_id": session_id,
                "service": service,
                "ocr_results": {},
                "mapping_results": {},
                "created_at": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"새 세션 생성 실패: {e}")
            return {
                "session_id": "error",
                "service": None,
                "error": str(e),
                "status": "error"
            }
    
    def load_existing_session(self, session_id: str) -> Dict:
        """기존 세션 로드
        
        Args:
            session_id: 로드할 세션 ID
            
        Returns:
            Dict: 세션 정보 또는 에러 정보
        """
        try:
            service = create_estimator_service(session_id)
            session_info = service.get_session_info()
            
            if session_info:
                logger.info(f"기존 세션 로드: {session_id}")
                
                return {
                    "session_id": session_id,
                    "service": service,
                    "ocr_results": service.current_results.get("ocr_results", {}),
                    "mapping_results": service.current_results.get("mapping_results", {}),
                    "loaded_at": datetime.now().isoformat(),
                    "status": "success"
                }
            else:
                return {
                    "session_id": "error",
                    "service": None,
                    "error": "세션을 찾을 수 없습니다.",
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"세션 로드 실패 {session_id}: {e}")
            return {
                "session_id": "error",
                "service": None,
                "error": str(e),
                "status": "error"
            }
    
    def clear_session_data(self, session_data: Dict) -> Dict:
        """세션 데이터 초기화
        
        Args:
            session_data: 현재 세션 데이터
            
        Returns:
            Dict: 초기화된 세션 데이터
        """
        if session_data and session_data.get("service"):
            try:
                session_data["service"].clear_results()
                session_data["ocr_results"] = {}
                session_data["mapping_results"] = {}
                
                logger.info(f"세션 데이터 초기화: {session_data.get('session_id', 'unknown')}")
                
                return session_data
            except Exception as e:
                logger.error(f"세션 데이터 초기화 실패: {e}")
        
        return session_data
    
    def get_session_dropdown_choices(self) -> List[tuple]:
        """세션 드롭다운 선택지 생성
        
        Returns:
            List[tuple]: (display_name, session_id) 튜플 리스트
        """
        try:
            sessions = list_all_sessions()
            choices = []
            
            for session in sessions[:20]:  # 최대 20개만 표시
                project_name = session.get("project_name", "Unknown")
                session_id = session.get("session_id", "")
                last_accessed = session.get("last_accessed", "")
                
                if last_accessed:
                    try:
                        dt = datetime.fromisoformat(last_accessed)
                        time_str = dt.strftime("%m/%d %H:%M")
                    except:
                        time_str = "Unknown"
                else:
                    time_str = "Unknown"
                
                display_name = f"{project_name} ({session_id[:8]}...) - {time_str}"
                choices.append((display_name, session_id))
            
            return choices
            
        except Exception as e:
            logger.error(f"세션 목록 조회 실패: {e}")
            return []
    
    def get_session_status_message(self, session_data: Dict, operation: str = "load") -> str:
        """세션 상태 메시지 생성
        
        Args:
            session_data: 세션 데이터
            operation: 작업 유형 ("create", "load", "clear")
            
        Returns:
            str: 상태 메시지
        """
        if not session_data or session_data.get("status") == "error":
            error_msg = session_data.get("error", "Unknown error") if session_data else "Unknown error"
            return f"❌ 세션 {operation} 실패: {error_msg}"
        
        service = session_data.get("service")
        session_id = session_data.get("session_id", "unknown")
        
        if not service:
            return f"❌ 세션 {operation} 실패: 서비스 인스턴스 없음"
        
        try:
            session_info = service.get_session_info()
            project_name = session_info.get('project_name', 'Unknown Project')
            
            if operation == "create":
                status_msg = f"✅ 새 세션 생성 완료!\n"
                status_msg += f"🆔 세션: {session_id[:12]}...\n"
                status_msg += f"📁 프로젝트: {project_name}"
                
            elif operation == "load":
                status_msg = f"✅ 세션 로드 완료!\n"
                status_msg += f"🆔 세션: {session_id[:12]}...\n"
                status_msg += f"📁 프로젝트: {project_name}\n"
                status_msg += f"📊 이미지: {session_info.get('images_count', 0)}개\n"
                status_msg += f"🔍 OCR: {'완료' if session_info.get('has_ocr_results') else '대기'}\n"
                status_msg += f"🔗 매핑: {'완료' if session_info.get('has_mapping_results') else '대기'}"
                
            elif operation == "clear":
                status_msg = f"✅ 세션 데이터 초기화 완료!\n"
                status_msg += f"🆔 세션: {session_id[:12]}...\n"
                status_msg += f"📁 프로젝트: {project_name}"
                
            else:
                status_msg = f"✅ 세션 {operation} 완료! (세션: {session_id[:12]}...)"
            
            return status_msg
            
        except Exception as e:
            logger.error(f"세션 상태 메시지 생성 실패: {e}")
            return f"⚠️ 세션 {operation} 완료 (상태 정보 조회 실패)"
    
    def validate_session(self, session_data: Dict) -> tuple[bool, str]:
        """세션 유효성 검사
        
        Args:
            session_data: 검사할 세션 데이터
            
        Returns:
            tuple: (유효여부, 메시지)
        """
        if not session_data:
            return False, "세션 데이터가 없습니다."
        
        if session_data.get("status") == "error":
            return False, f"세션 에러: {session_data.get('error', 'Unknown error')}"
        
        if not session_data.get("service"):
            return False, "세션 서비스 인스턴스가 없습니다."
        
        return True, "세션이 유효합니다."
    
    def get_session_summary(self, session_data: Dict) -> Dict:
        """세션 요약 정보 생성
        
        Args:
            session_data: 세션 데이터
            
        Returns:
            Dict: 세션 요약 정보
        """
        summary = {
            "session_id": session_data.get("session_id", "unknown"),
            "valid": False,
            "project_name": "Unknown",
            "images_count": 0,
            "has_ocr_results": False,
            "has_mapping_results": False,
            "created_at": session_data.get("created_at"),
            "loaded_at": session_data.get("loaded_at")
        }
        
        is_valid, _ = self.validate_session(session_data)
        summary["valid"] = is_valid
        
        if is_valid:
            try:
                service = session_data["service"]
                session_info = service.get_session_info()
                
                summary.update({
                    "project_name": session_info.get("project_name", "Unknown"),
                    "images_count": session_info.get("images_count", 0),
                    "has_ocr_results": session_info.get("has_ocr_results", False),
                    "has_mapping_results": session_info.get("has_mapping_results", False)
                })
                
            except Exception as e:
                logger.error(f"세션 요약 정보 생성 실패: {e}")
        
        return summary