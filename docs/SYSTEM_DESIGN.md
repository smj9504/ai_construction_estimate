# Reconstruction Estimation System Design

## Executive Summary

This document outlines the complete system design for an AI-powered reconstruction estimation application targeting the East US market. The system automates the entire estimation workflow from photo analysis through final cost validation.

## System Requirements

### Functional Requirements
1. **Photo Processing**: Extract measurements from multiple construction photos using OCR
2. **Work Scope Mapping**: Automatically map extracted data to reconstruction work scopes
3. **Three-Phase Estimation**:
   - Phase 1: Quantification (measurements, quantities, debris estimation)
   - Phase 2: Costing (material/labor pricing, regional adjustments)
   - Phase 3: Finalization (timeline, disposal, O&P, tax, validation)
4. **Conflict Detection**: Identify material/scope conflicts
5. **Regional Pricing**: East US specific pricing and regulations

### Non-Functional Requirements
- **Performance**: Process 10-20 photos within 30 seconds
- **Accuracy**: 95%+ OCR accuracy, 98%+ cost calculation accuracy
- **Usability**: Single-user optimized interface
- **Reliability**: Persistent session management, error recovery
- **Maintainability**: Modular architecture, clear separation of concerns

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          UI Layer                                │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐            │
│  │   Upload    │ │   Mapping    │ │  Estimation   │            │
│  │   Screen    │ │   Screen     │ │    Screen     │            │
│  └─────────────┘ └──────────────┘ └───────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐            │
│  │Quantification│ │   Costing    │ │  Estimation   │            │
│  │  Workflow   │ │   Workflow   │ │   Workflow    │            │
│  └─────────────┘ └──────────────┘ └───────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                       Domain Layer                               │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐            │
│  │Quantification│ │   Costing    │ │  Estimation   │            │
│  │   Domain    │ │    Domain    │ │    Domain     │            │
│  └─────────────┘ └──────────────┘ └───────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                          │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐            │
│  │     OCR     │ │   Database   │ │External APIs  │            │
│  │   Service   │ │   (SQLite)   │ │  (Pricing)    │            │
│  └─────────────┘ └──────────────┘ └───────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Domain Model Design

### Quantification Domain

```python
# Core Entities
class Measurement:
    id: str
    source_image: str
    measurement_type: MeasurementType  # LINEAR, AREA, VOLUME
    value: float
    unit: Unit  # FEET, INCHES, SQFT, CUFT
    confidence: float
    location: Optional[str]  # Room/area identifier

class WorkScope:
    id: str
    name: str
    category: WorkCategory  # DEMOLITION, INSTALLATION, FINISHING
    measurement_type: MeasurementType
    unit_of_measure: Unit
    material_requirements: List[MaterialRequirement]
    labor_requirements: LaborRequirement

class QuantificationItem:
    id: str
    work_scope: WorkScope
    measurements: List[Measurement]
    quantity: float
    debris_weight: Optional[float]  # For demolition items
    notes: Optional[str]

# Value Objects
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
```

### Costing Domain

```python
# Core Entities
class Material:
    id: str
    name: str
    category: str
    unit: Unit
    base_cost: Decimal
    regional_multiplier: Decimal  # East US adjustment
    supplier: Optional[str]
    last_updated: datetime

class Labor:
    id: str
    trade: str
    skill_level: SkillLevel
    hourly_rate: Decimal
    regional_rate: Decimal  # East US specific
    productivity_factor: float  # Units per hour

class CostItem:
    id: str
    quantification_item: QuantificationItem
    materials: List[MaterialCost]
    labor: LaborCost
    equipment: Optional[EquipmentCost]
    total_cost: Decimal

# Value Objects
class MaterialCost:
    material: Material
    quantity: float
    unit_cost: Decimal
    total_cost: Decimal
    waste_factor: float = 1.1  # 10% default waste

class LaborCost:
    labor: Labor
    hours: float
    rate: Decimal
    total_cost: Decimal
    difficulty_factor: float = 1.0
```

