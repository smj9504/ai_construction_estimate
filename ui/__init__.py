"""
UI 모듈 초기화
UI 관련 클래스와 함수들을 외부에서 쉽게 사용할 수 있도록 노출합니다.
"""

from .interface import (
    ConstructionEstimatorInterface,
    create_interface,
    create_interface_with_components,
    get_interface_manager,
    reset_interface_manager
)

from .components import (
    HeaderComponents,
    OCRComponents,
    MappingComponents,
    ResultComponents,
    UtilityComponents,
    HTMLGenerators,
    ComponentFactory,
    component_factory
)

from .handlers import (
    SessionHandlers,
    OCRHandlers,
    MappingHandlers,
    ResultsHandlers,
    ValidationHandlers,
    EventHandlerRegistry,
    get_session_handlers,
    get_ocr_handlers,
    get_mapping_handlers,
    get_results_handlers,
    get_validation_handlers,
    create_combined_ocr_handler,
    create_combined_mapping_handler,
    create_session_update_chain,
    handler_registry
)

from .styles import (
    get_main_css,
    get_dark_theme_css,
    get_component_class,
    get_full_css,
    COMPONENT_STYLES
)

# 주요 exports
__all__ = [
    # Interface
    'ConstructionEstimatorInterface',
    'create_interface',
    'create_interface_with_components',
    'get_interface_manager',
    'reset_interface_manager',
    
    # Components
    'HeaderComponents',
    'OCRComponents', 
    'MappingComponents',
    'ResultComponents',
    'UtilityComponents',
    'HTMLGenerators',
    'ComponentFactory',
    'component_factory',
    
    # Handlers
    'SessionHandlers',
    'OCRHandlers',
    'MappingHandlers', 
    'ResultsHandlers',
    'ValidationHandlers',
    'EventHandlerRegistry',
    'get_session_handlers',
    'get_ocr_handlers',
    'get_mapping_handlers',
    'get_results_handlers',
    'get_validation_handlers',
    'create_combined_ocr_handler',
    'create_combined_mapping_handler',
    'handler_registry',
    
    # Styles
    'get_main_css',
    'get_dark_theme_css',
    'get_component_class',
    'get_full_css',
    'COMPONENT_STYLES'
]

# 버전 정보
__version__ = "1.0.0"
__author__ = "Construction Estimator Team"
__description__ = "Construction Estimator Phase 1 MVP User Interface"