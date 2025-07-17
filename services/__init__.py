"""
Services 모듈 초기화
비즈니스 로직 서비스들을 외부에서 쉽게 사용할 수 있도록 노출합니다.
"""

from .estimator_service import (
    EstimatorService,
    get_estimator_service,
    reset_estimator_service
)

# 주요 exports
__all__ = [
    'EstimatorService',
    'get_estimator_service', 
    'reset_estimator_service'
]

# 버전 정보
__version__ = "1.0.0"
__author__ = "Construction Estimator Team"
__description__ = "Construction Estimator Phase 1 MVP Business Logic Services"