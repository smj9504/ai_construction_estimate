"""
Output formatting service for measurement data
"""

import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from decimal import Decimal
import json
import yaml
import csv
from datetime import datetime

from models.room_measurement import (
    RoomMeasurement, BulkProcessingResult, WallMeasurement, 
    CeilingMeasurement, FloorMeasurement, DoorOpening, WindowOpening, MissingWall
)

logger = logging.getLogger(__name__)


class MeasurementOutputFormatter:
    """Formats measurement data into various output formats"""
    
    def __init__(self):
        """Initialize the formatter"""
        pass
    
    def format_room_text(self, room: RoomMeasurement, include_metadata: bool = False) -> str:
        """
        Format room measurement as structured text matching the required format
        
        Args:
            room: RoomMeasurement object
            include_metadata: Whether to include processing metadata
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Room header
        room_title = f"Room: {room.get_display_name()}"
        lines.append(room_title)
        
        # Height
        if room.height:
            lines.append(f"  Height: {room.height}")
        
        # Measurements section
        lines.append("  Measurements:")
        
        # Walls
        if room.walls:
            lines.append("    Walls:")
            if room.walls.area:
                lines.append(f"      - Area: {room.walls.area.to_square_feet():.2f} SF")
            
            # Total wall and ceiling area
            total_area = room.get_total_wall_ceiling_area()
            if total_area:
                lines.append(f"      - Total (Walls & Ceiling): {total_area:.2f} SF")
        
        # Ceiling
        if room.ceiling:
            lines.append("    Ceiling:")
            if room.ceiling.area:
                lines.append(f"      - Area: {room.ceiling.area.to_square_feet():.2f} SF")
        
        # Floor
        if room.floor:
            lines.append("    Floor:")
            if room.floor.area:
                lines.append(f"      - Area: {room.floor.area.to_square_feet():.2f} SF")
            if room.floor.perimeter:
                lines.append(f"      - Perimeter: {room.floor.perimeter.value:.2f} LF")
            if room.floor.flooring_area:
                lines.append(f"      - Flooring: {room.floor.flooring_area.to_square_yards():.2f} SY")
        
        # Ceiling Perimeter
        if room.ceiling and room.ceiling.perimeter:
            lines.append("    Ceiling Perimeter:")
            lines.append(f"      - Length: {room.ceiling.perimeter.value:.2f} LF")
        
        # Doors
        if room.doors:
            lines.append("    Door:")
            for door in room.doors:
                lines.append(f"      - Dimensions: {door}")
                lines.append(f"      - Opens into: {door.opens_into}")
        
        # Windows (if any)
        if room.windows:
            lines.append("    Window:")
            for window in room.windows:
                lines.append(f"      - Dimensions: {window}")
        
        # Missing Walls
        if room.missing_walls:
            lines.append("    Missing Wall:")
            for wall in room.missing_walls:
                lines.append(f"      - Dimensions: {wall}")
                lines.append(f"      - Opens into: {wall.opens_into}")
        
        # Metadata (optional)
        if include_metadata:
            lines.append("  Metadata:")
            lines.append(f"    - Source: {room.source_filename}")
            lines.append(f"    - Confidence: {room.extraction_confidence:.2f}")
            if room.processing_notes:
                lines.append("    - Notes:")
                for note in room.processing_notes:
                    lines.append(f"      * {note}")
        
        return "\n".join(lines)
    
    def format_bulk_results_text(self, results: BulkProcessingResult, include_summary: bool = True) -> str:
        """
        Format bulk processing results as text
        
        Args:
            results: BulkProcessingResult object
            include_summary: Whether to include processing summary
            
        Returns:
            Formatted text string
        """
        lines = []
        
        if include_summary:
            # Processing summary
            lines.append("=== BULK PROCESSING RESULTS ===")
            lines.append(f"Total Images: {results.total_images}")
            lines.append(f"Successful Extractions: {results.successful_extractions}")
            lines.append(f"Failed Extractions: {results.failed_extractions}")
            lines.append(f"Success Rate: {results.success_rate:.1f}%")
            lines.append(f"Processing Time: {results.processing_time:.2f} seconds")
            lines.append("")
        
        # Room measurements
        lines.append("=== ROOM MEASUREMENTS ===")
        lines.append("")
        
        for i, room in enumerate(results.room_measurements, 1):
            lines.append(f"--- Room {i} ---")
            lines.append(self.format_room_text(room))
            lines.append("")
        
        # Errors (if any)
        if results.processing_errors:
            lines.append("=== PROCESSING ERRORS ===")
            for error in results.processing_errors:
                lines.append(f"File: {error.get('file', 'Unknown')}")
                lines.append(f"Error: {error.get('error', 'Unknown error')}")
                lines.append("")
        
        return "\n".join(lines)
    
    def format_room_json(self, room: RoomMeasurement, pretty: bool = True) -> str:
        """
        Format room measurement as JSON
        
        Args:
            room: RoomMeasurement object
            pretty: Whether to use pretty formatting
            
        Returns:
            JSON string
        """
        data = self._room_to_dict(room)
        
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        else:
            return json.dumps(data, ensure_ascii=False, default=str)
    
    def format_room_yaml(self, room: RoomMeasurement) -> str:
        """
        Format room measurement as YAML
        
        Args:
            room: RoomMeasurement object
            
        Returns:
            YAML string
        """
        data = self._room_to_dict(room)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    
    def format_bulk_results_csv(self, results: BulkProcessingResult) -> str:
        """
        Format bulk results as CSV for spreadsheet analysis
        
        Args:
            results: BulkProcessingResult object
            
        Returns:
            CSV string
        """
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        headers = [
            'Room Name', 'Room Type', 'Subroom', 'Height (ft)',
            'Wall Area (SF)', 'Ceiling Area (SF)', 'Floor Area (SF)',
            'Floor Perimeter (LF)', 'Flooring (SY)', 'Ceiling Perimeter (LF)',
            'Total Wall+Ceiling (SF)', 'Door Count', 'Window Count', 'Missing Wall Count',
            'Source File', 'Confidence', 'Processing Notes'
        ]
        writer.writerow(headers)
        
        # Data rows
        for room in results.room_measurements:
            row = [
                room.room_name,
                room.room_type.value if room.room_type else '',
                room.subroom,
                float(room.height.value) if room.height else '',
                float(room.walls.area.to_square_feet()) if room.walls and room.walls.area else '',
                float(room.ceiling.area.to_square_feet()) if room.ceiling and room.ceiling.area else '',
                float(room.floor.area.to_square_feet()) if room.floor and room.floor.area else '',
                float(room.floor.perimeter.value) if room.floor and room.floor.perimeter else '',
                float(room.floor.flooring_area.to_square_yards()) if room.floor and room.floor.flooring_area else '',
                float(room.ceiling.perimeter.value) if room.ceiling and room.ceiling.perimeter else '',
                float(room.get_total_wall_ceiling_area()) if room.get_total_wall_ceiling_area() else '',
                len(room.doors),
                len(room.windows),
                len(room.missing_walls),
                room.source_filename,
                room.extraction_confidence,
                '; '.join(room.processing_notes) if room.processing_notes else ''
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def save_room_measurement(self, 
                            room: RoomMeasurement, 
                            output_path: str, 
                            format_type: str = 'text') -> bool:
        """
        Save room measurement to file
        
        Args:
            room: RoomMeasurement object
            output_path: Output file path
            format_type: Format type ('text', 'json', 'yaml')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type.lower() == 'text':
                content = self.format_room_text(room, include_metadata=True)
            elif format_type.lower() == 'json':
                content = self.format_room_json(room, pretty=True)
            elif format_type.lower() == 'yaml':
                content = self.format_room_yaml(room)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved room measurement: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving room measurement: {e}")
            return False
    
    def save_bulk_results(self, 
                         results: BulkProcessingResult, 
                         output_dir: str,
                         formats: List[str] = None) -> Dict[str, bool]:
        """
        Save bulk results in multiple formats
        
        Args:
            results: BulkProcessingResult object
            output_dir: Output directory
            formats: List of formats to save ('text', 'json', 'csv', 'individual_json')
            
        Returns:
            Dictionary of format -> success status
        """
        if formats is None:
            formats = ['text', 'json', 'csv']
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_status = {}
        
        for format_type in formats:
            try:
                if format_type == 'text':
                    filename = f"measurement_results_{timestamp}.txt"
                    content = self.format_bulk_results_text(results)
                    
                elif format_type == 'json':
                    filename = f"measurement_results_{timestamp}.json"
                    content = json.dumps(self._bulk_results_to_dict(results), 
                                       indent=2, ensure_ascii=False, default=str)
                    
                elif format_type == 'csv':
                    filename = f"measurement_results_{timestamp}.csv"
                    content = self.format_bulk_results_csv(results)
                    
                elif format_type == 'individual_json':
                    # Save individual JSON files for each room
                    for i, room in enumerate(results.room_measurements):
                        room_filename = f"room_{i+1}_{self._sanitize_filename(room.get_display_name())}_{timestamp}.json"
                        room_path = output_path / room_filename
                        with open(room_path, 'w', encoding='utf-8') as f:
                            f.write(self.format_room_json(room))
                    results_status[format_type] = True
                    continue
                    
                else:
                    logger.warning(f"Unknown format: {format_type}")
                    results_status[format_type] = False
                    continue
                
                # Save the file
                file_path = output_path / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"Saved {format_type} results: {file_path}")
                results_status[format_type] = True
                
            except Exception as e:
                logger.error(f"Error saving {format_type} results: {e}")
                results_status[format_type] = False
        
        return results_status
    
    def _room_to_dict(self, room: RoomMeasurement) -> Dict[str, Any]:
        """Convert RoomMeasurement to dictionary"""
        data = {
            'room_name': room.room_name,
            'room_type': room.room_type.value if room.room_type else None,
            'subroom': room.subroom,
            'source_filename': room.source_filename,
            'extraction_confidence': float(room.extraction_confidence),
        }
        
        # Height
        if room.height:
            data['height'] = {
                'value': float(room.height.value),
                'unit': room.height.unit.value,
                'display': str(room.height)
            }
        
        # Measurements
        measurements = {}
        
        # Walls
        if room.walls:
            wall_data = {}
            if room.walls.area:
                wall_data['area'] = {
                    'value': float(room.walls.area.to_square_feet()),
                    'unit': 'SF'
                }
            
            total_area = room.get_total_wall_ceiling_area()
            if total_area:
                wall_data['total_with_ceiling'] = {
                    'value': float(total_area),
                    'unit': 'SF'
                }
            
            if wall_data:
                measurements['walls'] = wall_data
        
        # Ceiling
        if room.ceiling:
            ceiling_data = {}
            if room.ceiling.area:
                ceiling_data['area'] = {
                    'value': float(room.ceiling.area.to_square_feet()),
                    'unit': 'SF'
                }
            if room.ceiling.perimeter:
                ceiling_data['perimeter'] = {
                    'value': float(room.ceiling.perimeter.value),
                    'unit': room.ceiling.perimeter.unit.value
                }
            
            if ceiling_data:
                measurements['ceiling'] = ceiling_data
        
        # Floor
        if room.floor:
            floor_data = {}
            if room.floor.area:
                floor_data['area'] = {
                    'value': float(room.floor.area.to_square_feet()),
                    'unit': 'SF'
                }
            if room.floor.perimeter:
                floor_data['perimeter'] = {
                    'value': float(room.floor.perimeter.value),
                    'unit': room.floor.perimeter.unit.value
                }
            if room.floor.flooring_area:
                floor_data['flooring'] = {
                    'value': float(room.floor.flooring_area.to_square_yards()),
                    'unit': 'SY'
                }
            
            if floor_data:
                measurements['floor'] = floor_data
        
        if measurements:
            data['measurements'] = measurements
        
        # Openings
        if room.doors:
            data['doors'] = [
                {
                    'dimensions': str(door),
                    'width': {'value': float(door.width.value), 'unit': door.width.unit.value},
                    'height': {'value': float(door.height.value), 'unit': door.height.unit.value},
                    'opens_into': door.opens_into,
                    'confidence': door.confidence
                }
                for door in room.doors
            ]
        
        if room.windows:
            data['windows'] = [
                {
                    'dimensions': str(window),
                    'width': {'value': float(window.width.value), 'unit': window.width.unit.value},
                    'height': {'value': float(window.height.value), 'unit': window.height.unit.value},
                    'confidence': window.confidence
                }
                for window in room.windows
            ]
        
        if room.missing_walls:
            data['missing_walls'] = [
                {
                    'dimensions': str(wall),
                    'width': {'value': float(wall.width.value), 'unit': wall.width.unit.value},
                    'height': {'value': float(wall.height.value), 'unit': wall.height.unit.value},
                    'opens_into': wall.opens_into,
                    'confidence': wall.confidence
                }
                for wall in room.missing_walls
            ]
        
        # Processing notes
        if room.processing_notes:
            data['processing_notes'] = room.processing_notes
        
        return data
    
    def _bulk_results_to_dict(self, results: BulkProcessingResult) -> Dict[str, Any]:
        """Convert BulkProcessingResult to dictionary"""
        return {
            'summary': {
                'total_images': results.total_images,
                'successful_extractions': results.successful_extractions,
                'failed_extractions': results.failed_extractions,
                'success_rate': results.success_rate,
                'processing_time': results.processing_time,
                'generated_at': datetime.now().isoformat()
            },
            'room_measurements': [self._room_to_dict(room) for room in results.room_measurements],
            'processing_errors': results.processing_errors
        }
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for file system compatibility"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove extra spaces and limit length
        filename = ''.join(filename.split())[:50]
        
        return filename or 'unnamed'
    
    def create_measurement_report(self, 
                                results: BulkProcessingResult,
                                output_path: str,
                                include_charts: bool = False) -> bool:
        """
        Create a comprehensive measurement report
        
        Args:
            results: BulkProcessingResult object
            output_path: Output file path for the report
            include_charts: Whether to include charts (requires matplotlib)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            report_lines = []
            
            # Title and summary
            report_lines.append("CONSTRUCTION MEASUREMENT ANALYSIS REPORT")
            report_lines.append("=" * 50)
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # Executive summary
            report_lines.append("EXECUTIVE SUMMARY")
            report_lines.append("-" * 20)
            report_lines.append(f"Total Images Processed: {results.total_images}")
            report_lines.append(f"Successful Extractions: {results.successful_extractions}")
            report_lines.append(f"Success Rate: {results.success_rate:.1f}%")
            report_lines.append(f"Processing Time: {results.processing_time:.2f} seconds")
            report_lines.append("")
            
            # Room type statistics
            room_types = {}
            total_areas = {'walls': 0, 'ceiling': 0, 'floor': 0}
            
            for room in results.room_measurements:
                room_type = room.room_type.value if room.room_type else 'Unknown'
                room_types[room_type] = room_types.get(room_type, 0) + 1
                
                if room.walls and room.walls.area:
                    total_areas['walls'] += room.walls.area.to_square_feet()
                if room.ceiling and room.ceiling.area:
                    total_areas['ceiling'] += room.ceiling.area.to_square_feet()
                if room.floor and room.floor.area:
                    total_areas['floor'] += room.floor.area.to_square_feet()
            
            report_lines.append("ROOM TYPE DISTRIBUTION")
            report_lines.append("-" * 25)
            for room_type, count in sorted(room_types.items()):
                report_lines.append(f"{room_type}: {count} rooms")
            report_lines.append("")
            
            report_lines.append("TOTAL AREAS")
            report_lines.append("-" * 15)
            report_lines.append(f"Total Wall Area: {total_areas['walls']:.2f} SF")
            report_lines.append(f"Total Ceiling Area: {total_areas['ceiling']:.2f} SF")
            report_lines.append(f"Total Floor Area: {total_areas['floor']:.2f} SF")
            report_lines.append("")
            
            # Detailed room measurements
            report_lines.append("DETAILED ROOM MEASUREMENTS")
            report_lines.append("-" * 30)
            report_lines.append("")
            
            for i, room in enumerate(results.room_measurements, 1):
                report_lines.append(f"Room {i}: {room.get_display_name()}")
                report_lines.append(self.format_room_text(room, include_metadata=True))
                report_lines.append("")
            
            # Save report
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            logger.info(f"Created measurement report: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating measurement report: {e}")
            return False