### Estimation Domain

```python
# Core Entities
class Project:
    id: str
    name: str
    location: str  # East US specific location
    created_date: datetime
    status: ProjectStatus
    quantification_items: List[QuantificationItem]
    cost_items: List[CostItem]
    timeline: Timeline
    estimate: Estimate

class Timeline:
    id: str
    tasks: List[Task]
    critical_path: List[Task]
    total_duration: int  # days
    buffer_percentage: float = 0.15  # 15% buffer

class Task:
    id: str
    name: str
    work_scope: WorkScope
    duration: int  # days
    dependencies: List[Task]
    can_parallel: bool
    crew_size: int

class Estimate:
    id: str
    project: Project
    direct_costs: Decimal
    disposal_costs: DisposalCost
    overhead_percentage: float
    profit_percentage: float
    sales_tax: SalesTax
    total_estimate: Decimal
    validation_status: ValidationStatus
    validation_checks: List[ValidationCheck]

# Value Objects
class DisposalCost:
    total_weight: float  # lbs
    disposal_method: DisposalMethod  # DUMPSTER, PICKUP
    unit_cost: Decimal
    total_cost: Decimal
    cleanup_cost: Decimal

class SalesTax:
    material_tax_rate: float
    labor_tax_rate: float
    tax_responsibility: TaxResponsibility  # CUSTOMER, CONTRACTOR
    total_tax: Decimal

class ValidationCheck:
    check_type: str
    status: bool
    message: str
    severity: Severity  # ERROR, WARNING, INFO
```

## Service Layer Design

### Core Services

```python
# services/ocr_enhanced_service.py
class EnhancedOCRService:
    """Enhanced OCR service with construction-specific processing"""
    def process_image(self, image_path: str) -> List[OCRResult]:
        # Preprocessing for construction drawings
        # Multi-pass OCR for accuracy
        # Pattern matching for measurements
        pass
    
    def extract_measurements(self, ocr_results: List[OCRResult]) -> List[Measurement]:
        # Parse feet/inches patterns
        # Extract dimensions (LxW)
        # Identify room/area labels
        pass

# services/quantification_service.py
class QuantificationService:
    """Handles all quantification logic"""
    def map_to_work_scopes(self, measurements: List[Measurement], 
                          work_scope_text: str) -> List[QuantificationItem]:
        # NLP processing of work scope text
        # Intelligent mapping to measurements
        # Quantity calculations
        pass
    
    def calculate_debris(self, items: List[QuantificationItem]) -> Dict[str, float]:
        # Calculate demolition debris by type
        # Estimate weights based on material
        pass
    
    def detect_conflicts(self, items: List[QuantificationItem]) -> List[Conflict]:
        # Check for material conflicts
        # Validate scope compatibility
        pass

# services/pricing_service.py
class PricingService:
    """Regional pricing and cost calculations"""
    def __init__(self, region: str = "EAST_US"):
        self.region = region
        self.pricing_engine = RegionalPricingEngine(region)
    
    def calculate_material_costs(self, item: QuantificationItem) -> List[MaterialCost]:
        # Lookup current regional prices
        # Apply waste factors
        # Calculate totals
        pass
    
    def calculate_labor_costs(self, item: QuantificationItem) -> LaborCost:
        # Determine crew requirements
        # Apply regional labor rates
        # Factor in complexity
        pass

# services/estimation_service.py
class EstimationService:
    """Final estimation and validation"""
    def generate_timeline(self, cost_items: List[CostItem]) -> Timeline:
        # Create task dependencies
        # Calculate critical path
        # Optimize for parallel work
        pass
    
    def calculate_overhead_profit(self, project: Project) -> Tuple[float, float]:
        # Complexity-based O&P calculation
        # Industry standard ranges
        pass
    
    def validate_estimate(self, estimate: Estimate) -> List[ValidationCheck]:
        # Price reasonableness checks
        # Quantity validation
        # Timeline feasibility
        pass
```

