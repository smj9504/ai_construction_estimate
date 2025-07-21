# API Specification for Reconstruction Estimation System

## Overview

This document defines the complete API specification for the reconstruction estimation system, including service contracts, data models, and integration patterns.

## Core Domain Interfaces

### Quantification Domain APIs

```python
# domain/quantification/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from enum import Enum

# Enumerations
class MeasurementType(Enum):
    LINEAR = "linear"
    AREA = "area"
    VOLUME = "volume"
    COUNT = "count"

class Unit(Enum):
    FEET = "ft"
    INCHES = "in"
    SQUARE_FEET = "sqft"
    CUBIC_FEET = "cuft"
    CUBIC_YARDS = "cuyd"
    POUNDS = "lbs"
    EACH = "ea"

class WorkCategory(Enum):
    DEMOLITION = "demolition"
    INSTALLATION = "installation"
    FINISHING = "finishing"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"

# Data Transfer Objects
@dataclass
class MeasurementDTO:
    source_image: str
    measurement_type: MeasurementType
    value: float
    unit: Unit
    confidence: float
    location: Optional[str] = None
    extracted_text: Optional[str] = None

@dataclass
class WorkScopeDTO:
    name: str
    category: WorkCategory
    measurement_type: MeasurementType
    unit_of_measure: Unit
    description: Optional[str] = None

@dataclass
class QuantificationItemDTO:
    work_scope: WorkScopeDTO
    measurements: List[MeasurementDTO]
    quantity: float
    debris_weight: Optional[float] = None
    notes: Optional[str] = None

@dataclass
class ConflictDTO:
    item1: QuantificationItemDTO
    item2: QuantificationItemDTO
    conflict_type: str
    severity: str  # "error", "warning"
    message: str

# Service Interfaces
class IOCRService(ABC):
    @abstractmethod
    async def process_image(self, image_path: str) -> List[Dict[str, any]]:
        """Process an image and return raw OCR results"""
        pass
    
    @abstractmethod
    async def extract_measurements(self, 
                                  ocr_results: List[Dict[str, any]]) -> List[MeasurementDTO]:
        """Extract measurements from OCR results"""
        pass
    
    @abstractmethod
    async def batch_process_images(self, 
                                  image_paths: List[str]) -> Dict[str, List[MeasurementDTO]]:
        """Process multiple images in parallel"""
        pass

class IQuantificationService(ABC):
    @abstractmethod
    async def map_measurements_to_scopes(self, 
                                        measurements: List[MeasurementDTO],
                                        work_scope_text: str) -> List[QuantificationItemDTO]:
        """Map measurements to work scopes based on text description"""
        pass
    
    @abstractmethod
    async def calculate_quantities(self, 
                                  items: List[QuantificationItemDTO]) -> Dict[str, float]:
        """Calculate total quantities by work scope"""
        pass
    
    @abstractmethod
    async def estimate_debris_weight(self, 
                                    items: List[QuantificationItemDTO]) -> Dict[str, float]:
        """Estimate debris weight for demolition items"""
        pass
    
    @abstractmethod
    async def detect_conflicts(self, 
                              items: List[QuantificationItemDTO]) -> List[ConflictDTO]:
        """Detect conflicts between work scope items"""
        pass

class IWorkScopeRepository(ABC):
    @abstractmethod
    async def get_all_scopes(self) -> List[WorkScopeDTO]:
        """Retrieve all available work scopes"""
        pass
    
    @abstractmethod
    async def get_scope_by_name(self, name: str) -> Optional[WorkScopeDTO]:
        """Get a specific work scope by name"""
        pass
    
    @abstractmethod
    async def search_scopes(self, query: str) -> List[WorkScopeDTO]:
        """Search work scopes by keyword"""
        pass
```

### Costing Domain APIs

