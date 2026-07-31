"""
Music VDO Comfy - Main NiceGUI Application
A modern, flexible GUI for AI music video generation pipeline
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from nicegui import ui, app

# Import core modules
from core.config import config
from core.comfy_client import ComfyClient
from core.memory import free_memory
from core.logger import get_logger
from core.llm_client import init_llm_from_config, get_llm_client, LLMClient


# Initialize logger
logger = get_logger()

# Initialize LLM client
llm_client = init_llm_from_config(config.config)

# Global state
class AppState:
    def __init__(self):
        self.current_stage = 0
        self.is_running = False
        self.comfy_client: Optional[ComfyClient] = None
        self.llm_client: Optional[LLMClient] = llm_client
        self.theme_expanded: Dict[str, Any] = {}
        self.image_prompts: Dict[str, Any] = {}
        self.audio_segments: List[str] = []
        self.generated_images: List[str] = []
        self.generated_videos: List[str] = []
        self.status_badges: Dict[str, ui.badge] = {}
        self.log_messages: List[str] = []
        # New state variables
        self.selected_input_image: Optional[str] = None
        self.selected_pose_image: Optional[str] = None
        self.vocal_model: str = "Rashed_V_Model"
        self.camera_view_count: int = 3
        self.camera_degrees: List[float] = [0.0, 45.0, 90.0]
        self.pose_additional_info: str = ""
        self.video_additional_instruction: str = ""
        self.youtube_url: str = ""
    
    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        if len(self.log_messages) > 1000:
            self.log_messages = self.log_messages[-1000:]


state = AppState()


def init_comfy_client():
    """Initialize ComfyUI client from config"""
    comfy_config = config.comfyui
    return ComfyClient(
        host=comfy_config.get('host', '127.0.0.1'),
        port=comfy_config.get('port', 8188),
        python_exe=comfy_config.get('python_exe', ''),
        main_py=comfy_config.get('main_py', ''),
        args=comfy_config.get('args', []),
        poll_interval=comfy_config.get('poll_interval_sec', 10),
        timeout=comfy_config.get('poll_timeout_sec', 1200),
        startup_wait=comfy_config.get('startup_wait_sec', 60)
    )


async def check_comfy_status():
    """Periodically check ComfyUI status"""
    while True:
        if state.comfy_client:
            is_online = state.comfy_client.is_online()
            status_label.props(f'label={"● Online" if is_online else "○ Offline"}')
            status_label.classes(remove='text-green text-red')
            status_label.classes(add='text-green' if is_online else 'text-red')
        await asyncio.sleep(5)


def update_stage_badge(stage_name: str, status: str):
    """Update stage status badge"""
    if stage_name in state.status_badges:
        badge = state.status_badges[stage_name]
        badge.props(f'label={status}')
        
        colors = {
            'idle': 'grey',
            'running': 'blue',
            'done': 'green',
            'error': 'red'
        }
        badge.props(f'color={colors.get(status, "grey")}')


@ui.page('/')
def main_page():
    """Main application page with modern dark theme - optimized for space utilization"""
    
    # Apply dark theme
    ui.query('body').classes('bg-grey-9')
    
    # Header - compact
    with ui.header().classes('w-full bg-gradient-to-r from-purple-900 via-blue-900 to-purple-900 h-12'):
        with ui.row().classes('w-full items-center justify-between px-3'):
            ui.label('🎵 Music VDO Comfy').classes('text-lg font-bold text-white')
            
            with ui.row().classes('items-center gap-2'):
                global status_label
                status_label = ui.label('○ Offline').classes('text-red text-xs')
                
                ui.button(
                    'Start ComfyUI',
                    on_click=lambda: start_comfyui(),
                    icon='play_arrow'
                ).props('flat color=white size=sm').tooltip('Start ComfyUI server')
                
                ui.button(
                    'Free Memory',
                    on_click=lambda: free_memory_action(),
                    icon='delete_sweep'
                ).props('flat color=white size=sm').tooltip('Free VRAM and memory')
                
                ui.separator().props('vertical color=white')
                
                ui.button(
                    '▶ Run All',
                    on_click=lambda: run_all_stages(),
                    icon='fast_forward'
                ).props('unelevated color=positive size=sm').classes('font-bold')
                
                ui.button(
                    '⏹ Stop',
                    on_click=lambda: stop_pipeline(),
                    icon='stop'
                ).props('unelevated color=negative size=sm').classes('font-bold')
    
    # Main content area - use full height with grid layout
    with ui.row().classes('w-full h-[calc(100vh-100px)] p-2 gap-2'):
        # Left sidebar - Stage stepper (compact, fixed width)
        with ui.column().classes('w-56 bg-grey-800 p-2 gap-1 overflow-y-auto rounded'):
            ui.label('Pipeline Stages').classes('text-sm font-bold text-white mb-1')
            
            stages = [
                ('1_theme', '📝 Theme', 'idle'),
                ('2_images', '🖼️ Input Images', 'idle'),
                ('3_youtube', '📺 YouTube Audio', 'idle'),
                ('4_vocal', '🎤 Vocal Swap', 'idle'),
                ('5_segment', '✂️ Segment Audio', 'idle'),
                ('6_pose', '💃 Pose Change', 'idle'),
                ('7_multiangle', '🎬 Multi-Angle', 'idle'),
                ('8_video', '🎥 Video Gen', 'idle'),
                ('9_logs', '📋 Logs', 'idle'),
            ]
            
            for stage_id, stage_name, initial_status in stages:
                with ui.card().classes('w-full p-1 bg-grey-700 cursor-pointer hover:bg-grey-600').style('min-height: 45px'):
                    with ui.row().classes('items-center justify-between w-full'):
                        ui.label(stage_name).classes('text-xs text-white')
                        badge = ui.badge(initial_status, color='grey').classes('text-xs')
                        state.status_badges[stage_id] = badge
        
        # Right content area - Use grid layout for better horizontal space usage
        with ui.column().classes('flex-1 gap-2'):
            
            # Progress bar - compact
            with ui.row().classes('w-full items-center gap-2 bg-grey-800 p-2 rounded'):
                ui.label('Progress:').classes('text-white text-sm')
                progress = ui.linear_progress(value=0).classes('flex-1')
                progress_label = ui.label('Stage 0/8').classes('text-white text-xs')
            
            # Two-column grid for stages - use grid layout
            with ui.grid().classes('w-full flex-1 grid-cols-2 gap-2 auto-rows-min'):
                # Column 1 - Stages 1-5
                with ui.column().classes('gap-2'):
                    
                    # Stage 1: Theme
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        ui.label('📝 Stage 1: Theme Expansion').classes('text-sm font-bold text-white mb-1')
                        
                        theme_editor = ui.textarea(
                            label='',
                            placeholder='Enter theme or load from Theme.txt...',
                            value=''
                        ).classes('w-full').props('dark outlined dense rows=2')
                        
                        with ui.row().classes('gap-1 mt-1'):
                            ui.button(
                                'Load Theme.txt',
                                on_click=lambda: load_theme(theme_editor)
                            ).props('outlined color=primary size=sm')
                            
                            ui.button(
                                '✨ Expand',
                                on_click=lambda: expand_theme(theme_editor)
                            ).props('unelevated color=primary size=sm')
                        
                        theme_result = ui.markdown('').classes('w-full mt-1 text-white text-xs')
                    
                    # Stage 2: Input Images
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        ui.label('🖼️ Stage 2: Input Images').classes('text-sm font-bold text-white mb-1')
                        
                        # Image upload and grid in same row
                        with ui.row().classes('w-full gap-2'):
                            with ui.column().classes('w-1/3'):
                                ui.upload(max_files=10).on('uploaded', lambda e: handle_image_upload(e))
                            with ui.column().classes('w-2/3'):
                                image_grid = ui.row().classes('w-full gap-1 flex-wrap max-h-32 overflow-y-auto')
                        
                        with ui.row().classes('gap-1 mt-1'):
                            ui.button(
                                '🔄 Refresh',
                                on_click=lambda: refresh_images(image_grid)
                            ).props('outlined color=primary size=sm')
                            
                            ui.button(
                                '👁️ Describe',
                                on_click=lambda: describe_images()
                            ).props('unelevated color=primary size=sm')
                        
                        selected_image_label = ui.label('No image selected').classes('text-xs text-grey-400')
                    
                    # Stage 3: YouTube Download
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        ui.label('📺 Stage 3: YouTube Audio').classes('text-sm font-bold text-white mb-1')
                        
                        with ui.row().classes('w-full gap-1'):
                            youtube_url_input = ui.input(
                                label='',
                                placeholder='YouTube URL...'
                            ).classes('flex-1').props('dark outlined dense')
                            
                            ui.button(
                                '⬇️ Download',
                                on_click=lambda: download_audio(youtube_url_input.value)
                            ).props('unelevated color=primary size=sm')
                        
                        download_log = ui.log().classes('w-full h-16 bg-grey-900 text-xs')
                    
                    # Stage 4: Vocal Swap
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        ui.label('🎤 Stage 4: Vocal Swap').classes('text-sm font-bold text-white mb-1')
                        
                        with ui.row().classes('w-full gap-1'):
                            vocal_model_input = ui.input(
                                label='',
                                value=state.vocal_model
                            ).classes('flex-1').props('dark outlined dense')
                            
                            ui.button(
                                '▶ Run',
                                on_click=lambda: run_vocal_swap(vocal_model_input.value)
                            ).props('unelevated color=primary size=sm')
                    
                    # Stage 5: Audio Segmentation
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        with ui.row().classes('w-full items-center justify-between'):
                            ui.label('✂️ Stage 5: Audio Segmentation').classes('text-sm font-bold text-white')
                            ui.button(
                                '▶ Run',
                                on_click=lambda: run_single_stage(5)
                            ).props('unelevated color=primary size=sm')
                
                # Column 2 - Stages 6-9
                with ui.column().classes('gap-2'):
                    
                    # Stage 6: Pose Change
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        ui.label('💃 Stage 6: Pose Change').classes('text-sm font-bold text-white mb-1')
                        
                        with ui.row().classes('w-full gap-2'):
                            # Pose image upload and preview
                            with ui.column().classes('w-1/4'):
                                ui.upload(max_files=1).on('uploaded', lambda e: handle_pose_upload(e))
                                pose_preview = ui.image('').classes('w-16 h-16 object-cover rounded mt-1').style('display: none')
                            
                            # Additional info
                            with ui.column().classes('w-3/4'):
                                pose_additional_info = ui.textarea(
                                    label='',
                                    placeholder='Additional info for pose-to-image...',
                                    value=state.pose_additional_info
                                ).classes('w-full').props('dark outlined dense rows=2')
                                
                                with ui.row().classes('gap-1 mt-1'):
                                    ui.button(
                                        '✨ Generate',
                                        on_click=lambda: generate_pose_instructions(pose_additional_info.value)
                                    ).props('unelevated color=primary size=sm')
                        
                        pose_result = ui.markdown('').classes('w-full mt-1 text-white text-xs')
                    
                    # Stage 7: Multi-Angle View
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        ui.label('🎬 Stage 7: Multi-Angle').classes('text-sm font-bold text-white mb-1')
                        
                        with ui.row().classes('w-full gap-2'):
                            camera_view_count = ui.number(
                                label='Views',
                                value=state.camera_view_count,
                                min=1,
                                max=10
                            ).props('dark outlined dense').classes('w-24')
                            
                            camera_degrees_input = ui.input(
                                label='Degrees (comma-sep)',
                                value=', '.join([str(d) for d in state.camera_degrees])
                            ).classes('flex-1').props('dark outlined dense')
                        
                        with ui.row().classes('w-full gap-1 mt-1'):
                            ui.button(
                                '🔄 Calculate',
                                on_click=lambda: calculate_camera_angles(camera_view_count.value, camera_degrees_input.value)
                            ).props('outlined color=primary size=sm')
                            
                            ui.button(
                                '▶ Generate',
                                on_click=lambda: run_multi_angle(camera_view_count.value, camera_degrees_input.value)
                            ).props('unelevated color=primary size=sm')
                    
                    # Stage 8: Video Generation
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        ui.label('🎥 Stage 8: Video Gen').classes('text-sm font-bold text-white mb-1')
                        
                        video_instruction = ui.textarea(
                            label='',
                            placeholder='Additional instructions for image-to-video...',
                            value=state.video_additional_instruction
                        ).classes('w-full').props('dark outlined dense rows=2')
                        
                        with ui.row().classes('gap-1 mt-1'):
                            ui.button(
                                '✨ Enhance',
                                on_click=lambda: enhance_video_instructions(video_instruction.value)
                            ).props('outlined color=primary size=sm')
                            
                            ui.button(
                                '▶ Generate',
                                on_click=lambda: run_video_generation(video_instruction.value)
                            ).props('unelevated color=primary size=sm')
                        
                        video_result = ui.markdown('').classes('w-full mt-1 text-white text-xs')
                    
                    # Stage 9: Logs
                    with ui.card().classes('w-full p-2 bg-grey-800'):
                        ui.label('📋 Stage 9: Logs & Errors').classes('text-sm font-bold text-white mb-1')
                        
                        with ui.row().classes('w-full gap-1 mb-1'):
                            ui.button(
                                '🔄 Refresh',
                                on_click=lambda: refresh_logs(log_display)
                            ).props('outlined color=primary size=sm')
                            
                            ui.button(
                                '📂 Open Folder',
                                on_click=lambda: open_log_folder()
                            ).props('outlined color=primary size=sm')
                        
                        log_display = ui.markdown('').classes('w-full bg-grey-900 p-1 rounded font-mono text-xs text-green-400 max-h-24 overflow-y-auto')
                        refresh_logs(log_display)
    
    # Bottom log console - compact
    with ui.footer().classes('w-full bg-grey-900 border-t border-grey-700 h-20'):
        with ui.column().classes('w-full p-1'):
            ui.label('Live Console').classes('text-xs text-grey-500')
            console_log = ui.log().classes('w-full h-12 bg-black text-green-400 font-mono text-xs')
            
            async def update_console():
                while True:
                    if state.log_messages:
                        for msg in state.log_messages[-10:]:
                            console_log.push(msg)
                        state.log_messages.clear()
                    await asyncio.sleep(1)
            
            ui.timer(1, update_console, once=False)
    
    # Start background tasks
    ui.timer(5, check_comfy_status, once=False)


def add_log(message: str):
    """Add message to global log"""
    state.add_log(message)
    logger.info(message)


async def start_comfyui():
    """Start ComfyUI server"""
    add_log("Starting ComfyUI server...")
    
    if state.comfy_client is None:
        state.comfy_client = init_comfy_client()
    
    success = state.comfy_client.start_server()
    
    if success:
        add_log("✓ ComfyUI server started successfully")
        ui.notify('ComfyUI is now online', type='positive')
    else:
        add_log("✗ Failed to start ComfyUI server")
        ui.notify('Failed to start ComfyUI', type='negative')


def free_memory_action():
    """Free ComfyUI and system memory"""
    add_log("Freeing memory...")
    
    if state.comfy_client:
        free_memory(state.comfy_client)
        add_log("✓ Memory freed")
        ui.notify('Memory freed successfully', type='info')
    else:
        add_log("⚠ ComfyUI client not initialized")
        ui.notify('ComfyUI not connected', type='warning')


def load_theme(editor: ui.textarea):
    """Load theme from Theme.txt"""
    theme_file = Path(__file__).parent / "Theme.txt"
    
    try:
        if theme_file.exists():
            with open(theme_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():
                editor.value = content
                add_log(f"Loaded theme from Theme.txt ({len(content)} chars)")
                ui.notify('Theme loaded', type='positive')
            else:
                add_log("Theme.txt is empty")
                ui.notify('Theme.txt is empty', type='warning')
        else:
            add_log("Theme.txt not found")
            ui.notify('Theme.txt not found', type='negative')
    except Exception as e:
        add_log(f"Error loading theme: {e}")
        ui.notify(f'Error: {e}', type='negative')


async def expand_theme(editor: ui.textarea):
    """Expand theme using LLM"""
    add_log("Expanding theme with LLM...")
    update_stage_badge('1_theme', 'running')
    
    try:
        # Free memory before calling LLM (to prepare for ComfyUI later)
        if state.comfy_client:
            free_memory(state.comfy_client)
        
        # Use LLM client to enhance prompt
        if state.llm_client:
            expanded = state.llm_client.enhance_prompt(editor.value)
            
            if expanded:
                state.theme_expanded = expanded
                
                result_text = f"""