### Integration Services

```python
# services/workflow_orchestrator.py
class WorkflowOrchestrator:
    """Coordinates the three-phase estimation process"""
    def __init__(self):
        self.quantification_service = QuantificationService()
        self.pricing_service = PricingService()
        self.estimation_service = EstimationService()
    
    async def process_estimation(self, 
                                images: List[str], 
                                work_scope: str) -> Estimate:
        # Phase 1: Quantification
        measurements = await self._extract_measurements(images)
        quant_items = await self._map_work_scopes(measurements, work_scope)
        
        # Phase 2: Costing
        cost_items = await self._calculate_costs(quant_items)
        
        # Phase 3: Finalization
        estimate = await self._finalize_estimate(cost_items)
        
        return estimate
```

## Data Layer Design

### Database Schema (SQLite)

```sql
-- Work Scopes and Materials
CREATE TABLE work_scopes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    measurement_type TEXT NOT NULL,
    unit_of_measure TEXT NOT NULL,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE materials (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    base_cost DECIMAL(10,2) NOT NULL,
    east_us_multiplier DECIMAL(3,2) DEFAULT 1.0,
    supplier TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE labor_rates (
    id TEXT PRIMARY KEY,
    trade TEXT NOT NULL,
    skill_level TEXT NOT NULL,
    base_hourly_rate DECIMAL(6,2) NOT NULL,
    east_us_rate DECIMAL(6,2) NOT NULL,
    productivity_factor DECIMAL(4,2) DEFAULT 1.0
);

-- Projects and Estimates
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'DRAFT',
    metadata JSON
);

CREATE TABLE measurements (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    source_image TEXT NOT NULL,
    measurement_type TEXT NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    unit TEXT NOT NULL,
    confidence DECIMAL(3,2),
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quantification_items (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    work_scope_id TEXT REFERENCES work_scopes(id),
    quantity DECIMAL(10,2) NOT NULL,
    debris_weight DECIMAL(10,2),
    notes TEXT
);

CREATE TABLE cost_items (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    quantification_item_id TEXT REFERENCES quantification_items(id),
    material_cost DECIMAL(10,2),
    labor_cost DECIMAL(10,2),
    equipment_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2) NOT NULL
);

CREATE TABLE estimates (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    direct_costs DECIMAL(12,2) NOT NULL,
    disposal_costs DECIMAL(10,2),
    overhead_percentage DECIMAL(5,2),
    profit_percentage DECIMAL(5,2),
    sales_tax DECIMAL(10,2),
    total_estimate DECIMAL(12,2) NOT NULL,
    validation_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_materials_category ON materials(category);
CREATE INDEX idx_labor_trade ON labor_rates(trade);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_measurements_project ON measurements(project_id);
```

## API Design

### RESTful API Endpoints

```yaml
# Project Management
POST   /api/projects                    # Create new project
GET    /api/projects/{id}              # Get project details
PUT    /api/projects/{id}              # Update project
DELETE /api/projects/{id}              # Delete project

# Image Processing
POST   /api/projects/{id}/images       # Upload images
GET    /api/projects/{id}/images       # List images
POST   /api/projects/{id}/process-ocr  # Trigger OCR processing

# Quantification
POST   /api/projects/{id}/work-scopes  # Add work scope text
GET    /api/projects/{id}/quantification # Get quantification results
PUT    /api/projects/{id}/quantification/{item_id} # Update quantity

# Costing
GET    /api/projects/{id}/costs        # Get cost breakdown
POST   /api/projects/{id}/recalculate  # Recalculate costs

# Estimation
GET    /api/projects/{id}/estimate     # Get final estimate
POST   /api/projects/{id}/validate     # Run validation checks
GET    /api/projects/{id}/timeline     # Get project timeline

# Reference Data
GET    /api/materials                  # List materials with pricing
GET    /api/labor-rates               # List labor rates
GET    /api/work-scopes               # List available work scopes
```

