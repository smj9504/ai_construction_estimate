# Implementation Guide for Reconstruction Estimation System

## Overview

This guide provides detailed implementation instructions for building the reconstruction estimation system based on the comprehensive design specifications. It includes step-by-step development phases, code patterns, and best practices.

## Implementation Strategy

### Phase-Based Development Approach

The implementation follows a **Domain-Driven Development** strategy with incremental delivery:

1. **Foundation Phase** (Weeks 1-2): Core infrastructure and domain models
2. **Quantification Phase** (Weeks 3-4): OCR processing and work scope mapping
3. **Costing Phase** (Weeks 5-6): Pricing engine and cost calculations
4. **Estimation Phase** (Weeks 7-8): Timeline, disposal, and final estimates
5. **Integration Phase** (Weeks 9-10): Workflow orchestration and UI
6. **Polish Phase** (Weeks 11-12): Performance optimization and testing

## Phase 1: Foundation Implementation

### Project Structure Setup

```
ai_construction_estimate/
├── domain/
│   ├── __init__.py
│   ├── quantification/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── value_objects.py
│   │   ├── repositories.py
│   │   └── services.py
│   ├── costing/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── value_objects.py
│   │   ├── repositories.py
│   │   └── services.py
│   └── estimation/
│       ├── __init__.py
│       ├── entities.py
│       ├── value_objects.py
│       ├── repositories.py
│       └── services.py
├── application/
│   ├── __init__.py
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── quantification_workflow.py
│   │   ├── costing_workflow.py
│   │   └── estimation_workflow.py
│   └── services/
│       ├── __init__.py
│       └── orchestrator.py
├── infrastructure/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── migrations/
│   ├── external/
│   │   ├── __init__.py
│   │   ├── ocr_service.py
│   │   └── pricing_api.py
│   └── config/
│       ├── __init__.py
│       ├── database.py
│       └── settings.py
├── ui/
│   ├── __init__.py
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── quantification_screen.py
│   │   ├── costing_screen.py
│   │   └── estimation_screen.py
│   ├── components/
│   │   ├── __init__.py
│   │   └── estimation_components.py
│   └── handlers/
│       ├── __init__.py
│       └── estimation_handlers.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── data/
│   ├── database/
│   ├── uploads/
│   └── backups/
├── docs/
├── main.py
├── requirements.txt
└── pyproject.toml
```

### Core Domain Models Implementation

```python
# domain/quantification/entities.py
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from enum import Enum
import uuid

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

@dataclass
class Measurement:
    """Domain entity representing an extracted measurement"""
    id: str
    source_image: str
    measurement_type: MeasurementType
    value: Decimal
    unit: Unit
    confidence: float
    location: Optional[str] = None
    extracted_text: Optional[str] = None
    bounding_box: Optional[dict] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def is_high_confidence(self) -> bool:
        """Check if measurement has high confidence"""
        return self.confidence >= 0.8
    
    def to_square_feet(self) -> Decimal:
        """Convert measurement to square feet if applicable"""
        if self.unit == Unit.SQUARE_FEET:
            return self.value
        elif self.unit == Unit.FEET and self.measurement_type == MeasurementType.AREA:
            # Assume square if only one dimension given
            return self.value * self.value
        else:
            raise ValueError(f"Cannot convert {self.unit} to square feet")

@dataclass
class WorkScope:
    """Domain entity representing a work scope definition"""
    id: str
    code: str
    name: str
    category: WorkCategory
    measurement_type: MeasurementType
    unit_of_measure: Unit
    description: Optional[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.keywords is None:
            self.keywords = []
    
    def matches_keywords(self, text: str) -> bool:
        """Check if text contains any of the work scope keywords"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.keywords)

@dataclass
class QuantificationItem:
    """Domain entity representing a quantified work scope item"""
    id: str
    work_scope: WorkScope
    measurements: List[Measurement]
    quantity: Decimal
    unit: Unit
    location: Optional[str] = None
    debris_weight: Optional[Decimal] = None
    notes: Optional[str] = None
    manual_override: bool = False
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def calculate_total_quantity(self) -> Decimal:
        """Calculate total quantity from measurements"""
        if self.manual_override:
            return self.quantity
        
        total = Decimal('0')
        for measurement in self.measurements:
            if measurement.unit == self.unit:
                total += measurement.value
        
        return total
    
    def estimate_debris_weight(self) -> Decimal:
        """Estimate debris weight for demolition work"""
        if self.work_scope.category != WorkCategory.DEMOLITION:
            return Decimal('0')
        
        # Weight factors per sqft/linear ft based on material type
        weight_factors = {
            'drywall': Decimal('2.5'),  # lbs per sqft
            'flooring': Decimal('1.5'),  # lbs per sqft
            'tile': Decimal('4.0'),     # lbs per sqft
            'trim': Decimal('1.0'),     # lbs per linear ft
        }
        
        # Simple keyword-based weight estimation
        for keyword, factor in weight_factors.items():
            if any(keyword in kw.lower() for kw in self.work_scope.keywords):
                return self.quantity * factor
        
        # Default weight factor
        return self.quantity * Decimal('2.0')
```

