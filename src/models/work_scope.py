"""
Data models for construction estimation application
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Union
from datetime import datetime
import json
import yaml


@dataclass
class Measurement:
    """Individual measurement data"""
    type: str  # 'length', 'dimension', 'area', 'volume'
    value: Union[float, Dict]  # numeric value or dict for dimensions
    unit: str  # 'inches', 'feet', 'sq_ft', 'cu_ft'
    display: str  # human-readable format
    original_text: str  # source text from OCR
    confidence: float  # OCR confidence score
    location: Optional[str] = None  # room/area where measured
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Measurement':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class WorkScope:
    """Work scope definition"""
    id: str
    name: str
    category: str  # 'demolition', 'framing', 'electrical', etc.
    description: str
    unit_type: str  # 'linear_ft', 'sq_ft', 'each', etc.
    base_rate: float  # cost per unit
    labor_hours: float  # hours per unit
    material_factor: float  # material cost multiplier
    complexity_factor: float  # 1.0 = normal, >1.0 = complex
    keywords: List[str]  # for automatic mapping
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkScope':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ProjectData:
    """Complete project data structure"""
    project_id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    measurements: List[Measurement]
    work_scopes: List[WorkScope]
    mapping_results: Dict[str, List[str]]  # measurement_id -> scope_ids
    status: str  # 'draft', 'in_progress', 'completed'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectData':
        """Create from dictionary"""
        # Convert datetime strings back to datetime objects
        if isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Convert measurement dictionaries to Measurement objects
        data['measurements'] = [
            Measurement.from_dict(m) if isinstance(m, dict) else m 
            for m in data['measurements']
        ]
        
        # Convert work scope dictionaries to WorkScope objects
        data['work_scopes'] = [
            WorkScope.from_dict(w) if isinstance(w, dict) else w 
            for w in data['work_scopes']
        ]
        
        return cls(**data)
    
    def to_yaml(self) -> str:
        """Export to YAML format"""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
    
    def to_json(self) -> str:
        """Export to JSON format"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'ProjectData':
        """Load from YAML content"""
        data = yaml.safe_load(yaml_content)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, json_content: str) -> 'ProjectData':
        """Load from JSON content"""
        data = json.loads(json_content)
        return cls.from_dict(data)


@dataclass
class UploadSession:
    """Track upload session data"""
    session_id: str
    uploaded_files: List[str]
    processed_measurements: List[Measurement]
    selected_work_scopes: List[str]
    status: str  # 'uploading', 'processing', 'completed', 'error'
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)