### Internal Service Interfaces

```python
# interfaces/quantification_interface.py
class IQuantificationService(ABC):
    @abstractmethod
    async def process_measurements(self, 
                                  images: List[str]) -> List[Measurement]:
        pass
    
    @abstractmethod
    async def map_work_scopes(self, 
                             measurements: List[Measurement],
                             work_scope_text: str) -> List[QuantificationItem]:
        pass
    
    @abstractmethod
    async def calculate_quantities(self, 
                                  items: List[QuantificationItem]) -> Dict[str, float]:
        pass

# interfaces/costing_interface.py
class ICostingService(ABC):
    @abstractmethod
    async def price_materials(self, 
                             item: QuantificationItem) -> List[MaterialCost]:
        pass
    
    @abstractmethod
    async def price_labor(self, 
                         item: QuantificationItem) -> LaborCost:
        pass
    
    @abstractmethod
    async def calculate_total_cost(self, 
                                  item: QuantificationItem) -> CostItem:
        pass

# interfaces/estimation_interface.py
class IEstimationService(ABC):
    @abstractmethod
    async def create_timeline(self, 
                             cost_items: List[CostItem]) -> Timeline:
        pass
    
    @abstractmethod
    async def calculate_final_costs(self, 
                                   project: Project) -> Estimate:
        pass
    
    @abstractmethod
    async def validate_estimate(self, 
                               estimate: Estimate) -> ValidationResult:
        pass
```

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
1. Set up enhanced project structure
2. Implement domain models
3. Create database schema
4. Build core service interfaces

### Phase 2: Quantification (Weeks 3-4)
1. Enhance OCR service for construction drawings
2. Implement measurement extraction
3. Build work scope mapping with NLP
4. Add conflict detection

### Phase 3: Costing (Weeks 5-6)
1. Create pricing database for East US
2. Implement material/labor calculators
3. Build cost aggregation logic
4. Add regional adjustments

### Phase 4: Estimation (Weeks 7-8)
1. Implement timeline generation
2. Add disposal cost calculations
3. Build O&P calculators
4. Implement tax calculations
5. Create validation engine

### Phase 5: Integration (Weeks 9-10)
1. Build workflow orchestrator
2. Create API endpoints
3. Enhance UI for new features
4. Implement end-to-end testing

### Phase 6: Polish (Weeks 11-12)
1. Performance optimization
2. Error handling improvements
3. User experience enhancements
4. Documentation completion

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (for API layer)
- **Database**: SQLite (embedded, perfect for single user)
- **ORM**: SQLAlchemy 2.0
- **Task Queue**: Celery (for async OCR processing)

### Libraries
- **OCR**: EasyOCR + Tesseract (dual engine for accuracy)
- **NLP**: spaCy (for work scope parsing)
- **Image Processing**: OpenCV + Pillow
- **Validation**: Pydantic
- **Testing**: pytest + pytest-asyncio

### Frontend
- **Framework**: Gradio (existing) + React components
- **State Management**: Redux Toolkit
- **Styling**: Tailwind CSS
- **Charts**: Chart.js (for cost breakdowns)

## Security Considerations

1. **Data Protection**: All project data encrypted at rest
2. **API Security**: Token-based authentication (even for single user)
3. **Input Validation**: Strict validation on all inputs
4. **File Upload**: Virus scanning, size limits, type validation
5. **Audit Trail**: Complete logging of all operations

## Performance Optimization

1. **OCR Caching**: Cache processed images to avoid reprocessing
2. **Batch Processing**: Process multiple images in parallel
3. **Database Indexes**: Optimize queries with proper indexing
4. **Lazy Loading**: Load data on demand in UI
5. **Background Jobs**: Heavy processing in background tasks

## Conclusion

This design provides a robust, scalable foundation for your reconstruction estimation system. The three-phase approach (Quantification → Costing → Estimation) is clearly reflected in the architecture, with proper separation of concerns and extensibility for future enhancements.