### Database Models and Repository Implementation

```python
# infrastructure/database/models.py
from sqlalchemy import Column, String, Decimal, Integer, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class ProjectModel(Base):
    __tablename__ = 'projects'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String, nullable=False)
    address = Column(String)
    customer_name = Column(String)
    customer_email = Column(String)
    customer_phone = Column(String)
    status = Column(String, nullable=False, default='DRAFT')
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime)
    
    # Relationships
    images = relationship("ProjectImageModel", back_populates="project")
    quantification_items = relationship("QuantificationItemModel", back_populates="project")
    cost_items = relationship("CostItemModel", back_populates="project")
    estimates = relationship("ProjectEstimateModel", back_populates="project")

class ProjectImageModel(Base):
    __tablename__ = 'project_images'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now)
    processed = Column(Boolean, default=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="images")
    measurements = relationship("MeasurementModel", back_populates="image")

class WorkScopeModel(Base):
    __tablename__ = 'work_scopes'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    measurement_type = Column(String, nullable=False)
    unit_of_measure = Column(String, nullable=False)
    description = Column(Text)
    keywords = Column(Text)  # Comma-separated
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    quantification_items = relationship("QuantificationItemModel", back_populates="work_scope")

class MeasurementModel(Base):
    __tablename__ = 'measurements'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    image_id = Column(String, ForeignKey('project_images.id'), nullable=False)
    measurement_type = Column(String, nullable=False)
    value = Column(Decimal(10, 3), nullable=False)
    unit = Column(String, nullable=False)
    confidence = Column(Decimal(3, 2))
    location = Column(String)
    extracted_text = Column(Text)
    bounding_box = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    project = relationship("ProjectModel")
    image = relationship("ProjectImageModel", back_populates="measurements")

class QuantificationItemModel(Base):
    __tablename__ = 'quantification_items'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    work_scope_id = Column(String, ForeignKey('work_scopes.id'), nullable=False)
    quantity = Column(Decimal(10, 3), nullable=False)
    unit = Column(String, nullable=False)
    location = Column(String)
    debris_weight = Column(Decimal(10, 2))
    notes = Column(Text)
    manual_override = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="quantification_items")
    work_scope = relationship("WorkScopeModel", back_populates="quantification_items")
    cost_items = relationship("CostItemModel", back_populates="quantification_item")

# Repository Implementation
# infrastructure/database/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from domain.quantification.repositories import IProjectRepository
from domain.quantification.entities import Project, QuantificationItem
from infrastructure.database.models import ProjectModel, QuantificationItemModel

class SQLiteProjectRepository(IProjectRepository):
    def __init__(self, session: Session):
        self.session = session
    
    async def create(self, project: Project) -> str:
        """Create a new project"""
        project_model = ProjectModel(
            id=project.id,
            name=project.name,
            description=project.description,
            location=project.location,
            status=project.status.value
        )
        
        self.session.add(project_model)
        self.session.commit()
        return project_model.id
    
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        project_model = self.session.query(ProjectModel).filter(
            ProjectModel.id == project_id,
            ProjectModel.deleted_at.is_(None)
        ).first()
        
        if not project_model:
            return None
        
        return self._model_to_entity(project_model)
    
    async def update(self, project: Project) -> bool:
        """Update existing project"""
        project_model = self.session.query(ProjectModel).filter(
            ProjectModel.id == project.id
        ).first()
        
        if not project_model:
            return False
        
        project_model.name = project.name
        project_model.description = project.description
        project_model.location = project.location
        project_model.status = project.status.value
        
        self.session.commit()
        return True
    
    async def list_all(self, status: Optional[str] = None) -> List[Project]:
        """List all projects"""
        query = self.session.query(ProjectModel).filter(
            ProjectModel.deleted_at.is_(None)
        )
        
        if status:
            query = query.filter(ProjectModel.status == status)
        
        project_models = query.order_by(ProjectModel.created_at.desc()).all()
        return [self._model_to_entity(model) for model in project_models]
    
    def _model_to_entity(self, model: ProjectModel) -> Project:
        """Convert database model to domain entity"""
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            location=model.location,
            status=ProjectStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at
        )
```

### Service Layer Implementation

