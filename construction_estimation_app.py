#!/usr/bin/env python3
"""
Construction Estimation Project Management App
Features: Project creation, YAML upload, work scope forms, database integration
"""

import gradio as gr
import sys
import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.services.project_service import get_project_service
from src.models.database import get_db_manager

class ConstructionEstimationApp:
    """Main application for construction estimation project management"""
    
    def __init__(self):
        """Initialize the application"""
        self.project_service = get_project_service()
        self.current_project_id = None
        self.current_room_id = None
        
        # Initialize database
        self.db_manager = get_db_manager()
        print("Database initialized successfully")
    
    def create_project(self, name: str, description: str) -> str:
        """Create a new project"""
        if not name.strip():
            return "Error: Project name is required"
        
        try:
            project = self.project_service.create_project(name.strip(), description.strip())
            self.current_project_id = project.id
            return f"Project '{name}' created successfully (ID: {project.id})"
        except Exception as e:
            return f"Error creating project: {str(e)}"
    
    def upload_yaml_measurements(self, yaml_content: str) -> Tuple[str, str]:
        """Upload YAML measurement data"""
        if not self.current_project_id:
            return "Error: No project selected", ""
        
        if not yaml_content.strip():
            return "Error: No YAML content provided", ""
        
        try:
            success, message, rooms = self.project_service.upload_yaml_measurements(
                self.current_project_id, yaml_content
            )
            
            if success:
                # Generate summary
                summary_lines = [f"✅ {message}\n"]
                for room in rooms:
                    summary_lines.append(f"📍 {room['floor']} - {room['room']}")
                    if room.get('dimensions'):
                        summary_lines.append(f"   Dimensions: {room['dimensions']}")
                
                return message, "\n".join(summary_lines)
            else:
                return f"Error: {message}", ""
                
        except Exception as e:
            return f"Error uploading YAML: {str(e)}", ""
    
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
            # Parse project choice (format: "Project Name")
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
                    room_choices.append(f"{floor['name']} - {room['name']}")
            
            return room_choices
            
        except Exception as e:
            print(f"Error getting room choices: {e}")
            return []
    
    def select_room_for_work_scope(self, room_choice: str) -> Dict:
        """Select room and load work scope form"""
        if not room_choice:
            return self._empty_work_scope_form()
        
        try:
            # Parse room choice (format: "floor_name - room_name")
            if " - " not in room_choice:
                return self._empty_work_scope_form()
            
            floor_name, room_name = room_choice.split(" - ", 1)
            
            # Find room ID
            project_data = self.project_service.get_project_with_rooms(self.current_project_id)
            if not project_data:
                return self._empty_work_scope_form()
            
            room_id = None
            for floor in project_data['floors']:
                if floor['name'] == floor_name:
                    for room in floor['rooms']:
                        if room['name'] == room_name:
                            room_id = room['id']
                            break
                    break
            
            if not room_id:
                return self._empty_work_scope_form()
            
            self.current_room_id = room_id
            
            # Get work scope data
            work_scope_data = self.project_service.get_room_work_scope(room_id)
            if not work_scope_data:
                return self._empty_work_scope_form()
            
            # Convert to form values
            ws = work_scope_data['work_scope']
            defaults = work_scope_data['project_defaults']
            
            return {
                'room_name': work_scope_data['room_name'],
                'use_defaults': ws['use_project_defaults'],
                'flooring_override': ws.get('flooring_override', ''),
                'wall_finish_override': ws.get('wall_finish_override', ''),
                'ceiling_finish_override': ws.get('ceiling_finish_override', ''),
                'paint_scope': ws.get('paint_scope', 'both'),
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
            lines.append(f"   • Crown Molding: {trim.get('crown_molding', 'Not set')}")
        
        return "\n".join(lines)
    
    def save_work_scope(self, use_defaults: bool, flooring: str, wall_finish: str, 
                       ceiling_finish: str, paint_scope: str, notes: str) -> str:
        """Save work scope for current room"""
        if not self.current_room_id:
            return "Error: No room selected"
        
        try:
            work_scope_data = {
                'use_project_defaults': use_defaults,
                'flooring_override': flooring.strip() if not use_defaults else None,
                'wall_finish_override': wall_finish.strip() if not use_defaults else None,
                'ceiling_finish_override': ceiling_finish.strip() if not use_defaults else None,
                'paint_scope': paint_scope,
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
        """Create the main Gradio interface"""
        
        with gr.Blocks(title="Construction Estimation Manager", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🏗️ Construction Estimation Manager")
            gr.Markdown("Project management for construction estimation with YAML measurement data and work scope forms.")
            
            with gr.Tabs():
                # Project Management Tab
                with gr.TabItem("📂 Projects"):
                    gr.Markdown("### Create New Project or Select Existing")
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("#### Create New Project")
                            project_name = gr.Textbox(label="Project Name", placeholder="Enter project name...")
                            project_desc = gr.Textbox(label="Description", placeholder="Project description (optional)", lines=3)
                            create_btn = gr.Button("Create Project", variant="primary")
                            create_status = gr.Textbox(label="Status", interactive=False)
                            
                        with gr.Column(scale=1):
                            gr.Markdown("#### Select Existing Project")
                            project_dropdown = gr.Dropdown(
                                label="Select Project",
                                choices=[],
                                interactive=True
                            )
                            select_btn = gr.Button("Load Project", variant="secondary")
                            project_summary = gr.Textbox(label="Project Summary", lines=10, interactive=False)
                            refresh_btn = gr.Button("Refresh Project List", size="sm")
                
                # YAML Upload Tab
                with gr.TabItem("📤 Upload Measurements"):
                    gr.Markdown("### Upload YAML Measurement Data")
                    gr.Markdown("Upload measurement data in the specified YAML format to create rooms automatically.")
                    
                    yaml_input = gr.Textbox(
                        label="YAML Measurement Data",
                        placeholder="Paste your YAML measurement data here...",
                        lines=15,
                        max_lines=20
                    )
                    
                    with gr.Row():
                        upload_btn = gr.Button("Upload Measurements", variant="primary", size="lg")
                        
                    upload_status = gr.Textbox(label="Upload Status", interactive=False)
                    upload_summary = gr.Textbox(label="Rooms Created", lines=8, interactive=False)
                    
                    # Example YAML
                    gr.Markdown("#### Example YAML Format")
                    example_yaml = """- floor: ground_floor
  rooms:
    - room: Bathroom
      dimensions: 7' 11" x 5' 3 3/4"
      ceiling_height: 7'
      measurements:
        volume: 267.56 ft³
        ground_surface_without_walls: 38.22 sq ft
        walls_with_opening: 185.18 sq ft"""
                    
                    gr.Code(value=example_yaml, language="yaml", label="Sample YAML Structure")
                
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
                            
                            project_defaults_display = gr.Textbox(
                                label="Project Defaults",
                                lines=8,
                                interactive=False
                            )
                            
                        with gr.Column(scale=2):
                            gr.Markdown("#### Room Configuration")
                            
                            room_name_display = gr.Textbox(label="Room Name", interactive=False)
                            
                            use_defaults_checkbox = gr.Checkbox(
                                label="Use Project Defaults for All Finishes",
                                value=True
                            )
                            
                            gr.Markdown("##### Override Finishes (only if not using defaults)")
                            
                            with gr.Group():
                                flooring_override = gr.Dropdown(
                                    label="Flooring Override",
                                    choices=["", "hardwood", "laminate", "carpet", "tile", "vinyl", "other"],
                                    value="",
                                    interactive=True
                                )
                                
                                wall_finish_override = gr.Dropdown(
                                    label="Wall Finish Override", 
                                    choices=["", "painted_drywall", "textured_drywall", "tile", "wallpaper", "wood", "brick", "other"],
                                    value="",
                                    interactive=True
                                )
                                
                                ceiling_finish_override = gr.Dropdown(
                                    label="Ceiling Finish Override",
                                    choices=["", "painted_drywall", "textured_drywall", "tile", "wood", "drop_ceiling", "other"],
                                    value="",
                                    interactive=True
                                )
                            
                            paint_scope = gr.Radio(
                                label="Paint Scope",
                                choices=["walls_only", "ceiling_only", "both", "none"],
                                value="both"
                            )
                            
                            notes = gr.Textbox(
                                label="General Notes for Room",
                                placeholder="Enter any specific notes or requirements...",
                                lines=4
                            )
                            
                            save_scope_btn = gr.Button("Save Work Scope", variant="primary", size="lg")
                            save_status = gr.Textbox(label="Save Status", interactive=False)
                
                # Export Tab
                with gr.TabItem("📤 Export"):
                    gr.Markdown("### Export Project Data")
                    
                    export_btn = gr.Button("Export Project to YAML", variant="primary", size="lg")
                    export_status = gr.Textbox(label="Export Status", interactive=False)
                    
                    exported_yaml = gr.Code(
                        label="Exported YAML",
                        language="yaml",
                        lines=20
                    )
            
            # Event Handlers
            
            # Project creation
            create_btn.click(
                fn=self.create_project,
                inputs=[project_name, project_desc],
                outputs=[create_status]
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
            
            # YAML upload
            upload_btn.click(
                fn=self.upload_yaml_measurements,
                inputs=[yaml_input],
                outputs=[upload_status, upload_summary]
            )
            
            # Room selection for work scope
            def update_room_dropdown():
                return gr.Dropdown(choices=self.get_room_choices())
            
            load_room_btn.click(
                fn=update_room_dropdown,
                outputs=[room_dropdown]
            )
            
            # Load room work scope
            def load_room_scope(room_choice):
                form_data = self.select_room_for_work_scope(room_choice)
                return (
                    form_data['room_name'],
                    form_data['use_defaults'],
                    form_data['flooring_override'],
                    form_data['wall_finish_override'],
                    form_data['ceiling_finish_override'],
                    form_data['paint_scope'],
                    form_data['notes'],
                    form_data['project_defaults_text']
                )
            
            room_dropdown.change(
                fn=load_room_scope,
                inputs=[room_dropdown],
                outputs=[
                    room_name_display, use_defaults_checkbox,
                    flooring_override, wall_finish_override, ceiling_finish_override,
                    paint_scope, notes, project_defaults_display
                ]
            )
            
            # Save work scope
            save_scope_btn.click(
                fn=self.save_work_scope,
                inputs=[
                    use_defaults_checkbox, flooring_override, wall_finish_override,
                    ceiling_finish_override, paint_scope, notes
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
        app = ConstructionEstimationApp()
        interface = app.create_interface()
        
        print("🏗️ Construction Estimation Manager Starting...")
        print("📊 Database: SQLite")
        print("🌐 Web Interface: http://localhost:7860")
        print("✅ Ready for project management!")
        
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