# Migration Plan: Flat Structure to Package Architecture

## Overview

This document provides a detailed, step-by-step migration plan to transform the current flat file structure into the proposed package architecture. The migration is designed to be gradual, safe, and reversible.

## Migration Strategy

### Principles
1. **Incremental**: Move one component at a time
2. **Reversible**: Maintain ability to rollback at each step
3. **Testable**: Validate functionality after each migration
4. **Non-disruptive**: Keep application running during migration

### File Mapping

```yaml
Current Structure → New Structure:

# Root files to migrate:
app.py → 
  - src/ui/app.py (main Gradio app)
  - src/ui/handlers/ocr.py (OCR handlers)
  - src/services/ocr/easy_ocr.py (OCR service)

config.py → src/core/config.py

data_models.py → 
  - src/models/measurement.py
  - src/models/work_scope.py  
  - src/models/project.py

data_service.py → src/services/data/persistence.py

gcp_ocr_service.py → src/services/ocr/gcp_ocr.py

# Test files:
test_*.py → tests/unit/ or tests/integration/

# Keep in place:
sample_measurements.yaml
sample_work_scopes.json
requirements.txt
pyproject.toml
```

## Phase-by-Phase Migration

### Phase 1: Foundation Setup (Day 1-2)

#### Step 1.1: Create Directory Structure
```bash
mkdir -p src/{services/{ocr,data,estimation,integration},models,ui/{components,handlers,formatters},core/{utils},api}
mkdir -p tests/{unit/{services,models,ui,core},integration,e2e}
mkdir -p scripts docs/{api,architecture,user_guide}
```

#### Step 1.2: Create __init__.py Files
```bash
# Create all necessary __init__.py files
touch src/__init__.py
touch src/services/__init__.py
touch src/services/ocr/__init__.py
touch src/services/data/__init__.py
touch src/services/estimation/__init__.py
touch src/services/integration/__init__.py
touch src/models/__init__.py
touch src/ui/__init__.py
touch src/ui/components/__init__.py
touch src/ui/handlers/__init__.py
touch src/ui/formatters/__init__.py
touch src/core/__init__.py
touch src/core/utils/__init__.py
touch src/api/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py
touch scripts/__init__.py
```

#### Step 1.3: Create Migration Script
Create `scripts/migrate.py` to automate file movements and import updates.

### Phase 2: Core Utilities Migration (Day 2-3)

#### Step 2.1: Move Configuration
```bash
# Move and update config.py
cp config.py src/core/config.py
# Update imports in config.py to use relative imports
```

#### Step 2.2: Create Core Utilities
Extract utility functions from existing files into:
- `src/core/utils/image.py` - Image processing utilities
- `src/core/utils/text.py` - Text processing utilities  
- `src/core/utils/validation.py` - Input validation
- `src/core/constants.py` - Application constants
- `src/core/exceptions.py` - Custom exceptions
- `src/core/logging.py` - Logging configuration

#### Step 2.3: Update Imports
Update all references to config.py throughout the codebase:
```python
# Old import
import config

# New import  
from src.core import config
```

### Phase 3: Models Migration (Day 3-4)

#### Step 3.1: Analyze and Split data_models.py
Examine `data_models.py` and plan the split:
```python
# Current data_models.py contains:
# - Measurement class → src/models/measurement.py
# - WorkScope class → src/models/work_scope.py  
# - ProjectData class → src/models/project.py
# - UploadSession class → src/models/project.py
```

#### Step 3.2: Create Model Files
```bash
# Create individual model files
# Each will contain related classes and maintain existing functionality
```

#### Step 3.3: Create Models __init__.py
```python
# src/models/__init__.py
from .measurement import Measurement
from .work_scope import WorkScope
from .project import ProjectData, UploadSession

__all__ = ['Measurement', 'WorkScope', 'ProjectData', 'UploadSession']
```

#### Step 3.4: Update Model Imports
Update all imports throughout codebase:
```python
# Old import
from data_models import Measurement, WorkScope

# New import
from src.models import Measurement, WorkScope
```

### Phase 4: Services Migration (Day 4-6)

#### Step 4.1: Create OCR Service Base
```python
# src/services/ocr/base.py
from abc import ABC, abstractmethod

class OCRServiceBase(ABC):
    @abstractmethod
    def extract_text(self, image_path: str) -> dict:
        pass
```

#### Step 4.2: Move GCP OCR Service
```bash
# Move and refactor gcp_ocr_service.py
cp gcp_ocr_service.py src/services/ocr/gcp_ocr.py
# Update to inherit from OCRServiceBase
```

#### Step 4.3: Extract OCR Logic from app.py
Move OCR-related code from `app.py` to `src/services/ocr/easy_ocr.py`

#### Step 4.4: Move Data Service
```bash
cp data_service.py src/services/data/persistence.py
# Update imports and dependencies
```