```python
# domain/quantification/services.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from domain.quantification.entities import Measurement, QuantificationItem, WorkScope, Conflict
from domain.quantification.repositories import IQuantificationRepository, IWorkScopeRepository
from infrastructure.external.ocr_service import IOCRService

class QuantificationService:
    def __init__(self, 
                 ocr_service: IOCRService,
                 quantification_repo: IQuantificationRepository,
                 work_scope_repo: IWorkScopeRepository):
        self.ocr_service = ocr_service
        self.quantification_repo = quantification_repo
        self.work_scope_repo = work_scope_repo
    
    async def process_images_and_extract_measurements(self, 
                                                     project_id: str,
                                                     image_paths: List[str]) -> List[Measurement]:
        """Process images and extract measurements using OCR"""
        all_measurements = []
        
        for image_path in image_paths:
            # Process image with OCR
            ocr_results = await self.ocr_service.process_image(image_path)
            
            # Extract measurements from OCR results
            measurements = await self.ocr_service.extract_measurements(ocr_results)
            
            # Store measurements
            for measurement in measurements:
                measurement.project_id = project_id
                await self.quantification_repo.save_measurement(measurement)
                all_measurements.append(measurement)
        
        return all_measurements
    
    async def map_measurements_to_work_scopes(self, 
                                            measurements: List[Measurement],
                                            work_scope_text: str) -> List[QuantificationItem]:
        """Map measurements to work scopes based on text description"""
        # Get all available work scopes
        work_scopes = await self.work_scope_repo.get_all_active()
        
        # Parse work scope text using NLP
        parsed_scopes = await self._parse_work_scope_text(work_scope_text)
        
        quantification_items = []
        
        for scope_info in parsed_scopes:
            # Find matching work scope
            work_scope = await self._find_matching_work_scope(scope_info, work_scopes)
            
            if work_scope:
                # Find relevant measurements
                relevant_measurements = self._find_relevant_measurements(
                    measurements, work_scope, scope_info
                )
                
                if relevant_measurements:
                    # Calculate quantity
                    quantity = self._calculate_quantity(relevant_measurements, work_scope)
                    
                    # Create quantification item
                    item = QuantificationItem(
                        id=None,  # Will be generated
                        work_scope=work_scope,
                        measurements=relevant_measurements,
                        quantity=quantity,
                        unit=work_scope.unit_of_measure,
                        location=scope_info.get('location')
                    )
                    
                    # Estimate debris weight if demolition
                    if work_scope.category == WorkCategory.DEMOLITION:
                        item.debris_weight = item.estimate_debris_weight()
                    
                    quantification_items.append(item)
        
        return quantification_items
    
    async def detect_conflicts(self, items: List[QuantificationItem]) -> List[Conflict]:
        """Detect conflicts between quantification items"""
        conflicts = []
        
        for i, item1 in enumerate(items):
            for item2 in items[i+1:]:
                conflict = await self._check_item_conflict(item1, item2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _parse_work_scope_text(self, text: str) -> List[Dict]:
        """Parse work scope text using NLP (simplified implementation)"""
        # This would use spaCy or similar NLP library in production
        # For now, simple keyword matching
        parsed_scopes = []
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # Extract room/location if mentioned
                location = None
                for room_keyword in ['kitchen', 'bathroom', 'living room', 'bedroom']:
                    if room_keyword.lower() in line.lower():
                        location = room_keyword
                        break
                
                parsed_scopes.append({
                    'text': line,
                    'location': location
                })
        
        return parsed_scopes
    
    async def _find_matching_work_scope(self, 
                                      scope_info: Dict,
                                      work_scopes: List[WorkScope]) -> Optional[WorkScope]:
        """Find best matching work scope for parsed scope info"""
        text = scope_info['text'].lower()
        
        best_match = None
        best_score = 0
        
        for work_scope in work_scopes:
            score = 0
            for keyword in work_scope.keywords:
                if keyword.lower() in text:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = work_scope
        
        return best_match if best_score > 0 else None
    
    def _find_relevant_measurements(self, 
                                   measurements: List[Measurement],
                                   work_scope: WorkScope,
                                   scope_info: Dict) -> List[Measurement]:
        """Find measurements relevant to a work scope"""
        relevant = []
        
        for measurement in measurements:
            # Check measurement type compatibility
            if measurement.measurement_type == work_scope.measurement_type:
                # Check location match if specified
                location = scope_info.get('location')
                if location:
                    if measurement.location and location.lower() in measurement.location.lower():
                        relevant.append(measurement)
                else:
                    # No location specified, include all compatible measurements
                    relevant.append(measurement)
        
        return relevant
    
    def _calculate_quantity(self, 
                           measurements: List[Measurement],
                           work_scope: WorkScope) -> Decimal:
        """Calculate total quantity from measurements"""
        total = Decimal('0')
        
        for measurement in measurements:
            # Convert to work scope unit if needed
            if measurement.unit == work_scope.unit_of_measure:
                total += measurement.value
            else:
                # Unit conversion logic would go here
                converted_value = self._convert_units(
                    measurement.value, 
                    measurement.unit, 
                    work_scope.unit_of_measure
                )
                total += converted_value
        
        return total
    
    def _convert_units(self, value: Decimal, from_unit: Unit, to_unit: Unit) -> Decimal:
        """Convert between measurement units"""
        # Simplified unit conversion
        if from_unit == to_unit:
            return value
        
        # Add conversion logic based on your needs
        # For example: feet to square feet, inches to feet, etc.
        conversion_factors = {
            (Unit.INCHES, Unit.FEET): Decimal('0.0833'),
            (Unit.FEET, Unit.SQUARE_FEET): value,  # Assuming square for area
        }
        
        factor = conversion_factors.get((from_unit, to_unit))
        if factor:
            return value * factor
        
        return value  # No conversion available
    
    async def _check_item_conflict(self, 
                                 item1: QuantificationItem,
                                 item2: QuantificationItem) -> Optional[Conflict]:
        """Check for conflicts between two quantification items"""
        # Example conflict detection logic
        
        # Same location, overlapping work
        if (item1.location == item2.location and 
            item1.work_scope.category == item2.work_scope.category):
            
            # Check for material conflicts
            if self._has_material_conflict(item1.work_scope, item2.work_scope):
                return Conflict(
                    item1=item1,
                    item2=item2,
                    conflict_type="MATERIAL",
                    severity="WARNING",
                    message=f"Potential material conflict between {item1.work_scope.name} and {item2.work_scope.name} in {item1.location}"
                )
        
        return None
    
    def _has_material_conflict(self, scope1: WorkScope, scope2: WorkScope) -> bool:
        """Check if two work scopes have material conflicts"""
        # Simplified conflict detection
        conflicting_combinations = [
            ('drywall', 'paint'),  # Painting drywall that's being removed
            ('flooring', 'subflooring')  # Installing flooring without subfloor
        ]
        
        for conflict in conflicting_combinations:
            if (any(conflict[0] in kw.lower() for kw in scope1.keywords) and
                any(conflict[1] in kw.lower() for kw in scope2.keywords)):
                return True
        
        return False
```

