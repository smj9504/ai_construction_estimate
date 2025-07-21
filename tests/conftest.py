"""Pytest configuration and fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "Test project description",
        "measurements": [],
        "work_scopes": []
    }

@pytest.fixture  
def sample_image_path():
    """Sample image path for testing."""
    return Path(__file__).parent / "fixtures" / "sample_image.jpg"
