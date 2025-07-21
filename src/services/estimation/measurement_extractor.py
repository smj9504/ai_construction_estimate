"""
Measurement extraction service for parsing OCR results into structured measurements.
"""

import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class MeasurementExtractor:
    """Extract and parse measurements from OCR text"""
    
    def __init__(self):
        """Initialize measurement patterns"""
        self.patterns = {
            'feet_inches': r"(\d+)'-?(\d+)?\"?",  # 10'-6", 10'6", 10'
            'dimensions': r"(\d+)\s*[xX]\s*(\d+)",  # 10x12, 10 x 12
            'decimal_feet': r"(\d+\.?\d*)\s*(?:ft|feet)",  # 10.5 ft
            'inches': r"(\d+\.?\d*)\s*(?:in|inches|\")",  # 12 in, 12"
            'area': r"(\d+\.?\d*)\s*(?:sq ft|sqft|sf)",  # 100 sq ft
        }
    
    def extract_measurements(self, ocr_results: List[Dict]) -> List[Dict]:
        """Extract measurements from OCR results"""
        measurements = []
        
        for result in ocr_results:
            text = result['text'].strip()
            confidence = result['confidence']
            
            # Try each pattern
            for pattern_name, pattern in self.patterns.items():
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    measurement = self._parse_measurement(match, pattern_name, text, confidence)
                    if measurement:
                        measurements.append(measurement)
        
        return measurements
    
    def _parse_measurement(self, match, pattern_name: str, original_text: str, confidence: float) -> Optional[Dict]:
        """Parse a specific measurement match"""
        try:
            if pattern_name == 'feet_inches':
                feet = int(match.group(1))
                inches = int(match.group(2)) if match.group(2) else 0
                total_inches = feet * 12 + inches
                return {
                    'type': 'length',
                    'value': total_inches,
                    'unit': 'inches',
                    'display': f"{feet}'-{inches}\"",
                    'original_text': original_text,
                    'confidence': confidence
                }
            
            elif pattern_name == 'dimensions':
                width = float(match.group(1))
                height = float(match.group(2))
                return {
                    'type': 'dimension',
                    'width': width,
                    'height': height,
                    'area': width * height,
                    'display': f"{width} x {height}",
                    'original_text': original_text,
                    'confidence': confidence
                }
            
            elif pattern_name == 'decimal_feet':
                feet = float(match.group(1))
                inches = feet * 12
                return {
                    'type': 'length',
                    'value': inches,
                    'unit': 'inches',
                    'display': f"{feet} ft",
                    'original_text': original_text,
                    'confidence': confidence
                }
            
            elif pattern_name == 'inches':
                inches = float(match.group(1))
                return {
                    'type': 'length',
                    'value': inches,
                    'unit': 'inches',
                    'display': f"{inches}\"",
                    'original_text': original_text,
                    'confidence': confidence
                }
            
            elif pattern_name == 'area':
                area = float(match.group(1))
                return {
                    'type': 'area',
                    'value': area,
                    'unit': 'sq_ft',
                    'display': f"{area} sq ft",
                    'original_text': original_text,
                    'confidence': confidence
                }
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse measurement: {e}")
            return None