## Phase 2: Quantification Implementation

### Enhanced OCR Service

```python
# infrastructure/external/ocr_service.py
import cv2
import numpy as np
from PIL import Image
import easyocr
import re
from typing import List, Dict, Tuple
from decimal import Decimal
from domain.quantification.entities import Measurement, MeasurementType, Unit

class EnhancedOCRService:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])
        
        # Measurement patterns for construction drawings
        self.patterns = {
            'feet_inches': re.compile(r"(\d+)'-?(\d+)?\"?"),  # 10'-6" or 10'
            'decimal_feet': re.compile(r"(\d+\.?\d*)\s*'?ft"),  # 10.5 ft
            'dimensions': re.compile(r"(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)"),  # 10x12
            'area': re.compile(r"(\d+\.?\d*)\s*sq\.?\s*ft|(\d+\.?\d*)\s*ft²"),  # 100 sq ft
            'linear': re.compile(r"(\d+\.?\d*)\s*lin\.?\s*ft|(\d+\.?\d*)\s*lf"),  # 50 lin ft
        }
    
    async def process_image(self, image_path: str) -> List[Dict]:
        """Process image with enhanced OCR for construction drawings"""
        
        # Preprocess image for better OCR
        preprocessed_image = self._preprocess_image(image_path)
        
        # Run OCR with multiple confidence thresholds
        results = []
        
        # Primary OCR pass
        primary_results = self.reader.readtext(preprocessed_image)
        results.extend(self._format_ocr_results(primary_results, 'primary'))
        
        # Secondary pass with different preprocessing
        contrast_enhanced = self._enhance_contrast(preprocessed_image)
        secondary_results = self.reader.readtext(contrast_enhanced)
        results.extend(self._format_ocr_results(secondary_results, 'secondary'))
        
        return results
    
    async def extract_measurements(self, ocr_results: List[Dict]) -> List[Measurement]:
        """Extract construction measurements from OCR results"""
        measurements = []
        
        for result in ocr_results:
            text = result['text']
            confidence = result['confidence']
            bbox = result['bbox']
            
            # Try to extract different types of measurements
            extracted = self._extract_all_measurement_types(text, confidence, bbox)
            measurements.extend(extracted)
        
        # Remove duplicates and low-confidence measurements
        filtered_measurements = self._filter_and_deduplicate(measurements)
        
        return filtered_measurements
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR accuracy"""
        image = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Resize if too small (minimum 1000px width)
        height, width = gray.shape
        if width < 1000:
            scale_factor = 1000 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Adaptive threshold for better text extraction
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast for secondary OCR pass"""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(image)
        return enhanced
    
    def _format_ocr_results(self, raw_results: List, pass_type: str) -> List[Dict]:
        """Format raw OCR results into standardized format"""
        formatted = []
        
        for item in raw_results:
            bbox, text, confidence = item
            
            formatted.append({
                'text': text.strip(),
                'confidence': float(confidence),
                'bbox': bbox,
                'pass_type': pass_type
            })
        
        return formatted
    
    def _extract_all_measurement_types(self, 
                                     text: str, 
                                     confidence: float,
                                     bbox: List) -> List[Measurement]:
        """Extract all possible measurements from text"""
        measurements = []
        
        # Try each pattern type
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                measurement = self._create_measurement_from_match(
                    match, pattern_name, text, confidence, bbox
                )
                if measurement:
                    measurements.append(measurement)
        
        return measurements
    
    def _create_measurement_from_match(self, 
                                     match: re.Match,
                                     pattern_type: str,
                                     original_text: str,
                                     confidence: float,
                                     bbox: List) -> Optional[Measurement]:
        """Create measurement entity from regex match"""
        
        try:
            if pattern_type == 'feet_inches':
                feet = int(match.group(1))
                inches = int(match.group(2)) if match.group(2) else 0
                total_feet = Decimal(str(feet + inches / 12))
                
                return Measurement(
                    id=None,
                    source_image="",  # Will be set by caller
                    measurement_type=MeasurementType.LINEAR,
                    value=total_feet,
                    unit=Unit.FEET,
                    confidence=confidence,
                    extracted_text=original_text,
                    bounding_box={'coordinates': bbox}
                )
            
            elif pattern_type == 'decimal_feet':
                feet = Decimal(match.group(1))
                
                return Measurement(
                    id=None,
                    source_image="",
                    measurement_type=MeasurementType.LINEAR,
                    value=feet,
                    unit=Unit.FEET,
                    confidence=confidence,
                    extracted_text=original_text,
                    bounding_box={'coordinates': bbox}
                )
            
            elif pattern_type == 'dimensions':
                width = Decimal(match.group(1))
                length = Decimal(match.group(2))
                area = width * length
                
                return Measurement(
                    id=None,
                    source_image="",
                    measurement_type=MeasurementType.AREA,
                    value=area,
                    unit=Unit.SQUARE_FEET,
                    confidence=confidence,
                    extracted_text=original_text,
                    bounding_box={'coordinates': bbox}
                )
            
            elif pattern_type == 'area':
                area_value = Decimal(match.group(1) or match.group(2))
                
                return Measurement(
                    id=None,
                    source_image="",
                    measurement_type=MeasurementType.AREA,
                    value=area_value,
                    unit=Unit.SQUARE_FEET,
                    confidence=confidence,
                    extracted_text=original_text,
                    bounding_box={'coordinates': bbox}
                )
            
            elif pattern_type == 'linear':
                linear_value = Decimal(match.group(1) or match.group(2))
                
                return Measurement(
                    id=None,
                    source_image="",
                    measurement_type=MeasurementType.LINEAR,
                    value=linear_value,
                    unit=Unit.FEET,
                    confidence=confidence,
                    extracted_text=original_text,
                    bounding_box={'coordinates': bbox}
                )
        
        except (ValueError, TypeError, IndexError):
            return None
        
        return None
    
    def _filter_and_deduplicate(self, measurements: List[Measurement]) -> List[Measurement]:
        """Filter low confidence and remove duplicate measurements"""
        
        # Filter by confidence threshold
        filtered = [m for m in measurements if m.confidence >= 0.3]
        
        # Remove near-duplicates (same value, type, and close bbox)
        deduplicated = []
        
        for measurement in filtered:
            is_duplicate = False
            
            for existing in deduplicated:
                if (measurement.measurement_type == existing.measurement_type and
                    measurement.unit == existing.unit and
                    abs(measurement.value - existing.value) < Decimal('0.1') and
                    self._bboxes_overlap(measurement.bounding_box, existing.bounding_box)):
                    
                    # Keep the one with higher confidence
                    if measurement.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(measurement)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(measurement)
        
        return deduplicated
    
    def _bboxes_overlap(self, bbox1: Dict, bbox2: Dict) -> bool:
        """Check if two bounding boxes overlap significantly"""
        coords1 = bbox1.get('coordinates', [])
        coords2 = bbox2.get('coordinates', [])
        
        if len(coords1) < 4 or len(coords2) < 4:
            return False
        
        # Simple overlap check (would be more sophisticated in production)
        x1_min = min(point[0] for point in coords1)
        x1_max = max(point[0] for point in coords1)
        y1_min = min(point[1] for point in coords1)
        y1_max = max(point[1] for point in coords1)
        
        x2_min = min(point[0] for point in coords2)
        x2_max = max(point[0] for point in coords2)
        y2_min = min(point[1] for point in coords2)
        y2_max = max(point[1] for point in coords2)
        
        # Check for overlap
        if (x1_max < x2_min or x2_max < x1_min or 
            y1_max < y2_min or y2_max < y1_min):
            return False
        
        # Calculate overlap percentage
        overlap_x = min(x1_max, x2_max) - max(x1_min, x2_min)
        overlap_y = min(y1_max, y2_max) - max(y1_min, y2_min)
        
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        overlap_area = overlap_x * overlap_y
        
        # Consider overlap if more than 30% of either bbox overlaps
        return (overlap_area / area1 > 0.3) or (overlap_area / area2 > 0.3)
```