```python
# domain/costing/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from enum import Enum

# Enumerations
class SkillLevel(Enum):
    APPRENTICE = "apprentice"
    JOURNEYMAN = "journeyman"
    MASTER = "master"

class PriceSource(Enum):
    MANUAL = "manual"
    API = "api"
    DATABASE = "database"
    ESTIMATED = "estimated"

# Data Transfer Objects
@dataclass
class MaterialDTO:
    name: str
    category: str
    unit: Unit
    base_cost: Decimal
    regional_multiplier: Decimal = Decimal("1.0")
    supplier: Optional[str] = None
    last_updated: Optional[datetime] = None
    price_source: PriceSource = PriceSource.DATABASE

@dataclass
class LaborDTO:
    trade: str
    skill_level: SkillLevel
    hourly_rate: Decimal
    regional_rate: Decimal
    productivity_factor: float = 1.0
    crew_size: int = 1

@dataclass
class MaterialCostDTO:
    material: MaterialDTO
    quantity: float
    unit_cost: Decimal
    waste_factor: float
    total_cost: Decimal

@dataclass
class LaborCostDTO:
    labor: LaborDTO
    hours: float
    rate: Decimal
    difficulty_factor: float
    total_cost: Decimal

@dataclass
class EquipmentCostDTO:
    equipment_name: str
    daily_rate: Decimal
    days: float
    total_cost: Decimal

@dataclass
class CostItemDTO:
    quantification_item: QuantificationItemDTO
    materials: List[MaterialCostDTO]
    labor: LaborCostDTO
    equipment: Optional[EquipmentCostDTO]
    subtotal: Decimal
    markup_percentage: float
    total_cost: Decimal

# Service Interfaces
class IPricingService(ABC):
    @abstractmethod
    async def get_material_price(self, 
                                material_name: str,
                                region: str = "EAST_US") -> MaterialDTO:
        """Get current material pricing for region"""
        pass
    
    @abstractmethod
    async def get_labor_rate(self, 
                            trade: str,
                            skill_level: SkillLevel,
                            region: str = "EAST_US") -> LaborDTO:
        """Get current labor rate for trade and region"""
        pass
    
    @abstractmethod
    async def calculate_material_costs(self, 
                                      item: QuantificationItemDTO) -> List[MaterialCostDTO]:
        """Calculate material costs for a quantification item"""
        pass
    
    @abstractmethod
    async def calculate_labor_costs(self, 
                                   item: QuantificationItemDTO) -> LaborCostDTO:
        """Calculate labor costs for a quantification item"""
        pass
    
    @abstractmethod
    async def calculate_equipment_costs(self, 
                                       item: QuantificationItemDTO) -> Optional[EquipmentCostDTO]:
        """Calculate equipment costs if needed"""
        pass

class ICostCalculationService(ABC):
    @abstractmethod
    async def calculate_item_cost(self, 
                                 item: QuantificationItemDTO) -> CostItemDTO:
        """Calculate total cost for a single item"""
        pass
    
    @abstractmethod
    async def calculate_project_costs(self, 
                                     items: List[QuantificationItemDTO]) -> List[CostItemDTO]:
        """Calculate costs for all project items"""
        pass
    
    @abstractmethod
    async def apply_regional_adjustments(self, 
                                        costs: List[CostItemDTO],
                                        region: str) -> List[CostItemDTO]:
        """Apply regional cost adjustments"""
        pass

class IPriceRepository(ABC):
    @abstractmethod
    async def get_materials_by_category(self, 
                                       category: str) -> List[MaterialDTO]:
        """Get all materials in a category"""
        pass
    
    @abstractmethod
    async def get_labor_rates_by_trade(self, 
                                      trade: str) -> List[LaborDTO]:
        """Get all labor rates for a trade"""
        pass
    
    @abstractmethod
    async def update_material_price(self, 
                                   material_id: str,
                                   new_price: Decimal) -> bool:
        """Update material pricing"""
        pass
```

### Estimation Domain APIs

