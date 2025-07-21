#!/usr/bin/env python3
"""
Construction Estimation Project Management App V2
Enhanced with project defaults, room editing, and comprehensive work scope forms
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


class ConstructionEstimationAppV2:
    """Enhanced construction estimation app with comprehensive work scope forms"""
    
    def __init__(self):
        """Initialize the application"""
        self.project_service = get_project_service()
        self.current_project_id = None
        self.current_room_id = None
        
        # Initialize database
        self.db_manager = get_db_manager()
        print("Database initialized successfully")
    
    def create_project_with_defaults(self, name: str, description: str,
                                   flooring: str, wall_finish: str, ceiling_finish: str,
                                   baseboard_type: str, baseboard_material: str,
                                   quarter_round: bool, quarter_round_material: str,
                                   crown_molding: str, yaml_content: str) -> Tuple[str, str]:
        """Create project with defaults and optionally upload YAML"""
        if not name.strip():
            return "Error: Project name is required", ""
        
        try:
            # Prepare default finishes
            default_finishes = {
                'flooring': flooring or 'hardwood',
                'wall_finish': wall_finish or 'painted_drywall',
                'ceiling_finish': ceiling_finish or 'painted_drywall'
            }
            
            # Prepare default trim
            default_trim = {
                'baseboard': {
                    'type': baseboard_type or 'standard',
                    'material': baseboard_material or 'painted_wood'
                },
                'quarter_round': {
                    'enabled': quarter_round,
                    'material': quarter_round_material or 'painted_wood'
                },
                'crown_molding': crown_molding or 'none'
            }
            
            # Create project
            project = self.project_service.create_project(
                name.strip(), 
                description.strip(),
                default_finishes,
                default_trim
            )
            self.current_project_id = project.id
            
            status_msg = f"✅ Project '{name}' created successfully (ID: {project.id})"
            summary = ""
            
            # If YAML content provided, upload it
            if yaml_content.strip():
                success, message, rooms = self.project_service.upload_yaml_measurements(
                    self.current_project_id, yaml_content
                )
                
                if success:
                    summary_lines = [f"📍 {room['floor']} - {room['room']}" for room in rooms]
                    summary = "\n".join(summary_lines)
                    status_msg += f"\n✅ {message}"
                else:
                    status_msg += f"\n❌ YAML Error: {message}"
            
            return status_msg, summary
            
        except Exception as e:
            return f"Error creating project: {str(e)}", ""
    
    def get_project_list(self) -> List[List]:
        """Get list of all projects for dropdown"""
        try:
            projects = self.project_service.get_all_projects()
            return [[p['name'], p['id']] for p in projects]
        except Exception as e:
            print(f"Error getting projects: {e}")
            return []
    
    def select_project(self, project_choice: str) -> Tuple[str, str]:
        """Select a project and load its data"""
        if not project_choice:
            return "No project selected", ""
        
        try:
            projects = self.project_service.get_all_projects()
            selected_project = None
            
            for project in projects:
                if project['name'] == project_choice:
                    selected_project = project
                    break
            
            if not selected_project:
                return "Project not found", ""
            
            self.current_project_id = selected_project['id']
            
            # Get project details
            project_data = self.project_service.get_project_with_rooms(self.current_project_id)
            if not project_data:
                return "Error loading project data", ""
            
            # Generate project summary
            summary_lines = [
                f"📂 Project: {project_data['name']}",
                f"📝 Description: {project_data.get('description', 'No description')}",
                f"🏢 Floors: {len(project_data['floors'])}",
                f"🏠 Total Rooms: {sum(len(floor['rooms']) for floor in project_data['floors'])}",
                "",
                "📋 PROJECT DEFAULTS:",
                f"Flooring: {project_data['default_finishes'].get('flooring', 'Not set')}",
                f"Wall Finish: {project_data['default_finishes'].get('wall_finish', 'Not set')}",
                f"Ceiling Finish: {project_data['default_finishes'].get('ceiling_finish', 'Not set')}",
                ""
            ]
            
            # List floors and rooms
            for floor in project_data['floors']:
                summary_lines.append(f"📍 {floor['name'].upper()}:")
                for room in floor['rooms']:
                    status = "✅" if room['has_work_scope'] else "⏳"
                    summary_lines.append(f"   {status} {room['name']} ({room.get('dimensions', 'No dimensions')})")
                summary_lines.append("")
            
            return f"Project '{project_data['name']}' loaded successfully", "\n".join(summary_lines)
            
        except Exception as e:
            return f"Error selecting project: {str(e)}", ""
    
    def get_room_choices(self) -> List[str]:
        """Get room choices for current project"""
        if not self.current_project_id:
            return []
        
        try:
            project_data = self.project_service.get_project_with_rooms(self.current_project_id)
            if not project_data:
                return []
            
            room_choices = []
            for floor in project_data['floors']:
                for room in floor['rooms']:
                    room_choices.append(f"{floor['name']} - {room['name']} (ID: {room['id']})")
            
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
            
            # Extract task lists
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
                # Task lists as JSON strings for display
                'remove_replace_json': json.dumps(remove_replace, indent=2),
                'detach_reset_json': json.dumps(detach_reset, indent=2),
                'protection_json': json.dumps(protection, indent=2),
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
            'remove_replace_json': '[]',
            'detach_reset_json': '[]',
            'protection_json': '[]',
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
    
    def save_comprehensive_work_scope(self, *args) -> str:
        """Save comprehensive work scope including demo and removal scopes"""
        if not self.current_room_id:
            return "Error: No room selected"
        
        try:
            # Unpack arguments
            (use_defaults, flooring, wall_finish, ceiling_finish, paint_scope,
             demod_floor, demod_floor_sf, demod_walls, demod_walls_sf, 
             demod_ceiling, demod_ceiling_sf, demod_wall_insulation, demod_wall_insulation_sf,
             demod_ceiling_insulation, demod_ceiling_insulation_sf, demod_baseboard, demod_baseboard_lf,
             removal_floor, removal_walls, removal_ceiling, 
             removal_wall_insulation, removal_ceiling_insulation, removal_baseboard,
             remove_replace_json, detach_reset_json, protection_json, notes) = args
            
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
            
            # Parse task lists
            try:
                remove_replace_items = json.loads(remove_replace_json) if remove_replace_json else []
            except:
                remove_replace_items = []
            
            try:
                detach_reset_items = json.loads(detach_reset_json) if detach_reset_json else []
            except:
                detach_reset_items = []
            
            try:
                protection_items = json.loads(protection_json) if protection_json else []
            except:
                protection_items = []
            
            # Build work scope data
            work_scope_data = {
                'use_project_defaults': use_defaults,
                'flooring_override': flooring.strip() if not use_defaults else None,
                'wall_finish_override': wall_finish.strip() if not use_defaults else None,
                'ceiling_finish_override': ceiling_finish.strip() if not use_defaults else None,
                'paint_scope': paint_scope,
                'demod_scope': demod_scope,
                'removal_scope': removal_scope,
                'remove_replace_items': remove_replace_items,
                'detach_reset_items': detach_reset_items,
                'protection_items': protection_items,
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
    
    def create_interface(self) -> gr.Blocks:
        """Create the enhanced Gradio interface"""
        
        with gr.Blocks(title="Construction Estimation Manager V2", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🏗️ Construction Estimation Manager V2")
            gr.Markdown("Enhanced project management with comprehensive work scope forms")
            
            with gr.Tabs():
                # Project Management Tab
                with gr.TabItem("📂 Projects"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### Create New Project")
                            project_name = gr.Textbox(label="Project Name*", placeholder="Enter project name...")
                            project_desc = gr.Textbox(label="Description", placeholder="Project description...", lines=2)
                            
                            gr.Markdown("#### Project-Wide Defaults")
                            
                            # Finishes
                            gr.Markdown("**Finishes**")
                            default_flooring = gr.Dropdown(
                                label="Default Flooring",
                                choices=["hardwood", "laminate", "carpet", "tile", "vinyl", "other"],
                                value="hardwood"
                            )
                            default_wall_finish = gr.Dropdown(
                                label="Default Wall Finish",
                                choices=["painted_drywall", "textured_drywall", "tile", "wallpaper", "wood", "brick", "other"],
                                value="painted_drywall"
                            )
                            default_ceiling_finish = gr.Dropdown(
                                label="Default Ceiling Finish",
                                choices=["painted_drywall", "textured_drywall", "tile", "wood", "drop_ceiling", "other"],
                                value="painted_drywall"
                            )
                            
                            # Trim
                            gr.Markdown("**Trim**")
                            with gr.Group():
                                baseboard_type = gr.Dropdown(
                                    label="Baseboard Type",
                                    choices=["standard", "medium", "tall", "decorative", "none"],
                                    value="standard"
                                )
                                baseboard_material = gr.Dropdown(
                                    label="Baseboard Material",
                                    choices=["painted_wood", "stained_wood", "mdf"],
                                    value="painted_wood"
                                )
                                quarter_round_check = gr.Checkbox(label="Quarter Round", value=False)
                                quarter_round_material = gr.Dropdown(
                                    label="Quarter Round Material",
                                    choices=["painted_wood", "stained_wood", "mdf"],
                                    value="painted_wood",
                                    visible=False
                                )
                                crown_molding = gr.Dropdown(
                                    label="Crown Molding",
                                    choices=["none", "standard", "decorative", "contemporary"],
                                    value="none"
                                )
                            
                            gr.Markdown("#### Optional: Upload YAML Measurements")
                            yaml_upload = gr.Textbox(
                                label="YAML Measurement Data",
                                placeholder="Paste YAML data here (optional)...",
                                lines=5
                            )
                            
                            create_btn = gr.Button("Create Project", variant="primary", size="lg")
                            create_status = gr.Textbox(label="Status", interactive=False)
                            rooms_created = gr.Textbox(label="Rooms Created", lines=5, interactive=False)
                            
                        with gr.Column(scale=1):
                            gr.Markdown("### Select Existing Project")
                            project_dropdown = gr.Dropdown(
                                label="Select Project",
                                choices=[],
                                interactive=True
                            )
                            select_btn = gr.Button("Load Project", variant="secondary")
                            project_summary = gr.Textbox(label="Project Summary", lines=20, interactive=False)
                            refresh_btn = gr.Button("Refresh Project List", size="sm")
                
                # Work Scope Tab
                with gr.TabItem("📋 Work Scope"):
                    gr.Markdown("### Room Work Scope Configuration")
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            room_dropdown = gr.Dropdown(
                                label="Select Room",
                                choices=[],
                                interactive=True
                            )
                            load_room_btn = gr.Button("Load Room", variant="secondary")
                            
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
                                            choices=["", "hardwood", "laminate", "carpet", "tile", "vinyl", "other"],
                                            value=""
                                        )
                                        
                                        wall_finish_override = gr.Dropdown(
                                            label="Wall Finish Override", 
                                            choices=["", "painted_drywall", "textured_drywall", "tile", "wallpaper", "wood", "brick", "other"],
                                            value=""
                                        )
                                        
                                        ceiling_finish_override = gr.Dropdown(
                                            label="Ceiling Finish Override",
                                            choices=["", "painted_drywall", "textured_drywall", "tile", "wood", "drop_ceiling", "other"],
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
                                    gr.Markdown("##### Remove & Replace Items")
                                    gr.Markdown("Format: [{\"item\": \"Door\", \"quantity\": 2, \"unit\": \"ea\"}, ...]")
                                    remove_replace_json = gr.Code(
                                        label="Remove & Replace Items (JSON)",
                                        language="json",
                                        lines=5,
                                        value="[]"
                                    )
                                    
                                    gr.Markdown("##### Detach & Reset Items")
                                    gr.Markdown("Format: [{\"item\": \"Cabinet\", \"quantity\": 4, \"unit\": \"ea\"}, ...]")
                                    detach_reset_json = gr.Code(
                                        label="Detach & Reset Items (JSON)",
                                        language="json",
                                        lines=5,
                                        value="[]"
                                    )
                                    
                                    gr.Markdown("##### Protection Required")
                                    gr.Markdown("Format: [{\"item\": \"Flooring\", \"quantity\": 150, \"unit\": \"sf\"}, ...]")
                                    protection_json = gr.Code(
                                        label="Protection Items (JSON)",
                                        language="json",
                                        lines=5,
                                        value="[]"
                                    )
                                    
                                    notes = gr.Textbox(
                                        label="General Notes for Room",
                                        placeholder="Enter any specific notes or requirements...",
                                        lines=6
                                    )
                    
                    save_scope_btn = gr.Button("Save Complete Work Scope", variant="primary", size="lg")
                    save_status = gr.Textbox(label="Save Status", interactive=False)
                
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
            
            # Event Handlers
            
            # Toggle quarter round material visibility
            quarter_round_check.change(
                fn=lambda x: gr.Dropdown(visible=x),
                inputs=[quarter_round_check],
                outputs=[quarter_round_material]
            )
            
            # Project creation with defaults and YAML
            create_btn.click(
                fn=self.create_project_with_defaults,
                inputs=[
                    project_name, project_desc,
                    default_flooring, default_wall_finish, default_ceiling_finish,
                    baseboard_type, baseboard_material,
                    quarter_round_check, quarter_round_material,
                    crown_molding, yaml_upload
                ],
                outputs=[create_status, rooms_created]
            )
            
            # Refresh project list
            def refresh_projects():
                return gr.Dropdown(choices=[p[0] for p in self.get_project_list()])
            
            refresh_btn.click(
                fn=refresh_projects,
                outputs=[project_dropdown]
            )
            
            # Project selection
            select_btn.click(
                fn=self.select_project,
                inputs=[project_dropdown],
                outputs=[create_status, project_summary]
            )
            
            # Room selection for work scope
            def update_room_dropdown():
                return gr.Dropdown(choices=self.get_room_choices())
            
            load_room_btn.click(
                fn=update_room_dropdown,
                outputs=[room_dropdown]
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
                    form_data['remove_replace_json'],
                    form_data['detach_reset_json'],
                    form_data['protection_json'],
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
                    remove_replace_json, detach_reset_json, protection_json,
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
                    remove_replace_json, detach_reset_json, protection_json,
                    notes
                ],
                outputs=[save_status]
            )
            
            # Export project
            def export_project():
                status, yaml_content = self.export_project_yaml()
                return status, yaml_content or ""
            
            export_btn.click(
                fn=export_project,
                outputs=[export_status, exported_yaml]
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
        app = ConstructionEstimationAppV2()
        interface = app.create_interface()
        
        print("🏗️ Construction Estimation Manager V2 Starting...")
        print("📊 Database: SQLite")
        print("🌐 Web Interface: http://localhost:7860")
        print("✅ Ready for comprehensive project management!")
        
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=True,
            show_error=True
        )
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()