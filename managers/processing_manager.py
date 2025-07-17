"""
처리 관리자 (ProcessingManager)

OCR 처리, 매핑 처리 등의 데이터 처리 책임을 전담합니다.
"""

import json
import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

class ProcessingManager:
    """데이터 처리 작업을 담당하는 매니저"""
    
    def __init__(self):
        """ProcessingManager 초기화"""
        logger.info("ProcessingManager 초기화")
    
    def validate_uploaded_files(self, uploaded_files: List) -> Tuple[bool, str, List]:
        """업로드된 파일 유효성 검사
        
        Args:
            uploaded_files: 업로드된 파일 리스트
            
        Returns:
            Tuple: (유효여부, 메시지, 유효한 파일 리스트)
        """
        if not uploaded_files:
            return False, "업로드된 파일이 없습니다.", []
        
        valid_files = []
        invalid_files = []
        
        # 지원되는 이미지 확장자
        supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        
        for file in uploaded_files:
            if not file:
                continue
                
            try:
                # 파일명 검사
                filename = getattr(file, 'name', str(file))
                file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
                
                if f'.{file_ext}' not in supported_extensions:
                    invalid_files.append(f"{filename} (지원되지 않는 형식)")
                    continue
                
                # 파일 크기 검사 (10MB 제한)
                if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:
                    invalid_files.append(f"{filename} (파일 크기 초과)")
                    continue
                
                valid_files.append(file)
                
            except Exception as e:
                invalid_files.append(f"{filename} (검사 실패: {str(e)})")
        
        if not valid_files:
            return False, f"유효한 파일이 없습니다. 오류: {', '.join(invalid_files)}", []
        
        message = f"✅ {len(valid_files)}개 파일 유효성 검사 완료"
        if invalid_files:
            message += f"\n⚠️ 제외된 파일: {', '.join(invalid_files)}"
        
        return True, message, valid_files
    
    def process_images_ocr(self, uploaded_files: List, session_data: Dict, progress_callback=None) -> Tuple[bool, str, str, Dict]:
        """이미지 OCR 처리
        
        Args:
            uploaded_files: 업로드된 파일 리스트
            session_data: 세션 데이터
            progress_callback: 진행률 콜백 함수
            
        Returns:
            Tuple: (성공여부, JSON결과, 상태메시지, 업데이트된 세션데이터)
        """
        # 세션 유효성 검사
        is_valid, error_msg = self._validate_session_for_processing(session_data)
        if not is_valid:
            return False, "", error_msg, session_data
        
        try:
            if progress_callback:
                progress_callback(0.1, desc="이미지 저장 중...")
            
            service = session_data["service"]
            success, ocr_results, status_msg, summary = service.process_images_ocr(uploaded_files)
            
            if success:
                if progress_callback:
                    progress_callback(0.8, desc="결과 생성 중...")
                
                # 세션 상태 업데이트
                session_data["ocr_results"] = ocr_results
                
                # JSON 결과 포맷팅
                json_result = json.dumps(ocr_results, indent=2, ensure_ascii=False)
                
                if progress_callback:
                    progress_callback(1.0, desc="완료!")
                
                logger.info(f"OCR 처리 완료: {session_data.get('session_id', 'unknown')}")
                return True, json_result, status_msg, session_data
            else:
                logger.warning(f"OCR 처리 실패: {status_msg}")
                return False, "", status_msg, session_data
                
        except Exception as e:
            error_msg = f"❌ OCR 처리 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg, session_data
    
    def validate_scope_text(self, scope_text: str) -> Tuple[bool, str]:
        """작업범위 텍스트 유효성 검사
        
        Args:
            scope_text: 작업범위 텍스트
            
        Returns:
            Tuple: (유효여부, 메시지)
        """
        if not scope_text or not scope_text.strip():
            return False, "작업범위 텍스트가 비어있습니다."
        
        # 최소 길이 검사
        if len(scope_text.strip()) < 10:
            return False, "작업범위 텍스트가 너무 짧습니다. (최소 10자 이상)"
        
        # 최대 길이 검사
        if len(scope_text.strip()) > 10000:
            return False, "작업범위 텍스트가 너무 깁니다. (최대 10,000자)"
        
        # 기본 형식 검사 (선택사항)
        lines = scope_text.strip().split('\n')
        valid_lines = [line for line in lines if line.strip()]
        
        if len(valid_lines) < 1:
            return False, "최소 1줄 이상의 작업범위를 입력해주세요."
        
        return True, f"✅ 작업범위 유효성 검사 완료 ({len(valid_lines)}줄)"
    
    def process_scope_mapping(self, scope_text: str, session_data: Dict, progress_callback=None) -> Tuple[bool, str, str, Dict]:
        """작업범위 매핑 처리
        
        Args:
            scope_text: 작업범위 텍스트
            session_data: 세션 데이터
            progress_callback: 진행률 콜백 함수
            
        Returns:
            Tuple: (성공여부, JSON결과, 상태메시지, 업데이트된 세션데이터)
        """
        # 세션 유효성 검사
        is_valid, error_msg = self._validate_session_for_processing(session_data)
        if not is_valid:
            return False, "", error_msg, session_data
        
        try:
            if progress_callback:
                progress_callback(0.2, desc="작업범위 파싱 중...")
            
            service = session_data["service"]
            success, mapping_results, status_msg, summary = service.process_scope_mapping(scope_text)
            
            if success:
                if progress_callback:
                    progress_callback(0.8, desc="결과 생성 중...")
                
                # 세션 상태 업데이트
                session_data["mapping_results"] = mapping_results
                
                # JSON 결과 포맷팅
                json_result = json.dumps(mapping_results, indent=2, ensure_ascii=False)
                
                if progress_callback:
                    progress_callback(1.0, desc="완료!")
                
                logger.info(f"매핑 처리 완료: {session_data.get('session_id', 'unknown')}")
                return True, json_result, status_msg, session_data
            else:
                logger.warning(f"매핑 처리 실패: {status_msg}")
                return False, "", status_msg, session_data
                
        except Exception as e:
            error_msg = f"❌ 매핑 처리 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg, session_data
    
    def get_all_results(self, session_data: Dict) -> Dict:
        """전체 결과 조회
        
        Args:
            session_data: 세션 데이터
            
        Returns:
            Dict: 전체 결과 또는 에러 정보
        """
        is_valid, error_msg = self._validate_session_for_processing(session_data)
        if not is_valid:
            return {"error": error_msg}
        
        try:
            service = session_data["service"]
            results = service.get_all_results()
            
            logger.info(f"전체 결과 조회: {session_data.get('session_id', 'unknown')}")
            return results
            
        except Exception as e:
            error_msg = f"전체 결과 조회 실패: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def get_processing_status(self, session_data: Dict) -> Dict:
        """현재 처리 상태 조회
        
        Args:
            session_data: 세션 데이터
            
        Returns:
            Dict: 처리 상태 정보
        """
        status = {
            "session_valid": False,
            "has_ocr_results": False,
            "has_mapping_results": False,
            "ocr_count": 0,
            "mapping_count": 0,
            "ready_for_ocr": False,
            "ready_for_mapping": False
        }
        
        is_valid, _ = self._validate_session_for_processing(session_data)
        status["session_valid"] = is_valid
        
        if is_valid:
            try:
                service = session_data["service"]
                session_info = service.get_session_info()
                
                status.update({
                    "has_ocr_results": session_info.get("has_ocr_results", False),
                    "has_mapping_results": session_info.get("has_mapping_results", False),
                    "ocr_count": len(session_data.get("ocr_results", {})),
                    "mapping_count": len(session_data.get("mapping_results", {})),
                    "ready_for_ocr": True,  # 파일 업로드만 되면 OCR 가능
                    "ready_for_mapping": bool(session_data.get("ocr_results"))  # OCR 결과가 있어야 매핑 가능
                })
                
            except Exception as e:
                logger.error(f"처리 상태 조회 실패: {e}")
        
        return status
    
    def get_processing_summary(self, session_data: Dict) -> str:
        """처리 상태 요약 메시지 생성
        
        Args:
            session_data: 세션 데이터
            
        Returns:
            str: 처리 상태 요약 메시지
        """
        status = self.get_processing_status(session_data)
        
        if not status["session_valid"]:
            return "❌ 유효하지 않은 세션입니다."
        
        summary = "📊 처리 상태 요약\n"
        summary += f"🔍 OCR 결과: {'있음' if status['has_ocr_results'] else '없음'} ({status['ocr_count']}개)\n"
        summary += f"🔗 매핑 결과: {'있음' if status['has_mapping_results'] else '없음'} ({status['mapping_count']}개)\n"
        
        # 다음 단계 안내
        if not status["has_ocr_results"]:
            summary += "\n💡 다음 단계: 측량 사진을 업로드하고 OCR 처리를 시작하세요."
        elif not status["has_mapping_results"]:
            summary += "\n💡 다음 단계: 작업범위를 입력하고 데이터 매핑을 시작하세요."
        else:
            summary += "\n✅ 모든 처리가 완료되었습니다!"
        
        return summary
    
    def _validate_session_for_processing(self, session_data: Dict) -> Tuple[bool, str]:
        """처리 작업을 위한 세션 유효성 검사
        
        Args:
            session_data: 세션 데이터
            
        Returns:
            Tuple: (유효여부, 에러메시지)
        """
        if not session_data:
            return False, "❌ 세션 데이터가 없습니다. 새 세션을 생성하거나 기존 세션을 로드하세요."
        
        if not session_data.get("service"):
            return False, "❌ 세션 서비스가 없습니다. 세션을 다시 로드하세요."
        
        if session_data.get("status") == "error":
            return False, f"❌ 세션 에러: {session_data.get('error', 'Unknown error')}"
        
        return True, "세션이 유효합니다."
    
    def validate_file_format(self, filename: str) -> bool:
        """파일 형식 검증
        
        Args:
            filename: 파일명
            
        Returns:
            bool: 유효한 형식인지 여부
        """
        supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return f'.{file_ext}' in supported_extensions
    
    def validate_file_size(self, file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """파일 크기 검증
        
        Args:
            file_size: 파일 크기 (바이트)
            max_size: 최대 허용 크기 (기본값: 10MB)
            
        Returns:
            bool: 허용 가능한 크기인지 여부
        """
        return file_size <= max_size
    
    def get_file_info(self, file) -> Dict:
        """파일 정보 조회
        
        Args:
            file: 파일 객체
            
        Returns:
            Dict: 파일 정보
        """
        try:
            return {
                "name": getattr(file, 'name', 'unknown'),
                "size": getattr(file, 'size', 0),
                "type": getattr(file, 'type', 'unknown'),
                "valid_format": self.validate_file_format(getattr(file, 'name', '')),
                "valid_size": self.validate_file_size(getattr(file, 'size', 0))
            }
        except Exception as e:
            logger.error(f"파일 정보 조회 실패: {e}")
            return {
                "name": "unknown",
                "size": 0,
                "type": "unknown",
                "valid_format": False,
                "valid_size": False,
                "error": str(e)
            }
    
    def format_file_size(self, size_bytes: int) -> str:
        """파일 크기 포맷팅
        
        Args:
            size_bytes: 바이트 단위 크기
            
        Returns:
            str: 포맷된 크기 문자열
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"