```python
# domain/estimation/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum

# Enumerations
class ProjectStatus(Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"

class DisposalMethod(Enum):
    DUMPSTER = "dumpster"
    PICKUP = "pickup"
    RECYCLING = "recycling"

class TaxResponsibility(Enum):
    CUSTOMER = "customer"
    CONTRACTOR = "contractor"

class ValidationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNINGS = "warnings"

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

# Data Transfer Objects
@dataclass
class TaskDTO:
    name: str
    work_scope: WorkScopeDTO
    duration_days: int
    dependencies: List[str]  # Task IDs
    can_parallel: bool
    crew_size: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

@dataclass
class TimelineDTO:
    tasks: List[TaskDTO]
    critical_path: List[str]  # Task IDs
    total_duration_days: int
    buffer_percentage: float
    start_date: datetime
    end_date: datetime

@dataclass
class DisposalCostDTO:
    total_weight_lbs: float
    disposal_method: DisposalMethod
    container_size: Optional[str]
    unit_cost: Decimal
    disposal_cost: Decimal
    cleanup_labor_hours: float
    cleanup_cost: Decimal
    total_cost: Decimal

@dataclass
class SalesTaxDTO:
    material_tax_rate: float
    labor_tax_rate: float
    tax_responsibility: TaxResponsibility
    taxable_materials: Decimal
    taxable_labor: Decimal
    material_tax: Decimal
    labor_tax: Decimal
    total_tax: Decimal

@dataclass
class ValidationCheckDTO:
    check_type: str
    status: bool
    message: str
    severity: Severity
    details: Optional[Dict[str, any]] = None

@dataclass
class EstimateDTO:
    project_id: str
    direct_costs: Decimal
    disposal_costs: DisposalCostDTO
    overhead_percentage: float
    overhead_amount: Decimal
    profit_percentage: float
    profit_amount: Decimal
    sales_tax: SalesTaxDTO
    subtotal: Decimal
    total_estimate: Decimal
    validation_status: ValidationStatus
    validation_checks: List[ValidationCheckDTO]
    created_date: datetime
    valid_until: datetime

@dataclass
class ProjectDTO:
    id: str
    name: str
    location: str
    customer_name: Optional[str]
    created_date: datetime
    status: ProjectStatus
    quantification_items: List[QuantificationItemDTO]
    cost_items: List[CostItemDTO]
    timeline: Optional[TimelineDTO]
    estimate: Optional[EstimateDTO]

# Service Interfaces
class ITimelineService(ABC):
    @abstractmethod
    async def create_timeline(self, 
                             cost_items: List[CostItemDTO]) -> TimelineDTO:
        """Generate project timeline from cost items"""
        pass
    
    @abstractmethod
    async def optimize_timeline(self, 
                               timeline: TimelineDTO) -> TimelineDTO:
        """Optimize timeline for parallel execution"""
        pass
    
    @abstractmethod
    async def calculate_critical_path(self, 
                                     tasks: List[TaskDTO]) -> List[str]:
        """Calculate critical path through tasks"""
        pass

class IDisposalService(ABC):
    @abstractmethod
    async def calculate_disposal_costs(self, 
                                      debris_weights: Dict[str, float],
                                      method: DisposalMethod) -> DisposalCostDTO:
        """Calculate disposal and cleanup costs"""
        pass
    
    @abstractmethod
    async def recommend_disposal_method(self, 
                                       total_weight: float) -> DisposalMethod:
        """Recommend best disposal method based on weight"""
        pass

class IEstimationService(ABC):
    @abstractmethod
    async def calculate_overhead_profit(self, 
                                       project: ProjectDTO) -> Tuple[float, float]:
        """Calculate overhead and profit percentages"""
        pass
    
    @abstractmethod
    async def calculate_sales_tax(self, 
                                 project: ProjectDTO,
                                 tax_config: Dict[str, any]) -> SalesTaxDTO:
        """Calculate sales tax based on location and rules"""
        pass
    
    @abstractmethod
    async def generate_estimate(self, 
                               project: ProjectDTO) -> EstimateDTO:
        """Generate complete estimate for project"""
        pass
    
    @abstractmethod
    async def validate_estimate(self, 
                               estimate: EstimateDTO) -> List[ValidationCheckDTO]:
        """Validate estimate for accuracy and completeness"""
        pass

class IProjectRepository(ABC):
    @abstractmethod
    async def create_project(self, 
                            project: ProjectDTO) -> str:
        """Create new project and return ID"""
        pass
    
    @abstractmethod
    async def get_project(self, 
                         project_id: str) -> Optional[ProjectDTO]:
        """Retrieve project by ID"""
        pass
    
    @abstractmethod
    async def update_project(self, 
                            project: ProjectDTO) -> bool:
        """Update existing project"""
        pass
    
    @abstractmethod
    async def list_projects(self, 
                           status: Optional[ProjectStatus] = None) -> List[ProjectDTO]:
        """List all projects, optionally filtered by status"""
        pass
```