## Phase 3: Costing Implementation

### Pricing Service with Regional Adjustments

```python
# domain/costing/services.py
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from domain.quantification.entities import QuantificationItem
from domain.costing.entities import Material, Labor, CostItem, MaterialCost, LaborCost
from domain.costing.repositories import IMaterialRepository, ILaborRepository

class PricingService:
    def __init__(self,
                 material_repo: IMaterialRepository,
                 labor_repo: ILaborRepository,
                 region: str = "EAST_US"):
        self.material_repo = material_repo
        self.labor_repo = labor_repo
        self.region = region
        self.price_cache = {}
        self.cache_ttl = timedelta(hours=1)
    
    async def calculate_item_cost(self, item: QuantificationItem) -> CostItem:
        """Calculate complete cost for a quantification item"""
        
        # Get material costs
        material_costs = await self.calculate_material_costs(item)
        
        # Get labor costs
        labor_cost = await self.calculate_labor_costs(item)
        
        # Calculate equipment costs if needed
        equipment_cost = await self.calculate_equipment_costs(item)
        
        # Calculate totals
        total_material = sum(mc.total_cost for mc in material_costs)
        total_labor = labor_cost.total_cost if labor_cost else Decimal('0')
        total_equipment = equipment_cost.total_cost if equipment_cost else Decimal('0')
        
        subtotal = total_material + total_labor + total_equipment
        
        # Apply markup (could be variable based on item type)
        markup_percentage = self._get_markup_percentage(item)
        total_cost = subtotal * (1 + markup_percentage / 100)
        
        return CostItem(
            id=None,
            quantification_item=item,
            materials=material_costs,
            labor=labor_cost,
            equipment=equipment_cost,
            subtotal=subtotal,
            markup_percentage=markup_percentage,
            total_cost=total_cost
        )
    
    async def calculate_material_costs(self, item: QuantificationItem) -> List[MaterialCost]:
        """Calculate material costs for a quantification item"""
        material_costs = []
        
        # Get required materials for this work scope
        required_materials = await self._get_work_scope_materials(item.work_scope)
        
        for material_req in required_materials:
            # Get current material pricing
            material = await self._get_material_with_pricing(material_req['material_id'])
            
            if material:
                # Calculate quantity needed
                quantity_needed = item.quantity * material_req['quantity_per_unit']
                
                # Apply waste factor
                waste_factor = material_req.get('waste_factor', Decimal('1.1'))
                final_quantity = quantity_needed * waste_factor
                
                # Get regional price
                unit_cost = self._get_regional_price(material)
                total_cost = final_quantity * unit_cost
                
                material_cost = MaterialCost(
                    material=material,
                    quantity=final_quantity,
                    unit_cost=unit_cost,
                    waste_factor=waste_factor,
                    total_cost=total_cost
                )
                
                material_costs.append(material_cost)
        
        return material_costs
    
    async def calculate_labor_costs(self, item: QuantificationItem) -> Optional[LaborCost]:
        """Calculate labor costs for a quantification item"""
        
        # Get labor requirements for this work scope
        labor_req = await self._get_work_scope_labor(item.work_scope)
        
        if not labor_req:
            return None
        
        # Get current labor rates
        labor = await self._get_labor_with_rates(labor_req['labor_rate_id'])
        
        if not labor:
            return None
        
        # Calculate hours needed
        hours_needed = item.quantity * labor_req['hours_per_unit']
        
        # Apply difficulty factor
        difficulty_factor = labor_req.get('difficulty_factor', Decimal('1.0'))
        final_hours = hours_needed * difficulty_factor
        
        # Get regional rate
        hourly_rate = self._get_regional_labor_rate(labor)
        total_cost = final_hours * hourly_rate
        
        return LaborCost(
            labor=labor,
            hours=final_hours,
            rate=hourly_rate,
            difficulty_factor=difficulty_factor,
            total_cost=total_cost
        )
    
    async def calculate_equipment_costs(self, item: QuantificationItem) -> Optional[EquipmentCost]:
        """Calculate equipment costs if needed"""
        
        # Equipment requirements based on work scope
        equipment_req = await self._get_work_scope_equipment(item.work_scope)
        
        if not equipment_req:
            return None
        
        # Get equipment rates
        equipment = await self._get_equipment_rates(equipment_req['equipment_id'])
        
        if not equipment:
            return None
        
        # Estimate days needed based on quantity and crew productivity
        days_needed = self._estimate_equipment_days(item, equipment_req)
        
        total_cost = days_needed * equipment.daily_rate
        
        return EquipmentCost(
            equipment_name=equipment.name,
            daily_rate=equipment.daily_rate,
            days=days_needed,
            total_cost=total_cost
        )
    
    def _get_regional_price(self, material: Material) -> Decimal:
        """Apply regional price adjustments"""
        base_price = material.base_cost
        regional_multiplier = getattr(material, f'{self.region.lower()}_multiplier', Decimal('1.0'))
        
        return base_price * regional_multiplier
    
    def _get_regional_labor_rate(self, labor: Labor) -> Decimal:
        """Apply regional labor rate adjustments"""
        regional_rate = getattr(labor, f'{self.region.lower()}_rate', labor.base_hourly_rate)
        
        return regional_rate
    
    def _get_markup_percentage(self, item: QuantificationItem) -> Decimal:
        """Get markup percentage based on item type and complexity"""
        
        # Base markup percentages by category
        markup_by_category = {
            'DEMOLITION': Decimal('15.0'),
            'INSTALLATION': Decimal('25.0'),
            'FINISHING': Decimal('30.0'),
            'MECHANICAL': Decimal('35.0'),
            'ELECTRICAL': Decimal('40.0'),
            'PLUMBING': Decimal('35.0')
        }
        
        base_markup = markup_by_category.get(
            item.work_scope.category.value, 
            Decimal('25.0')
        )
        
        # Adjust for complexity (higher quantities get lower markup)
        if item.quantity > Decimal('1000'):
            return base_markup * Decimal('0.9')  # 10% reduction
        elif item.quantity < Decimal('50'):
            return base_markup * Decimal('1.1')  # 10% increase
        
        return base_markup
    
    async def _get_work_scope_materials(self, work_scope) -> List[Dict]:
        """Get material requirements for a work scope"""
        # This would query the work_scope_materials table
        return await self.material_repo.get_materials_for_scope(work_scope.id)
    
    async def _get_work_scope_labor(self, work_scope) -> Optional[Dict]:
        """Get labor requirements for a work scope"""
        # This would query the work_scope_labor table
        return await self.labor_repo.get_labor_for_scope(work_scope.id)
    
    async def _get_work_scope_equipment(self, work_scope) -> Optional[Dict]:
        """Get equipment requirements for a work scope"""
        # Equipment requirements based on work scope type
        equipment_mapping = {
            'DEMOLITION': {'equipment_id': 'DEMO_HAMMER', 'factor': 0.1},
            'INSTALLATION': None,  # Most installation doesn't need special equipment
            'FINISHING': None,
        }
        
        return equipment_mapping.get(work_scope.category.value)
    
    def _estimate_equipment_days(self, item: QuantificationItem, equipment_req: Dict) -> Decimal:
        """Estimate equipment rental days needed"""
        
        # Base estimation: area/volume per day based on equipment type
        productivity_rates = {
            'DEMO_HAMMER': Decimal('500'),  # 500 sqft per day
            'FLOOR_SANDER': Decimal('800'),  # 800 sqft per day
        }
        
        equipment_type = equipment_req.get('equipment_type', 'DEMO_HAMMER')
        daily_rate = productivity_rates.get(equipment_type, Decimal('500'))
        
        days = (item.quantity / daily_rate).quantize(Decimal('0.1'))
        
        # Minimum 1 day rental
        return max(days, Decimal('1.0'))
```

