"""
업무용 건축 견적서 서비스
세션 기반으로 여러 사용자가 동시에 사용할 수 있는 시스템
"""

import json
import traceback
import tempfile
import os
import shutil
import uuid
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from pathlib import Path

from core.ocr_service import create_ocr_service
from core.data_mapper import create_data_mapper
from config import config, Config

logger = logging.getLogger(__name__)

class EstimatorService:
    """세션 기반 건축 견적서 생성기 서비스"""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        서비스 초기화
        Args:
            session_id: 세션 ID (없으면 자동 생성)
        """
        # 세션 ID 설정
        if session_id is None:
            session_id = self._generate_session_id()
        
        self.session_id = session_id
        logger.info(f"EstimatorService 초기화: 세션 {self.session_id}")
        
        # 설정 검증
        self.config_issues = Config.validate_config()
        if self.config_issues:
            logger.warning(f"설정 문제: {self.config_issues}")
        
        # 세션별 폴더 설정
        self.sessions_root = Path("data/sessions")
        self.sessions_root.mkdir(parents=True, exist_ok=True)
        
        self.session_dir = self.sessions_root / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        # 세션 폴더 구조 생성
        (self.session_dir / "images").mkdir(exist_ok=True)
        (self.session_dir / "results").mkdir(exist_ok=True)
        (self.session_dir / "temp").mkdir(exist_ok=True)
        
        # 세션 메타데이터 저장/로드
        self.session_meta_file = self.session_dir / "session_meta.json"
        self.session_meta = self._load_session_meta()
        
        # 핵심 서비스들
        self.ocr_service = None  # 필요할 때 생성
        self.data_mapper = create_data_mapper()
        
        # 현재 작업 결과 로드
        self.current_results = self._load_results()
        
        logger.info(f"세션 {self.session_id} 초기화 완료")
    
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        return f"session_{timestamp}_{unique_id}"
    
    def _load_session_meta(self) -> Dict:
        """세션 메타데이터 로드"""
        if self.session_meta_file.exists():
            try:
                with open(self.session_meta_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"세션 메타데이터 로드 실패: {e}")
        
        # 기본 메타데이터 생성
        meta = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "project_name": "New Project",
            "status": "active"
        }
        self._save_session_meta(meta)
        return meta
    
    def _save_session_meta(self, meta: Dict):
        """세션 메타데이터 저장"""
        meta["last_accessed"] = datetime.now().isoformat()
        try:
            with open(self.session_meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            self.session_meta = meta
        except Exception as e:
            logger.error(f"세션 메타데이터 저장 실패: {e}")
    
    def _load_results(self) -> Dict:
        """저장된 결과 로드"""
        results_file = self.session_dir / "results" / "current_results.json"
        if results_file.exists():
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"세션 {self.session_id} 결과 로드 완료")
                return data.get('results', {})
            except Exception as e:
                logger.warning(f"결과 로드 실패: {e}")
        return {}
    
    def _save_results(self):
        """현재 결과 저장"""
        results_file = self.session_dir / "results" / "current_results.json"
        try:
            save_data = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "results": self.current_results
            }
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            # 메타데이터 업데이트
            self._save_session_meta(self.session_meta)
            
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
    
    def get_config_issues(self) -> List[str]:
        """설정 문제 목록 반환"""
        return self.config_issues
    
    def has_config_issues(self) -> bool:
        """설정 문제 여부 확인"""
        return bool(self.config_issues)
    
    def get_session_info(self) -> Dict:
        """세션 정보 반환"""
        images_count = len(list((self.session_dir / "images").glob("*")))
        results_count = len(list((self.session_dir / "results").glob("*.json")))
        
        return {
            "session_id": self.session_id,
            "project_name": self.session_meta.get("project_name", "Unknown"),
            "created_at": self.session_meta.get("created_at"),
            "last_accessed": self.session_meta.get("last_accessed"),
            "images_count": images_count,
            "results_count": results_count,
            "has_ocr_results": "ocr_results" in self.current_results,
            "has_mapping_results": "mapping_results" in self.current_results,
            "session_dir": str(self.session_dir)
        }
    
    def update_project_name(self, project_name: str):
        """프로젝트 이름 업데이트"""
        self.session_meta["project_name"] = project_name
        self._save_session_meta(self.session_meta)
    
    def process_images_ocr(self, uploaded_files) -> Tuple[bool, Dict, str, Dict]:
        """이미지 OCR 처리"""
        if not uploaded_files:
            return False, {}, "❌ 업로드할 이미지를 선택하세요.", {}
        
        try:
            logger.info(f"세션 {self.session_id}: 이미지 OCR 처리 시작 ({len(uploaded_files)}개)")
            
            # 1. 세션별 이미지 저장
            saved_paths = self._save_session_images(uploaded_files)
            if not saved_paths:
                return False, {}, "❌ 이미지 저장 실패", {}
            
            # 2. OCR 서비스 초기화
            if self.ocr_service is None:
                logger.info("OCR 서비스 초기화 중...")
                self.ocr_service = create_ocr_service()
            
            # 3. OCR 처리
            ocr_results = self.ocr_service.process_multiple_images(saved_paths)
            
            # 4. 결과 저장
            self.current_results['ocr_results'] = ocr_results
            self._save_results()
            
            # 5. 요약 정보 생성
            summary = self._create_ocr_summary(ocr_results)
            
            # 6. 상태 메시지 생성
            status_msg = f"✅ OCR 처리 완료! (세션: {self.session_id[:12]}...)\n"
            status_msg += f"📸 처리된 이미지: {summary['total_images']}개\n"
            status_msg += f"📏 추출된 측정값: {summary['total_measurements']}개\n"
            if summary['error_count'] > 0:
                status_msg += f"❌ 처리 실패: {summary['error_count']}개"
            
            logger.info(f"세션 {self.session_id}: OCR 처리 완료")
            return True, ocr_results, status_msg, summary
            
        except Exception as e:
            error_msg = f"❌ OCR 처리 실패: {str(e)}"
            logger.error(f"세션 {self.session_id}: {error_msg}\n{traceback.format_exc()}")
            return False, {}, error_msg, {}
    
    def process_scope_mapping(self, scope_text: str) -> Tuple[bool, Dict, str, Dict]:
        """작업 범위와 측정값 매핑 처리"""
        if not scope_text.strip():
            return False, {}, "❌ 작업 범위를 입력하세요.", {}
        
        if 'ocr_results' not in self.current_results:
            return False, {}, "❌ 먼저 이미지를 업로드하고 OCR 처리를 완료하세요.", {}
        
        try:
            logger.info(f"세션 {self.session_id}: 작업 범위 매핑 시작")
            
            # 1. 작업 범위 파싱
            work_scopes = self.data_mapper.parse_work_scope(scope_text)
            
            # 2. 측정 데이터 처리
            measurements = self.data_mapper.process_measurements(self.current_results['ocr_results'])
            
            # 3. 매핑 수행
            mapping_result = self.data_mapper.map_scope_to_measurements(work_scopes, measurements)
            
            # 4. 결과 저장
            self.current_results['mapping_results'] = mapping_result
            self.current_results['scope_text'] = scope_text  # 입력된 텍스트도 저장
            self._save_results()
            
            # 5. 요약 데이터
            summary = mapping_result.get('summary', {})
            
            # 6. 상태 메시지 생성
            status_msg = f"✅ 데이터 매핑 완료! (세션: {self.session_id[:12]}...)\n"
            status_msg += f"🏠 작업 범위: {summary.get('total_work_scopes', 0)}개\n"
            status_msg += f"📏 측정 데이터: {summary.get('total_measurements', 0)}개\n"
            status_msg += f"🔗 성공적 매핑: {summary.get('successful_mappings', 0)}개\n"
            status_msg += f"⚠️ 미매핑 측정값: {summary.get('unmatched_measurements', 0)}개"
            
            if summary.get('quality_score'):
                quality = summary['quality_score'] * 100
                status_msg += f"\n🎯 매핑 품질: {quality:.0f}%"
            
            logger.info(f"세션 {self.session_id}: 매핑 처리 완료")
            return True, mapping_result, status_msg, summary
            
        except Exception as e:
            error_msg = f"❌ 데이터 매핑 실패: {str(e)}"
            logger.error(f"세션 {self.session_id}: {error_msg}\n{traceback.format_exc()}")
            return False, {}, error_msg, {}
    
    def get_all_results(self) -> Dict:
        """전체 처리 결과 반환"""
        return self.current_results.copy()
    
    def clear_results(self):
        """결과 초기화"""
        self.current_results = {}
        self._save_results()
        logger.info(f"세션 {self.session_id}: 결과 초기화 완료")
    
    def export_results(self, format: str = 'json') -> Tuple[bool, str, str]:
        """결과 내보내기"""
        if not self.current_results:
            return False, "", "❌ 내보낼 결과가 없습니다."
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"estimator_export_{self.session_id}_{timestamp}.{format}"
            export_dir = self.session_dir / "exports"
            export_dir.mkdir(exist_ok=True)
            filepath = export_dir / filename
            
            if format == 'json':
                export_data = {
                    "session_id": self.session_id,
                    "project_name": self.session_meta.get("project_name"),
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "results": self.current_results
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                return True, str(filepath), f"✅ 결과를 JSON으로 내보냈습니다: {filename}"
            else:
                return False, "", f"❌ 지원하지 않는 형식: {format}"
                
        except Exception as e:
            error_msg = f"❌ 결과 내보내기 실패: {str(e)}"
            logger.error(f"세션 {self.session_id}: {error_msg}")
            return False, "", error_msg
    
    def _save_session_images(self, uploaded_files) -> List[str]:
        """세션별 이미지 저장"""
        saved_paths = []
        images_dir = self.session_dir / "images"
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # 파일명 생성
                original_name = getattr(uploaded_file, 'name', f'image_{i+1}.jpg')
                if os.path.sep in original_name or '/' in original_name:
                    original_name = os.path.basename(original_name)
                
                # 확장자 확인
                allowed_exts = list(config.ALLOWED_EXTENSIONS)
                if not any(original_name.lower().endswith(ext) for ext in allowed_exts):
                    logger.warning(f"지원하지 않는 파일 형식: {original_name}")
                    continue
                
                # 파일 경로 (중복 방지)
                timestamp = datetime.now().strftime('%H%M%S')
                safe_name = f"{timestamp}_{i+1}_{original_name}"
                file_path = images_dir / safe_name
                
                # 파일 저장
                if hasattr(uploaded_file, 'name') and os.path.exists(uploaded_file.name):
                    shutil.copy2(uploaded_file.name, file_path)
                    saved_paths.append(str(file_path))
                    logger.debug(f"세션 이미지 저장: {file_path}")
                else:
                    logger.warning(f"파일 처리 실패: {uploaded_file}")
                
            except Exception as e:
                logger.error(f"세션 이미지 저장 실패: {uploaded_file} - {e}")
        
        logger.info(f"세션 {self.session_id}: {len(saved_paths)}개 이미지 저장 완료")
        return saved_paths
    
    def _create_ocr_summary(self, ocr_results: Dict) -> Dict:
        """OCR 결과 요약 생성"""
        total_images = len(ocr_results)
        total_measurements = sum(
            result.get('summary', {}).get('measurement_count', 0) 
            for result in ocr_results.values() 
            if 'error' not in result
        )
        error_count = sum(1 for result in ocr_results.values() if 'error' in result)
        
        return {
            'total_images': total_images,
            'total_measurements': total_measurements,
            'error_count': error_count,
            'success_rate': (total_images - error_count) / total_images if total_images > 0 else 0
        }

    def __del__(self):
        """소멸자 - 정리 작업"""
        try:
            # 마지막 접근 시간 업데이트
            if hasattr(self, 'session_meta'):
                self._save_session_meta(self.session_meta)
        except Exception:
            pass

# 세션 관리 유틸리티 함수들
def list_all_sessions() -> List[Dict]:
    """모든 세션 목록 반환"""
    sessions_root = Path("data/sessions")
    sessions = []
    
    if not sessions_root.exists():
        return sessions
    
    for session_dir in sessions_root.iterdir():
        if session_dir.is_dir():
            try:
                meta_file = session_dir / "session_meta.json"
                if meta_file.exists():
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    
                    # 추가 정보 수집
                    images_count = len(list((session_dir / "images").glob("*")))
                    results_file = session_dir / "results" / "current_results.json"
                    has_results = results_file.exists()
                    
                    sessions.append({
                        "session_id": meta.get("session_id"),
                        "project_name": meta.get("project_name", "Unknown"),
                        "created_at": meta.get("created_at"),
                        "last_accessed": meta.get("last_accessed"),
                        "images_count": images_count,
                        "has_results": has_results,
                        "status": meta.get("status", "unknown")
                    })
            except Exception as e:
                logger.warning(f"세션 정보 로드 실패 {session_dir.name}: {e}")
    
    # 최근 접근 순으로 정렬
    sessions.sort(key=lambda x: x.get("last_accessed", ""), reverse=True)
    return sessions

def delete_session(session_id: str) -> bool:
    """세션 삭제"""
    try:
        sessions_root = Path("data/sessions")
        session_dir = sessions_root / session_id
        
        if session_dir.exists():
            shutil.rmtree(session_dir)
            logger.info(f"세션 삭제 완료: {session_id}")
            return True
        else:
            logger.warning(f"삭제할 세션을 찾을 수 없음: {session_id}")
            return False
    except Exception as e:
        logger.error(f"세션 삭제 실패 {session_id}: {e}")
        return False

def cleanup_old_sessions(days_old: int = 30) -> int:
    """오래된 세션들 정리"""
    from datetime import timedelta
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    deleted_count = 0
    
    sessions = list_all_sessions()
    for session in sessions:
        try:
            last_accessed = datetime.fromisoformat(session["last_accessed"])
            if last_accessed < cutoff_time:
                if delete_session(session["session_id"]):
                    deleted_count += 1
        except Exception as e:
            logger.warning(f"오래된 세션 정리 실패 {session['session_id']}: {e}")
    
    logger.info(f"{deleted_count}개의 오래된 세션 정리 완료")
    return deleted_count

# 싱글톤이 아닌 팩토리 패턴으로 변경
def create_estimator_service(session_id: Optional[str] = None) -> EstimatorService:
    """EstimatorService 인스턴스 생성"""
    return EstimatorService(session_id=session_id)

def get_estimator_service(session_id: Optional[str] = None) -> EstimatorService:
    """EstimatorService 인스턴스 반환 (하위 호환성)"""
    return create_estimator_service(session_id=session_id)