## Workflow Orchestration API

```python
# application/workflow/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncIterator
from dataclasses import dataclass

@dataclass
class WorkflowStepResult:
    step_name: str
    status: str  # "success", "failed", "skipped"
    duration_seconds: float
    data: Optional[Dict[str, any]] = None
    error: Optional[str] = None

@dataclass
class WorkflowProgress:
    current_step: str
    total_steps: int
    completed_steps: int
    percentage: float
    estimated_time_remaining: Optional[float] = None

class IWorkflowOrchestrator(ABC):
    @abstractmethod
    async def start_estimation_workflow(self, 
                                       project_id: str,
                                       images: List[str],
                                       work_scope_text: str) -> AsyncIterator[WorkflowProgress]:
        """Start the three-phase estimation workflow"""
        pass
    
    @abstractmethod
    async def get_workflow_status(self, 
                                 workflow_id: str) -> Dict[str, any]:
        """Get current status of a workflow"""
        pass
    
    @abstractmethod
    async def cancel_workflow(self, 
                             workflow_id: str) -> bool:
        """Cancel a running workflow"""
        pass

# Phase-specific orchestrators
class IQuantificationOrchestrator(ABC):
    @abstractmethod
    async def execute_phase1(self, 
                            images: List[str],
                            work_scope_text: str) -> List[QuantificationItemDTO]:
        """Execute Phase 1: Quantification"""
        pass

class ICostingOrchestrator(ABC):
    @abstractmethod
    async def execute_phase2(self, 
                            quantification_items: List[QuantificationItemDTO],
                            region: str = "EAST_US") -> List[CostItemDTO]:
        """Execute Phase 2: Costing"""
        pass

class IEstimationOrchestrator(ABC):
    @abstractmethod
    async def execute_phase3(self, 
                            project: ProjectDTO) -> EstimateDTO:
        """Execute Phase 3: Estimation & Validation"""
        pass
```

## Event-Driven Communication

```python
# infrastructure/events/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DomainEvent:
    event_type: str
    aggregate_id: str
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None

# Event Types
class QuantificationEvents:
    MEASUREMENTS_EXTRACTED = "quantification.measurements_extracted"
    WORK_SCOPES_MAPPED = "quantification.work_scopes_mapped"
    CONFLICTS_DETECTED = "quantification.conflicts_detected"
    QUANTIFICATION_COMPLETED = "quantification.completed"

class CostingEvents:
    MATERIALS_PRICED = "costing.materials_priced"
    LABOR_CALCULATED = "costing.labor_calculated"
    COSTS_CALCULATED = "costing.costs_calculated"
    COSTING_COMPLETED = "costing.completed"

class EstimationEvents:
    TIMELINE_GENERATED = "estimation.timeline_generated"
    DISPOSAL_CALCULATED = "estimation.disposal_calculated"
    OVERHEAD_PROFIT_CALCULATED = "estimation.overhead_profit_calculated"
    TAX_CALCULATED = "estimation.tax_calculated"
    ESTIMATE_GENERATED = "estimation.estimate_generated"
    VALIDATION_COMPLETED = "estimation.validation_completed"

# Event Bus Interface
class IEventBus(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event"""
        pass
    
    @abstractmethod
    def subscribe(self, 
                  event_type: str,
                  handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe to a domain event"""
        pass
    
    @abstractmethod
    def unsubscribe(self, 
                    event_type: str,
                    handler: Callable[[DomainEvent], None]) -> None:
        """Unsubscribe from a domain event"""
        pass
```

