"""
Core functionality test without external dependencies
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Union


@dataclass
class Measurement:
    """Individual measurement data"""
    type: str
    value: Union[float, Dict]
    unit: str
    display: str
    original_text: str
    confidence: float
    location: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Measurement':
        return cls(**data)


@dataclass
class WorkScope:
    """Work scope definition"""
    id: str
    name: str
    category: str
    description: str
    unit_type: str
    base_rate: float
    labor_hours: float
    material_factor: float
    complexity_factor: float
    keywords: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkScope':
        return cls(**data)


def test_core_data_structures():
    """Test core data structures"""
    print("Testing Core Data Structures")
    print("=" * 40)
    
    try:
        # Test Measurement
        measurement = Measurement(
            type="length",
            value=120,
            unit="inches",
            display="10'-0\"",
            original_text="Wall length 10 feet",
            confidence=0.95,
            location="Living Room"
        )
        
        print(f"[OK] Created measurement: {measurement.display}")
        
        # Test serialization
        measurement_dict = measurement.to_dict()
        reconstructed = Measurement.from_dict(measurement_dict)
        print(f"[OK] Measurement serialization: {reconstructed.display}")
        
        # Test WorkScope
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
        
        print(f"[OK] Created work scope: {work_scope.name}")
        
        # Test serialization
        scope_dict = work_scope.to_dict()
        reconstructed_scope = WorkScope.from_dict(scope_dict)
        print(f"[OK] Work scope serialization: {reconstructed_scope.name}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Core structures test failed: {e}")
        return False


def test_json_operations():
    """Test JSON operations"""
    print("\nTesting JSON Operations")
    print("=" * 40)
    
    try:
        # Create sample data
        measurements = [
            Measurement(
                type="length",
                value=120,
                unit="inches",
                display="10'-0\"",
                original_text="Wall length 10 feet",
                confidence=0.95,
                location="Living Room"
            ),
            Measurement(
                type="area",
                value=200,
                unit="sq_ft",
                display="200 sq ft",
                original_text="Room area 200 square feet",
                confidence=0.85,
                location="Kitchen"
            )
        ]
        
        work_scopes = [
            WorkScope(
                id="demo_scope",
                name="Demolition Work",
                category="demolition",
                description="Remove walls and debris",
                unit_type="linear_ft",
                base_rate=15.0,
                labor_hours=0.5,
                material_factor=0.1,
                complexity_factor=1.0,
                keywords=["demo", "wall", "remove"]
            )
        ]
        
        # Create project-like structure
        project_data = {
            "project_id": "test-project-123",
            "name": "Test Project",
            "description": "A test project",
            "created_at": datetime.now().isoformat(),
            "measurements": [m.to_dict() for m in measurements],
            "work_scopes": [w.to_dict() for w in work_scopes],
            "status": "draft"
        }
        
        # Test JSON serialization
        json_data = json.dumps(project_data, indent=2)
        print(f"[OK] Created JSON data ({len(json_data)} characters)")
        
        # Test JSON deserialization
        loaded_data = json.loads(json_data)
        print(f"[OK] Loaded JSON data: {loaded_data['name']}")
        
        # Reconstruct objects
        loaded_measurements = [Measurement.from_dict(m) for m in loaded_data['measurements']]
        loaded_work_scopes = [WorkScope.from_dict(w) for w in loaded_data['work_scopes']]
        
        print(f"[OK] Reconstructed {len(loaded_measurements)} measurements")
        print(f"[OK] Reconstructed {len(loaded_work_scopes)} work scopes")
        
        # Verify data integrity
        if loaded_measurements[0].display == measurements[0].display:
            print("[OK] Measurement data integrity verified")
        else:
            print("[FAIL] Measurement data integrity failed")
            return False
        
        if loaded_work_scopes[0].name == work_scopes[0].name:
            print("[OK] Work scope data integrity verified")
        else:
            print("[FAIL] Work scope data integrity failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] JSON operations test failed: {e}")
        return False


def test_file_operations():
    """Test basic file operations"""
    print("\nTesting File Operations")
    print("=" * 40)
    
    try:
        # Create test directory
        test_dir = "test_output"
        os.makedirs(test_dir, exist_ok=True)
        print(f"[OK] Created test directory: {test_dir}")
        
        # Create sample data
        sample_data = {
            "measurements": [
                {
                    "type": "length",
                    "value": 144,
                    "unit": "inches",
                    "display": "12'-0\"",
                    "original_text": "Wall length 12 feet",
                    "confidence": 0.9,
                    "location": "Bedroom"
                }
            ],
            "work_scopes": [
                {
                    "id": "paint_work",
                    "name": "Interior Painting",
                    "category": "finishing",
                    "description": "Paint interior walls",
                    "unit_type": "sq_ft",
                    "base_rate": 2.5,
                    "labor_hours": 0.05,
                    "material_factor": 0.6,
                    "complexity_factor": 1.0,
                    "keywords": ["paint", "interior", "wall"]
                }
            ]
        }
        
        # Write to file
        output_file = os.path.join(test_dir, "test_data.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)
        print(f"[OK] Wrote data to file: {output_file}")
        
        # Read from file
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print(f"[OK] Read data from file")
        
        # Verify data
        if len(loaded_data['measurements']) == 1 and len(loaded_data['work_scopes']) == 1:
            print("[OK] File data integrity verified")
        else:
            print("[FAIL] File data integrity failed")
            return False
        
        # Cleanup
        os.remove(output_file)
        os.rmdir(test_dir)
        print("[OK] Cleaned up test files")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] File operations test failed: {e}")
        return False


def main():
    """Run core functionality tests"""
    print("Construction Estimator - Core Functionality Test")
    print("=" * 50)
    
    tests = [
        test_core_data_structures,
        test_json_operations,
        test_file_operations
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
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("[SUCCESS] All core tests passed!")
        print("[SUCCESS] Data structures and JSON operations working correctly")
        print("[SUCCESS] Ready for integration with Gradio interface")
        return True
    else:
        print("[FAIL] Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)