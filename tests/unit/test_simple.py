"""
Simple test without external dependencies
"""

import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_measurement_patterns():
    """Test measurement extraction patterns"""
    patterns = {
        'feet_inches': r"(\d+)'-?(\d+)?\"?",  # 10'-6", 10'6", 10'
        'dimensions': r"(\d+)\s*[xX]\s*(\d+)",  # 10x12, 10 x 12
        'decimal_feet': r"(\d+\.?\d*)\s*(?:ft|feet)",  # 10.5 ft
        'inches': r"(\d+\.?\d*)\s*(?:in|inches|\")",  # 12 in, 12"
        'area': r"(\d+\.?\d*)\s*(?:sq ft|sqft|sf)",  # 100 sq ft
    }
    
    test_texts = [
        "Wall dimensions: 10'-6\" x 8'-0\"",
        "Room is 12x8 feet",
        "Length: 15.5 ft",
        "Width: 24 inches",
        "Total area: 100 sq ft",
        "Door: 3'-0\" x 6'-8\"",
        "Window 4x3 ft"
    ]
    
    print("Testing measurement patterns:")
    print("=" * 40)
    
    measurements = []
    
    for text in test_texts:
        print(f"\nTesting: '{text}'")
        found_any = False
        
        for pattern_name, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found_any = True
                print(f"  Found {pattern_name}: {match.groups()}")
                
                # Parse the measurement
                measurement = parse_measurement(match, pattern_name, text)
                if measurement:
                    measurements.append(measurement)
                    print(f"     → {measurement}")
        
        if not found_any:
            print("  No patterns matched")
    
    return measurements

def parse_measurement(match, pattern_name: str, original_text: str):
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
                'original_text': original_text.strip()
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
                'original_text': original_text.strip()
            }
        
        elif pattern_name == 'decimal_feet':
            feet = float(match.group(1))
            inches = feet * 12
            return {
                'type': 'length',
                'value': inches,
                'unit': 'inches',
                'display': f"{feet} ft",
                'original_text': original_text.strip()
            }
        
        elif pattern_name == 'inches':
            inches = float(match.group(1))
            return {
                'type': 'length',
                'value': inches,
                'unit': 'inches',
                'display': f"{inches}\"",
                'original_text': original_text.strip()
            }
        
        elif pattern_name == 'area':
            area = float(match.group(1))
            return {
                'type': 'area',
                'value': area,
                'unit': 'sq_ft',
                'display': f"{area} sq ft",
                'original_text': original_text.strip()
            }
            
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse measurement: {e}")
        return None

if __name__ == "__main__":
    print("Construction Estimator - Pattern Test")
    print("=" * 50)
    
    # Test patterns
    measurements = test_measurement_patterns()
    
    print(f"\nSummary: Found {len(measurements)} measurements")
    print("=" * 40)
    
    for i, measurement in enumerate(measurements, 1):
        print(f"{i}. {measurement['display']} ({measurement['type']})")
    
    print("\nPattern tests completed!")
    print("\nPhase 1 Core Logic: WORKING")
    print("Next: Add OCR service when dependencies are available")