## External Integration APIs

```python
# infrastructure/external/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from decimal import Decimal

class IPricingDataProvider(ABC):
    """Interface for external pricing data sources"""
    
    @abstractmethod
    async def get_material_prices(self, 
                                 materials: List[str],
                                 region: str) -> Dict[str, Decimal]:
        """Fetch current material prices from external source"""
        pass
    
    @abstractmethod
    async def get_labor_rates(self, 
                             trades: List[str],
                             region: str) -> Dict[str, Decimal]:
        """Fetch current labor rates from external source"""
        pass

class IAddressValidationService(ABC):
    """Interface for address validation and geocoding"""
    
    @abstractmethod
    async def validate_address(self, 
                              address: str) -> Dict[str, any]:
        """Validate and standardize address"""
        pass
    
    @abstractmethod
    async def get_tax_jurisdiction(self, 
                                   address: str) -> Dict[str, float]:
        """Get tax rates for address"""
        pass

class IDocumentGenerationService(ABC):
    """Interface for generating estimate documents"""
    
    @abstractmethod
    async def generate_pdf_estimate(self, 
                                   estimate: EstimateDTO) -> bytes:
        """Generate PDF estimate document"""
        pass
    
    @abstractmethod
    async def generate_excel_breakdown(self, 
                                      project: ProjectDTO) -> bytes:
        """Generate Excel cost breakdown"""
        pass
```

## Error Handling

```python
# common/exceptions.py
class DomainException(Exception):
    """Base exception for domain errors"""
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.code = code

class QuantificationException(DomainException):
    """Exceptions related to quantification phase"""
    pass

class CostingException(DomainException):
    """Exceptions related to costing phase"""
    pass

class EstimationException(DomainException):
    """Exceptions related to estimation phase"""
    pass

# Specific exceptions
class OCRProcessingError(QuantificationException):
    """Error during OCR processing"""
    pass

class WorkScopeMappingError(QuantificationException):
    """Error mapping measurements to work scopes"""
    pass

class PricingDataNotFoundError(CostingException):
    """Pricing data not available"""
    pass

class InvalidEstimateError(EstimationException):
    """Estimate validation failed"""
    pass
```

## Implementation Guidelines

### Service Implementation Pattern

```python
# Example service implementation
class QuantificationService(IQuantificationService):
    def __init__(self, 
                 ocr_service: IOCRService,
                 work_scope_repo: IWorkScopeRepository,
                 event_bus: IEventBus):
        self.ocr_service = ocr_service
        self.work_scope_repo = work_scope_repo
        self.event_bus = event_bus
    
    async def map_measurements_to_scopes(self, 
                                        measurements: List[MeasurementDTO],
                                        work_scope_text: str) -> List[QuantificationItemDTO]:
        try:
            # Implementation logic here
            result = await self._perform_mapping(measurements, work_scope_text)
            
            # Publish event
            await self.event_bus.publish(DomainEvent(
                event_type=QuantificationEvents.WORK_SCOPES_MAPPED,
                aggregate_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                data={"item_count": len(result)}
            ))
            
            return result
        except Exception as e:
            raise WorkScopeMappingError(f"Failed to map measurements: {str(e)}")
```

### Repository Implementation Pattern

```python
# Example repository implementation
class SQLiteProjectRepository(IProjectRepository):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    async def create_project(self, project: ProjectDTO) -> str:
        async with aiosqlite.connect(self.connection_string) as db:
            project_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO projects (id, name, location, status, created_date) VALUES (?, ?, ?, ?, ?)",
                (project_id, project.name, project.location, project.status.value, project.created_date)
            )
            await db.commit()
            return project_id
```

This API specification provides a complete contract-based design for the reconstruction estimation system, ensuring clean separation of concerns and testability.