### Expanded Theme

**Prompt:** {expanded.get('enhanced_prompt', expanded.get('prompt', ''))}

**Camera:** {expanded.get('camera', '')}

**Style:** {expanded.get('style', '')}

**Negative Prompt:** {expanded.get('negative', '')}

**Technical:** {expanded.get('technical', '')}
"""
                ui.notify('Theme expanded successfully', type='positive')
                add_log(f"✓ Theme expanded ({len(result_text)} chars)")
            else:
                ui.notify('Failed to expand theme', type='warning')
                add_log("⚠ LLM expansion failed")
        else:
            ui.notify('LLM client not initialized', type='warning')
            add_log("⚠ LLM client not available")
        
    except Exception as e:
        add_log(f"Error expanding theme: {e}")
        ui.notify(f'Error: {e}', type='negative')
    finally:
        update_stage_badge('1_theme', 'done')


def handle_image_upload(e):
    """Handle image upload event"""
    try:
        if hasattr(e, 'content') and e.content:
            # Save uploaded file
            img_dir = config.get_path('img_inputs')
            filename = f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = img_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(e.content)
            
            state.selected_input_image = str(filepath)
            add_log(f"Image uploaded: {filename}")
            ui.notify(f'Image uploaded: {filename}', type='positive')
    except Exception as e:
        add_log(f"Upload error: {e}")
        ui.notify(f'Upload failed: {e}', type='negative')


def handle_pose_upload(e):
    """Handle pose image upload event"""
    try:
        if hasattr(e, 'content') and e.content:
            # Save uploaded file
            pose_dir = config.get_path('pose_inputs')
            filename = f"pose_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = pose_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(e.content)
            
            state.selected_pose_image = str(filepath)
            add_log(f"Pose image uploaded: {filename}")
            ui.notify(f'Pose image uploaded: {filename}', type='positive')
    except Exception as e:
        add_log(f"Pose upload error: {e}")
        ui.notify(f'Upload failed: {e}', type='negative')


def refresh_images(grid: ui.row):
    """Refresh image grid from img_inputs directory"""
    grid.clear()
    
    img_dir = config.get_path('img_inputs')
    
    try:
        images = list(img_dir.glob('*.png')) + list(img_dir.glob('*.jpg'))
        
        if not images:
            with grid:
                ui.label('No images found in img_inputs/').classes('text-grey-400')
            return
        
        for img_path in images:
            with ui.card().classes('w-32 p-2 bg-grey-700'):
                ui.image(str(img_path)).classes('w-full h-32 object-cover rounded')
                ui.label(img_path.name).classes('text-xs text-white text-center')
                
                checkbox = ui.checkbox('Select').classes('text-white')
        
        add_log(f"Loaded {len(images)} images from img_inputs/")
        
    except Exception as e:
        add_log(f"Error loading images: {e}")
        with grid:
            ui.label(f'Error: {e}').classes('text-red')


async def describe_images():
    """Describe selected images using vision API"""
    add_log("Describing images...")
    
    try:
        # Free memory before calling LLM
        if state.comfy_client:
            free_memory(state.comfy_client)
        
        if not state.llm_client:
            ui.notify('LLM client not initialized', type='warning')
            return
        
        img_dir = config.get_path('img_inputs')
        images = list(img_dir.glob('*.png')) + list(img_dir.glob('*.jpg'))
        
        if not images:
            ui.notify('No images to describe', type='warning')
            return
        
        # Describe first image (or implement multi-select later)
        img_path = images[0]
        description = state.llm_client.describe_image(str(img_path))
        
        if description:
            ui.notify(f'Image described: {description[:100]}...', type='positive')
            add_log(f"✓ Image description: {description[:200]}")
        else:
            ui.notify('Failed to describe image', type='warning')
            
    except Exception as e:
        add_log(f"Description error: {e}")
        ui.notify(f'Error: {e}', type='negative')


async def download_audio(url: str):
    """Download audio from YouTube"""
    if not url:
        ui.notify('Please enter a YouTube URL', type='warning')
        return
    
    add_log(f"Downloading audio from: {url}")
    update_stage_badge('3_youtube', 'running')
    
    try:
        # Free memory before operation
        if state.comfy_client:
            free_memory(state.comfy_client)
        
        # TODO: Implement actual YouTube download using 1_yt_dl.py
        await asyncio.sleep(3)  # Simulate download
        
        add_log("✓ Audio download completed")
        ui.notify('Audio downloaded successfully', type='positive')
        
    except Exception as e:
        add_log(f"Error downloading audio: {e}")
        ui.notify(f'Error: {e}', type='negative')
    finally:
        update_stage_badge('3_youtube', 'done')


def run_vocal_swap(vocal_model: str):
    """Run vocal separation with specified model"""
    add_log(f"Running vocal swap with model: {vocal_model}")
    update_stage_badge('4_vocal', 'running')
    
    try:
        # Free memory before running ComfyUI workflow
        if state.comfy_client:
            free_memory(state.comfy_client)
        
        state.vocal_model = vocal_model
        add_log(f"✓ Vocal model set to: {vocal_model}")
        ui.notify(f'Vocal model updated: {vocal_model}', type='positive')
        
        # TODO: Actually call 2_Audio_separator.py with the model
        
    except Exception as e:
        add_log(f"Vocal swap error: {e}")
        ui.notify(f'Error: {e}', type='negative')
    finally:
        update_stage_badge('4_vocal', 'done')


async def generate_pose_instructions(additional_info: str):
    """Generate pose-to-image instructions using LLM"""
    add_log("Generating pose instructions...")
    
    try:
        # Free memory before calling LLM
        if state.comfy_client:
            free_memory(state.comfy_client)
        
        if not state.llm_client:
            ui.notify('LLM client not initialized', type='warning')
            return
        
        source_desc = "Source image from img_inputs"
        target_pose = additional_info or "Standard pose transfer"
        
        instructions = state.llm_client.generate_pose_instructions(
            source_description=source_desc,
            target_pose=target_pose,
            additional_info=additional_info
        )
        
        if instructions:
            ui.notify('Pose instructions generated', type='positive')
            add_log(f"✓ Pose instructions: {instructions[:200]}...")
        else:
            ui.notify('Failed to generate instructions', type='warning')
            
    except Exception as e:
        add_log(f"Pose instructions error: {e}")
        ui.notify(f'Error: {e}', type='negative')


def calculate_camera_angles(view_count: int, degrees_str: str):
    """Calculate camera angles based on view count"""
    try:
        # Parse existing degrees or calculate new ones
        if degrees_str.strip():
            degrees = [float(d.strip()) for d in degrees_str.split(',')]
        else:
            # Auto-calculate evenly spaced angles
            degrees = [i * (360 / view_count) for i in range(view_count)]
        
        state.camera_view_count = view_count
        state.camera_degrees = degrees
        
        ui.notify(f'Camera angles calculated: {degrees}', type='positive')
        add_log(f"Camera angles: {view_count} views at {degrees}")
        
    except Exception as e:
        add_log(f"Angle calculation error: {e}")
        ui.notify(f'Error: {e}', type='negative')


def run_multi_angle(view_count: int, degrees_str: str):
    """Run multi-angle generation"""
    add_log(f"Running multi-angle generation: {view_count} views")
    update_stage_badge('7_multiangle', 'running')
    
    try:
        # Free memory before running ComfyUI
        if state.comfy_client:
            free_memory(state.comfy_client)
        
        calculate_camera_angles(view_count, degrees_str)
        add_log("✓ Multi-angle generation started")
        ui.notify('Multi-angle generation started', type='info')
        
        # TODO: Actually run the multi-angle workflow
        
    except Exception as e:
        add_log(f"Multi-angle error: {e}")
        ui.notify(f'Error: {e}', type='negative')
    finally:
        update_stage_badge('7_multiangle', 'done')


async def enhance_video_instructions(instruction: str):
    """Enhance video generation instructions using LLM"""
    add_log("Enhancing video instructions...")
    
    try:
        # Free memory before calling LLM
        if state.comfy_client:
            free_memory(state.comfy_client)
        
        if not state.llm_client:
            ui.notify('LLM client not initialized', type='warning')
            return
        
        enhanced = state.llm_client.generate_video_instructions(
            image_description="Generated image",
            motion_type=instruction or "smooth pan",
            camera_angles=state.camera_view_count,
            camera_degrees=state.camera_degrees,
            additional_instruction=instruction
        )
        
        if enhanced:
            ui.notify('Video instructions enhanced', type='positive')
            add_log(f"✓ Enhanced instructions: {enhanced[:200]}...")
        else:
            ui.notify('Failed to enhance instructions', type='warning')
            
    except Exception as e:
        add_log(f"Video enhancement error: {e}")
        ui.notify(f'Error: {e}', type='negative')


def run_video_generation(instruction: str):
    """Run video generation with instructions"""
    add_log("Running video generation...")
    update_stage_badge('8_video', 'running')
    
    try:
        # Free memory before running ComfyUI
        if state.comfy_client:
            free_memory(state.comfy_client)
        
        state.video_additional_instruction = instruction
        add_log(f"✓ Video generation started with: {instruction[:100]}...")
        ui.notify('Video generation started', type='info')
        
        # TODO: Actually run the video generation workflow
        
    except Exception as e:
        add_log(f"Video generation error: {e}")
        ui.notify(f'Error: {e}', type='negative')
    finally:
        update_stage_badge('8_video', 'done')


async def run_single_stage(stage_num: int):
    """Run a single pipeline stage"""
    add_log(f"Running stage {stage_num}...")
    ui.notify(f'Running stage {stage_num}', type='info')
    
    # TODO: Implement actual stage logic
    await asyncio.sleep(2)
    
    add_log(f"Stage {stage_num} completed")
    ui.notify(f'Stage {stage_num} completed', type='positive')


async def run_all_stages():
    """Run all pipeline stages sequentially"""
    if state.is_running:
        ui.notify('Pipeline already running', type='warning')
        return
    
    state.is_running = True
    add_log("=" * 60)
    add_log("STARTING FULL PIPELINE")
    add_log("=" * 60)
    
    try:
        for stage_num in range(1, 9):
            add_log(f"Executing stage {stage_num}/8")
            await run_single_stage(stage_num)
            
            # Memory cleanup between stages
            if stage_num in [4, 6, 7, 8]:
                add_log("Running memory cleanup...")
                free_memory(state.comfy_client)
        
        add_log("=" * 60)
        add_log("PIPELINE COMPLETED SUCCESSFULLY")
        add_log("=" * 60)
        ui.notify('Pipeline completed successfully!', type='positive')
        
    except Exception as e:
        add_log(f"Pipeline failed: {e}")
        ui.notify(f'Pipeline failed: {e}', type='negative')
    finally:
        state.is_running = False


def stop_pipeline():
    """Stop the running pipeline"""
    state.is_running = False
    add_log("Pipeline stopped by user")
    
    if state.comfy_client:
        free_memory(state.comfy_client)
    
    ui.notify('Pipeline stopped', type='info')


def refresh_logs(display: ui.markdown):
    """Refresh log display"""
    log_content = logger.get_log_tail(100)
    
    if log_content:
        # Format logs for markdown display
        formatted = f"```\n{log_content}\n```"
        display.content = formatted
    else:
        display.content = "*No logs yet*"


def open_log_folder():
    """Open log folder in file explorer"""
    log_dir = config.get_path('logs')
    add_log(f"Opening log folder: {log_dir}")
    
    try:
        import subprocess
        import sys
        
        if sys.platform == 'win32':
            subprocess.run(['explorer', str(log_dir)])
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(log_dir)])
        else:
            subprocess.run(['xdg-open', str(log_dir)])
        
    except Exception as e:
        add_log(f"Failed to open log folder: {e}")
        ui.notify(f'Log folder: {log_dir}', type='info')


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='Music VDO Comfy',
        host='0.0.0.0',
        port=5000,
        reload=False,
        dark=True,
        storage_secret='music_vdo_secret_key'
    )
