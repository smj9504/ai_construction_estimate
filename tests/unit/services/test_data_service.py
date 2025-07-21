"""
Simple test script for data functionality without external dependencies
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_models import ProjectData, Measurement, WorkScope
    from data_service import DataService
except ImportError as e:
    print(f"Import error: {e}")
    print("This test requires the data_models and data_service modules")
    sys.exit(1)

def test_basic_functionality():
    """Test basic data functionality"""
    print("Testing Basic Data Functionality")
    print("=" * 40)
    
    try:
        # Test creating a measurement
        measurement = Measurement(
            type="length",
            value=120,
            unit="inches",
            display="10'-0\"",
            original_text="Wall length 10 feet",
            confidence=0.95,
            location="Living Room"
        )
        print(f"✓ Created measurement: {measurement.display}")
        
        # Test creating a work scope
        work_scope = WorkScope(
            id="test_scope",
            name="Test Work Scope",
            category="testing",
            description="A test work scope",
            unit_type="each",
            base_rate=100.0,
            labor_hours=2.0,
            material_factor=1.0,
            complexity_factor=1.0,
            keywords=["test", "scope"]
        )
        print(f"✓ Created work scope: {work_scope.name}")
        
        # Test data conversion
        measurement_dict = measurement.to_dict()
        measurement_from_dict = Measurement.from_dict(measurement_dict)
        print(f"✓ Measurement serialization: {measurement_from_dict.display}")
        
        work_scope_dict = work_scope.to_dict()
        work_scope_from_dict = WorkScope.from_dict(work_scope_dict)
        print(f"✓ Work scope serialization: {work_scope_from_dict.name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def test_project_operations():
    """Test project creation and operations"""
    print("\nTesting Project Operations")
    print("=" * 40)
    
    try:
        # Test data service initialization
        data_service = DataService("test_data")
        print("✓ Data service initialized")
        
        # Test project creation
        project = data_service.create_project("Test Project", "A test project")
        print(f"✓ Created project: {project.name}")
        print(f"  Project ID: {project.project_id}")
        print(f"  Status: {project.status}")
        print(f"  Created: {project.created_at}")
        
        # Add some test data
        measurement = Measurement(
            type="length",
            value=144,
            unit="inches",
            display="12'-0\"",
            original_text="Wall length 12 feet",
            confidence=0.9
        )
        project.measurements.append(measurement)
        print("✓ Added measurement to project")
        
        # Test saving
        saved = data_service.save_project(project)
        print(f"✓ Project saved: {saved}")
        
        # Test loading
        loaded_project = data_service.load_project(project.project_id)
        if loaded_project:
            print(f"✓ Project loaded: {loaded_project.name}")
            print(f"  Measurements: {len(loaded_project.measurements)}")
        else:
            print("✗ Failed to load project")
            return False
        
        # Test listing projects
        projects = data_service.list_projects()
        print(f"✓ Found {len(projects)} projects")
        
        return True
        
    except Exception as e:
        print(f"✗ Project operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_parsing():
    """Test JSON data parsing"""
    print("\nTesting JSON Data Parsing")
    print("=" * 40)
    
    try:
        data_service = DataService("test_data")
        
        # Create sample JSON data
        sample_json = {
            "measurements": [
                {
                    "type": "length",
                    "value": 120,
                    "unit": "inches",
                    "display": "10'-0\"",
                    "original_text": "Wall length 10 feet",
                    "confidence": 0.95,
                    "location": "Living Room"
                }
            ],
            "work_scopes": [
                {
                    "id": "test_scope",
                    "name": "Test Work Scope",
                    "category": "testing",
                    "description": "A test work scope",
                    "unit_type": "each",
                    "base_rate": 100.0,
                    "labor_hours": 2.0,
                    "material_factor": 1.0,
                    "complexity_factor": 1.0,
                    "keywords": ["test", "scope"]
                }
            ]
        }
        
        json_content = json.dumps(sample_json, indent=2)
        print("✓ Created sample JSON data")
        
        # Test validation
        is_valid, message = data_service.validate_data_format(json_content, 'json')
        print(f"✓ JSON validation: {is_valid} - {message}")
        
        if is_valid:
            # Test parsing
            measurements, work_scopes = data_service.parse_uploaded_data(json_content, 'json')
            print(f"✓ Parsed {len(measurements)} measurements and {len(work_scopes)} work scopes")
            
            if measurements:
                print(f"  First measurement: {measurements[0].display}")
            if work_scopes:
                print(f"  First work scope: {work_scopes[0].name}")
        else:
            print("✗ JSON validation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ JSON parsing test failed: {e}")
        return False

def test_project_export():
    """Test project export to JSON"""
    print("\nTesting Project Export")
    print("=" * 40)
    
    try:
        data_service = DataService("test_data")
        
        # Create a project with data
        project = data_service.create_project("Export Test", "Testing export")
        
        # Add measurement
        measurement = Measurement(
            type="area",
            value=200,
            unit="sq_ft",
            display="200 sq ft",
            original_text="Room area 200 square feet",
            confidence=0.85
        )
        project.measurements.append(measurement)
        
        # Add work scope
        work_scope = WorkScope(
            id="export_scope",
            name="Export Test Scope",
            category="testing",
            description="Testing export functionality",
            unit_type="sq_ft",
            base_rate=5.0,
            labor_hours=0.2,
            material_factor=0.8,
            complexity_factor=1.0,
            keywords=["export", "test"]
        )
        project.work_scopes.append(work_scope)
        
        # Test JSON export
        json_export = data_service.export_project_data(project, 'json')
        print(f"✓ JSON export created ({len(json_export)} characters)")
        
        # Test importing back
        imported_project = ProjectData.from_json(json_export)
        print(f"✓ Imported project: {imported_project.name}")
        print(f"  Measurements: {len(imported_project.measurements)}")
        print(f"  Work scopes: {len(imported_project.work_scopes)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Project export test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Construction Estimator - Data Flow Testing")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_project_operations,
        test_json_parsing,
        test_project_export
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("Test failed!")
        except Exception as e:
            print(f"Test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"Tests Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! Data functionality is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)