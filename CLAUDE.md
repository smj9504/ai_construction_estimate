# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a construction estimation application that uses OCR to extract measurements from construction survey images and maps them to work scopes. It's built with Python and Gradio for the web interface.

## Development Commands

### Setup and Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (launches on port 7860)
python main.py
```

### Code Quality
```bash
# Format code with Black (line length 120)
black .

# Lint with flake8
flake8

# Type checking with mypy
mypy .

# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py
```

## Architecture

### Core Services Architecture
The application follows a modular service architecture with clear separation of concerns:

1. **Services Layer** (`services/`):
   - `OCRService`: Handles all OCR operations using EasyOCR. Global instance management via `get_ocr_service()`
   - `MappingService`: Maps OCR results to work scopes using keyword-based detection
   - `EstimatorService`: Placeholder for cost estimation (minimal implementation)

2. **Managers Layer** (`managers/`):
   - `SessionManager`: Handles project sessions, persistence, and state management
   - `UIHelper`: Generates HTML summaries and status displays
   - Optional managers: `ErrorManager`, `LoggingManager`, `ValidationManager`

3. **UI Architecture**:
   - **Component Factory Pattern** (`components/`): Reusable UI components created via factory functions
   - **Screen Classes** (`screens/`): `Phase1Screen` (main app), `AdminScreen` (admin interface)
   - **Handlers** (`handlers/`): Business logic separated from UI, handles events and orchestrates services

### Key Design Patterns
- **Factory Pattern**: UI components are created through factory functions for consistency
- **Service Locator**: Services can be accessed globally (e.g., `get_ocr_service()`)
- **Handler Pattern**: UI events are processed by dedicated handler classes that coordinate between services

### Data Flow
1. User uploads construction images → OCRHandler processes with OCRService
2. OCR results → MappingHandler uses MappingService to map to work scopes
3. Mapped data → EstimatorService (placeholder) for cost calculation
4. Results displayed via UIHelper HTML generation

## Important Implementation Details

### OCR Processing
- Supports multiple measurement patterns: feet/inches (e.g., "10'-6""), dimensions (e.g., "10x12"), areas
- Image preprocessing includes resizing, denoising, and enhancement
- Confidence threshold: 0.3 (configurable in config.py)

### Session Management
- Sessions stored in `data/sessions/` directory
- Each session has metadata (name, description, timestamps) and data
- Session validation checks for required fields and proper structure

### Configuration
- Environment variables loaded from `.env` file
- ANTHROPIC_API_KEY required but not currently used in core functionality
- Supported image formats: .png, .jpg, .jpeg, .bmp, .tiff (max 10MB)

## Current Development State

The project is actively being developed with:
- Core OCR and mapping functionality complete
- Estimation features pending implementation
- Some files recently reorganized (components/, handlers/, screens/ directories are new)
- Korean comments present in some files

When implementing new features:
1. Follow the existing service/manager/handler pattern
2. Use the component factory for UI elements
3. Maintain separation between UI and business logic
4. Add appropriate type hints for mypy compliance