## Implementation Testing Strategy

### Unit Testing Framework

```python
# tests/unit/test_quantification_service.py
import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from domain.quantification.services import QuantificationService
from domain.quantification.entities import Measurement, MeasurementType, Unit, WorkScope, WorkCategory

class TestQuantificationService:
    
    @pytest.fixture
    def mock_dependencies(self):
        ocr_service = Mock()
        quantification_repo = Mock()
        work_scope_repo = Mock()
        
        return {
            'ocr_service': ocr_service,
            'quantification_repo': quantification_repo,
            'work_scope_repo': work_scope_repo
        }
    
    @pytest.fixture
    def service(self, mock_dependencies):
        return QuantificationService(**mock_dependencies)
    
    @pytest.fixture
    def sample_measurements(self):
        return [
            Measurement(
                id="test1",
                source_image="test.jpg",
                measurement_type=MeasurementType.AREA,
                value=Decimal('100'),
                unit=Unit.SQUARE_FEET,
                confidence=0.9,
                location="kitchen"
            ),
            Measurement(
                id="test2",
                source_image="test.jpg",
                measurement_type=MeasurementType.LINEAR,
                value=Decimal('50'),
                unit=Unit.FEET,
                confidence=0.8,
                location="kitchen"
            )
        ]
    
    @pytest.fixture
    def sample_work_scope(self):
        return WorkScope(
            id="ws1",
            code="DEMO_DW",
            name="Drywall Demolition",
            category=WorkCategory.DEMOLITION,
            measurement_type=MeasurementType.AREA,
            unit_of_measure=Unit.SQUARE_FEET,
            keywords=["drywall", "wall", "demolition"]
        )
    
    @pytest.mark.asyncio
    async def test_map_measurements_to_work_scopes(self, 
                                                  service, 
                                                  mock_dependencies,
                                                  sample_measurements,
                                                  sample_work_scope):
        # Arrange
        work_scope_text = "Remove drywall in kitchen - 100 sq ft"
        mock_dependencies['work_scope_repo'].get_all_active = AsyncMock(
            return_value=[sample_work_scope]
        )
        
        # Act
        result = await service.map_measurements_to_work_scopes(
            sample_measurements, work_scope_text
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].work_scope.code == "DEMO_DW"
        assert result[0].quantity == Decimal('100')
        assert result[0].location == "kitchen"
    
    @pytest.mark.asyncio
    async def test_calculate_quantity_unit_conversion(self, service):
        # Test unit conversion functionality
        measurements = [
            Measurement(
                id="test1",
                source_image="test.jpg",
                measurement_type=MeasurementType.LINEAR,
                value=Decimal('12'),  # 12 inches
                unit=Unit.INCHES,
                confidence=0.9
            )
        ]
        
        work_scope = WorkScope(
            id="ws1",
            code="TRIM_INST",
            name="Trim Installation",
            category=WorkCategory.FINISHING,
            measurement_type=MeasurementType.LINEAR,
            unit_of_measure=Unit.FEET,
            keywords=["trim"]
        )
        
        # Act
        result = service._calculate_quantity(measurements, work_scope)
        
        # Assert
        assert result == Decimal('1.0')  # 12 inches = 1 foot
    
    def test_conflict_detection(self, service):
        # Test conflict detection between items
        item1 = Mock()
        item1.location = "kitchen"
        item1.work_scope.category = WorkCategory.DEMOLITION
        item1.work_scope.keywords = ["drywall"]
        
        item2 = Mock()
        item2.location = "kitchen"
        item2.work_scope.category = WorkCategory.FINISHING
        item2.work_scope.keywords = ["paint"]
        
        # Act
        conflict = service._check_item_conflict(item1, item2)
        
        # Assert - Should detect painting drywall that's being demolished
        assert conflict is not None
        assert conflict.conflict_type == "MATERIAL"
```

