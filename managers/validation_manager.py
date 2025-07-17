"""
검증 관리자 (ValidationManager)

파일 검증, 사용자 입력 검증, 비즈니스 룰 검증 등을 담당합니다.
"""

import re
import os
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

# PIL 이미지 처리를 위한 import (선택사항)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ValidationType(Enum):
    """검증 타입"""
    FILE = "file"
    TEXT = "text"
    PROJECT = "project"
    SESSION = "session"
    BUSINESS_RULE = "business_rule"

class ValidationSeverity(Enum):
    """검증 심각도"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """검증 결과 데이터 클래스"""
    is_valid: bool
    validation_type: ValidationType
    severity: ValidationSeverity
    errors: List[str]
    warnings: List[str]
    info: List[str]
    metadata: Dict[str, Any]
    timestamp: str
    
    def add_error(self, message: str):
        """에러 메시지 추가"""
        self.errors.append(message)
        self.is_valid = False
        if self.severity != ValidationSeverity.CRITICAL:
            self.severity = ValidationSeverity.ERROR
    
    def add_warning(self, message: str):
        """경고 메시지 추가"""
        self.warnings.append(message)
        if self.severity == ValidationSeverity.INFO:
            self.severity = ValidationSeverity.WARNING
    
    def add_info(self, message: str):
        """정보 메시지 추가"""
        self.info.append(message)

class ValidationManager:
    """검증 시스템을 관리하는 매니저"""
    
    def __init__(self, logging_manager=None):
        """ValidationManager 초기화
        
        Args:
            logging_manager: LoggingManager 인스턴스 (선택사항)
        """
        self.logging_manager = logging_manager
        self.validation_rules = self._define_validation_rules()
        self.validation_history = []
        
        if self.logging_manager:
            self.logging_manager.log_app_activity("ValidationManager 초기화 완료")
    
    def _define_validation_rules(self) -> Dict[str, Dict]:
        """검증 규칙 정의"""
        return {
            "file": {
                "max_size": 10 * 1024 * 1024,  # 10MB
                "allowed_extensions": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"],
                "allowed_mime_types": [
                    "image/png", "image/jpeg", "image/bmp", "image/tiff"
                ],
                "min_resolution": (100, 100),
                "max_resolution": (10000, 10000),
                "min_file_size": 1024  # 1KB
            },
            "project": {
                "name_min_length": 1,
                "name_max_length": 100,
                "name_pattern": r"^[a-zA-Z0-9\s\-_\.\(\)]+$",
                "forbidden_names": ["test", "temp", "tmp", "admin", "system"]
            },
            "scope_text": {
                "min_length": 10,
                "max_length": 10000,
                "required_format": r".*-.*",  # 기본적으로 "방이름 - 작업내용" 형식
                "min_lines": 1,
                "max_lines": 100
            },
            "session": {
                "max_images": 50,
                "max_session_age_days": 30,
                "required_fields": ["session_id", "created_at"],
                "session_id_pattern": r"^session_\d{8}_\d{6}_[a-f0-9]{8}$"
            },
            "business": {
                "max_concurrent_sessions": 10,
                "max_daily_sessions": 100,
                "max_processing_time": 300,  # 5분
                "required_api_keys": ["ANTHROPIC_API_KEY"]
            }
        }
    
    def validate_uploaded_file(self, file, index: int = 0) -> ValidationResult:
        """업로드된 파일 검증
        
        Args:
            file: 업로드된 파일 객체
            index: 파일 인덱스
            
        Returns:
            ValidationResult: 검증 결과
        """
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.FILE,
            severity=ValidationSeverity.INFO,
            errors=[],
            warnings=[],
            info=[],
            metadata={"file_index": index},
            timestamp=datetime.now().isoformat()
        )
        
        if not file:
            result.add_error("파일이 없습니다.")
            return result
        
        try:
            # 파일명 검증
            filename = getattr(file, 'name', f'file_{index}')
            result.metadata["filename"] = filename
            
            if not filename:
                result.add_error("파일명이 없습니다.")
                return result
            
            # 파일 확장자 검증
            file_ext = self._get_file_extension(filename)
            if file_ext not in self.validation_rules["file"]["allowed_extensions"]:
                result.add_error(f"지원되지 않는 파일 형식입니다: {file_ext}")
                result.add_info(f"지원되는 형식: {', '.join(self.validation_rules['file']['allowed_extensions'])}")
            
            # 파일 크기 검증
            file_size = getattr(file, 'size', 0)
            result.metadata["file_size"] = file_size
            
            if file_size == 0:
                result.add_warning("파일 크기를 확인할 수 없습니다.")
            elif file_size < self.validation_rules["file"]["min_file_size"]:
                result.add_error(f"파일이 너무 작습니다. (최소: {self.validation_rules['file']['min_file_size']} bytes)")
            elif file_size > self.validation_rules["file"]["max_size"]:
                result.add_error(f"파일이 너무 큽니다. (최대: {self.validation_rules['file']['max_size']} bytes)")
            
            # MIME 타입 검증
            mime_type = mimetypes.guess_type(filename)[0]
            result.metadata["mime_type"] = mime_type
            
            if mime_type and mime_type not in self.validation_rules["file"]["allowed_mime_types"]:
                result.add_warning(f"예상치 못한 MIME 타입입니다: {mime_type}")
            
            # 이미지 검증 (PIL이 사용 가능한 경우)
            if PIL_AVAILABLE and hasattr(file, 'read'):
                try:
                    # 파일 포인터 위치 저장
                    original_position = file.tell() if hasattr(file, 'tell') else 0
                    
                    # 이미지 열기 시도
                    image = Image.open(file)
                    width, height = image.size
                    
                    result.metadata["resolution"] = {"width": width, "height": height}
                    result.metadata["image_mode"] = image.mode
                    result.metadata["image_format"] = image.format
                    
                    # 해상도 검증
                    min_w, min_h = self.validation_rules["file"]["min_resolution"]
                    max_w, max_h = self.validation_rules["file"]["max_resolution"]
                    
                    if width < min_w or height < min_h:
                        result.add_error(f"이미지 해상도가 너무 낮습니다. ({width}x{height}, 최소: {min_w}x{min_h})")
                    elif width > max_w or height > max_h:
                        result.add_error(f"이미지 해상도가 너무 높습니다. ({width}x{height}, 최대: {max_w}x{max_h})")
                    
                    # 이미지 품질 검증
                    if width * height < 50000:  # 50K 픽셀 미만
                        result.add_warning("이미지 해상도가 낮아 OCR 품질이 저하될 수 있습니다.")
                    
                    # 색상 모드 검증
                    if image.mode not in ["RGB", "RGBA", "L"]:
                        result.add_warning(f"일반적이지 않은 색상 모드입니다: {image.mode}")
                    
                    # 파일 포인터 위치 복원
                    if hasattr(file, 'seek'):
                        file.seek(original_position)
                    
                    result.add_info(f"이미지 정보: {width}x{height}, {image.mode}, {image.format}")
                    
                except Exception as e:
                    result.add_error(f"이미지 파일을 열 수 없습니다: {str(e)}")
            
            # 보안 검증
            if self._is_suspicious_filename(filename):
                result.add_warning("의심스러운 파일명입니다.")
            
            result.add_info(f"파일 검증 완료: {filename}")
            
        except Exception as e:
            result.add_error(f"파일 검증 중 오류 발생: {str(e)}")
        
        # 검증 기록
        self._record_validation(result)
        
        return result
    
    def validate_project_name(self, project_name: str) -> ValidationResult:
        """프로젝트 이름 검증
        
        Args:
            project_name: 프로젝트 이름
            
        Returns:
            ValidationResult: 검증 결과
        """
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.PROJECT,
            severity=ValidationSeverity.INFO,
            errors=[],
            warnings=[],
            info=[],
            metadata={"project_name": project_name},
            timestamp=datetime.now().isoformat()
        )
        
        if not project_name:
            result.add_error("프로젝트 이름이 비어있습니다.")
            return result
        
        # 길이 검증
        min_len = self.validation_rules["project"]["name_min_length"]
        max_len = self.validation_rules["project"]["name_max_length"]
        
        if len(project_name) < min_len:
            result.add_error(f"프로젝트 이름이 너무 짧습니다. (최소: {min_len}자)")
        elif len(project_name) > max_len:
            result.add_error(f"프로젝트 이름이 너무 깁니다. (최대: {max_len}자)")
        
        # 패턴 검증
        pattern = self.validation_rules["project"]["name_pattern"]
        if not re.match(pattern, project_name):
            result.add_error("프로젝트 이름에 허용되지 않는 문자가 포함되어 있습니다.")
            result.add_info("허용되는 문자: 영문, 숫자, 공백, 하이픈(-), 언더스코어(_), 점(.), 괄호()")
        
        # 금지된 이름 검증
        forbidden_names = self.validation_rules["project"]["forbidden_names"]
        if project_name.lower() in forbidden_names:
            result.add_error(f"사용할 수 없는 프로젝트 이름입니다: {project_name}")
        
        # 특수 문자 검증
        if project_name.startswith(" ") or project_name.endswith(" "):
            result.add_warning("프로젝트 이름의 앞뒤 공백은 제거됩니다.")
        
        result.add_info(f"프로젝트 이름 검증 완료: {project_name}")
        
        # 검증 기록
        self._record_validation(result)
        
        return result
    
    def validate_scope_text(self, scope_text: str) -> ValidationResult:
        """작업범위 텍스트 검증
        
        Args:
            scope_text: 작업범위 텍스트
            
        Returns:
            ValidationResult: 검증 결과
        """
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.TEXT,
            severity=ValidationSeverity.INFO,
            errors=[],
            warnings=[],
            info=[],
            metadata={"scope_text_length": len(scope_text) if scope_text else 0},
            timestamp=datetime.now().isoformat()
        )
        
        if not scope_text:
            result.add_error("작업범위 텍스트가 비어있습니다.")
            return result
        
        # 길이 검증
        min_len = self.validation_rules["scope_text"]["min_length"]
        max_len = self.validation_rules["scope_text"]["max_length"]
        
        if len(scope_text) < min_len:
            result.add_error(f"작업범위 텍스트가 너무 짧습니다. (최소: {min_len}자)")
        elif len(scope_text) > max_len:
            result.add_error(f"작업범위 텍스트가 너무 깁니다. (최대: {max_len}자)")
        
        # 라인 수 검증
        lines = scope_text.strip().split('\n')
        valid_lines = [line for line in lines if line.strip()]
        
        result.metadata["total_lines"] = len(lines)
        result.metadata["valid_lines"] = len(valid_lines)
        
        min_lines = self.validation_rules["scope_text"]["min_lines"]
        max_lines = self.validation_rules["scope_text"]["max_lines"]
        
        if len(valid_lines) < min_lines:
            result.add_error(f"최소 {min_lines}줄 이상의 작업범위를 입력해주세요.")
        elif len(valid_lines) > max_lines:
            result.add_error(f"최대 {max_lines}줄까지만 입력 가능합니다.")
        
        # 형식 검증
        format_pattern = self.validation_rules["scope_text"]["required_format"]
        valid_format_count = 0
        
        for line in valid_lines:
            if re.search(format_pattern, line):
                valid_format_count += 1
        
        if valid_format_count == 0:
            result.add_error("올바른 형식의 작업범위가 없습니다.")
            result.add_info("형식: '방 이름 - 작업 내용' (예: Kitchen - cabinet replacement)")
        elif valid_format_count < len(valid_lines):
            result.add_warning(f"{len(valid_lines) - valid_format_count}줄이 권장 형식과 다릅니다.")
        
        # 내용 품질 검증
        if self._contains_only_special_chars(scope_text):
            result.add_error("의미 있는 텍스트 내용이 없습니다.")
        
        # 중복 라인 검증
        unique_lines = set(line.strip().lower() for line in valid_lines)
        if len(unique_lines) < len(valid_lines):
            result.add_warning("중복된 작업범위가 있습니다.")
        
        result.add_info(f"작업범위 검증 완료: {len(valid_lines)}줄")
        
        # 검증 기록
        self._record_validation(result)
        
        return result
    
    def validate_session_data(self, session_data: Dict) -> ValidationResult:
        """세션 데이터 검증
        
        Args:
            session_data: 세션 데이터
            
        Returns:
            ValidationResult: 검증 결과
        """
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.SESSION,
            severity=ValidationSeverity.INFO,
            errors=[],
            warnings=[],
            info=[],
            metadata={"session_data_keys": list(session_data.keys()) if session_data else []},
            timestamp=datetime.now().isoformat()
        )
        
        if not session_data:
            result.add_error("세션 데이터가 없습니다.")
            return result
        
        # 필수 필드 검증
        required_fields = self.validation_rules["session"]["required_fields"]
        for field in required_fields:
            if field not in session_data:
                result.add_error(f"필수 필드가 누락되었습니다: {field}")
        
        # 세션 ID 형식 검증
        session_id = session_data.get("session_id")
        if session_id:
            pattern = self.validation_rules["session"]["session_id_pattern"]
            if not re.match(pattern, session_id):
                result.add_warning("세션 ID 형식이 일반적이지 않습니다.")
        
        # 세션 연령 검증
        created_at = session_data.get("created_at")
        if created_at:
            try:
                created_time = datetime.fromisoformat(created_at)
                age_days = (datetime.now() - created_time).days
                max_age = self.validation_rules["session"]["max_session_age_days"]
                
                if age_days > max_age:
                    result.add_warning(f"세션이 오래되었습니다. ({age_days}일 전 생성)")
            except ValueError:
                result.add_warning("생성 시간 형식이 잘못되었습니다.")
        
        # 서비스 인스턴스 검증
        if "service" not in session_data:
            result.add_error("세션 서비스 인스턴스가 없습니다.")
        elif session_data["service"] is None:
            result.add_error("세션 서비스 인스턴스가 None입니다.")
        
        # 데이터 무결성 검증
        ocr_results = session_data.get("ocr_results", {})
        mapping_results = session_data.get("mapping_results", {})
        
        result.metadata["ocr_count"] = len(ocr_results)
        result.metadata["mapping_count"] = len(mapping_results)
        
        if mapping_results and not ocr_results:
            result.add_warning("OCR 결과 없이 매핑 결과가 존재합니다.")
        
        result.add_info(f"세션 데이터 검증 완료: {session_id}")
        
        # 검증 기록
        self._record_validation(result)
        
        return result
    
    def validate_business_rules(self, context: Dict) -> ValidationResult:
        """비즈니스 룰 검증
        
        Args:
            context: 검증 컨텍스트
            
        Returns:
            ValidationResult: 검증 결과
        """
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.BUSINESS_RULE,
            severity=ValidationSeverity.INFO,
            errors=[],
            warnings=[],
            info=[],
            metadata=context,
            timestamp=datetime.now().isoformat()
        )
        
        # API 키 검증
        required_keys = self.validation_rules["business"]["required_api_keys"]
        for key in required_keys:
            if not os.getenv(key):
                result.add_error(f"필수 API 키가 설정되지 않았습니다: {key}")
        
        # 동시 세션 수 검증
        concurrent_sessions = context.get("concurrent_sessions", 0)
        max_concurrent = self.validation_rules["business"]["max_concurrent_sessions"]
        
        if concurrent_sessions > max_concurrent:
            result.add_error(f"동시 세션 수가 한계를 초과했습니다. ({concurrent_sessions}/{max_concurrent})")
        
        # 일일 세션 수 검증
        daily_sessions = context.get("daily_sessions", 0)
        max_daily = self.validation_rules["business"]["max_daily_sessions"]
        
        if daily_sessions > max_daily:
            result.add_warning(f"일일 세션 수가 많습니다. ({daily_sessions}/{max_daily})")
        
        # 처리 시간 검증
        processing_time = context.get("processing_time", 0)
        max_processing_time = self.validation_rules["business"]["max_processing_time"]
        
        if processing_time > max_processing_time:
            result.add_warning(f"처리 시간이 오래 걸렸습니다. ({processing_time}초)")
        
        result.add_info("비즈니스 룰 검증 완료")
        
        # 검증 기록
        self._record_validation(result)
        
        return result
    
    def validate_multiple_files(self, files: List) -> ValidationResult:
        """여러 파일 일괄 검증
        
        Args:
            files: 파일 리스트
            
        Returns:
            ValidationResult: 통합 검증 결과
        """
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.FILE,
            severity=ValidationSeverity.INFO,
            errors=[],
            warnings=[],
            info=[],
            metadata={"file_count": len(files) if files else 0},
            timestamp=datetime.now().isoformat()
        )
        
        if not files:
            result.add_error("파일이 없습니다.")
            return result
        
        # 파일 수 검증
        max_images = self.validation_rules["session"]["max_images"]
        if len(files) > max_images:
            result.add_error(f"파일 수가 너무 많습니다. ({len(files)}/{max_images})")
        
        valid_files = []
        invalid_files = []
        total_size = 0
        
        # 각 파일 검증
        for i, file in enumerate(files):
            file_result = self.validate_uploaded_file(file, i)
            
            if file_result.is_valid:
                valid_files.append(file)
            else:
                invalid_files.append(file)
                for error in file_result.errors:
                    result.add_error(f"파일 {i+1}: {error}")
            
            # 경고 및 정보 메시지 통합
            for warning in file_result.warnings:
                result.add_warning(f"파일 {i+1}: {warning}")
            
            # 총 크기 계산
            file_size = file_result.metadata.get("file_size", 0)
            total_size += file_size
        
        result.metadata["valid_files"] = len(valid_files)
        result.metadata["invalid_files"] = len(invalid_files)
        result.metadata["total_size"] = total_size
        
        # 전체 크기 검증
        max_total_size = self.validation_rules["file"]["max_size"] * len(files)
        if total_size > max_total_size:
            result.add_warning(f"전체 파일 크기가 큽니다. ({total_size} bytes)")
        
        if valid_files:
            result.add_info(f"유효한 파일: {len(valid_files)}개")
        
        if invalid_files:
            result.add_info(f"유효하지 않은 파일: {len(invalid_files)}개")
        
        # 검증 기록
        self._record_validation(result)
        
        return result
    
    def _get_file_extension(self, filename: str) -> str:
        """파일 확장자 추출"""
        return os.path.splitext(filename.lower())[1]
    
    def _is_suspicious_filename(self, filename: str) -> bool:
        """의심스러운 파일명 검사"""
        suspicious_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$',
            r'\.vbs$', r'\.js$', r'\.jar$', r'\.zip$'
        ]
        
        filename_lower = filename.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, filename_lower):
                return True
        
        return False
    
    def _contains_only_special_chars(self, text: str) -> bool:
        """특수문자만 포함된 텍스트 검사"""
        cleaned_text = re.sub(r'[^\w\s]', '', text)
        return len(cleaned_text.strip()) == 0
    
    def _record_validation(self, result: ValidationResult):
        """검증 기록"""
        self.validation_history.append(result)
        
        # 최대 1000개까지만 보관
        if len(self.validation_history) > 1000:
            self.validation_history.pop(0)
        
        # 로깅
        if self.logging_manager:
            self.logging_manager.log_app_activity(
                f"검증 완료: {result.validation_type.value}",
                level="INFO" if result.is_valid else "WARNING",
                extra_data={
                    "validation_type": result.validation_type.value,
                    "is_valid": result.is_valid,
                    "error_count": len(result.errors),
                    "warning_count": len(result.warnings)
                }
            )
    
    def get_validation_statistics(self) -> Dict:
        """검증 통계 조회
        
        Returns:
            Dict: 검증 통계
        """
        total_validations = len(self.validation_history)
        successful_validations = sum(1 for r in self.validation_history if r.is_valid)
        
        by_type = {}
        by_severity = {}
        
        for result in self.validation_history:
            # 타입별 통계
            type_name = result.validation_type.value
            if type_name not in by_type:
                by_type[type_name] = {"total": 0, "successful": 0}
            by_type[type_name]["total"] += 1
            if result.is_valid:
                by_type[type_name]["successful"] += 1
            
            # 심각도별 통계
            severity_name = result.severity.value
            by_severity[severity_name] = by_severity.get(severity_name, 0) + 1
        
        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": successful_validations / total_validations * 100 if total_validations > 0 else 0,
            "by_type": by_type,
            "by_severity": by_severity,
            "recent_validations": [
                {
                    "type": r.validation_type.value,
                    "is_valid": r.is_valid,
                    "timestamp": r.timestamp,
                    "error_count": len(r.errors)
                }
                for r in self.validation_history[-10:]  # 최근 10개
            ]
        }
    
    def create_validation_report(self, results: List[ValidationResult]) -> str:
        """검증 결과 보고서 생성
        
        Args:
            results: 검증 결과 리스트
            
        Returns:
            str: 검증 보고서
        """
        report = "📋 검증 보고서\n"
        report += f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "=" * 50 + "\n\n"
        
        total_count = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        
        report += f"전체 검증: {total_count}개\n"
        report += f"성공: {valid_count}개\n"
        report += f"실패: {total_count - valid_count}개\n"
        report += f"성공률: {valid_count / total_count * 100:.1f}%\n\n"
        
        # 검증 결과 상세
        for i, result in enumerate(results, 1):
            status = "✅ 성공" if result.is_valid else "❌ 실패"
            report += f"{i}. {result.validation_type.value} 검증: {status}\n"
            
            if result.errors:
                report += f"   에러: {', '.join(result.errors)}\n"
            if result.warnings:
                report += f"   경고: {', '.join(result.warnings)}\n"
            if result.info:
                report += f"   정보: {', '.join(result.info)}\n"
            
            report += "\n"
        
        return report
    
    def clear_validation_history(self):
        """검증 히스토리 초기화"""
        self.validation_history.clear()
        
        if self.logging_manager:
            self.logging_manager.log_app_activity("검증 히스토리 초기화")
    
    def update_validation_rules(self, rules: Dict):
        """검증 규칙 업데이트
        
        Args:
            rules: 새로운 검증 규칙
        """
        self.validation_rules.update(rules)
        
        if self.logging_manager:
            self.logging_manager.log_app_activity("검증 규칙 업데이트")