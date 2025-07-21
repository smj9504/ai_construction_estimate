#!/usr/bin/env python3
"""
Construction Estimation Project Management App V4
Enhanced with 'none' options, manual input for 'other', and dynamic task input boxes
"""

import gradio as gr
import sys
import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.services.project_service import get_project_service
from src.models.database import get_db_manager


class ConstructionEstimationAppV4:
    """Enhanced construction estimation app with improved input handling"""
    
    def __init__(self):
        """Initialize the application"""
        self.project_service = get_project_service()
        self.current_project_id = None
        self.current_room_id = None
        
        # Initialize database
        self.db_manager = get_db_manager()
        print("Database initialized successfully")
        
        # Define choice lists with 'none' and 'other' options
        self.finish_choices = {
            'flooring': ["none", "hardwood", "laminate", "carpet", "tile", "vinyl", "other"],
            'wall_finish': ["none", "painted_drywall", "textured_drywall", "tile", "wallpaper", "wood", "brick", "other"],
            'ceiling_finish': ["none", "painted_drywall", "textured_drywall", "tile", "wood", "drop_ceiling", "other"],
            'baseboard_type': ["none", "standard", "medium", "tall", "decorative", "other"],
            'baseboard_material': ["none", "painted_wood", "stained_wood", "mdf", "other"],
            'quarter_round_material': ["none", "painted_wood", "stained_wood", "mdf", "other"],
            'crown_molding': ["none", "standard", "decorative", "contemporary", "other"]
        }
    
    def get_project_list_formatted(self) -> List[List]:
        """Get formatted project list for dropdown"""
        try:
            projects = self.project_service.get_all_projects()
            if not projects:
                return [["No projects found - Create a new project", None]]
            
            formatted_list = []
            for p in projects:
                label = f"{p['name']} ({p['room_count']} rooms, {p['floor_count']} floors)"
                formatted_list.append([label, p['id']])
            
            return formatted_list
        except Exception as e:
            print(f"Error getting projects: {e}")
            return [["Error loading projects", None]]
    
    def load_project_details(self, project_choice: str) -> Dict:
        """Load selected project details into form fields"""
        if not project_choice or "No projects found" in project_choice or "Error" in project_choice:
            return self._empty_project_form()
        
        try:
            # Extract project ID from choice
            project_id = None
            for label, pid in self.get_project_list_formatted():
                if label == project_choice:
                    project_id = pid
                    break
            
            if not project_id:
                return self._empty_project_form()
            
            self.current_project_id = project_id
            
            # Get project details
            project_data = self.project_service.get_project_with_rooms(project_id)
            if not project_data:
                return self._empty_project_form()
            
            # Extract defaults
            finishes = project_data.get('default_finishes', {})
            trim = project_data.get('default_trim', {})
            baseboard = trim.get('baseboard', {})
            quarter_round = trim.get('quarter_round', {})
            
            # Get active rooms for proper counting
            active_rooms = self.project_service.get_active_rooms(self.current_project_id)
            active_rooms_by_floor = {}
            for room in active_rooms:
                floor_name = room['floor_name']
                if floor_name not in active_rooms_by_floor:
                    active_rooms_by_floor[floor_name] = []
                active_rooms_by_floor[floor_name].append(room)
            
            # Generate project summary
            summary_lines = [
                f"📂 Project: {project_data['name']}",
                f"🏢 Floors: {len(project_data['floors'])}",
                f"🏠 Active Rooms: {len(active_rooms)}",
                "",
                "📋 CURRENT DEFAULTS:",
                f"• Flooring: {finishes.get('flooring', 'Not set')}",
                f"• Wall Finish: {finishes.get('wall_finish', 'Not set')}",
                f"• Ceiling Finish: {finishes.get('ceiling_finish', 'Not set')}",
                f"• Baseboard: {baseboard.get('type', 'Not set')} ({baseboard.get('material', 'Not set')})",
                f"• Quarter Round: {'Yes' if quarter_round.get('enabled') else 'No'}",
                f"• Crown Molding: {trim.get('crown_molding', 'Not set')}",
                ""
            ]
            
            # List floors and active rooms only
            for floor in project_data['floors']:
                floor_rooms = active_rooms_by_floor.get(floor['name'], [])
                if floor_rooms:  # Only show floors that have active rooms
                    summary_lines.append(f"📍 {floor['name'].upper()}:")
                    for room in floor_rooms:
                        status = "✅" if room['has_work_scope'] else "⏳"
                        summary_lines.append(f"   {status} {room['name']} ({room.get('dimensions', 'No dimensions')})")
            
            return {
                'name': project_data['name'],
                'description': project_data.get('description', ''),
                'flooring': finishes.get('flooring', 'hardwood'),
                'flooring_other': finishes.get('flooring_other', ''),
                'wall_finish': finishes.get('wall_finish', 'painted_drywall'),
                'wall_finish_other': finishes.get('wall_finish_other', ''),
                'ceiling_finish': finishes.get('ceiling_finish', 'painted_drywall'),
                'ceiling_finish_other': finishes.get('ceiling_finish_other', ''),
                'baseboard_type': baseboard.get('type', 'standard'),
                'baseboard_type_other': baseboard.get('type_other', ''),
                'baseboard_material': baseboard.get('material', 'painted_wood'),
                'baseboard_material_other': baseboard.get('material_other', ''),
                'quarter_round': quarter_round.get('enabled', False),
                'quarter_round_material': quarter_round.get('material', 'painted_wood'),
                'quarter_round_material_other': quarter_round.get('material_other', ''),
                'crown_molding': trim.get('crown_molding', 'none'),
                'crown_molding_other': trim.get('crown_molding_other', ''),
                'summary': "\n".join(summary_lines),
                'form_visible': True
            }
            
        except Exception as e:
            print(f"Error loading project: {e}")
            return self._empty_project_form()
    
    def _empty_project_form(self) -> Dict:
        """Return empty project form values"""
        return {
            'name': '',
            'description': '',
            'flooring': 'hardwood',
            'flooring_other': '',
            'wall_finish': 'painted_drywall',
            'wall_finish_other': '',
            'ceiling_finish': 'painted_drywall',
            'ceiling_finish_other': '',
            'baseboard_type': 'standard',
            'baseboard_type_other': '',
            'baseboard_material': 'painted_wood',
            'baseboard_material_other': '',
            'quarter_round': False,
            'quarter_round_material': 'painted_wood',
            'quarter_round_material_other': '',
            'crown_molding': 'none',
            'crown_molding_other': '',
            'summary': 'No project selected',
            'form_visible': False
        }
    
    def save_project_changes(self, name: str, description: str,
                           flooring: str, flooring_other: str,
                           wall_finish: str, wall_finish_other: str,
                           ceiling_finish: str, ceiling_finish_other: str,
                           baseboard_type: str, baseboard_type_other: str,
                           baseboard_material: str, baseboard_material_other: str,
                           quarter_round: bool, quarter_round_material: str, quarter_round_material_other: str,
                           crown_molding: str, crown_molding_other: str) -> Tuple[str, gr.Dropdown]:
        """Save changes to existing project"""
        if not self.current_project_id:
            return "No project selected", gr.Dropdown(choices=[c[0] for c in self.get_project_list_formatted()])
        
        try:
            # Prepare defaults with 'other' values
            default_finishes = {
                'flooring': flooring_other if flooring == 'other' else flooring,
                'flooring_other': flooring_other,
                'wall_finish': wall_finish_other if wall_finish == 'other' else wall_finish,
                'wall_finish_other': wall_finish_other,
                'ceiling_finish': ceiling_finish_other if ceiling_finish == 'other' else ceiling_finish,
                'ceiling_finish_other': ceiling_finish_other
            }
            
            default_trim = {
                'baseboard': {
                    'type': baseboard_type_other if baseboard_type == 'other' else baseboard_type,
                    'type_other': baseboard_type_other,
                    'material': baseboard_material_other if baseboard_material == 'other' else baseboard_material,
                    'material_other': baseboard_material_other
                },
                'quarter_round': {
                    'enabled': quarter_round,
                    'material': quarter_round_material_other if quarter_round_material == 'other' else quarter_round_material,
                    'material_other': quarter_round_material_other
                },
                'crown_molding': crown_molding_other if crown_molding == 'other' else crown_molding,
                'crown_molding_other': crown_molding_other
            }
            
            # Update project
            success, message = self.project_service.update_project(
                self.current_project_id,
                name,
                description,
                default_finishes,
                default_trim
            )
            
            # Refresh project list
            updated_choices = [c[0] for c in self.get_project_list_formatted()]
            
            if success:
                return f"✅ {message}", gr.Dropdown(choices=updated_choices)
            else:
                return f"❌ {message}", gr.Dropdown(choices=updated_choices)
                
        except Exception as e:
            return f"Error: {str(e)}", gr.Dropdown(choices=[c[0] for c in self.get_project_list_formatted()])
    
    def create_new_project_form(self, name: str, description: str,
                              flooring: str, flooring_other: str,
                              wall_finish: str, wall_finish_other: str,
                              ceiling_finish: str, ceiling_finish_other: str,
                              baseboard_type: str, baseboard_type_other: str,
                              baseboard_material: str, baseboard_material_other: str,
                              quarter_round: bool, quarter_round_material: str, quarter_round_material_other: str,
                              crown_molding: str, crown_molding_other: str,
                              yaml_content: str) -> Tuple[str, gr.Dropdown, Dict]:
        """Create new project with defaults and optional YAML"""
        if not name.strip():
            return "Error: Project name is required", gr.Dropdown(choices=[c[0] for c in self.get_project_list_formatted()]), {}
        
        try:
            # Prepare defaults with 'other' values
            default_finishes = {
                'flooring': flooring_other if flooring == 'other' else flooring,
                'flooring_other': flooring_other,
                'wall_finish': wall_finish_other if wall_finish == 'other' else wall_finish,
                'wall_finish_other': wall_finish_other,
                'ceiling_finish': ceiling_finish_other if ceiling_finish == 'other' else ceiling_finish,
                'ceiling_finish_other': ceiling_finish_other
            }
            
            default_trim = {
                'baseboard': {
                    'type': baseboard_type_other if baseboard_type == 'other' else baseboard_type,
                    'type_other': baseboard_type_other,
                    'material': baseboard_material_other if baseboard_material == 'other' else baseboard_material,
                    'material_other': baseboard_material_other
                },
                'quarter_round': {
                    'enabled': quarter_round,
                    'material': quarter_round_material_other if quarter_round_material == 'other' else quarter_round_material,
                    'material_other': quarter_round_material_other
                },
                'crown_molding': crown_molding_other if crown_molding == 'other' else crown_molding,
                'crown_molding_other': crown_molding_other
            }
            
            # Create project
            project = self.project_service.create_project(
                name.strip(), 
                description.strip(),
                default_finishes,
                default_trim
            )
            self.current_project_id = project.id
            
            status_msg = f"✅ Project '{name}' created successfully"
            
            # If YAML content provided, upload it
            if yaml_content.strip():
                success, message, rooms = self.project_service.upload_yaml_measurements(
                    self.current_project_id, yaml_content
                )
                
                if success:
                    status_msg += f"\n✅ {message}"
                else:
                    status_msg += f"\n❌ YAML Error: {message}"
            
            # Refresh project list and select new project
            updated_choices = self.get_project_list_formatted()
            new_project_choice = None
            for label, pid in updated_choices:
                if pid == project.id:
                    new_project_choice = label
                    break
            
            # Load the new project details
            project_details = self.load_project_details(new_project_choice)
            
            return status_msg, gr.Dropdown(choices=[c[0] for c in updated_choices], value=new_project_choice), project_details
            
        except Exception as e:
            return f"Error creating project: {str(e)}", gr.Dropdown(choices=[c[0] for c in self.get_project_list_formatted()]), {}
    
    def upload_yaml_to_current_project(self, yaml_content: str) -> str:
        """Upload YAML measurements to current project"""
        if not self.current_project_id:
            return "Error: No project selected"
        
        if not yaml_content.strip():
            return "Error: No YAML content provided"
        
        try:
            success, message, rooms = self.project_service.upload_yaml_measurements(
                self.current_project_id, yaml_content
            )
            
            if success:
                summary_lines = [f"✅ {message}"]
                for room in rooms:
                    summary_lines.append(f"📍 {room['floor']} - {room['room']}")
                return "\n".join(summary_lines)
            else:
                return f"❌ Error: {message}"
                
        except Exception as e:
            return f"Error uploading YAML: {str(e)}"
    
    def get_room_choices(self) -> List[str]:
        """Get active room choices for current project (excluding merged rooms)"""
        if not self.current_project_id:
            return []
        
        try:
            active_rooms = self.project_service.get_active_rooms(self.current_project_id)
            room_choices = []
            for room in active_rooms:
                room_choices.append(f"{room['floor_name']} - {room['name']} (ID: {room['id']})")
            
            return room_choices
            
        except Exception as e:
            print(f"Error getting room choices: {e}")
            return []
    
    def update_room_name(self, new_name: str) -> Tuple[str, gr.Dropdown]:
        """Update current room name and refresh dropdown"""
        if not self.current_room_id or not new_name.strip():
            return "No room selected or empty name", gr.Dropdown(choices=self.get_room_choices())
        
        try:
            success, message = self.project_service.update_room_name(self.current_room_id, new_name)
            
            # Refresh room choices
            updated_choices = self.get_room_choices()
            
            if success:
                return f"✅ {message}", gr.Dropdown(choices=updated_choices)
            else:
                return f"❌ {message}", gr.Dropdown(choices=updated_choices)
                
        except Exception as e:
            return f"Error: {str(e)}", gr.Dropdown(choices=self.get_room_choices())
    
    def select_room_for_work_scope(self, room_choice: str) -> Dict:
        """Select room and load work scope form"""
        if not room_choice:
            return self._empty_work_scope_form()
        
        try:
            # Parse room ID from choice
            if "(ID: " not in room_choice:
                return self._empty_work_scope_form()
            
            room_id_str = room_choice.split("(ID: ")[-1].rstrip(")")
            room_id = int(room_id_str)
            
            self.current_room_id = room_id
            
            # Get work scope data
            work_scope_data = self.project_service.get_room_work_scope(room_id)
            if not work_scope_data:
                return self._empty_work_scope_form()
            
            # Convert to form values
            ws = work_scope_data['work_scope']
            defaults = work_scope_data['project_defaults']
            
            # Extract demo'd scope
            demod = ws.get('demod_scope', {})
            
            # Extract removal scope
            removal = ws.get('removal_scope', {})
            
            # Extract task lists and prepare for display
            remove_replace = ws.get('remove_replace_items', [])
            detach_reset = ws.get('detach_reset_items', [])
            protection = ws.get('protection_items', [])
            
            return {
                'room_name': work_scope_data['room_name'],
                'use_defaults': ws['use_project_defaults'],
                'flooring_override': ws.get('flooring_override', ''),
                'wall_finish_override': ws.get('wall_finish_override', ''),
                'ceiling_finish_override': ws.get('ceiling_finish_override', ''),
                'paint_scope': ws.get('paint_scope', 'both'),
                # Demo'd scope
                'demod_floor': demod.get('floor', 'n/a'),
                'demod_floor_sf': demod.get('floor_sf', ''),
                'demod_walls': demod.get('walls', 'n/a'),
                'demod_walls_sf': demod.get('walls_sf', ''),
                'demod_ceiling': demod.get('ceiling', 'n/a'),
                'demod_ceiling_sf': demod.get('ceiling_sf', ''),
                'demod_wall_insulation': demod.get('wall_insulation', 'n/a'),
                'demod_wall_insulation_sf': demod.get('wall_insulation_sf', ''),
                'demod_ceiling_insulation': demod.get('ceiling_insulation', 'n/a'),
                'demod_ceiling_insulation_sf': demod.get('ceiling_insulation_sf', ''),
                'demod_baseboard': demod.get('baseboard', 'n/a'),
                'demod_baseboard_lf': demod.get('baseboard_lf', ''),
                # Removal scope
                'removal_floor': removal.get('floor', 'n/a'),
                'removal_walls': removal.get('walls', 'n/a'),
                'removal_ceiling': removal.get('ceiling', 'n/a'),
                'removal_wall_insulation': removal.get('wall_insulation', 'n/a'),
                'removal_ceiling_insulation': removal.get('ceiling_insulation', 'n/a'),
                'removal_baseboard': removal.get('baseboard', 'n/a'),
                # Task lists
                'remove_replace_items': remove_replace,
                'detach_reset_items': detach_reset,
                'protection_items': protection,
                'notes': ws.get('notes', ''),
                'project_defaults_text': self._format_project_defaults(defaults)
            }
            
        except Exception as e:
            print(f"Error selecting room: {e}")
            return self._empty_work_scope_form()
    
    def _empty_work_scope_form(self) -> Dict:
        """Return empty work scope form"""
        return {
            'room_name': '',
            'use_defaults': True,
            'flooring_override': '',
            'wall_finish_override': '',
            'ceiling_finish_override': '',
            'paint_scope': 'both',
            # Demo'd scope
            'demod_floor': 'n/a',
            'demod_floor_sf': '',
            'demod_walls': 'n/a',
            'demod_walls_sf': '',
            'demod_ceiling': 'n/a',
            'demod_ceiling_sf': '',
            'demod_wall_insulation': 'n/a',
            'demod_wall_insulation_sf': '',
            'demod_ceiling_insulation': 'n/a',
            'demod_ceiling_insulation_sf': '',
            'demod_baseboard': 'n/a',
            'demod_baseboard_lf': '',
            # Removal scope
            'removal_floor': 'n/a',
            'removal_walls': 'n/a',
            'removal_ceiling': 'n/a',
            'removal_wall_insulation': 'n/a',
            'removal_ceiling_insulation': 'n/a',
            'removal_baseboard': 'n/a',
            # Task lists
            'remove_replace_items': [],
            'detach_reset_items': [],
            'protection_items': [],
            'notes': '',
            'project_defaults_text': ''
        }
    
    def _format_project_defaults(self, defaults: Dict) -> str:
        """Format project defaults for display"""
        lines = ["📋 PROJECT DEFAULTS:"]
        
        finishes = defaults.get('finishes', {})
        if finishes:
            lines.append("🎨 Finishes:")
            lines.append(f"   • Flooring: {finishes.get('flooring', 'Not set')}")
            lines.append(f"   • Wall: {finishes.get('wall_finish', 'Not set')}")
            lines.append(f"   • Ceiling: {finishes.get('ceiling_finish', 'Not set')}")
        
        trim = defaults.get('trim', {})
        if trim:
            lines.append("🔧 Trim:")
            baseboard = trim.get('baseboard', {})
            if baseboard:
                lines.append(f"   • Baseboard: {baseboard.get('type', 'Not set')} ({baseboard.get('material', 'Not set')})")
            
            quarter_round = trim.get('quarter_round', {})
            if quarter_round.get('enabled'):
                lines.append(f"   • Quarter Round: Yes ({quarter_round.get('material', 'Not set')})")
            
            lines.append(f"   • Crown Molding: {trim.get('crown_molding', 'Not set')}")
        
        return "\n".join(lines)
    
    def save_comprehensive_work_scope(self, use_defaults, flooring, wall_finish, ceiling_finish, paint_scope,
                                    demod_floor, demod_floor_sf, demod_walls, demod_walls_sf,
                                    demod_ceiling, demod_ceiling_sf, demod_wall_insulation, demod_wall_insulation_sf,
                                    demod_ceiling_insulation, demod_ceiling_insulation_sf, demod_baseboard, demod_baseboard_lf,
                                    removal_floor, removal_walls, removal_ceiling,
                                    removal_wall_insulation, removal_ceiling_insulation, removal_baseboard,
                                    remove_replace_data, detach_reset_data, protection_data, notes) -> str:
        """Save comprehensive work scope"""
        if not self.current_room_id:
            return "Error: No room selected"
        
        try:
            # Build demo'd scope
            demod_scope = {
                'floor': demod_floor,
                'floor_sf': demod_floor_sf if demod_floor == 'partial' else '',
                'walls': demod_walls,
                'walls_sf': demod_walls_sf if demod_walls == 'partial' else '',
                'ceiling': demod_ceiling,
                'ceiling_sf': demod_ceiling_sf if demod_ceiling == 'partial' else '',
                'wall_insulation': demod_wall_insulation,
                'wall_insulation_sf': demod_wall_insulation_sf if demod_wall_insulation == 'partial' else '',
                'ceiling_insulation': demod_ceiling_insulation,
                'ceiling_insulation_sf': demod_ceiling_insulation_sf if demod_ceiling_insulation == 'partial' else '',
                'baseboard': demod_baseboard,
                'baseboard_lf': demod_baseboard_lf if demod_baseboard == 'partial' else ''
            }
            
            # Build removal scope
            removal_scope = {
                'floor': removal_floor,
                'walls': removal_walls,
                'ceiling': removal_ceiling,
                'wall_insulation': removal_wall_insulation,
                'ceiling_insulation': removal_ceiling_insulation,
                'baseboard': removal_baseboard
            }
            
            # Build work scope data
            work_scope_data = {
                'use_project_defaults': use_defaults,
                'flooring_override': flooring.strip() if not use_defaults else None,
                'wall_finish_override': wall_finish.strip() if not use_defaults else None,
                'ceiling_finish_override': ceiling_finish.strip() if not use_defaults else None,
                'paint_scope': paint_scope,
                'demod_scope': demod_scope,
                'removal_scope': removal_scope,
                'remove_replace_items': remove_replace_data,
                'detach_reset_items': detach_reset_data,
                'protection_items': protection_data,
                'notes': notes.strip()
            }
            
            success, message = self.project_service.save_work_scope(self.current_room_id, work_scope_data)
            
            if success:
                return f"✅ {message}"
            else:
                return f"❌ {message}"
                
        except Exception as e:
            return f"Error saving work scope: {str(e)}"
    
    def export_project_yaml(self) -> Tuple[str, Optional[str]]:
        """Export current project to YAML"""
        if not self.current_project_id:
            return "Error: No project selected", None
        
        try:
            yaml_content = self.project_service.export_project_to_yaml(self.current_project_id)
            if yaml_content:
                return "Project exported successfully", yaml_content
            else:
                return "Error exporting project", None
                
        except Exception as e:
            return f"Error exporting project: {str(e)}", None
    
    def get_mergeable_rooms(self) -> List[str]:
        """Get list of active (non-merged) rooms that can be merged"""
        if not self.current_project_id:
            return []
        
        try:
            active_rooms = self.project_service.get_active_rooms(self.current_project_id)
            room_choices = []
            for room in active_rooms:
                room_choices.append(f"{room['floor_name']} - {room['name']} (ID: {room['id']})")
            
            return room_choices
            
        except Exception as e:
            print(f"Error getting mergeable rooms: {e}")
            return []
    
    def preview_room_merge(self, selected_rooms: List[str]) -> str:
        """Preview what the merged room will look like"""
        if not selected_rooms or len(selected_rooms) < 2:
            return "Please select at least 2 rooms to merge"
        
        if not self.current_project_id:
            return "Error: No project selected"
        
        try:
            # Get room IDs from selected rooms
            room_ids = []
            for room_choice in selected_rooms:
                if "(ID: " in room_choice:
                    room_id_str = room_choice.split("(ID: ")[-1].rstrip(")")
                    room_ids.append(int(room_id_str))
            
            # Get room data
            project_data = self.project_service.get_project_with_rooms(self.current_project_id)
            if not project_data:
                return "Error: Could not load project data"
            
            # Find selected rooms
            selected_room_data = []
            for floor in project_data['floors']:
                for room in floor['rooms']:
                    if room['id'] in room_ids:
                        selected_room_data.append({
                            'floor': floor['name'],
                            'room': room,
                            'measurements': room.get('measurements', {})
                        })
            
            if len(selected_room_data) < 2:
                return "Error: Could not find selected rooms"
            
            # Calculate merged measurements
            merged_measurements = self._calculate_merged_measurements(selected_room_data)
            
            # Generate preview
            preview_lines = ["📋 MERGE PREVIEW:", ""]
            preview_lines.append(f"🔗 Merging {len(selected_room_data)} rooms:")
            for room_data in selected_room_data:
                preview_lines.append(f"   • {room_data['floor']} - {room_data['room']['name']}")
            
            preview_lines.extend(["", "📊 COMBINED MEASUREMENTS:"])
            preview_lines.append(f"   • Total Ground Surface: {merged_measurements.get('ground_surface_without_walls', 0):.2f} sq ft")
            preview_lines.append(f"   • Total Wall Surface: {merged_measurements.get('walls_with_opening', 0):.2f} sq ft")
            preview_lines.append(f"   • Total Volume: {merged_measurements.get('volume', 0):.2f} ft³")
            preview_lines.append(f"   • Total Perimeter: {merged_measurements.get('ground_perimeter', 0):.2f} LF")
            preview_lines.append(f"   • Total Window Surface: {merged_measurements.get('surface_of_windows', 0):.2f} sq ft")
            preview_lines.append(f"   • Total Door Surface: {merged_measurements.get('surface_of_doors', 0):.2f} sq ft")
            
            return "\n".join(preview_lines)
            
        except Exception as e:
            return f"Error generating preview: {str(e)}"
    
    def _calculate_merged_measurements(self, room_data_list: List[Dict]) -> Dict:
        """Calculate combined measurements for merged rooms"""
        merged = {
            'volume': 0,
            'ground_surface_without_walls': 0,
            'walls_with_opening': 0,
            'walls_without_opening': 0,
            'ground_perimeter': 0,
            'ceiling_perimeter': 0,
            'surface_of_windows': 0,
            'surface_of_doors': 0
        }
        
        for room_data in room_data_list:
            measurements = room_data['measurements']
            for key in merged.keys():
                value = measurements.get(key, 0)
                merged[key] += self._parse_measurement_value(value)
        
        return merged
    
    def _parse_measurement_value(self, value) -> float:
        """Parse measurement value and extract numeric part"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove common units and extract numeric value
            value = value.strip()
            
            # Handle empty or 'n/a' values
            if not value or value.lower() in ['n/a', 'na', '']:
                return 0.0
            
            # Remove units: ft³, sq ft, LF, etc.
            import re
            # Extract first number found in the string (including decimals)
            match = re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', value.replace(',', ''))
            if match:
                return float(match.group().replace(',', ''))
            else:
                return 0.0
        
        return 0.0
    
    def merge_selected_rooms(self, selected_rooms: List[str], new_room_name: str) -> str:
        """Merge selected rooms into one room"""
        if not selected_rooms or len(selected_rooms) < 2:
            return "Error: Please select at least 2 rooms to merge"
        
        if not new_room_name.strip():
            return "Error: Please enter a name for the merged room"
        
        if not self.current_project_id:
            return "Error: No project selected"
        
        try:
            # Get room IDs from selected rooms
            room_ids = []
            for room_choice in selected_rooms:
                if "(ID: " in room_choice:
                    room_id_str = room_choice.split("(ID: ")[-1].rstrip(")")
                    room_ids.append(int(room_id_str))
            
            # Get room data
            project_data = self.project_service.get_project_with_rooms(self.current_project_id)
            if not project_data:
                return "Error: Could not load project data"
            
            # Find selected rooms
            selected_room_data = []
            floors_to_update = {}
            
            for floor in project_data['floors']:
                for room in floor['rooms']:
                    if room['id'] in room_ids:
                        selected_room_data.append({
                            'floor': floor['name'],
                            'floor_id': floor['id'],
                            'room': room,
                            'measurements': room.get('measurements', {})
                        })
                        
                        if floor['id'] not in floors_to_update:
                            floors_to_update[floor['id']] = floor['name']
            
            if len(selected_room_data) < 2:
                return "Error: Could not find selected rooms"
            
            # Calculate merged measurements
            merged_measurements = self._calculate_merged_measurements(selected_room_data)
            
            # Create merged room data
            # Use the first room as base and update with merged data
            base_room = selected_room_data[0]['room']
            merged_room_data = {
                'name': new_room_name.strip(),
                'dimensions': f"Merged from {len(selected_room_data)} rooms",
                'ceiling_height': base_room.get('ceiling_height', '8\''),
                'measurements': merged_measurements
            }
            
            # Use project service to merge rooms
            # Note: This would need to be implemented in the project service
            success, message = self._perform_room_merge(
                room_ids, 
                merged_room_data, 
                selected_room_data[0]['floor_id']  # Put merged room in first floor
            )
            
            if success:
                return f"✅ Successfully merged {len(selected_room_data)} rooms into '{new_room_name}'"
            else:
                return f"❌ Error merging rooms: {message}"
                
        except Exception as e:
            return f"Error merging rooms: {str(e)}"
    
    def _perform_room_merge(self, room_ids_to_delete: List[int], merged_room_data: Dict, target_floor_id: int) -> Tuple[bool, str]:
        """Perform the actual room merge operation using proper database operations"""
        try:
            # Use the project service's new merge_rooms method
            success, message = self.project_service.merge_rooms(
                room_ids_to_merge=room_ids_to_delete,
                merged_room_name=merged_room_data['name'],
                target_floor_id=target_floor_id,
                merged_measurements=merged_room_data['measurements']
            )
            
            return success, message
            
        except Exception as e:
            return False, str(e)
    
    def create_dynamic_task_section(self, task_type: str, initial_items: List = None):
        """Create dynamic task input section"""
        if initial_items is None:
            initial_items = []
        
        items_state = gr.State(initial_items)
        
        with gr.Group() as task_group:
            gr.Markdown(f"##### {task_type}")
            
            # Container for items
            items_container = gr.Column()
            
            # Add button
            add_button = gr.Button(f"+ Add {task_type} Item", size="sm")
            
            def update_items_display(items):
                """Update the display of items"""
                if not items:
                    return gr.Column(visible=True)
                
                components = []
                for i, item in enumerate(items):
                    with gr.Row():
                        item_field = gr.Textbox(
                            label=f"Item {i+1}",
                            value=item.get('item', ''),
                            placeholder="e.g., Door, Cabinet, Flooring"
                        )
                        quantity_field = gr.Number(
                            label="Quantity",
                            value=item.get('quantity', 1),
                            minimum=0
                        )
                        unit_field = gr.Dropdown(
                            label="Unit",
                            choices=["ea", "sf", "lf", "sy", "ton", "lb", "gal"],
                            value=item.get('unit', 'ea')
                        )
                        remove_btn = gr.Button("🗑️", size="sm", variant="secondary")
                    components.append((item_field, quantity_field, unit_field, remove_btn))
                
                return gr.Column(components, visible=True)
            
            def add_item(items):
                new_item = {'item': '', 'quantity': 1, 'unit': 'ea'}
                updated_items = items + [new_item]
                return updated_items, update_items_display(updated_items)
            
            def remove_item(items, index):
                updated_items = items[:index] + items[index+1:]
                return updated_items, update_items_display(updated_items)
            
            add_button.click(
                fn=add_item,
                inputs=[items_state],
                outputs=[items_state, items_container]
            )
        
        return task_group, items_state
    
    def create_interface(self) -> gr.Blocks:
        """Create the enhanced Gradio interface"""
        
        with gr.Blocks(title="Construction Estimation Manager V4", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🏗️ Construction Estimation Manager")
            gr.Markdown("Enhanced project management with improved input handling")
            
            # Store current project state
            project_state = gr.State()
            
            with gr.Tabs() as main_tabs:
                # Project Management Tab
                with gr.TabItem("📂 Project Management", id="project_tab"):
                    
                    # Main Project Selection/Creation Tabs
                    with gr.Tabs() as project_workflow_tabs:
                        
                        # Existing Projects Tab
                        with gr.TabItem("📋 Select Existing Project", id="existing_tab"):
                            gr.Markdown("### Choose from your existing projects")
                            
                            with gr.Row():
                                project_dropdown = gr.Dropdown(
                                    label="Select Project",
                                    choices=[c[0] for c in self.get_project_list_formatted()],
                                    interactive=True,
                                    scale=3
                                )
                                refresh_projects_btn = gr.Button("🔄 Refresh", scale=1)
                            
                            # Current Project Info (toggleable)
                            with gr.Accordion("📋 Current Project Overview", open=True):
                                current_project_info = gr.Textbox(
                                    label="Project Summary",
                                    lines=8,
                                    interactive=False,
                                    value="No project selected",
                                    visible=True
                                )
                            
                            gr.Markdown("*Select a project above to edit its settings and manage rooms*")
                        
                        # Create New Project Tab
                        with gr.TabItem("➕ Create New Project", id="new_tab"):
                            gr.Markdown("### Start a new construction project")
                            
                            with gr.Row():
                                new_project_name = gr.Textbox(
                                    label="Project Name*", 
                                    placeholder="Enter project name...",
                                    scale=2
                                )
                                new_project_desc = gr.Textbox(
                                    label="Description", 
                                    placeholder="Project description...", 
                                    lines=2,
                                    scale=3
                                )
                            
                            gr.Markdown("#### Set Default Finishes for All Rooms")
                            with gr.Row():
                                new_flooring = gr.Dropdown(
                                    label="Default Flooring", 
                                    choices=self.finish_choices['flooring'], 
                                    value="hardwood"
                                )
                                new_flooring_other = gr.Textbox(
                                    label="Flooring (Other)", 
                                    placeholder="Specify flooring type...", 
                                    visible=False
                                )
                                new_wall_finish = gr.Dropdown(
                                    label="Default Wall Finish", 
                                    choices=self.finish_choices['wall_finish'], 
                                    value="painted_drywall"
                                )
                                new_wall_finish_other = gr.Textbox(
                                    label="Wall Finish (Other)", 
                                    placeholder="Specify wall finish...", 
                                    visible=False
                                )
                            
                            with gr.Row():
                                new_ceiling_finish = gr.Dropdown(
                                    label="Default Ceiling Finish", 
                                    choices=self.finish_choices['ceiling_finish'], 
                                    value="painted_drywall"
                                )
                                new_ceiling_finish_other = gr.Textbox(
                                    label="Ceiling Finish (Other)", 
                                    placeholder="Specify ceiling finish...", 
                                    visible=False
                                )
                            
                            gr.Markdown("#### Trim & Molding Defaults")
                            with gr.Row():
                                new_baseboard_type = gr.Dropdown(
                                    label="Baseboard Type", 
                                    choices=self.finish_choices['baseboard_type'], 
                                    value="standard"
                                )
                                new_baseboard_type_other = gr.Textbox(
                                    label="Baseboard Type (Other)", 
                                    placeholder="Specify baseboard type...", 
                                    visible=False
                                )
                                new_baseboard_material = gr.Dropdown(
                                    label="Baseboard Material", 
                                    choices=self.finish_choices['baseboard_material'], 
                                    value="painted_wood"
                                )
                                new_baseboard_material_other = gr.Textbox(
                                    label="Baseboard Material (Other)", 
                                    placeholder="Specify material...", 
                                    visible=False
                                )
                            
                            with gr.Row():
                                new_quarter_round = gr.Checkbox(
                                    label="Include Quarter Round", 
                                    value=False
                                )
                                new_quarter_round_material = gr.Dropdown(
                                    label="Quarter Round Material", 
                                    choices=self.finish_choices['quarter_round_material'], 
                                    value="painted_wood", 
                                    visible=False
                                )
                                new_quarter_round_material_other = gr.Textbox(
                                    label="Quarter Round Material (Other)", 
                                    placeholder="Specify material...", 
                                    visible=False
                                )
                                new_crown_molding = gr.Dropdown(
                                    label="Crown Molding", 
                                    choices=self.finish_choices['crown_molding'], 
                                    value="none"
                                )
                                new_crown_molding_other = gr.Textbox(
                                    label="Crown Molding (Other)", 
                                    placeholder="Specify crown molding...", 
                                    visible=False
                                )
                            
                            gr.Markdown("#### Optional: Import Room Measurements")
                            new_yaml_upload = gr.Textbox(
                                label="YAML Measurement Data", 
                                placeholder="Paste YAML data here to automatically create rooms with measurements (optional)...", 
                                lines=6
                            )
                            
                            with gr.Row():
                                save_new_project_btn = gr.Button("✅ Create Project", variant="primary", size="lg")
                            
                            new_project_status = gr.Textbox(label="Status", interactive=False)
                    
                    # Project Edit Section (shown when a project is selected)
                    with gr.Group(visible=False) as project_edit_group:
                        gr.Markdown("### 🔧 Edit Project Settings")
                        gr.Markdown("*Modify project details and default finishes*")
                        
                        with gr.Row():
                            project_name = gr.Textbox(label="Project Name", interactive=True)
                            project_desc = gr.Textbox(label="Description", lines=2, interactive=True)
                        
                        with gr.Accordion("🎨 Default Finishes", open=False):
                            gr.Markdown("*These settings apply to all new rooms unless overridden*")
                            
                            with gr.Row():
                                default_flooring = gr.Dropdown(label="Default Flooring", choices=self.finish_choices['flooring'], interactive=True)
                                default_flooring_other = gr.Textbox(label="Flooring (Other)", placeholder="Specify flooring type...", visible=False, interactive=True)
                                default_wall_finish = gr.Dropdown(label="Default Wall Finish", choices=self.finish_choices['wall_finish'], interactive=True)
                                default_wall_finish_other = gr.Textbox(label="Wall Finish (Other)", placeholder="Specify wall finish...", visible=False, interactive=True)
                            
                            with gr.Row():
                                default_ceiling_finish = gr.Dropdown(label="Default Ceiling Finish", choices=self.finish_choices['ceiling_finish'], interactive=True)
                                default_ceiling_finish_other = gr.Textbox(label="Ceiling Finish (Other)", placeholder="Specify ceiling finish...", visible=False, interactive=True)
                            
                            with gr.Row():
                                baseboard_type = gr.Dropdown(label="Baseboard Type", choices=self.finish_choices['baseboard_type'], interactive=True)
                                baseboard_type_other = gr.Textbox(label="Baseboard Type (Other)", placeholder="Specify baseboard type...", visible=False, interactive=True)
                                baseboard_material = gr.Dropdown(label="Baseboard Material", choices=self.finish_choices['baseboard_material'], interactive=True)
                                baseboard_material_other = gr.Textbox(label="Baseboard Material (Other)", placeholder="Specify material...", visible=False, interactive=True)
                            
                            with gr.Row():
                                quarter_round_check = gr.Checkbox(label="Quarter Round", interactive=True)
                                quarter_round_material = gr.Dropdown(label="Quarter Round Material", choices=self.finish_choices['quarter_round_material'], visible=False, interactive=True)
                                quarter_round_material_other = gr.Textbox(label="Quarter Round Material (Other)", placeholder="Specify material...", visible=False, interactive=True)
                                crown_molding = gr.Dropdown(label="Crown Molding", choices=self.finish_choices['crown_molding'], interactive=True)
                                crown_molding_other = gr.Textbox(label="Crown Molding (Other)", placeholder="Specify crown molding...", visible=False, interactive=True)
                        
                        with gr.Accordion("🔗 Merge Rooms", open=False):
                            gr.Markdown("*Combine multiple related rooms (e.g., Kitchen + Kitchen Bay Area)*")
                            
                            with gr.Row():
                                merge_room_dropdown = gr.Dropdown(
                                    label="Select Rooms to Merge",
                                    choices=[],
                                    multiselect=True,
                                    interactive=True
                                )
                                refresh_merge_rooms_btn = gr.Button("🔄 Refresh Rooms", size="sm")
                            
                            new_merged_room_name = gr.Textbox(
                                label="New Room Name",
                                placeholder="Enter name for merged room (e.g., 'Kitchen', 'Bedroom')..."
                            )
                            
                            merge_preview = gr.Textbox(
                                label="Merge Preview",
                                lines=8,
                                interactive=False,
                                placeholder="Select rooms above to see merge preview..."
                            )
                            
                            with gr.Row():
                                merge_rooms_btn = gr.Button("🔗 Merge Selected Rooms", variant="primary")
                            
                            merge_status = gr.Textbox(label="Merge Status", interactive=False)
                        
                        with gr.Accordion("📤 Add More Rooms", open=False):
                            gr.Markdown("*Import additional room measurements to this project*")
                            yaml_upload_input = gr.Textbox(
                                label="YAML Measurement Data",
                                placeholder="Paste YAML measurement data here to add more rooms...",
                                lines=8
                            )
                            upload_yaml_btn = gr.Button("📤 Upload Measurements", variant="secondary")
                            upload_status = gr.Textbox(label="Upload Status", interactive=False)
                        
                        # Save button at the very end
                        gr.Markdown("---")
                        with gr.Row():
                            save_project_btn = gr.Button("💾 Save All Changes", variant="primary", size="lg")
                        save_status = gr.Textbox(label="Save Status", interactive=False)
                
                # Work Scope Tab
                with gr.TabItem("📋 Work Scope", id="work_scope_tab"):
                    gr.Markdown("### Room Work Scope Configuration")
                    
                    # Room selection notice
                    work_scope_notice = gr.Markdown("⚠️ Please select a project first", visible=True)
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            room_dropdown = gr.Dropdown(
                                label="Select Room",
                                choices=[],
                                interactive=True
                            )
                            
                            gr.Markdown("#### Edit Room Name")
                            room_name_edit = gr.Textbox(label="Room Name", interactive=True)
                            update_name_btn = gr.Button("Update Room Name", size="sm")
                            update_status = gr.Textbox(label="Update Status", interactive=False)
                            
                            project_defaults_display = gr.Textbox(
                                label="Project Defaults",
                                lines=10,
                                interactive=False
                            )
                            
                        with gr.Column(scale=2):
                            with gr.Tabs():
                                # Finishes Tab
                                with gr.TabItem("Finishes & Paint"):
                                    use_defaults_checkbox = gr.Checkbox(
                                        label="Use Project Defaults for All Finishes",
                                        value=True
                                    )
                                    
                                    gr.Markdown("##### Override Finishes (only if not using defaults)")
                                    
                                    with gr.Group():
                                        flooring_override = gr.Dropdown(
                                            label="Flooring Override",
                                            choices=[""] + self.finish_choices['flooring'],
                                            value=""
                                        )
                                        
                                        wall_finish_override = gr.Dropdown(
                                            label="Wall Finish Override", 
                                            choices=[""] + self.finish_choices['wall_finish'],
                                            value=""
                                        )
                                        
                                        ceiling_finish_override = gr.Dropdown(
                                            label="Ceiling Finish Override",
                                            choices=[""] + self.finish_choices['ceiling_finish'],
                                            value=""
                                        )
                                    
                                    paint_scope = gr.Radio(
                                        label="Paint Scope",
                                        choices=["walls_only", "ceiling_only", "both", "none"],
                                        value="both"
                                    )
                                
                                # Demo'd Scope Tab
                                with gr.TabItem("Demo'd Scope"):
                                    gr.Markdown("##### Already Demolished (No demo cost, only installation)")
                                    
                                    with gr.Group():
                                        gr.Markdown("**Floor**")
                                        demod_floor = gr.Radio(
                                            label="Floor Status",
                                            choices=["n/a", "all", "partial"],
                                            value="n/a"
                                        )
                                        demod_floor_sf = gr.Textbox(
                                            label="Partial SF",
                                            placeholder="Square feet...",
                                            visible=False
                                        )
                                        
                                        gr.Markdown("**Walls**")
                                        demod_walls = gr.Radio(
                                            label="Walls Status",
                                            choices=["n/a", "all", "partial"],
                                            value="n/a"
                                        )
                                        demod_walls_sf = gr.Textbox(
                                            label="Partial SF",
                                            placeholder="Square feet...",
                                            visible=False
                                        )
                                        
                                        gr.Markdown("**Ceiling**")
                                        demod_ceiling = gr.Radio(
                                            label="Ceiling Status",
                                            choices=["n/a", "all", "partial"],
                                            value="n/a"
                                        )
                                        demod_ceiling_sf = gr.Textbox(
                                            label="Partial SF",
                                            placeholder="Square feet...",
                                            visible=False
                                        )
                                        
                                        gr.Markdown("**Wall Insulation**")
                                        demod_wall_insulation = gr.Radio(
                                            label="Wall Insulation Status",
                                            choices=["n/a", "all", "partial"],
                                            value="n/a"
                                        )
                                        demod_wall_insulation_sf = gr.Textbox(
                                            label="Partial SF",
                                            placeholder="Square feet...",
                                            visible=False
                                        )
                                        
                                        gr.Markdown("**Ceiling Insulation**")
                                        demod_ceiling_insulation = gr.Radio(
                                            label="Ceiling Insulation Status",
                                            choices=["n/a", "all", "partial"],
                                            value="n/a"
                                        )
                                        demod_ceiling_insulation_sf = gr.Textbox(
                                            label="Partial SF",
                                            placeholder="Square feet...",
                                            visible=False
                                        )
                                        
                                        gr.Markdown("**Baseboard**")
                                        demod_baseboard = gr.Radio(
                                            label="Baseboard Status",
                                            choices=["n/a", "all", "partial"],
                                            value="n/a"
                                        )
                                        demod_baseboard_lf = gr.Textbox(
                                            label="Partial LF",
                                            placeholder="Linear feet...",
                                            visible=False
                                        )
                                
                                # Removal Scope Tab
                                with gr.TabItem("Removal Scope"):
                                    gr.Markdown("##### To Be Demolished (Demo + disposal + installation costs)")
                                    
                                    with gr.Group():
                                        removal_floor = gr.Radio(
                                            label="Floor",
                                            choices=["n/a", "all", "remaining"],
                                            value="n/a"
                                        )
                                        
                                        removal_walls = gr.Radio(
                                            label="Walls",
                                            choices=["n/a", "all", "remaining"],
                                            value="n/a"
                                        )
                                        
                                        removal_ceiling = gr.Radio(
                                            label="Ceiling",
                                            choices=["n/a", "all", "remaining"],
                                            value="n/a"
                                        )
                                        
                                        removal_wall_insulation = gr.Radio(
                                            label="Wall Insulation",
                                            choices=["n/a", "all", "remaining"],
                                            value="n/a"
                                        )
                                        
                                        removal_ceiling_insulation = gr.Radio(
                                            label="Ceiling Insulation",
                                            choices=["n/a", "all", "remaining"],
                                            value="n/a"
                                        )
                                        
                                        removal_baseboard = gr.Radio(
                                            label="Baseboard",
                                            choices=["n/a", "all", "remaining"],
                                            value="n/a"
                                        )
                                
                                # Specific Tasks Tab
                                with gr.TabItem("Specific Tasks"):
                                    # Remove & Replace Items
                                    gr.Markdown("##### Remove & Replace Items")
                                    gr.Markdown("Items to be removed and replaced with similar/identical new items")
                                    
                                    remove_replace_state = gr.State([])
                                    with gr.Column() as remove_replace_container:
                                        remove_replace_items_display = gr.HTML("")
                                    
                                    with gr.Row():
                                        rr_item = gr.Textbox(label="Item", placeholder="e.g., Door, Window, Cabinet")
                                        rr_quantity = gr.Number(label="Quantity", value=1, minimum=0)
                                        rr_unit = gr.Dropdown(label="Unit", choices=["ea", "sf", "lf", "sy", "ton", "lb", "gal"], value="ea")
                                        add_rr_btn = gr.Button("+ Add", size="sm", variant="secondary")
                                    
                                    # Detach & Reset Items
                                    gr.Markdown("##### Detach & Reset Items")
                                    gr.Markdown("Items to be detached/removed without demolition, then reinstalled")
                                    
                                    detach_reset_state = gr.State([])
                                    with gr.Column() as detach_reset_container:
                                        detach_reset_items_display = gr.HTML("")
                                    
                                    with gr.Row():
                                        dr_item = gr.Textbox(label="Item", placeholder="e.g., Cabinet, Fixture, Appliance")
                                        dr_quantity = gr.Number(label="Quantity", value=1, minimum=0)
                                        dr_unit = gr.Dropdown(label="Unit", choices=["ea", "sf", "lf", "sy", "ton", "lb", "gal"], value="ea")
                                        add_dr_btn = gr.Button("+ Add", size="sm", variant="secondary")
                                    
                                    # Protection Required
                                    gr.Markdown("##### Protection Required")
                                    gr.Markdown("Items to be protected during work")
                                    
                                    protection_state = gr.State([])
                                    with gr.Column() as protection_container:
                                        protection_items_display = gr.HTML("")
                                    
                                    with gr.Row():
                                        p_item = gr.Textbox(label="Item", placeholder="e.g., Flooring, Furniture, Equipment")
                                        p_quantity = gr.Number(label="Quantity", value=1, minimum=0)
                                        p_unit = gr.Dropdown(label="Unit", choices=["ea", "sf", "lf", "sy", "ton", "lb", "gal"], value="sf")
                                        add_p_btn = gr.Button("+ Add", size="sm", variant="secondary")
                                    
                                    notes = gr.Textbox(
                                        label="General Notes for Room",
                                        placeholder="Enter any specific notes or requirements...",
                                        lines=6
                                    )
                    
                    save_scope_btn = gr.Button("Save Complete Work Scope", variant="primary", size="lg")
                    save_work_status = gr.Textbox(label="Save Status", interactive=False)
                
                # Export Tab
                with gr.TabItem("📤 Export"):
                    gr.Markdown("### Export Project Data")
                    
                    export_btn = gr.Button("Export Project to YAML", variant="primary", size="lg")
                    export_status = gr.Textbox(label="Export Status", interactive=False)
                    
                    exported_yaml = gr.Code(
                        label="Exported YAML (includes measurements and work scopes)",
                        language="yaml",
                        lines=25
                    )
            
            # Helper functions for task management
            def update_task_display(items, container_id):
                """Generate HTML display for task items"""
                if not items:
                    return ""
                
                html_items = []
                for i, item in enumerate(items):
                    html_items.append(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; 
                                background: #f8f9fa; padding: 8px; margin: 4px 0; border-radius: 4px;">
                        <span><strong>{item['item']}</strong> - {item['quantity']} {item['unit']}</span>
                        <button onclick="removeTaskItem('{container_id}', {i})" 
                                style="background: #dc3545; color: white; border: none; padding: 4px 8px; 
                                       border-radius: 4px; cursor: pointer;">Remove</button>
                    </div>
                    """)
                
                return "".join(html_items)
            
            def add_task_item(items, item, quantity, unit):
                """Add new task item"""
                if item.strip():
                    new_item = {'item': item.strip(), 'quantity': quantity, 'unit': unit}
                    updated_items = items + [new_item]
                    return updated_items, "", 1, "ea"
                return items, item, quantity, unit
            
            def remove_task_item(items, index):
                """Remove task item"""
                if 0 <= index < len(items):
                    updated_items = items[:index] + items[index+1:]
                    return updated_items
                return items
            
            # Event Handlers
            
            # Project selection and editing visibility logic
            def show_project_edit_section(project_choice):
                """Show edit section when project is selected"""
                has_project = project_choice and "No projects found" not in project_choice and "Error" not in project_choice
                return gr.Group(visible=has_project)
            
            # Toggle 'other' field visibility for new project form
            new_flooring.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[new_flooring],
                outputs=[new_flooring_other]
            )
            
            new_wall_finish.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[new_wall_finish],
                outputs=[new_wall_finish_other]
            )
            
            new_ceiling_finish.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[new_ceiling_finish],
                outputs=[new_ceiling_finish_other]
            )
            
            new_baseboard_type.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[new_baseboard_type],
                outputs=[new_baseboard_type_other]
            )
            
            new_baseboard_material.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[new_baseboard_material],
                outputs=[new_baseboard_material_other]
            )
            
            new_quarter_round.change(
                fn=lambda x: (gr.Dropdown(visible=x), gr.Textbox(visible=x)),
                inputs=[new_quarter_round],
                outputs=[new_quarter_round_material, new_quarter_round_material_other]
            )
            
            new_quarter_round_material.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[new_quarter_round_material],
                outputs=[new_quarter_round_material_other]
            )
            
            new_crown_molding.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[new_crown_molding],
                outputs=[new_crown_molding_other]
            )
            
            # Toggle 'other' field visibility for existing project form
            default_flooring.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[default_flooring],
                outputs=[default_flooring_other]
            )
            
            default_wall_finish.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[default_wall_finish],
                outputs=[default_wall_finish_other]
            )
            
            default_ceiling_finish.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[default_ceiling_finish],
                outputs=[default_ceiling_finish_other]
            )
            
            baseboard_type.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[baseboard_type],
                outputs=[baseboard_type_other]
            )
            
            baseboard_material.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[baseboard_material],
                outputs=[baseboard_material_other]
            )
            
            quarter_round_check.change(
                fn=lambda x: (gr.Dropdown(visible=x), gr.Textbox(visible=x)),
                inputs=[quarter_round_check],
                outputs=[quarter_round_material, quarter_round_material_other]
            )
            
            quarter_round_material.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[quarter_round_material],
                outputs=[quarter_round_material_other]
            )
            
            crown_molding.change(
                fn=lambda x: gr.Textbox(visible=(x == "other")),
                inputs=[crown_molding],
                outputs=[crown_molding_other]
            )
            
            # Load project details when selected
            def load_and_update_all(project_choice):
                details = self.load_project_details(project_choice)
                
                # Update room dropdown
                room_choices = self.get_room_choices()
                
                # Update mergeable rooms dropdown
                mergeable_rooms = self.get_mergeable_rooms()
                
                # Determine if we have a project selected
                has_project = details['form_visible']
                
                return [
                    # Current project info
                    details['summary'],
                    # Project edit group visibility
                    gr.Group(visible=has_project),
                    # Project details for editing
                    details['name'],
                    details['description'],
                    details['flooring'],
                    details['flooring_other'],
                    gr.Textbox(visible=(details['flooring'] == "other"), value=details['flooring_other']),
                    details['wall_finish'],
                    details['wall_finish_other'],
                    gr.Textbox(visible=(details['wall_finish'] == "other"), value=details['wall_finish_other']),
                    details['ceiling_finish'],
                    details['ceiling_finish_other'],
                    gr.Textbox(visible=(details['ceiling_finish'] == "other"), value=details['ceiling_finish_other']),
                    details['baseboard_type'],
                    details['baseboard_type_other'],
                    gr.Textbox(visible=(details['baseboard_type'] == "other"), value=details['baseboard_type_other']),
                    details['baseboard_material'],
                    details['baseboard_material_other'],
                    gr.Textbox(visible=(details['baseboard_material'] == "other"), value=details['baseboard_material_other']),
                    details['quarter_round'],
                    gr.Dropdown(visible=details['quarter_round'], value=details['quarter_round_material']),
                    details['quarter_round_material_other'],
                    gr.Textbox(visible=(details['quarter_round'] and details['quarter_round_material'] == "other"), value=details['quarter_round_material_other']),
                    details['crown_molding'],
                    details['crown_molding_other'],
                    gr.Textbox(visible=(details['crown_molding'] == "other"), value=details['crown_molding_other']),
                    # Merge room dropdown
                    gr.Dropdown(choices=mergeable_rooms),
                    # Room dropdown and notice
                    gr.Dropdown(choices=room_choices),
                    gr.Markdown(visible=not has_project, value="⚠️ Please select a project first" if not has_project else "")
                ]
            
            project_dropdown.change(
                fn=load_and_update_all,
                inputs=[project_dropdown],
                outputs=[
                    current_project_info,
                    project_edit_group,
                    project_name, project_desc,
                    default_flooring, default_flooring_other, default_flooring_other,
                    default_wall_finish, default_wall_finish_other, default_wall_finish_other,
                    default_ceiling_finish, default_ceiling_finish_other, default_ceiling_finish_other,
                    baseboard_type, baseboard_type_other, baseboard_type_other,
                    baseboard_material, baseboard_material_other, baseboard_material_other,
                    quarter_round_check, quarter_round_material, quarter_round_material_other, quarter_round_material_other,
                    crown_molding, crown_molding_other, crown_molding_other,
                    merge_room_dropdown,
                    room_dropdown, work_scope_notice
                ]
            )
            
            # Refresh project list
            def refresh_projects():
                choices = [c[0] for c in self.get_project_list_formatted()]
                return gr.Dropdown(choices=choices)
            
            refresh_projects_btn.click(
                fn=refresh_projects,
                outputs=[project_dropdown]
            )
            
            # Save project changes
            save_project_btn.click(
                fn=self.save_project_changes,
                inputs=[
                    project_name, project_desc,
                    default_flooring, default_flooring_other,
                    default_wall_finish, default_wall_finish_other,
                    default_ceiling_finish, default_ceiling_finish_other,
                    baseboard_type, baseboard_type_other,
                    baseboard_material, baseboard_material_other,
                    quarter_round_check, quarter_round_material, quarter_round_material_other,
                    crown_molding, crown_molding_other
                ],
                outputs=[save_status, project_dropdown]
            )
            
            # Create new project and redirect to Work Scope tab
            def create_and_select_project(*args):
                status, dropdown, details = self.create_new_project_form(*args)
                
                # Update room dropdown
                room_choices = self.get_room_choices()
                
                # Update mergeable rooms dropdown
                mergeable_rooms = self.get_mergeable_rooms()
                
                # Determine if project was created successfully
                has_project = details.get('form_visible', False)
                
                # Generate success message with instructions
                if has_project and "✅" in status:
                    status += "\n\n🎯 Project created! You can now configure room work scopes in the 'Work Scope' tab."
                
                return [
                    status,  # new_project_status
                    dropdown,  # project_dropdown (for existing projects tab)
                    # Update current project info
                    details.get('summary', 'No project selected'),
                    # Update project edit section
                    gr.Group(visible=has_project),  # project_edit_group
                    # Update existing project fields
                    details.get('name', ''),
                    details.get('description', ''),
                    details.get('flooring', 'hardwood'),
                    details.get('flooring_other', ''),
                    gr.Textbox(visible=(details.get('flooring') == "other"), value=details.get('flooring_other', '')),
                    details.get('wall_finish', 'painted_drywall'),
                    details.get('wall_finish_other', ''),
                    gr.Textbox(visible=(details.get('wall_finish') == "other"), value=details.get('wall_finish_other', '')),
                    details.get('ceiling_finish', 'painted_drywall'),
                    details.get('ceiling_finish_other', ''),
                    gr.Textbox(visible=(details.get('ceiling_finish') == "other"), value=details.get('ceiling_finish_other', '')),
                    details.get('baseboard_type', 'standard'),
                    details.get('baseboard_type_other', ''),
                    gr.Textbox(visible=(details.get('baseboard_type') == "other"), value=details.get('baseboard_type_other', '')),
                    details.get('baseboard_material', 'painted_wood'),
                    details.get('baseboard_material_other', ''),
                    gr.Textbox(visible=(details.get('baseboard_material') == "other"), value=details.get('baseboard_material_other', '')),
                    details.get('quarter_round', False),
                    gr.Dropdown(visible=details.get('quarter_round', False), value=details.get('quarter_round_material', 'painted_wood')),
                    details.get('quarter_round_material_other', ''),
                    gr.Textbox(visible=(details.get('quarter_round', False) and details.get('quarter_round_material') == "other"), value=details.get('quarter_round_material_other', '')),
                    details.get('crown_molding', 'none'),
                    details.get('crown_molding_other', ''),
                    gr.Textbox(visible=(details.get('crown_molding') == "other"), value=details.get('crown_molding_other', '')),
                    # Merge room dropdown
                    gr.Dropdown(choices=mergeable_rooms),
                    # Room dropdown and notice
                    gr.Dropdown(choices=room_choices),
                    gr.Markdown(visible=not has_project, value="⚠️ Please select a project first" if not has_project else "")
                ]
            
            save_new_project_btn.click(
                fn=create_and_select_project,
                inputs=[
                    new_project_name, new_project_desc,
                    new_flooring, new_flooring_other,
                    new_wall_finish, new_wall_finish_other,
                    new_ceiling_finish, new_ceiling_finish_other,
                    new_baseboard_type, new_baseboard_type_other,
                    new_baseboard_material, new_baseboard_material_other,
                    new_quarter_round, new_quarter_round_material, new_quarter_round_material_other,
                    new_crown_molding, new_crown_molding_other,
                    new_yaml_upload
                ],
                outputs=[
                    new_project_status, project_dropdown,
                    # Update current project info and edit section
                    current_project_info, project_edit_group,
                    # Update existing project fields
                    project_name, project_desc,
                    default_flooring, default_flooring_other, default_flooring_other,
                    default_wall_finish, default_wall_finish_other, default_wall_finish_other,
                    default_ceiling_finish, default_ceiling_finish_other, default_ceiling_finish_other,
                    baseboard_type, baseboard_type_other, baseboard_type_other,
                    baseboard_material, baseboard_material_other, baseboard_material_other,
                    quarter_round_check, quarter_round_material, quarter_round_material_other, quarter_round_material_other,
                    crown_molding, crown_molding_other, crown_molding_other,
                    merge_room_dropdown,
                    room_dropdown, work_scope_notice
                ]
            )
            
            # Upload YAML to current project
            upload_yaml_btn.click(
                fn=self.upload_yaml_to_current_project,
                inputs=[yaml_upload_input],
                outputs=[upload_status]
            )
            
            # Update room name
            update_name_btn.click(
                fn=self.update_room_name,
                inputs=[room_name_edit],
                outputs=[update_status, room_dropdown]
            )
            
            # Load room work scope
            def load_room_scope(room_choice):
                form_data = self.select_room_for_work_scope(room_choice)
                return [
                    form_data['room_name'],  # room_name_edit
                    form_data['use_defaults'],
                    form_data['flooring_override'],
                    form_data['wall_finish_override'],
                    form_data['ceiling_finish_override'],
                    form_data['paint_scope'],
                    # Demo'd scope
                    form_data['demod_floor'],
                    form_data['demod_floor_sf'],
                    form_data['demod_walls'],
                    form_data['demod_walls_sf'],
                    form_data['demod_ceiling'],
                    form_data['demod_ceiling_sf'],
                    form_data['demod_wall_insulation'],
                    form_data['demod_wall_insulation_sf'],
                    form_data['demod_ceiling_insulation'],
                    form_data['demod_ceiling_insulation_sf'],
                    form_data['demod_baseboard'],
                    form_data['demod_baseboard_lf'],
                    # Removal scope
                    form_data['removal_floor'],
                    form_data['removal_walls'],
                    form_data['removal_ceiling'],
                    form_data['removal_wall_insulation'],
                    form_data['removal_ceiling_insulation'],
                    form_data['removal_baseboard'],
                    # Task lists
                    form_data['remove_replace_items'],
                    update_task_display(form_data['remove_replace_items'], 'rr'),
                    form_data['detach_reset_items'],
                    update_task_display(form_data['detach_reset_items'], 'dr'),
                    form_data['protection_items'],
                    update_task_display(form_data['protection_items'], 'p'),
                    form_data['notes'],
                    form_data['project_defaults_text']
                ]
            
            room_dropdown.change(
                fn=load_room_scope,
                inputs=[room_dropdown],
                outputs=[
                    room_name_edit, use_defaults_checkbox,
                    flooring_override, wall_finish_override, ceiling_finish_override,
                    paint_scope,
                    # Demo'd scope
                    demod_floor, demod_floor_sf, demod_walls, demod_walls_sf,
                    demod_ceiling, demod_ceiling_sf, demod_wall_insulation, demod_wall_insulation_sf,
                    demod_ceiling_insulation, demod_ceiling_insulation_sf, demod_baseboard, demod_baseboard_lf,
                    # Removal scope
                    removal_floor, removal_walls, removal_ceiling,
                    removal_wall_insulation, removal_ceiling_insulation, removal_baseboard,
                    # Task lists
                    remove_replace_state, remove_replace_items_display,
                    detach_reset_state, detach_reset_items_display,
                    protection_state, protection_items_display,
                    notes, project_defaults_display
                ]
            )
            
            # Toggle partial SF/LF fields visibility
            demod_floor.change(
                fn=lambda x: gr.Textbox(visible=(x == "partial")),
                inputs=[demod_floor],
                outputs=[demod_floor_sf]
            )
            
            demod_walls.change(
                fn=lambda x: gr.Textbox(visible=(x == "partial")),
                inputs=[demod_walls],
                outputs=[demod_walls_sf]
            )
            
            demod_ceiling.change(
                fn=lambda x: gr.Textbox(visible=(x == "partial")),
                inputs=[demod_ceiling],
                outputs=[demod_ceiling_sf]
            )
            
            demod_wall_insulation.change(
                fn=lambda x: gr.Textbox(visible=(x == "partial")),
                inputs=[demod_wall_insulation],
                outputs=[demod_wall_insulation_sf]
            )
            
            demod_ceiling_insulation.change(
                fn=lambda x: gr.Textbox(visible=(x == "partial")),
                inputs=[demod_ceiling_insulation],
                outputs=[demod_ceiling_insulation_sf]
            )
            
            demod_baseboard.change(
                fn=lambda x: gr.Textbox(visible=(x == "partial")),
                inputs=[demod_baseboard],
                outputs=[demod_baseboard_lf]
            )
            
            # Task management event handlers
            add_rr_btn.click(
                fn=lambda items, item, qty, unit: add_task_item(items, item, qty, unit) + (update_task_display(add_task_item(items, item, qty, unit)[0], 'rr'),),
                inputs=[remove_replace_state, rr_item, rr_quantity, rr_unit],
                outputs=[remove_replace_state, rr_item, rr_quantity, rr_unit, remove_replace_items_display]
            )
            
            add_dr_btn.click(
                fn=lambda items, item, qty, unit: add_task_item(items, item, qty, unit) + (update_task_display(add_task_item(items, item, qty, unit)[0], 'dr'),),
                inputs=[detach_reset_state, dr_item, dr_quantity, dr_unit],
                outputs=[detach_reset_state, dr_item, dr_quantity, dr_unit, detach_reset_items_display]
            )
            
            add_p_btn.click(
                fn=lambda items, item, qty, unit: add_task_item(items, item, qty, unit) + (update_task_display(add_task_item(items, item, qty, unit)[0], 'p'),),
                inputs=[protection_state, p_item, p_quantity, p_unit],
                outputs=[protection_state, p_item, p_quantity, p_unit, protection_items_display]
            )
            
            # Save comprehensive work scope
            save_scope_btn.click(
                fn=self.save_comprehensive_work_scope,
                inputs=[
                    use_defaults_checkbox, flooring_override, wall_finish_override,
                    ceiling_finish_override, paint_scope,
                    # Demo'd scope
                    demod_floor, demod_floor_sf, demod_walls, demod_walls_sf,
                    demod_ceiling, demod_ceiling_sf, demod_wall_insulation, demod_wall_insulation_sf,
                    demod_ceiling_insulation, demod_ceiling_insulation_sf, demod_baseboard, demod_baseboard_lf,
                    # Removal scope
                    removal_floor, removal_walls, removal_ceiling,
                    removal_wall_insulation, removal_ceiling_insulation, removal_baseboard,
                    # Task lists
                    remove_replace_state, detach_reset_state, protection_state,
                    notes
                ],
                outputs=[save_work_status]
            )
            
            # Export project
            def export_project():
                status, yaml_content = self.export_project_yaml()
                return status, yaml_content or ""
            
            export_btn.click(
                fn=export_project,
                outputs=[export_status, exported_yaml]
            )
            
            # Room merging event handlers
            def refresh_merge_rooms():
                """Refresh the merge room dropdown"""
                rooms = self.get_mergeable_rooms()
                return gr.Dropdown(choices=rooms)
            
            refresh_merge_rooms_btn.click(
                fn=refresh_merge_rooms,
                outputs=[merge_room_dropdown]
            )
            
            merge_room_dropdown.change(
                fn=self.preview_room_merge,
                inputs=[merge_room_dropdown],
                outputs=[merge_preview]
            )
            
            def merge_rooms_and_refresh(selected_rooms, room_name):
                """Merge rooms and refresh all related UI components"""
                # Perform the merge
                merge_result = self.merge_selected_rooms(selected_rooms, room_name)
                
                # Refresh room-related dropdowns if merge was successful
                if "✅" in merge_result:
                    # Get updated data
                    room_choices = self.get_room_choices()
                    mergeable_rooms = self.get_mergeable_rooms()
                    
                    # Get updated project info
                    if self.current_project_id:
                        project_choice = None
                        for label, pid in self.get_project_list_formatted():
                            if pid == self.current_project_id:
                                project_choice = label
                                break
                        
                        if project_choice:
                            details = self.load_project_details(project_choice)
                            project_info = details['summary']
                        else:
                            project_info = "No project selected"
                    else:
                        project_info = "No project selected"
                    
                    return [
                        merge_result,  # merge_status
                        gr.Dropdown(choices=mergeable_rooms, value=[]),  # merge_room_dropdown (clear selection)
                        "",  # new_merged_room_name (clear input)
                        "",  # merge_preview (clear preview)
                        project_info,  # current_project_info
                        gr.Dropdown(choices=room_choices)  # room_dropdown
                    ]
                else:
                    # If merge failed, just return the error message
                    return [
                        merge_result,  # merge_status
                        merge_room_dropdown,  # keep current selection
                        new_merged_room_name,  # keep current name
                        merge_preview,  # keep current preview
                        current_project_info,  # keep current info
                        room_dropdown  # keep current room dropdown
                    ]
            
            merge_rooms_btn.click(
                fn=merge_rooms_and_refresh,
                inputs=[merge_room_dropdown, new_merged_room_name],
                outputs=[merge_status, merge_room_dropdown, new_merged_room_name, merge_preview, current_project_info, room_dropdown]
            )
            
            # Initialize project dropdown on load
            interface.load(
                fn=refresh_projects,
                outputs=[project_dropdown]
            )
        
        return interface


def main():
    """Main function to run the application"""
    try:
        app = ConstructionEstimationAppV4()
        interface = app.create_interface()
        
        print("Construction Estimation Manager V4 Starting...")
        print("Database: SQLite")
        print("Web Interface: http://localhost:7864")
        print("Ready for comprehensive project management!")
        
        interface.launch(
            server_name="0.0.0.0",
            server_port=7864,
            share=False,
            debug=True,
            show_error=True
        )
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()