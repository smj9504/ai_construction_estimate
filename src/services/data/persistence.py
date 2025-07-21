"""
Data service for handling file uploads, parsing, and persistence
"""

import os
import json
import yaml
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import logging

from models import ProjectData, Measurement, WorkScope, UploadSession

logger = logging.getLogger(__name__)


class DataService:
    """Service for data persistence and file operations"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize data service"""
        self.data_dir = Path(data_dir)
        self.projects_dir = self.data_dir / "projects"
        self.uploads_dir = self.data_dir / "uploads"
        self.work_scopes_dir = self.data_dir / "work_scopes"
        
        # Create directories if they don't exist
        for directory in [self.data_dir, self.projects_dir, self.uploads_dir, self.work_scopes_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize default work scopes if not exists
        self._initialize_default_work_scopes()
    
    def _initialize_default_work_scopes(self):
        """Create default work scopes if none exist"""
        default_scopes_file = self.work_scopes_dir / "default_work_scopes.yaml"
        
        if not default_scopes_file.exists():
            default_scopes = [
                WorkScope(
                    id="demo_wall_removal",
                    name="Interior Wall Demolition",
                    category="demolition",
                    description="Remove interior non-load bearing walls",
                    unit_type="linear_ft",
                    base_rate=15.0,
                    labor_hours=0.5,
                    material_factor=0.1,
                    complexity_factor=1.0,
                    keywords=["wall", "demolition", "remove", "demo"]
                ),
                WorkScope(
                    id="drywall_install",
                    name="Drywall Installation",
                    category="finishing",
                    description="Install and finish drywall",
                    unit_type="sq_ft",
                    base_rate=3.5,
                    labor_hours=0.1,
                    material_factor=0.8,
                    complexity_factor=1.0,
                    keywords=["drywall", "wall", "finish", "install"]
                ),
                WorkScope(
                    id="flooring_hardwood",
                    name="Hardwood Flooring Installation",
                    category="flooring",
                    description="Install hardwood flooring",
                    unit_type="sq_ft",
                    base_rate=12.0,
                    labor_hours=0.3,
                    material_factor=1.5,
                    complexity_factor=1.2,
                    keywords=["floor", "hardwood", "flooring", "wood"]
                ),
                WorkScope(
                    id="electrical_outlet",
                    name="Electrical Outlet Installation",
                    category="electrical",
                    description="Install standard electrical outlets",
                    unit_type="each",
                    base_rate=85.0,
                    labor_hours=1.0,
                    material_factor=0.3,
                    complexity_factor=1.0,
                    keywords=["outlet", "electrical", "plug", "electric"]
                ),
                WorkScope(
                    id="door_install",
                    name="Interior Door Installation",
                    category="carpentry",
                    description="Install interior doors with hardware",
                    unit_type="each",
                    base_rate=150.0,
                    labor_hours=3.0,
                    material_factor=1.0,
                    complexity_factor=1.1,
                    keywords=["door", "install", "interior", "entry"]
                )
            ]
            
            self.save_work_scopes(default_scopes, "default_work_scopes")
    
    def create_project(self, name: str, description: str = "") -> ProjectData:
        """Create a new project"""
        project_id = str(uuid.uuid4())
        now = datetime.now()
        
        project = ProjectData(
            project_id=project_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            measurements=[],
            work_scopes=[],
            mapping_results={},
            status="draft"
        )
        
        self.save_project(project)
        return project
    
    def save_project(self, project: ProjectData) -> bool:
        """Save project to file"""
        try:
            project.updated_at = datetime.now()
            project_file = self.projects_dir / f"{project.project_id}.yaml"
            
            with open(project_file, 'w', encoding='utf-8') as f:
                f.write(project.to_yaml())
            
            logger.info(f"Project {project.project_id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project {project.project_id}: {e}")
            return False
    
    def load_project(self, project_id: str) -> Optional[ProjectData]:
        """Load project from file"""
        try:
            project_file = self.projects_dir / f"{project_id}.yaml"
            
            if not project_file.exists():
                logger.warning(f"Project file not found: {project_id}")
                return None
            
            with open(project_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            project = ProjectData.from_yaml(content)
            logger.info(f"Project {project_id} loaded successfully")
            return project
            
        except Exception as e:
            logger.error(f"Failed to load project {project_id}: {e}")
            return None
    
    def list_projects(self) -> List[Dict]:
        """List all projects with basic info"""
        projects = []
        
        for project_file in self.projects_dir.glob("*.yaml"):
            try:
                project_id = project_file.stem
                project = self.load_project(project_id)
                
                if project:
                    projects.append({
                        'project_id': project.project_id,
                        'name': project.name,
                        'description': project.description,
                        'status': project.status,
                        'created_at': project.created_at.isoformat(),
                        'measurements_count': len(project.measurements),
                        'work_scopes_count': len(project.work_scopes)
                    })
                    
            except Exception as e:
                logger.error(f"Error processing project file {project_file}: {e}")
        
        return sorted(projects, key=lambda x: x['created_at'], reverse=True)
    
    def save_work_scopes(self, work_scopes: List[WorkScope], filename: str) -> bool:
        """Save work scopes to YAML file"""
        try:
            work_scopes_data = {
                'work_scopes': [scope.to_dict() for scope in work_scopes],
                'updated_at': datetime.now().isoformat()
            }
            
            file_path = self.work_scopes_dir / f"{filename}.yaml"
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(work_scopes_data, f, default_flow_style=False)
            
            logger.info(f"Work scopes saved to {filename}.yaml")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save work scopes: {e}")
            return False
    
    def load_work_scopes(self, filename: str) -> List[WorkScope]:
        """Load work scopes from YAML file"""
        try:
            file_path = self.work_scopes_dir / f"{filename}.yaml"
            
            if not file_path.exists():
                logger.warning(f"Work scopes file not found: {filename}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            work_scopes = [WorkScope.from_dict(scope_data) for scope_data in data['work_scopes']]
            logger.info(f"Loaded {len(work_scopes)} work scopes from {filename}")
            return work_scopes
            
        except Exception as e:
            logger.error(f"Failed to load work scopes from {filename}: {e}")
            return []
    
    def parse_uploaded_data(self, file_content: str, file_type: str) -> Tuple[List[Measurement], List[WorkScope]]:
        """Parse uploaded measurement and work scope data"""
        measurements = []
        work_scopes = []
        
        try:
            if file_type.lower() in ['yaml', 'yml']:
                data = yaml.safe_load(file_content)
            elif file_type.lower() == 'json':
                data = json.loads(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Parse measurements if present
            if 'measurements' in data:
                for measurement_data in data['measurements']:
                    try:
                        measurement = Measurement.from_dict(measurement_data)
                        measurements.append(measurement)
                    except Exception as e:
                        logger.warning(f"Failed to parse measurement: {e}")
            
            # Parse work scopes if present
            if 'work_scopes' in data:
                for scope_data in data['work_scopes']:
                    try:
                        work_scope = WorkScope.from_dict(scope_data)
                        work_scopes.append(work_scope)
                    except Exception as e:
                        logger.warning(f"Failed to parse work scope: {e}")
            
            logger.info(f"Parsed {len(measurements)} measurements and {len(work_scopes)} work scopes")
            
        except Exception as e:
            logger.error(f"Failed to parse uploaded data: {e}")
            raise
        
        return measurements, work_scopes
    
    def export_project_data(self, project: ProjectData, format_type: str = 'yaml') -> str:
        """Export project data in specified format"""
        if format_type.lower() == 'yaml':
            return project.to_yaml()
        elif format_type.lower() == 'json':
            return project.to_json()
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def create_upload_session(self) -> UploadSession:
        """Create a new upload session"""
        session = UploadSession(
            session_id=str(uuid.uuid4()),
            uploaded_files=[],
            processed_measurements=[],
            selected_work_scopes=[],
            status="uploading"
        )
        return session
    
    def validate_data_format(self, file_content: str, file_type: str) -> Tuple[bool, str]:
        """Validate uploaded data format"""
        try:
            if file_type.lower() in ['yaml', 'yml']:
                data = yaml.safe_load(file_content)
            elif file_type.lower() == 'json':
                data = json.loads(file_content)
            else:
                return False, f"Unsupported file type: {file_type}"
            
            # Check for required structure
            if not isinstance(data, dict):
                return False, "File must contain a dictionary/object structure"
            
            # Validate measurements if present
            if 'measurements' in data:
                if not isinstance(data['measurements'], list):
                    return False, "measurements must be a list"
                
                for i, measurement in enumerate(data['measurements']):
                    if not isinstance(measurement, dict):
                        return False, f"measurement {i} must be a dictionary"
                    
                    required_fields = ['type', 'value', 'unit', 'display', 'original_text', 'confidence']
                    for field in required_fields:
                        if field not in measurement:
                            return False, f"measurement {i} missing required field: {field}"
            
            # Validate work scopes if present
            if 'work_scopes' in data:
                if not isinstance(data['work_scopes'], list):
                    return False, "work_scopes must be a list"
                
                for i, scope in enumerate(data['work_scopes']):
                    if not isinstance(scope, dict):
                        return False, f"work_scope {i} must be a dictionary"
                    
                    required_fields = ['id', 'name', 'category', 'unit_type', 'base_rate']
                    for field in required_fields:
                        if field not in scope:
                            return False, f"work_scope {i} missing required field: {field}"
            
            return True, "Data format is valid"
            
        except yaml.YAMLError as e:
            return False, f"Invalid YAML format: {e}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"