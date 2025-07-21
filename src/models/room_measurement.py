"""
Enhanced data models for room measurements and construction estimation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
from decimal import Decimal
import re
from enum import Enum


class MeasurementUnit(Enum):
    """Supported measurement units"""
    FEET = "ft"
    INCHES = "in"
    SQUARE_FEET = "SF"
    SQUARE_YARDS = "SY"
    LINEAR_FEET = "LF"
    CUBIC_FEET = "CF"


class RoomType(Enum):
    """Common room types"""
    BEDROOM = "BEDROOM"
    BATHROOM = "BATHROOM"
    KITCHEN = "KITCHEN"
    LIVING_ROOM = "LIVING_ROOM"
    DINING_ROOM = "DINING_ROOM"
    OFFICE = "OFFICE"
    CLOSET = "CLOSET"
    HALLWAY = "HALLWAY"
    ENTRY_FOYER = "ENTRY_FOYER"
    GARAGE = "GARAGE"
    BASEMENT = "BASEMENT"
    ATTIC = "ATTIC"
    LAUNDRY = "LAUNDRY"
    OTHER = "OTHER"


@dataclass
class Dimension:
    """Represents a single dimension measurement"""
    value: Decimal
    unit: MeasurementUnit
    original_text: str = ""
    confidence: float = 1.0
    
    def to_feet(self) -> Decimal:
        """Convert dimension to feet"""
        if self.unit == MeasurementUnit.INCHES:
            return self.value / 12
        elif self.unit == MeasurementUnit.FEET:
            return self.value
        else:
            raise ValueError(f"Cannot convert {self.unit} to feet")
    
    def to_inches(self) -> Decimal:
        """Convert dimension to inches"""
        if self.unit == MeasurementUnit.FEET:
            return self.value * 12
        elif self.unit == MeasurementUnit.INCHES:
            return self.value
        else:
            raise ValueError(f"Cannot convert {self.unit} to inches")
    
    def __str__(self) -> str:
        """String representation of dimension"""
        if self.unit == MeasurementUnit.FEET and '.' in str(self.value):
            # Convert decimal feet to feet-inches format
            feet = int(self.value)
            inches = int((self.value - feet) * 12)
            if inches > 0:
                return f"{feet}'-{inches}\""
            else:
                return f"{feet}'"
        return f"{self.value} {self.unit.value}"


@dataclass
class Area:
    """Represents an area measurement"""
    value: Decimal
    unit: MeasurementUnit
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    original_text: str = ""
    confidence: float = 1.0
    
    def to_square_feet(self) -> Decimal:
        """Convert area to square feet"""
        if self.unit == MeasurementUnit.SQUARE_FEET:
            return self.value
        elif self.unit == MeasurementUnit.SQUARE_YARDS:
            return self.value * 9
        else:
            raise ValueError(f"Cannot convert {self.unit} to square feet")
    
    def to_square_yards(self) -> Decimal:
        """Convert area to square yards"""
        if self.unit == MeasurementUnit.SQUARE_YARDS:
            return self.value
        elif self.unit == MeasurementUnit.SQUARE_FEET:
            return self.value / 9
        else:
            raise ValueError(f"Cannot convert {self.unit} to square yards")


@dataclass
class DoorOpening:
    """Represents a door opening"""
    width: Dimension
    height: Dimension
    opens_into: str = "Unknown"
    door_type: str = "Standard"
    original_text: str = ""
    confidence: float = 1.0
    
    def __str__(self) -> str:
        return f"{self.width} X {self.height}"


@dataclass
class WindowOpening:
    """Represents a window opening"""
    width: Dimension
    height: Dimension
    window_type: str = "Standard"
    original_text: str = ""
    confidence: float = 1.0
    
    def __str__(self) -> str:
        return f"{self.width} X {self.height}"


@dataclass
class WallMeasurement:
    """Represents wall measurements"""
    area: Optional[Area] = None
    height: Optional[Dimension] = None
    length: Optional[Dimension] = None
    doors: List[DoorOpening] = field(default_factory=list)
    windows: List[WindowOpening] = field(default_factory=list)
    original_text: str = ""
    confidence: float = 1.0


@dataclass
class CeilingMeasurement:
    """Represents ceiling measurements"""
    area: Optional[Area] = None
    height: Optional[Dimension] = None
    perimeter: Optional[Dimension] = None
    original_text: str = ""
    confidence: float = 1.0


@dataclass
class FloorMeasurement:
    """Represents floor measurements"""
    area: Optional[Area] = None
    perimeter: Optional[Dimension] = None
    flooring_area: Optional[Area] = None  # In square yards
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    original_text: str = ""
    confidence: float = 1.0


@dataclass
class MissingWall:
    """Represents a missing wall/opening"""
    width: Dimension
    height: Dimension
    opens_into: str = "Unknown"
    original_text: str = ""
    confidence: float = 1.0
    
    def __str__(self) -> str:
        return f"{self.width} X {self.height}"


@dataclass
class RoomMeasurement:
    """Complete room measurement data"""
    room_name: str
    room_type: RoomType = RoomType.OTHER
    subroom: str = ""
    
    # Main measurements
    height: Optional[Dimension] = None
    walls: Optional[WallMeasurement] = None
    ceiling: Optional[CeilingMeasurement] = None
    floor: Optional[FloorMeasurement] = None
    
    # Openings
    doors: List[DoorOpening] = field(default_factory=list)
    windows: List[WindowOpening] = field(default_factory=list)
    missing_walls: List[MissingWall] = field(default_factory=list)
    
    # Metadata
    source_filename: str = ""
    extraction_confidence: float = 1.0
    processing_notes: List[str] = field(default_factory=list)
    
    def get_total_wall_ceiling_area(self) -> Optional[Decimal]:
        """Calculate total wall and ceiling area"""
        total = Decimal('0')
        
        if self.walls and self.walls.area:
            total += self.walls.area.to_square_feet()
        
        if self.ceiling and self.ceiling.area:
            total += self.ceiling.area.to_square_feet()
        
        return total if total > 0 else None
    
    def get_display_name(self) -> str:
        """Get formatted display name for the room"""
        if self.subroom:
            return f"{self.room_name} - {self.subroom}"
        return self.room_name


@dataclass
class BulkProcessingResult:
    """Results from bulk image processing"""
    total_images: int
    successful_extractions: int
    failed_extractions: int
    room_measurements: List[RoomMeasurement] = field(default_factory=list)
    processing_errors: List[Dict[str, str]] = field(default_factory=list)
    processing_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_images == 0:
            return 0.0
        return (self.successful_extractions / self.total_images) * 100


# Utility functions for measurement parsing
class MeasurementParser:
    """Enhanced parser for construction measurements"""
    
    # Enhanced regex patterns for various measurement formats
    PATTERNS = {
        'feet_inches_precise': re.compile(r"(\d+)(?:'|ft)\s*(?:(\d+)(?:\s*(\d+)/(\d+))?(?:\"|in))?", re.IGNORECASE),
        'feet_inches_decimal': re.compile(r"(\d+\.?\d*)\s*(?:'|ft)?\s*(\d+\.?\d*)\s*(?:\"|in)?", re.IGNORECASE),
        'dimensions': re.compile(r"(\d+(?:\.\d+)?(?:'[\s\-]*\d+(?:\s*\d+/\d+)?\"?)?)\s*[xX×]\s*(\d+(?:\.\d+)?(?:'[\s\-]*\d+(?:\s*\d+/\d+)?\"?)?)", re.IGNORECASE),
        'area_sf': re.compile(r"(\d+\.?\d*)\s*(?:sq\.?\s*ft\.?|sf|square\s+feet?)", re.IGNORECASE),
        'area_sy': re.compile(r"(\d+\.?\d*)\s*(?:sq\.?\s*y(?:ard)?s?\.?|sy|square\s+yards?)", re.IGNORECASE),
        'linear_feet': re.compile(r"(\d+\.?\d*)\s*(?:lin\.?\s*ft\.?|lf|linear\s+feet?)", re.IGNORECASE),
        'height': re.compile(r"(?:height|h):\s*(\d+(?:\.\d+)?(?:'[\s\-]*\d+(?:\s*\d+/\d+)?\"?)?)", re.IGNORECASE),
        'door_dimensions': re.compile(r"(?:door|opening):\s*(\d+(?:\.\d+)?(?:'[\s\-]*\d+(?:\s*\d+/\d+)?\"?)?)\s*[xX×]\s*(\d+(?:\.\d+)?(?:'[\s\-]*\d+(?:\s*\d+/\d+)?\"?)?)", re.IGNORECASE),
        'opens_into': re.compile(r"opens?\s+into:?\s*([A-Z_][A-Z_\s]*)", re.IGNORECASE),
        'room_name': re.compile(r"(?:room|location):\s*([A-Z_][A-Z_\s\-]*)", re.IGNORECASE),
    }
    
    @classmethod
    def parse_dimension(cls, text: str) -> Optional[Dimension]:
        """Parse a dimension from text"""
        # Try feet-inches format first
        match = cls.PATTERNS['feet_inches_precise'].search(text)
        if match:
            feet = Decimal(match.group(1))
            inches = Decimal(match.group(2) or '0')
            
            # Handle fractional inches
            if match.group(3) and match.group(4):
                inches += Decimal(match.group(3)) / Decimal(match.group(4))
            
            total_feet = feet + (inches / 12)
            return Dimension(
                value=total_feet,
                unit=MeasurementUnit.FEET,
                original_text=text,
                confidence=0.9
            )
        
        # Try decimal feet
        if 'ft' in text.lower() or "'" in text:
            numbers = re.findall(r'(\d+\.?\d*)', text)
            if numbers:
                return Dimension(
                    value=Decimal(numbers[0]),
                    unit=MeasurementUnit.FEET,
                    original_text=text,
                    confidence=0.8
                )
        
        # Try inches
        if 'in' in text.lower() or '"' in text:
            numbers = re.findall(r'(\d+\.?\d*)', text)
            if numbers:
                return Dimension(
                    value=Decimal(numbers[0]),
                    unit=MeasurementUnit.INCHES,
                    original_text=text,
                    confidence=0.8
                )
        
        return None
    
    @classmethod
    def parse_area(cls, text: str) -> Optional[Area]:
        """Parse an area measurement from text"""
        # Try square feet
        match = cls.PATTERNS['area_sf'].search(text)
        if match:
            return Area(
                value=Decimal(match.group(1)),
                unit=MeasurementUnit.SQUARE_FEET,
                original_text=text,
                confidence=0.9
            )
        
        # Try square yards
        match = cls.PATTERNS['area_sy'].search(text)
        if match:
            return Area(
                value=Decimal(match.group(1)),
                unit=MeasurementUnit.SQUARE_YARDS,
                original_text=text,
                confidence=0.9
            )
        
        return None
    
    @classmethod
    def parse_door_opening(cls, text: str) -> Optional[DoorOpening]:
        """Parse door opening from text"""
        match = cls.PATTERNS['door_dimensions'].search(text)
        if match:
            width = cls.parse_dimension(match.group(1))
            height = cls.parse_dimension(match.group(2))
            
            if width and height:
                # Look for "opens into" information
                opens_into = "Unknown"
                opens_match = cls.PATTERNS['opens_into'].search(text)
                if opens_match:
                    opens_into = opens_match.group(1).strip()
                
                return DoorOpening(
                    width=width,
                    height=height,
                    opens_into=opens_into,
                    original_text=text,
                    confidence=0.8
                )
        
        return None
    
    @classmethod
    def detect_room_type(cls, room_name: str) -> RoomType:
        """Detect room type from name"""
        name_lower = room_name.lower()
        
        if any(word in name_lower for word in ['bedroom', 'bed']):
            return RoomType.BEDROOM
        elif any(word in name_lower for word in ['bathroom', 'bath']):
            return RoomType.BATHROOM
        elif any(word in name_lower for word in ['kitchen', 'kit']):
            return RoomType.KITCHEN
        elif any(word in name_lower for word in ['living', 'family']):
            return RoomType.LIVING_ROOM
        elif any(word in name_lower for word in ['dining', 'din']):
            return RoomType.DINING_ROOM
        elif any(word in name_lower for word in ['office', 'study']):
            return RoomType.OFFICE
        elif any(word in name_lower for word in ['closet', 'clo']):
            return RoomType.CLOSET
        elif any(word in name_lower for word in ['hallway', 'hall', 'corridor']):
            return RoomType.HALLWAY
        elif any(word in name_lower for word in ['entry', 'foyer', 'entrance']):
            return RoomType.ENTRY_FOYER
        elif any(word in name_lower for word in ['garage', 'gar']):
            return RoomType.GARAGE
        elif any(word in name_lower for word in ['basement', 'cellar']):
            return RoomType.BASEMENT
        elif any(word in name_lower for word in ['attic', 'loft']):
            return RoomType.ATTIC
        elif any(word in name_lower for word in ['laundry', 'utility']):
            return RoomType.LAUNDRY
        else:
            return RoomType.OTHER