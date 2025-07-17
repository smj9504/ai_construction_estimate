"""
Core 모듈 초기화
핵심 기능 모듈들을 외부에서 쉽게 사용할 수 있도록 노출합니다.
"""

from .ocr_service import (
    OCRService,
    create_ocr_service,
    quick_extract_measurements,
    extract_from_single_image,
    get_global_ocr_service,
    reset_global_ocr_service
)

from .data_mapper import (
    DataMapper,
    RoomType,
    WorkType,
    WorkScope,
    MeasurementData,
    create_data_mapper,
    quick_mapping,
    parse_scope_only,
    process_measurements_only,
    get_global_data_mapper,
    reset_global_data_mapper
)

from .file_handler import (
    FileHandler,
    create_file_handler,
    quick_file_processing
)

# 주요 exports
__all__ = [
    # OCR Service
    'OCRService',
    'create_ocr_service',
    'quick_extract_measurements',
    'extract_from_single_image',
    'get_global_ocr_service',
    'reset_global_ocr_service',
    
    # Data Mapper
    'DataMapper',
    'RoomType',
    'WorkType', 
    'WorkScope',
    'MeasurementData',
    'create_data_mapper',
    'quick_mapping',
    'parse_scope_only',
    'process_measurements_only',
    'get_global_data_mapper',
    'reset_global_data_mapper',
    
    # File Handler
    'FileHandler',
    'create_file_handler',
    'quick_file_processing'
]

# 버전 정보
__version__ = "1.0.0"
__author__ = "Construction Estimator Team"
__description__ = "Construction Estimator Phase 1 MVP Core Modules"