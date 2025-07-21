"""
Advanced measurement extraction service for construction images
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from decimal import Decimal
import re
import json
from datetime import datetime

from models.room_measurement import (
    RoomMeasurement, WallMeasurement, CeilingMeasurement, FloorMeasurement,
    DoorOpening, WindowOpening, MissingWall, Area, Dimension, MeasurementUnit,
    RoomType, MeasurementParser, BulkProcessingResult
)

logger = logging.getLogger(__name__)

try:
    # Import OpenAI for complex parsing fallback
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Complex parsing will be limited.")


class AdvancedMeasurementExtractor:
    """Advanced measurement extraction with multiple parsing strategies"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the measurement extractor
        
        Args:
            openai_api_key: OpenAI API key for complex parsing
        """
        self.parser = MeasurementParser()
        self.openai_client = None
        
        if OPENAI_AVAILABLE and openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
            logger.info("OpenAI client initialized for complex parsing")
        
        # Load room name mapping patterns
        self.room_patterns = self._load_room_patterns()
    
    def _load_room_patterns(self) -> Dict[str, RoomType]:
        """Load room name patterns for detection"""
        return {
            # Bedroom variations
            r'(?:master\s*)?bedroom\d*': RoomType.BEDROOM,
            r'bed\s*room\d*': RoomType.BEDROOM,
            r'br\d*': RoomType.BEDROOM,
            r'mbr': RoomType.BEDROOM,
            
            # Bathroom variations
            r'(?:master\s*)?bathroom\d*': RoomType.BATHROOM,
            r'bath\s*room\d*': RoomType.BATHROOM,
            r'ba\d*': RoomType.BATHROOM,
            r'powder\s*room': RoomType.BATHROOM,
            r'half\s*bath': RoomType.BATHROOM,
            
            # Kitchen variations
            r'kitchen': RoomType.KITCHEN,
            r'kit': RoomType.KITCHEN,
            
            # Living areas
            r'living\s*room': RoomType.LIVING_ROOM,
            r'family\s*room': RoomType.LIVING_ROOM,
            r'great\s*room': RoomType.LIVING_ROOM,
            
            # Dining
            r'dining\s*room': RoomType.DINING_ROOM,
            r'din': RoomType.DINING_ROOM,
            
            # Other common rooms
            r'office': RoomType.OFFICE,
            r'study': RoomType.OFFICE,
            r'closet': RoomType.CLOSET,
            r'clo': RoomType.CLOSET,
            r'hall(?:way)?': RoomType.HALLWAY,
            r'corridor': RoomType.HALLWAY,
            r'entry': RoomType.ENTRY_FOYER,
            r'foyer': RoomType.ENTRY_FOYER,
            r'garage': RoomType.GARAGE,
            r'basement': RoomType.BASEMENT,
            r'attic': RoomType.ATTIC,
            r'laundry': RoomType.LAUNDRY,
            r'utility': RoomType.LAUNDRY,
        }
    
    def extract_room_from_filename(self, filename: str) -> Tuple[str, RoomType, str]:
        """
        Extract room information from filename
        
        Args:
            filename: Image filename
            
        Returns:
            Tuple of (room_name, room_type, subroom)
        """
        # Clean filename
        name = Path(filename).stem.lower()
        name = re.sub(r'[_\-]', ' ', name)
        
        # Look for room patterns
        room_name = "Unknown Room"
        room_type = RoomType.OTHER
        subroom = ""
        
        for pattern, rtype in self.room_patterns.items():
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                room_name = match.group(0).title()
                room_type = rtype
                break
        
        # Look for subroom indicators
        subroom_patterns = [
            r'master\s*(\w+)',
            r'(\w+)\s*\d+',
            r'(\w+)\s*[abc]'
        ]
        
        for pattern in subroom_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match and match.group(1).lower() not in ['room', 'bath']:
                subroom = match.group(1).title()
                break
        
        return room_name, room_type, subroom
    
    def extract_measurements_basic(self, ocr_results: List[Dict]) -> RoomMeasurement:
        """
        Extract measurements using basic pattern matching
        
        Args:
            ocr_results: OCR results from image processing
            
        Returns:
            RoomMeasurement object with extracted data
        """
        # Combine all OCR text
        full_text = " ".join([result['text'] for result in ocr_results])
        
        # Initialize room measurement
        room = RoomMeasurement(room_name="Unknown Room")
        
        # Extract room name from OCR if present
        room_match = re.search(r'(?:room|location):\s*([A-Z_][A-Z_\s\-]*)', full_text, re.IGNORECASE)
        if room_match:
            room.room_name = room_match.group(1).strip().title()
            room.room_type = self.parser.detect_room_type(room.room_name)
        
        # Extract height
        height_match = re.search(r'(?:height|h):\s*(\d+(?:\.\d+)?(?:\'[\s\-]*\d+(?:\s*\d+/\d+)?\"?)?)', full_text, re.IGNORECASE)
        if height_match:
            room.height = self.parser.parse_dimension(height_match.group(1))
        
        # Extract wall measurements
        wall_area_match = re.search(r'wall.*area:\s*(\d+\.?\d*)\s*sf', full_text, re.IGNORECASE)
        if wall_area_match:
            if not room.walls:
                room.walls = WallMeasurement()
            room.walls.area = Area(
                value=Decimal(wall_area_match.group(1)),
                unit=MeasurementUnit.SQUARE_FEET,
                original_text=wall_area_match.group(0)
            )
        
        # Extract ceiling measurements
        ceiling_area_match = re.search(r'ceiling.*area:\s*(\d+\.?\d*)\s*sf', full_text, re.IGNORECASE)
        if ceiling_area_match:
            if not room.ceiling:
                room.ceiling = CeilingMeasurement()
            room.ceiling.area = Area(
                value=Decimal(ceiling_area_match.group(1)),
                unit=MeasurementUnit.SQUARE_FEET,
                original_text=ceiling_area_match.group(0)
            )
        
        ceiling_perimeter_match = re.search(r'ceiling\s*perimeter.*length:\s*(\d+\.?\d*)\s*lf', full_text, re.IGNORECASE)
        if ceiling_perimeter_match:
            if not room.ceiling:
                room.ceiling = CeilingMeasurement()
            room.ceiling.perimeter = Dimension(
                value=Decimal(ceiling_perimeter_match.group(1)),
                unit=MeasurementUnit.LINEAR_FEET,
                original_text=ceiling_perimeter_match.group(0)
            )
        
        # Extract floor measurements
        floor_area_match = re.search(r'floor.*area:\s*(\d+\.?\d*)\s*sf', full_text, re.IGNORECASE)
        if floor_area_match:
            if not room.floor:
                room.floor = FloorMeasurement()
            room.floor.area = Area(
                value=Decimal(floor_area_match.group(1)),
                unit=MeasurementUnit.SQUARE_FEET,
                original_text=floor_area_match.group(0)
            )
        
        floor_perimeter_match = re.search(r'(?:floor\s*)?perimeter:\s*(\d+\.?\d*)\s*lf', full_text, re.IGNORECASE)
        if floor_perimeter_match:
            if not room.floor:
                room.floor = FloorMeasurement()
            room.floor.perimeter = Dimension(
                value=Decimal(floor_perimeter_match.group(1)),
                unit=MeasurementUnit.LINEAR_FEET,
                original_text=floor_perimeter_match.group(0)
            )
        
        flooring_match = re.search(r'flooring:\s*(\d+\.?\d*)\s*sy', full_text, re.IGNORECASE)
        if flooring_match:
            if not room.floor:
                room.floor = FloorMeasurement()
            room.floor.flooring_area = Area(
                value=Decimal(flooring_match.group(1)),
                unit=MeasurementUnit.SQUARE_YARDS,
                original_text=flooring_match.group(0)
            )
        
        # Extract door openings
        door_pattern = r'(?:door|opening).*?dimensions?:\s*(\d+(?:\'[\s\-]*\d+\"?)?)\s*[xX×]\s*(\d+(?:\'[\s\-]*\d+\"?)?)'
        for door_match in re.finditer(door_pattern, full_text, re.IGNORECASE):
            width = self.parser.parse_dimension(door_match.group(1))
            height = self.parser.parse_dimension(door_match.group(2))
            
            if width and height:
                # Look for "opens into" in the surrounding text
                opens_into = "Unknown"
                opens_pattern = r'opens?\s+into:\s*([A-Z_][A-Z_\s]*)'
                surrounding_text = full_text[max(0, door_match.start()-100):door_match.end()+100]
                opens_match = re.search(opens_pattern, surrounding_text, re.IGNORECASE)
                if opens_match:
                    opens_into = opens_match.group(1).strip()
                
                door = DoorOpening(
                    width=width,
                    height=height,
                    opens_into=opens_into,
                    original_text=door_match.group(0),
                    confidence=0.8
                )
                room.doors.append(door)
        
        # Extract missing walls
        missing_wall_pattern = r'missing\s+wall.*?dimensions?:\s*(\d+(?:\'[\s\-]*\d+(?:\s*\d+/\d+)?\"?)?)\s*[xX×]\s*(\d+(?:\'[\s\-]*\d+\"?)?)'
        for wall_match in re.finditer(missing_wall_pattern, full_text, re.IGNORECASE):
            width = self.parser.parse_dimension(wall_match.group(1))
            height = self.parser.parse_dimension(wall_match.group(2))
            
            if width and height:
                # Look for "opens into" in the surrounding text
                opens_into = "Unknown"
                opens_pattern = r'opens?\s+into:\s*([A-Z_][A-Z_\s]*)'
                surrounding_text = full_text[max(0, wall_match.start()-100):wall_match.end()+100]
                opens_match = re.search(opens_pattern, surrounding_text, re.IGNORECASE)
                if opens_match:
                    opens_into = opens_match.group(1).strip()
                
                missing_wall = MissingWall(
                    width=width,
                    height=height,
                    opens_into=opens_into,
                    original_text=wall_match.group(0),
                    confidence=0.8
                )
                room.missing_walls.append(missing_wall)
        
        return room
    
    def extract_measurements_openai(self, ocr_results: List[Dict], image_data: Optional[bytes] = None) -> Optional[RoomMeasurement]:
        """
        Extract measurements using OpenAI Vision API for complex parsing
        
        Args:
            ocr_results: OCR results from image processing
            image_data: Optional image data for vision analysis
            
        Returns:
            RoomMeasurement object or None if extraction fails
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available for complex parsing")
            return None
        
        try:
            # Combine OCR text
            full_text = " ".join([result['text'] for result in ocr_results])
            
            # Create structured prompt for measurement extraction
            prompt = f"""
            Analyze this construction measurement data and extract structured information:
            
            OCR Text: {full_text}
            
            Please extract and return a JSON object with the following structure:
            {{
                "room_name": "name of the room",
                "room_type": "BEDROOM|BATHROOM|KITCHEN|LIVING_ROOM|etc",
                "height": "room height in feet",
                "walls": {{
                    "area": "wall area in square feet",
                    "total_with_ceiling": "total wall and ceiling area in SF"
                }},
                "ceiling": {{
                    "area": "ceiling area in square feet", 
                    "perimeter": "ceiling perimeter in linear feet"
                }},
                "floor": {{
                    "area": "floor area in square feet",
                    "perimeter": "floor perimeter in linear feet",
                    "flooring": "flooring area in square yards"
                }},
                "doors": [
                    {{
                        "dimensions": "width x height",
                        "opens_into": "where it opens to"
                    }}
                ],
                "missing_walls": [
                    {{
                        "dimensions": "width x height",
                        "opens_into": "where it opens to"
                    }}
                ]
            }}
            
            Extract only the measurements that are clearly present in the text. Use "null" for missing values.
            """
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use the more cost-effective model
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting construction measurements from text. Return only valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle potential markdown formatting)
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            elif response_text.startswith('```') and response_text.endswith('```'):
                response_text = response_text[3:-3].strip()
            
            # Parse JSON response
            extracted_data = json.loads(response_text)
            
            # Convert to RoomMeasurement object
            room = self._convert_openai_response(extracted_data)
            room.extraction_confidence = 0.9  # High confidence for AI extraction
            
            return room
            
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return None
    
    def _convert_openai_response(self, data: Dict) -> RoomMeasurement:
        """Convert OpenAI response to RoomMeasurement object"""
        room = RoomMeasurement(
            room_name=data.get('room_name', 'Unknown Room'),
            room_type=getattr(RoomType, data.get('room_type', 'OTHER'), RoomType.OTHER)
        )
        
        # Parse height
        if data.get('height'):
            room.height = self.parser.parse_dimension(str(data['height']))
        
        # Parse walls
        if data.get('walls'):
            room.walls = WallMeasurement()
            if data['walls'].get('area'):
                room.walls.area = Area(
                    value=Decimal(str(data['walls']['area'])),
                    unit=MeasurementUnit.SQUARE_FEET,
                    confidence=0.9
                )
        
        # Parse ceiling
        if data.get('ceiling'):
            room.ceiling = CeilingMeasurement()
            if data['ceiling'].get('area'):
                room.ceiling.area = Area(
                    value=Decimal(str(data['ceiling']['area'])),
                    unit=MeasurementUnit.SQUARE_FEET,
                    confidence=0.9
                )
            if data['ceiling'].get('perimeter'):
                room.ceiling.perimeter = Dimension(
                    value=Decimal(str(data['ceiling']['perimeter'])),
                    unit=MeasurementUnit.LINEAR_FEET,
                    confidence=0.9
                )
        
        # Parse floor
        if data.get('floor'):
            room.floor = FloorMeasurement()
            if data['floor'].get('area'):
                room.floor.area = Area(
                    value=Decimal(str(data['floor']['area'])),
                    unit=MeasurementUnit.SQUARE_FEET,
                    confidence=0.9
                )
            if data['floor'].get('perimeter'):
                room.floor.perimeter = Dimension(
                    value=Decimal(str(data['floor']['perimeter'])),
                    unit=MeasurementUnit.LINEAR_FEET,
                    confidence=0.9
                )
            if data['floor'].get('flooring'):
                room.floor.flooring_area = Area(
                    value=Decimal(str(data['floor']['flooring'])),
                    unit=MeasurementUnit.SQUARE_YARDS,
                    confidence=0.9
                )
        
        # Parse doors
        for door_data in data.get('doors', []):
            if door_data.get('dimensions'):
                dims = door_data['dimensions'].split('x')
                if len(dims) == 2:
                    width = self.parser.parse_dimension(dims[0].strip())
                    height = self.parser.parse_dimension(dims[1].strip())
                    if width and height:
                        door = DoorOpening(
                            width=width,
                            height=height,
                            opens_into=door_data.get('opens_into', 'Unknown'),
                            confidence=0.9
                        )
                        room.doors.append(door)
        
        # Parse missing walls
        for wall_data in data.get('missing_walls', []):
            if wall_data.get('dimensions'):
                dims = wall_data['dimensions'].split('x')
                if len(dims) == 2:
                    width = self.parser.parse_dimension(dims[0].strip())
                    height = self.parser.parse_dimension(dims[1].strip())
                    if width and height:
                        missing_wall = MissingWall(
                            width=width,
                            height=height,
                            opens_into=wall_data.get('opens_into', 'Unknown'),
                            confidence=0.9
                        )
                        room.missing_walls.append(missing_wall)
        
        return room
    
    def extract_measurements(self, ocr_results: List[Dict], filename: str = "", 
                           image_data: Optional[bytes] = None, 
                           use_openai_fallback: bool = True) -> RoomMeasurement:
        """
        Extract measurements using multiple strategies
        
        Args:
            ocr_results: OCR results from image processing
            filename: Source filename for room detection
            image_data: Optional image data for vision analysis
            use_openai_fallback: Whether to use OpenAI for complex parsing
            
        Returns:
            RoomMeasurement object with extracted data
        """
        # Start with basic extraction
        room = self.extract_measurements_basic(ocr_results)
        
        # Set source filename
        room.source_filename = filename
        
        # Extract room info from filename if not found in OCR
        if room.room_name == "Unknown Room" and filename:
            room_name, room_type, subroom = self.extract_room_from_filename(filename)
            room.room_name = room_name
            room.room_type = room_type
            room.subroom = subroom
        
        # Try OpenAI extraction if basic extraction is incomplete and fallback is enabled
        if use_openai_fallback and self._is_extraction_incomplete(room):
            logger.info("Basic extraction incomplete, trying OpenAI fallback")
            openai_room = self.extract_measurements_openai(ocr_results, image_data)
            if openai_room:
                # Merge results, preferring OpenAI data for missing fields
                room = self._merge_room_measurements(room, openai_room)
                room.processing_notes.append("Enhanced with OpenAI extraction")
        
        # Calculate derived measurements
        self._calculate_derived_measurements(room)
        
        return room
    
    def _is_extraction_incomplete(self, room: RoomMeasurement) -> bool:
        """Check if extraction needs enhancement"""
        missing_count = 0
        
        if not room.height:
            missing_count += 1
        if not room.walls or not room.walls.area:
            missing_count += 1
        if not room.ceiling or not room.ceiling.area:
            missing_count += 1
        if not room.floor or not room.floor.area:
            missing_count += 1
        
        return missing_count >= 2  # If 2 or more major measurements are missing
    
    def _merge_room_measurements(self, basic: RoomMeasurement, enhanced: RoomMeasurement) -> RoomMeasurement:
        """Merge basic and enhanced measurements, preferring enhanced when available"""
        # Start with basic extraction
        merged = basic
        
        # Use enhanced measurements for missing or low-confidence data
        if not merged.height and enhanced.height:
            merged.height = enhanced.height
        
        if (not merged.walls or not merged.walls.area) and enhanced.walls and enhanced.walls.area:
            merged.walls = enhanced.walls
        
        if (not merged.ceiling or not merged.ceiling.area) and enhanced.ceiling and enhanced.ceiling.area:
            merged.ceiling = enhanced.ceiling
        
        if (not merged.floor or not merged.floor.area) and enhanced.floor and enhanced.floor.area:
            merged.floor = enhanced.floor
        
        # Merge doors and walls (combine unique entries)
        if enhanced.doors:
            merged.doors.extend(enhanced.doors)
        
        if enhanced.missing_walls:
            merged.missing_walls.extend(enhanced.missing_walls)
        
        # Use enhanced room name if more specific
        if enhanced.room_name != "Unknown Room" and merged.room_name == "Unknown Room":
            merged.room_name = enhanced.room_name
            merged.room_type = enhanced.room_type
        
        return merged
    
    def _calculate_derived_measurements(self, room: RoomMeasurement) -> None:
        """Calculate derived measurements and validate data"""
        try:
            # Calculate total wall and ceiling area if not present
            if room.walls and room.walls.area and room.ceiling and room.ceiling.area:
                total_area = room.get_total_wall_ceiling_area()
                if total_area:
                    room.processing_notes.append(f"Total wall + ceiling: {total_area:.2f} SF")
            
            # Validate floor area vs calculated area from dimensions
            if room.floor and room.floor.length and room.floor.width:
                calculated_area = room.floor.length.to_feet() * room.floor.width.to_feet()
                if room.floor.area:
                    actual_area = room.floor.area.to_square_feet()
                    if abs(calculated_area - actual_area) / actual_area > 0.1:  # 10% tolerance
                        room.processing_notes.append(f"Floor area discrepancy detected")
            
        except Exception as e:
            logger.warning(f"Error calculating derived measurements: {e}")
            room.processing_notes.append("Error in measurement calculations")