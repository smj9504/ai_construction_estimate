"""
YAML formatter for construction measurement data.
Formats measurements in the specific YAML structure required for construction estimation.
"""

import yaml
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConstructionYAMLFormatter:
    """Format construction measurements in YAML format"""
    
    def __init__(self):
        """Initialize YAML formatter"""
        self.yaml_config = {
            'default_flow_style': False,
            'allow_unicode': True,
            'sort_keys': False,
            'indent': 2
        }
    
    def format_room_to_yaml(self, room_data: Dict[str, Any]) -> str:
        """
        Format a single room's data to YAML string
        
        Args:
            room_data: Dictionary containing room measurement data
            
        Returns:
            YAML formatted string
        """
        try:
            # Ensure proper structure
            formatted_room = self._structure_room_data(room_data)
            
            # Convert to YAML
            yaml_str = yaml.dump([formatted_room], **self.yaml_config)
            
            return yaml_str
            
        except Exception as e:
            logger.error(f"Error formatting room to YAML: {e}")
            return ""
    
    def format_multiple_rooms_to_yaml(self, rooms_data: List[Dict[str, Any]]) -> str:
        """
        Format multiple rooms' data to YAML string
        
        Args:
            rooms_data: List of dictionaries containing room measurement data
            
        Returns:
            YAML formatted string
        """
        try:
            formatted_rooms = []
            
            for room_data in rooms_data:
                formatted_room = self._structure_room_data(room_data)
                formatted_rooms.append(formatted_room)
            
            # Convert to YAML
            yaml_str = yaml.dump(formatted_rooms, **self.yaml_config)
            
            return yaml_str
            
        except Exception as e:
            logger.error(f"Error formatting multiple rooms to YAML: {e}")
            return ""
    
    def _structure_room_data(self, room_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure room data according to the specified YAML format
        
        Args:
            room_data: Raw room data dictionary
            
        Returns:
            Structured dictionary matching YAML format
        """
        structured = {}
        
        # Room name (required)
        structured['Room'] = room_data.get('room_name', room_data.get('Room', 'Unknown Room'))
        
        # Height (optional)
        if 'height' in room_data or 'Height' in room_data:
            structured['Height'] = room_data.get('height', room_data.get('Height'))
        
        # Measurements (main content)
        measurements = room_data.get('measurements', room_data.get('Measurements', {}))
        if measurements:
            structured['Measurements'] = self._structure_measurements(measurements)
        
        return structured
    
    def _structure_measurements(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure measurements according to the specified format
        
        Args:
            measurements: Raw measurements dictionary
            
        Returns:
            Structured measurements dictionary
        """
        structured_measurements = {}
        
        # Process each measurement category
        for category, data in measurements.items():
            if isinstance(data, list):
                # Convert list items to proper format
                formatted_items = []
                for item in data:
                    if isinstance(item, dict):
                        formatted_items.append(item)
                    else:
                        # Convert string or simple values
                        formatted_items.append(str(item))
                
                structured_measurements[category] = formatted_items
            
            elif isinstance(data, dict):
                # Keep dict structure
                structured_measurements[category] = data
            
            else:
                # Convert simple values to list format
                structured_measurements[category] = [str(data)]
        
        return structured_measurements
    
    def save_to_yaml_file(self, rooms_data: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Save room measurements to YAML file
        
        Args:
            rooms_data: List of room measurement dictionaries
            output_path: Path to save YAML file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            yaml_content = self.format_multiple_rooms_to_yaml(rooms_data)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            logger.info(f"YAML data saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving YAML file: {e}")
            return False
    
    def parse_ocr_to_yaml(self, ocr_results: List[Dict], image_filename: Optional[str] = None) -> str:
        """
        Parse OCR results directly to YAML format
        
        Args:
            ocr_results: OCR results from image processing
            image_filename: Optional filename for room detection
            
        Returns:
            YAML formatted string
        """
        try:
            # Import the construction parser
            from .construction_parser import get_construction_parser
            
            parser = get_construction_parser()
            room_measurement = parser.parse_construction_image(ocr_results, image_filename)
            
            # Convert to YAML dict format
            room_dict = parser.to_yaml_dict(room_measurement)
            
            # Format to YAML string
            yaml_str = self.format_room_to_yaml(room_dict)
            
            return yaml_str
            
        except Exception as e:
            logger.error(f"Error parsing OCR to YAML: {e}")
            return ""


# Singleton instance
_formatter_instance = None


def get_yaml_formatter() -> ConstructionYAMLFormatter:
    """Get or create singleton instance of YAML formatter"""
    global _formatter_instance
    
    if _formatter_instance is None:
        _formatter_instance = ConstructionYAMLFormatter()
    
    return _formatter_instance