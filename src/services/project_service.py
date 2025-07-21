"""
Project service for managing projects, YAML upload, and work scopes
"""

import yaml
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.database import Project, Floor, Room, WorkScope, get_db_session

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing construction estimation projects"""
    
    def __init__(self):
        """Initialize project service"""
        pass
    
    def create_project(self, name: str, description: str = "", default_finishes: Dict = None, default_trim: Dict = None) -> Project:
        """
        Create a new project
        
        Args:
            name: Project name
            description: Project description
            default_finishes: Default finishes for all rooms
            default_trim: Default trim options for all rooms
            
        Returns:
            Created Project instance
        """
        try:
            session = get_db_session()
            
            # Default finishes if not provided
            if default_finishes is None:
                default_finishes = {
                    'flooring': 'hardwood',
                    'wall_finish': 'painted_drywall',
                    'ceiling_finish': 'painted_drywall'
                }
            
            # Default trim if not provided
            if default_trim is None:
                default_trim = {
                    'baseboard': {'type': 'standard', 'material': 'painted_wood'},
                    'quarter_round': {'enabled': False, 'material': 'painted_wood'},
                    'crown_molding': 'none'
                }
            
            project = Project(
                name=name,
                description=description,
                default_finishes=default_finishes,
                default_trim=default_trim
            )
            
            session.add(project)
            session.commit()
            session.refresh(project)
            
            logger.info(f"Created project: {name} (ID: {project.id})")
            return project
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating project: {e}")
            raise
        finally:
            session.close()
    
    def upload_yaml_measurements(self, project_id: int, yaml_content: str) -> Tuple[bool, str, List[Dict]]:
        """
        Upload YAML measurement data to project
        
        Args:
            project_id: Project ID
            yaml_content: YAML content string
            
        Returns:
            Tuple of (success, message, rooms_created)
        """
        try:
            session = get_db_session()
            
            # Parse YAML
            try:
                yaml_data = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                return False, f"Invalid YAML format: {e}", []
            
            # Validate YAML structure
            if not isinstance(yaml_data, list):
                return False, "YAML must be a list of floors", []
            
            # Get project
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False, "Project not found", []
            
            rooms_created = []
            
            # Process each floor
            for floor_data in yaml_data:
                if 'floor' not in floor_data or 'rooms' not in floor_data:
                    continue
                
                # Create or get floor
                floor = session.query(Floor).filter(
                    and_(Floor.project_id == project_id, Floor.name == floor_data['floor'])
                ).first()
                
                if not floor:
                    floor = Floor(project_id=project_id, name=floor_data['floor'])
                    session.add(floor)
                    session.flush()  # Get floor ID
                
                # Process rooms
                for room_data in floor_data['rooms']:
                    room_name = room_data.get('room', 'Unknown')
                    
                    # Check if room already exists
                    existing_room = session.query(Room).filter(
                        and_(Room.floor_id == floor.id, Room.name == room_name)
                    ).first()
                    
                    if existing_room:
                        # Update existing room
                        existing_room.dimensions = room_data.get('dimensions')
                        existing_room.ceiling_height = room_data.get('ceiling_height')
                        existing_room.measurements = room_data.get('measurements', {})
                        room = existing_room
                    else:
                        # Create new room
                        room = Room(
                            floor_id=floor.id,
                            name=room_name,
                            dimensions=room_data.get('dimensions'),
                            ceiling_height=room_data.get('ceiling_height'),
                            measurements=room_data.get('measurements', {})
                        )
                        session.add(room)
                        session.flush()  # Get room ID
                        
                        # Create default work scope
                        work_scope = WorkScope(
                            room_id=room.id,
                            use_project_defaults=True,
                            paint_scope='both'
                        )
                        session.add(work_scope)
                    
                    rooms_created.append({
                        'floor': floor_data['floor'],
                        'room': room_name,
                        'dimensions': room_data.get('dimensions'),
                        'measurements': room_data.get('measurements', {})
                    })
            
            session.commit()
            
            message = f"Successfully uploaded {len(rooms_created)} rooms across {len(yaml_data)} floors"
            logger.info(message)
            
            return True, message, rooms_created
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error uploading YAML: {e}")
            return False, f"Error uploading YAML: {str(e)}", []
        finally:
            session.close()
    
    def get_project_with_rooms(self, project_id: int) -> Optional[Dict]:
        """
        Get project with all floors and rooms
        
        Args:
            project_id: Project ID
            
        Returns:
            Project data with floors and rooms
        """
        try:
            session = get_db_session()
            
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project:
                return None
            
            project_data = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'default_finishes': project.default_finishes or {},
                'default_trim': project.default_trim or {},
                'floors': []
            }
            
            for floor in project.floors:
                floor_data = {
                    'id': floor.id,
                    'name': floor.name,
                    'rooms': []
                }
                
                for room in floor.rooms:
                    room_data = {
                        'id': room.id,
                        'name': room.name,
                        'dimensions': room.dimensions,
                        'ceiling_height': room.ceiling_height,
                        'measurements': room.measurements or {},
                        'has_work_scope': room.work_scope is not None
                    }
                    floor_data['rooms'].append(room_data)
                
                project_data['floors'].append(floor_data)
            
            return project_data
            
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None
        finally:
            session.close()
    
    def get_all_projects(self) -> List[Dict]:
        """Get all projects with basic info"""
        try:
            session = get_db_session()
            
            projects = session.query(Project).all()
            
            project_list = []
            for project in projects:
                room_count = sum(len(floor.rooms) for floor in project.floors)
                
                project_list.append({
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'room_count': room_count,
                    'floor_count': len(project.floors),
                    'created_at': project.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            return project_list
            
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []
        finally:
            session.close()
    
    def update_project(self, project_id: int, name: str, description: str, 
                      default_finishes: Dict, default_trim: Dict) -> Tuple[bool, str]:
        """
        Update project details and defaults
        
        Args:
            project_id: Project ID
            name: Project name
            description: Project description
            default_finishes: Default finishes
            default_trim: Default trim settings
            
        Returns:
            Tuple of (success, message)
        """
        try:
            session = get_db_session()
            
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False, "Project not found"
            
            project.name = name.strip()
            project.description = description.strip()
            project.default_finishes = default_finishes
            project.default_trim = default_trim
            
            session.commit()
            
            logger.info(f"Updated project {project_id}")
            return True, f"Project '{name}' updated successfully"
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating project: {e}")
            return False, f"Error updating project: {str(e)}"
        finally:
            session.close()
    
    def update_room_name(self, room_id: int, new_name: str) -> Tuple[bool, str]:
        """
        Update room name
        
        Args:
            room_id: Room ID
            new_name: New room name
            
        Returns:
            Tuple of (success, message)
        """
        try:
            session = get_db_session()
            
            room = session.query(Room).filter(Room.id == room_id).first()
            if not room:
                return False, "Room not found"
            
            room.name = new_name.strip()
            session.commit()
            
            logger.info(f"Updated room {room_id} name to '{new_name}'")
            return True, f"Room name updated to '{new_name}'"
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating room name: {e}")
            return False, f"Error updating room name: {str(e)}"
        finally:
            session.close()
    
    def get_room_work_scope(self, room_id: int) -> Optional[Dict]:
        """
        Get work scope for a room
        
        Args:
            room_id: Room ID
            
        Returns:
            Work scope data
        """
        try:
            session = get_db_session()
            
            room = session.query(Room).filter(Room.id == room_id).first()
            if not room:
                return None
            
            work_scope = room.work_scope
            if not work_scope:
                # Create default work scope
                work_scope = WorkScope(
                    room_id=room_id,
                    use_project_defaults=True,
                    paint_scope='both'
                )
                session.add(work_scope)
                session.commit()
                session.refresh(work_scope)
            
            return {
                'room_id': room.id,
                'room_name': room.name,
                'floor_name': room.floor.name,
                'project_name': room.floor.project.name,
                'project_defaults': {
                    'finishes': room.floor.project.default_finishes or {},
                    'trim': room.floor.project.default_trim or {}
                },
                'work_scope': {
                    'use_project_defaults': work_scope.use_project_defaults,
                    'flooring_override': work_scope.flooring_override,
                    'wall_finish_override': work_scope.wall_finish_override,
                    'ceiling_finish_override': work_scope.ceiling_finish_override,
                    'trim_overrides': work_scope.trim_overrides or {},
                    'paint_scope': work_scope.paint_scope or 'both',
                    'demod_scope': work_scope.demod_scope or {},
                    'removal_scope': work_scope.removal_scope or {},
                    'remove_replace_items': work_scope.remove_replace_items or [],
                    'detach_reset_items': work_scope.detach_reset_items or [],
                    'protection_items': work_scope.protection_items or [],
                    'notes': work_scope.notes or ''
                },
                'measurements': room.measurements or {}
            }
            
        except Exception as e:
            logger.error(f"Error getting work scope: {e}")
            return None
        finally:
            session.close()
    
    def save_work_scope(self, room_id: int, work_scope_data: Dict) -> Tuple[bool, str]:
        """
        Save work scope for a room
        
        Args:
            room_id: Room ID
            work_scope_data: Work scope data
            
        Returns:
            Tuple of (success, message)
        """
        try:
            session = get_db_session()
            
            # Get or create work scope
            work_scope = session.query(WorkScope).filter(WorkScope.room_id == room_id).first()
            if not work_scope:
                work_scope = WorkScope(room_id=room_id)
                session.add(work_scope)
            
            # Update work scope
            work_scope.use_project_defaults = work_scope_data.get('use_project_defaults', True)
            work_scope.flooring_override = work_scope_data.get('flooring_override')
            work_scope.wall_finish_override = work_scope_data.get('wall_finish_override')
            work_scope.ceiling_finish_override = work_scope_data.get('ceiling_finish_override')
            work_scope.trim_overrides = work_scope_data.get('trim_overrides', {})
            work_scope.paint_scope = work_scope_data.get('paint_scope', 'both')
            work_scope.demod_scope = work_scope_data.get('demod_scope', {})
            work_scope.removal_scope = work_scope_data.get('removal_scope', {})
            work_scope.remove_replace_items = work_scope_data.get('remove_replace_items', [])
            work_scope.detach_reset_items = work_scope_data.get('detach_reset_items', [])
            work_scope.protection_items = work_scope_data.get('protection_items', [])
            work_scope.notes = work_scope_data.get('notes', '')
            
            session.commit()
            
            logger.info(f"Saved work scope for room {room_id}")
            return True, "Work scope saved successfully"
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving work scope: {e}")
            return False, f"Error saving work scope: {str(e)}"
        finally:
            session.close()
    
    def export_project_to_yaml(self, project_id: int) -> Optional[str]:
        """
        Export project work scopes to YAML format
        
        Args:
            project_id: Project ID
            
        Returns:
            YAML string or None if error
        """
        try:
            project_data = self.get_project_with_rooms(project_id)
            if not project_data:
                return None
            
            # Build export data structure
            export_data = {
                'project': {
                    'name': project_data['name'],
                    'description': project_data['description'],
                    'default_finishes': project_data['default_finishes'],
                    'default_trim': project_data['default_trim']
                },
                'floors': []
            }
            
            session = get_db_session()
            
            for floor_data in project_data['floors']:
                floor_export = {
                    'floor': floor_data['name'],
                    'rooms': []
                }
                
                for room_data in floor_data['rooms']:
                    room = session.query(Room).filter(Room.id == room_data['id']).first()
                    if not room:
                        continue
                    
                    room_export = {
                        'room': room.name,
                        'dimensions': room.dimensions,
                        'ceiling_height': room.ceiling_height,
                        'measurements': room.measurements or {}
                    }
                    
                    # Add work scope if available
                    if room.work_scope:
                        ws = room.work_scope
                        room_export['work_scope'] = {
                            'use_project_defaults': ws.use_project_defaults,
                            'overrides': {
                                'flooring': ws.flooring_override,
                                'wall_finish': ws.wall_finish_override,
                                'ceiling_finish': ws.ceiling_finish_override,
                                'trim': ws.trim_overrides or {}
                            },
                            'paint_scope': ws.paint_scope,
                            'demo_scope': {
                                'demod': ws.demod_scope or {},
                                'removal': ws.removal_scope or {}
                            },
                            'tasks': {
                                'remove_replace': ws.remove_replace_items or [],
                                'detach_reset': ws.detach_reset_items or [],
                                'protection': ws.protection_items or []
                            },
                            'notes': ws.notes
                        }
                    
                    floor_export['rooms'].append(room_export)
                
                export_data['floors'].append(floor_export)
            
            session.close()
            
            # Convert to YAML
            yaml_output = yaml.dump(export_data, default_flow_style=False, sort_keys=False, indent=2)
            return yaml_output
            
        except Exception as e:
            logger.error(f"Error exporting project to YAML: {e}")
            return None
    
    def merge_rooms(self, room_ids_to_merge: List[int], merged_room_name: str, target_floor_id: int, merged_measurements: Dict) -> Tuple[bool, str]:
        """
        Merge multiple rooms into one room by soft deleting originals and creating new merged room
        
        Args:
            room_ids_to_merge: List of room IDs to merge
            merged_room_name: Name for the new merged room
            target_floor_id: Floor ID where the merged room should be created
            merged_measurements: Combined measurements for the merged room
            
        Returns:
            Tuple of (success, message)
        """
        try:
            session = get_db_session()
            
            # Validate input
            if len(room_ids_to_merge) < 2:
                return False, "At least 2 rooms are required for merging"
            
            if not merged_room_name.strip():
                return False, "Merged room name is required"
            
            # Get rooms to merge
            rooms_to_merge = session.query(Room).filter(Room.id.in_(room_ids_to_merge)).all()
            if len(rooms_to_merge) != len(room_ids_to_merge):
                return False, "Some rooms not found"
            
            # Get target floor
            target_floor = session.query(Floor).filter(Floor.id == target_floor_id).first()
            if not target_floor:
                return False, "Target floor not found"
            
            # Calculate combined dimensions (take from first room and modify)
            base_room = rooms_to_merge[0]
            merged_dimensions = f"Merged from {len(rooms_to_merge)} rooms"
            merged_ceiling_height = base_room.ceiling_height or "8'"
            
            # Create new merged room
            merged_room = Room(
                floor_id=target_floor_id,
                name=merged_room_name.strip(),
                dimensions=merged_dimensions,
                ceiling_height=merged_ceiling_height,
                measurements=merged_measurements
            )
            session.add(merged_room)
            session.flush()  # Get room ID
            
            # Create default work scope for merged room
            merged_work_scope = WorkScope(
                room_id=merged_room.id,
                use_project_defaults=True,
                paint_scope='both'
            )
            session.add(merged_work_scope)
            
            # Soft delete original rooms (mark them by prefixing name with [MERGED] and updating timestamp)
            for room in rooms_to_merge:
                room.name = f"[MERGED] {room.name}"
                room.updated_at = datetime.utcnow()
                
                # Also mark work scope if it exists
                if room.work_scope:
                    room.work_scope.notes = f"[MERGED INTO: {merged_room_name}] " + (room.work_scope.notes or "")
                    room.work_scope.updated_at = datetime.utcnow()
            
            session.commit()
            
            logger.info(f"Successfully merged {len(room_ids_to_merge)} rooms into '{merged_room_name}' (Room ID: {merged_room.id})")
            return True, f"Successfully merged {len(room_ids_to_merge)} rooms into '{merged_room_name}'"
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error merging rooms: {e}")
            return False, f"Error merging rooms: {str(e)}"
        finally:
            session.close()
    
    def get_active_rooms(self, project_id: int) -> List[Dict]:
        """
        Get only active (non-merged) rooms for a project
        
        Args:
            project_id: Project ID
            
        Returns:
            List of active room data
        """
        try:
            session = get_db_session()
            
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project:
                return []
            
            active_rooms = []
            for floor in project.floors:
                for room in floor.rooms:
                    # Skip rooms that have been marked as merged
                    if not room.name.startswith("[MERGED]"):
                        active_rooms.append({
                            'id': room.id,
                            'floor_id': floor.id,
                            'floor_name': floor.name,
                            'name': room.name,
                            'dimensions': room.dimensions,
                            'ceiling_height': room.ceiling_height,
                            'measurements': room.measurements or {},
                            'has_work_scope': room.work_scope is not None
                        })
            
            return active_rooms
            
        except Exception as e:
            logger.error(f"Error getting active rooms: {e}")
            return []
        finally:
            session.close()


# Global service instance
_project_service = None


def get_project_service() -> ProjectService:
    """Get or create project service singleton"""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
    return _project_service