### Integration Testing

```python
# tests/integration/test_estimation_workflow.py
import pytest
import tempfile
import os
from decimal import Decimal
from application.workflows.estimation_workflow import EstimationWorkflow
from infrastructure.database.repositories import SQLiteProjectRepository

class TestEstimationWorkflow:
    
    @pytest.fixture
    def temp_database(self):
        # Create temporary database for testing
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Initialize database schema
        # ... database setup code ...
        
        yield path
        
        # Cleanup
        os.unlink(path)
    
    @pytest.fixture
    def workflow(self, temp_database):
        # Create workflow with real dependencies
        return EstimationWorkflow(database_path=temp_database)
    
    @pytest.mark.asyncio
    async def test_complete_estimation_workflow(self, workflow):
        # Test the complete workflow from images to final estimate
        
        # Arrange
        project_data = {
            'name': 'Test Kitchen Renovation',
            'location': 'Boston, MA',
            'images': ['tests/fixtures/kitchen_plan.jpg'],
            'work_scope_text': 'Remove drywall and install new drywall in kitchen - 120 sq ft'
        }
        
        # Act
        result = await workflow.process_complete_estimation(**project_data)
        
        # Assert
        assert result.project_id is not None
        assert len(result.quantification_items) > 0
        assert len(result.cost_items) > 0
        assert result.estimate.total_estimate > Decimal('0')
        assert result.estimate.validation_status == 'PASSED'
        
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, workflow):
        # Test error handling in workflow
        
        # Arrange - Invalid image path
        project_data = {
            'name': 'Test Project',
            'location': 'Boston, MA', 
            'images': ['nonexistent.jpg'],
            'work_scope_text': 'Test work scope'
        }
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await workflow.process_complete_estimation(**project_data)
```

This implementation guide provides a solid foundation for building the reconstruction estimation system with proper architecture, testing, and error handling. The code examples demonstrate the domain-driven design approach with clear separation of concerns and comprehensive test coverage.