#### Step 4.5: Create Service Factories
```python
# src/services/__init__.py
from .ocr import get_ocr_service
from .data import get_data_service

def get_ocr_service(provider='easy'):
    if provider == 'easy':
        from .ocr.easy_ocr import EasyOCRService
        return EasyOCRService()
    elif provider == 'gcp':
        from .ocr.gcp_ocr import GCPOCRService
        return GCPOCRService()
    else:
        raise ValueError(f"Unknown OCR provider: {provider}")
```

### Phase 5: UI Migration (Day 6-8)

#### Step 5.1: Analyze app.py Structure
Identify components in app.py:
- Gradio interface setup
- Event handlers
- HTML formatting functions
- Main application logic

#### Step 5.2: Extract UI Components
```python
# src/ui/components/upload.py - Upload interface components
# src/ui/components/results.py - Results display components  
# src/ui/components/admin.py - Admin interface components
```

#### Step 5.3: Extract Event Handlers
```python
# src/ui/handlers/ocr.py - OCR processing handlers
# src/ui/handlers/session.py - Session management handlers
```

#### Step 5.4: Extract Formatters
```python
# src/ui/formatters/html.py - HTML generation utilities
```

#### Step 5.5: Create Streamlined app.py
```python
# src/ui/app.py - Main application orchestration
# Uses components, handlers, and formatters
```

### Phase 6: Test Migration (Day 8-9)

#### Step 6.1: Categorize Existing Tests
```bash
# Analyze test files and categorize:
test_app.py → tests/integration/test_app.py
test_data_flow.py → tests/integration/test_data_flow.py  
core_test.py → tests/unit/core/
simple_data_test.py → tests/unit/services/
simple_test.py → tests/unit/
```

#### Step 6.2: Update Test Imports
Update all test files to use new import paths:
```python
# Old import in tests
import app

# New import
from src.ui import app
```

#### Step 6.3: Create Test Configuration
```python
# tests/conftest.py
import pytest
import sys
from pathlib import Path

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
```

### Phase 7: Entry Point and Cleanup (Day 9-10)

#### Step 7.1: Create New Entry Point
```python
# main.py
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.app import main

if __name__ == "__main__":
    main()
```

#### Step 7.2: Update Requirements
```bash
# Create requirements-dev.txt for development dependencies
# Update requirements.txt for production dependencies
```

#### Step 7.3: Create Setup Configuration
```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="ai-construction-estimate",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
)
```

## Validation Steps

### After Each Phase
1. **Run Tests**: `python -m pytest tests/`
2. **Manual Testing**: Verify core functionality works
3. **Import Validation**: Check all imports resolve correctly
4. **Git Commit**: Commit working state for rollback capability

### Comprehensive Validation
```bash
# Check all imports
python -c "from src.ui.app import main; print('Success')"

# Run all tests
python -m pytest tests/ -v

# Start application
python main.py

# Check code quality
flake8 src/
mypy src/
black --check src/
```

## Rollback Procedures

### Immediate Rollback (within same phase)
```bash
git checkout HEAD~1  # Go back one commit
```

### Phase Rollback
```bash
git checkout <phase_start_commit>
```

### Complete Rollback
```bash
git checkout <migration_start_commit>
```

## Risk Mitigation

### Backup Strategy
1. **Git Tags**: Tag each phase completion
2. **Branch Strategy**: Use feature branch for migration
3. **File Backups**: Keep copies of original files during migration

### Testing Strategy
1. **Incremental Testing**: Test after each major move
2. **Regression Testing**: Run full test suite after each phase
3. **Manual Validation**: Verify UI functionality manually

### Dependencies Management
1. **Import Mapping**: Document all import changes
2. **Circular Dependencies**: Watch for and resolve circular imports
3. **External Dependencies**: Ensure external packages still work

## Post-Migration Tasks

### Documentation Updates
1. Update README.md with new structure
2. Create developer guide
3. Update API documentation
4. Create architecture diagrams

### CI/CD Updates
1. Update test paths in CI configuration
2. Update deployment scripts
3. Update environment setup instructions

### Code Quality
1. Add type hints throughout codebase
2. Increase test coverage to 80%+
3. Set up automated code quality checks
4. Configure pre-commit hooks

## Timeline Summary

| Phase | Duration | Key Activities | Validation |
|-------|----------|---------------|------------|
| 1     | 1-2 days | Directory setup, init files | Structure exists |
| 2     | 1 day    | Core utilities migration | Config accessible |
| 3     | 1 day    | Models migration | Models importable |
| 4     | 2 days   | Services migration | Services functional |
| 5     | 2 days   | UI migration | App runs |
| 6     | 1 day    | Test migration | Tests pass |
| 7     | 1 day    | Cleanup, documentation | Full functionality |

**Total Estimated Time**: 8-10 days

## Success Criteria

✅ All existing functionality preserved
✅ All tests passing  
✅ Clean package structure implemented
✅ No circular dependencies
✅ Documentation updated
✅ Team can develop efficiently

The migration plan provides a systematic approach to transforming the codebase while minimizing risk and maintaining functionality throughout the process.