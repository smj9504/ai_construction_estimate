"""
Enhanced construction measurement parser for extracting structured measurements from OCR results.
Designed to output measurements in the YAML format specified for construction estimation.
"""

import re
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RoomMeasurement:
    """Structured room measurement data"""
    room_name: str
    height: Optional[str] = None
    measurements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.measurements is None:
            self.measurements = {}


class ConstructionMeasurementParser:
    """Extract and parse construction measurements from OCR text into structured YAML format"""
    
    def __init__(self):
        """Initialize measurement patterns for construction drawings"""
        # Enhanced patterns for construction measurements
        self.patterns = {
            # Dimensions and lengths
            'feet_inches': r"(\d+)'-?(\d+)?\"?",  # 10'-6", 10'6", 10', 9'
            'feet_only': r"(\d+)'(?!\d)",  # 9' (not followed by digit)
            'inches_only': r"(\d+)\"",  # 4", 11"
            'dimensions': r"(\d+)\s*[xX]\s*(\d+)",  # 10x12, 10 x 12
            'decimal_feet': r"(\d+\.?\d*)\s*(?:ft|feet)",  # 10.5 ft
            
            # Areas and square footage
            'area_sqft': r"(\d+\.?\d*)\s*(?:sq\s*ft|sqft|sf)",  # 112 sqft, 423 sf
            'area_sy': r"(\d+\.?\d*)\s*(?:sy|sq\s*yd)",  # 5.44 SY
            
            # Room features
            'ceiling_height': r"ceiling\s*height\s*(\d+)'?",  # ceiling height 9'
            'baseboard': r"baseboard\s*(\d+)\"?",  # baseboard 4"
            
            # Materials
            'carpet': r"carpet\s*(\d+\.?\d*)\s*(?:sqft|sf)",  # carpet 112 sqft
            'drywall_paint': r"drywall\s*&?\s*paint\s*(\d+\.?\d*)\s*(?:sqft|sf)",  # drywall & paint 423 sqft
            
            # Special features
            'missing_wall': r"missing\s*wall",  # missing wall
            'door': r"door",  # door
            'basement': r"basement\s*#?(\d+)",  # basement #1
        }
        
        # Room name patterns
        self.room_patterns = [
            r"^([A-Za-z\s]+?)(?:\s*-\s*.*)?$",  # Extract main room name before dash
            r"room:\s*([A-Za-z\s]+)",  # Room: Hallway
            r"([A-Za-z\s]+)(?:\s+area)?$",  # Hallway, Bedroom area
        ]
    
    def parse_construction_image(self, ocr_results: List[Dict], image_filename: Optional[str] = None) -> RoomMeasurement:
        """
        Parse OCR results from a construction image into structured measurements
        
        Args:
            ocr_results: List of OCR text results with confidence scores
            image_filename: Optional filename for room detection
            
        Returns:
            RoomMeasurement object with structured data
        """
        try:
            # Extract all text
            all_text = ' '.join([result['text'] for result in ocr_results])
            
            # Detect room name
            room_name = self._detect_room_name(all_text, image_filename)
            
            # Initialize room measurement
            room = RoomMeasurement(room_name=room_name)
            
            # Extract height information
            room.height = self._extract_height(all_text)
            
            # Parse measurements
            measurements = self._parse_measurements(ocr_results, all_text)
            room.measurements = measurements
            
            return room
            
        except Exception as e:
            logger.error(f"Error parsing construction measurements: {e}")
            return RoomMeasurement(room_name="Unknown", measurements={})
    
    def _detect_room_name(self, text: str, filename: Optional[str] = None) -> str:
        """Detect room name from text and filename"""
        # Try to extract from filename first
        if filename:
            name_from_file = self._extract_room_from_filename(filename)
            if name_from_file:
                return name_from_file
        
        # Try to extract from text
        text_lower = text.lower()
        
        # Common room types
        room_types = [
            'hallway', 'bedroom', 'bathroom', 'kitchen', 'living room', 'dining room',
            'office', 'closet', 'basement', 'attic', 'garage', 'laundry', 'entry',
            'foyer', 'family room', 'den', 'study', 'pantry'
        ]
        
        for room_type in room_types:
            if room_type in text_lower:
                return room_type.title()
        
        # Try pattern matching
        for pattern in self.room_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        
        return "Unknown Room"
    
    def _extract_room_from_filename(self, filename: str) -> Optional[str]:
        """Extract room name from filename"""
        name = filename.lower()
        name = re.sub(r'\.(jpg|jpeg|png|bmp|tiff)$', '', name)
        
        room_types = [
            'hallway', 'bedroom', 'bathroom', 'kitchen', 'living', 'dining',
            'office', 'closet', 'basement', 'attic', 'garage', 'laundry'
        ]
        
        for room_type in room_types:
            if room_type in name:
                return room_type.title()
        
        return None
    
    def _extract_height(self, text: str) -> Optional[str]:
        """Extract ceiling height from text"""
        # Look for ceiling height patterns
        patterns = [
            r"ceiling\s*height\s*(\d+)'?",
            r"height\s*(\d+)'?",
            r"(\d+)'\s*ceiling",
            r"(\d+)'\s*high"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                height = match.group(1)
                return f"{height}'"
        
        return None
    
    def _parse_measurements(self, ocr_results: List[Dict], full_text: str) -> Dict[str, Any]:
        """Parse measurements from OCR results"""
        measurements = {}
        
        # Extract wall measurements
        walls = self._extract_wall_measurements(ocr_results, full_text)
        if walls:
            measurements['Walls'] = walls
        
        # Extract ceiling measurements
        ceiling = self._extract_ceiling_measurements(ocr_results, full_text)
        if ceiling:
            measurements['Ceiling'] = ceiling
        
        # Extract floor measurements
        floor = self._extract_floor_measurements(ocr_results, full_text)
        if floor:
            measurements['Floor'] = floor
        
        # Extract baseboard
        baseboard = self._extract_baseboard_measurements(full_text)
        if baseboard:
            measurements['Baseboard'] = baseboard
        
        # Extract doors
        doors = self._extract_door_measurements(full_text)
        if doors:
            measurements['Door'] = doors
        
        # Extract missing walls
        missing_walls = self._extract_missing_wall_measurements(ocr_results, full_text)
        if missing_walls:
            measurements['Missing Wall'] = missing_walls
        
        # Extract features
        features = self._extract_features(full_text)
        if features:
            measurements.update(features)
        
        return measurements
    
    def _extract_wall_measurements(self, ocr_results: List[Dict], text: str) -> Optional[List[Dict]]:
        """Extract wall-related measurements"""
        walls = []
        
        # Look for length measurements (walls)
        length_pattern = r"(\d+)'"
        matches = re.finditer(length_pattern, text)
        
        for match in matches:
            length = match.group(1)
            walls.append({'Length': f"{length}'"})
        
        return walls if walls else None
    
    def _extract_ceiling_measurements(self, ocr_results: List[Dict], text: str) -> Optional[List[Dict]]:
        """Extract ceiling measurements"""
        ceiling = []
        
        # Look for ceiling height
        height_match = re.search(r"ceiling\s*height\s*(\d+)'?", text, re.IGNORECASE)
        if height_match:
            height = height_match.group(1)
            ceiling.append({'Height': f"{height}'"})
        
        return ceiling if ceiling else None
    
    def _extract_floor_measurements(self, ocr_results: List[Dict], text: str) -> Optional[List[Dict]]:
        """Extract floor measurements including carpet and areas"""
        floor = []
        
        # Extract carpet area
        carpet_match = re.search(r"carpet\s*(\d+\.?\d*)\s*(?:sqft|sf)", text, re.IGNORECASE)
        if carpet_match:
            area = carpet_match.group(1)
            floor.append({'Carpet': f"{area} sqft"})
        
        return floor if floor else None
    
    def _extract_baseboard_measurements(self, text: str) -> Optional[List[Dict]]:
        """Extract baseboard measurements"""
        baseboard_match = re.search(r"baseboard\s*(\d+)\"?", text, re.IGNORECASE)
        if baseboard_match:
            height = baseboard_match.group(1)
            return [{'Height': f'{height}"'}]
        
        return None
    
    def _extract_door_measurements(self, text: str) -> Optional[List[Dict]]:
        """Extract door information"""
        if re.search(r"door", text, re.IGNORECASE):
            return [{'Location': 'Multiple doors indicated'}]
        
        return None
    
    def _extract_missing_wall_measurements(self, ocr_results: List[Dict], text: str) -> Optional[List[Dict]]:
        """Extract missing wall measurements"""
        missing_walls = []
        
        if re.search(r"missing\s*wall", text, re.IGNORECASE):
            # Look for associated measurements
            length_match = re.search(r"(\d+)'\s*.*missing", text, re.IGNORECASE)
            if length_match:
                length = length_match.group(1)
                missing_walls.append({'Length': f"{length}'"})
            else:
                missing_walls.append({'Note': 'Missing Wall'})
        
        return missing_walls if missing_walls else None
    
    def _extract_features(self, text: str) -> Dict[str, Any]:
        """Extract additional features and materials"""
        features = {}
        
        # Drywall & paint
        drywall_match = re.search(r"drywall\s*&?\s*paint\s*(\d+\.?\d*)\s*(?:sqft|sf)", text, re.IGNORECASE)
        if drywall_match:
            area = drywall_match.group(1)
            features['Drywall & Paint'] = [{'Area': f"{area} sqft"}]
        
        # Basement reference
        basement_match = re.search(r"basement\s*#?(\d+)", text, re.IGNORECASE)
        if basement_match:
            number = basement_match.group(1)
            features['Features'] = [f"Basement #{number}"]
        
        return features
    
    def to_yaml_dict(self, room: RoomMeasurement) -> Dict[str, Any]:
        """Convert RoomMeasurement to YAML-compatible dictionary"""
        result = {'Room': room.room_name}
        
        if room.height:
            result['Height'] = room.height
        
        if room.measurements:
            result['Measurements'] = room.measurements
        
        return result


# Singleton instance
_parser_instance = None


def get_construction_parser() -> ConstructionMeasurementParser:
    """Get or create singleton instance of construction parser"""
    global _parser_instance
    
    if _parser_instance is None:
        _parser_instance = ConstructionMeasurementParser()
    
    return _parser_instance