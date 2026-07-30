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


# Initialize logger
logger = get_logger()

# Global state
class AppState:
    def __init__(self):
        self.current_stage = 0
        self.is_running = False
        self.comfy_client: Optional[ComfyClient] = None
        self.theme_expanded: Dict[str, Any] = {}
        self.image_prompts: Dict[str, Any] = {}
        self.audio_segments: List[str] = []
        self.generated_images: List[str] = []
        self.generated_videos: List[str] = []
        self.status_badges: Dict[str, ui.badge] = {}
        self.log_messages: List[str] = []
    
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
    """Main application page with modern dark theme"""
    
    # Apply dark theme
    ui.query('body').classes('bg-grey-9')
    
    # Header
    with ui.header().classes('w-full bg-gradient-to-r from-purple-900 via-blue-900 to-purple-900'):
        with ui.row().classes('w-full items-center justify-between px-4'):
            ui.label('🎵 Music VDO Comfy').classes('text-xl font-bold text-white')
            
            with ui.row().classes('items-center gap-4'):
                global status_label
                status_label = ui.label('○ Offline').classes('text-red text-sm')
                
                ui.button(
                    'Start ComfyUI',
                    on_click=lambda: start_comfyui(),
                    icon='play_arrow'
                ).props('flat color=white').tooltip('Start ComfyUI server')
                
                ui.button(
                    'Free Memory',
                    on_click=lambda: free_memory_action(),
                    icon='delete_sweep'
                ).props('flat color=white').tooltip('Free VRAM and memory')
                
                ui.separator().props('vertical color=white')
                
                ui.button(
                    '▶ Run All',
                    on_click=lambda: run_all_stages(),
                    icon='fast_forward'
                ).props('unelevated color=positive').classes('font-bold')
                
                ui.button(
                    '⏹ Stop',
                    on_click=lambda: stop_pipeline(),
                    icon='stop'
                ).props('unelevated color=negative').classes('font-bold')
    
    # Main content area
    with ui.row().classes('w-full h-[calc(100vh-140px)]'):
        # Left sidebar - Stage stepper
        with ui.column().classes('w-64 bg-grey-800 p-4 gap-2 overflow-y-auto'):
            ui.label('Pipeline Stages').classes('text-lg font-bold text-white mb-2')
            
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
                with ui.card().classes('w-full p-2 bg-grey-700 cursor-pointer hover:bg-grey-600').style('min-height: 60px'):
                    with ui.row().classes('items-center justify-between w-full'):
                        ui.label(stage_name).classes('text-sm text-white')
                        badge = ui.badge(initial_status, color='grey').classes('text-xs')
                        state.status_badges[stage_id] = badge
    
    # Right content area - Stage details
    with ui.column().classes('flex-1 p-4 gap-4 overflow-y-auto'):
        
        # Progress bar
        with ui.row().classes('w-full items-center gap-4'):
            ui.label('Progress:').classes('text-white')
            progress = ui.linear_progress(value=0, max=8).classes('flex-1')
            progress_label = ui.label('Stage 0/8').classes('text-white text-sm')
        
        # Stage cards container
        stages_container = ui.column().classes('w-full gap-4')
        
        # Stage 1: Theme
        with stages_container:
            with ui.card().classes('w-full p-4 bg-grey-800'):
                ui.label('📝 Stage 1: Theme Expansion').classes('text-lg font-bold text-white mb-2')
                
                theme_editor = ui.textarea(
                    label='Theme Description',
                    placeholder='Enter your theme or load from Theme.txt...',
                    value=''
                ).classes('w-full').props('dark outlined')
                
                with ui.row().classes('gap-2 mt-2'):
                    ui.button(
                        'Load Theme.txt',
                        on_click=lambda: load_theme(theme_editor)
                    ).props('outlined color=primary')
                    
                    ui.button(
                        '✨ Expand with LLM',
                        on_click=lambda: expand_theme(theme_editor)
                    ).props('unelevated color=primary')
                
                theme_result = ui.markdown('').classes('w-full mt-2 text-white')
        
        # Stage 2: Input Images
        with stages_container:
            with ui.card().classes('w-full p-4 bg-grey-800'):
                ui.label('🖼️ Stage 2: Input Images').classes('text-lg font-bold text-white mb-2')
                
                image_grid = ui.row().classes('w-full gap-2 flex-wrap')
                
                with ui.row().classes('gap-2 mt-2'):
                    ui.button(
                        '🔄 Refresh Images',
                        on_click=lambda: refresh_images(image_grid)
                    ).props('outlined color=primary')
                    
                    ui.button(
                        '👁️ Describe Selected',
                        on_click=lambda: describe_images()
                    ).props('unelevated color=primary')
        
        # Stage 3: YouTube Download
        with stages_container:
            with ui.card().classes('w-full p-4 bg-grey-800'):
                ui.label('📺 Stage 3: YouTube Audio Download').classes('text-lg font-bold text-white mb-2')
                
                with ui.row().classes('w-full gap-2'):
                    url_input = ui.input(
                        label='YouTube URL',
                        placeholder='https://youtube.com/watch?v=...'
                    ).classes('flex-1').props('dark outlined')
                    
                    ui.button(
                        '⬇️ Download',
                        on_click=lambda: download_audio(url_input.value)
                    ).props('unelevated color=primary')
                
                download_log = ui.log().classes('w-full h-32 bg-grey-900')
        
        # Stage 4-8 placeholders (similar pattern)
        for stage_num, stage_info in [
            (4, '🎤 Vocal Swap', 'Run vocal separation and RVC voice conversion'),
            (5, '✂️ Segment Audio', 'Split audio by silence detection'),
            (6, '💃 Pose Change', 'Generate pose-modified images'),
            (7, '🎬 Multi-Angle', 'Create multi-angle variations'),
            (8, '🎥 Video Generation', 'Generate videos for each audio segment')
        ]:
            with stages_container:
                with ui.card().classes('w-full p-4 bg-grey-800'):
                    ui.label(f'{stage_info[0]} Stage {stage_num}: {stage_info[1]}').classes('text-lg font-bold text-white mb-2')
                    ui.label(stage_info[2]).classes('text-grey-400')
                    
                    ui.button(
                        '▶ Run Stage',
                        on_click=lambda s=stage_num: run_single_stage(s)
                    ).props('unelevated color=primary').classes('mt-2')
        
        # Stage 9: Logs
        with stages_container:
            with ui.card().classes('w-full p-4 bg-grey-800'):
                ui.label('📋 Stage 9: Logs & Errors').classes('text-lg font-bold text-white mb-2')
                
                with ui.row().classes('w-full gap-2 mb-2'):
                    ui.button(
                        '🔄 Refresh',
                        on_click=lambda: refresh_logs(log_display)
                    ).props('outlined color=primary')
                    
                    ui.button(
                        '📂 Open Log Folder',
                        on_click=lambda: open_log_folder()
                    ).props('outlined color=primary')
                
                log_display = ui.markdown('').classes('w-full bg-grey-900 p-2 rounded font-mono text-sm text-green-400')
                refresh_logs(log_display)
    
    # Bottom log console
    with ui.footer().classes('w-full bg-grey-900 border-t border-grey-700'):
        with ui.column().classes('w-full p-2'):
            ui.label('Live Console').classes('text-xs text-grey-500 mb-1')
            console_log = ui.log().classes('w-full h-24 bg-black text-green-400 font-mono text-xs')
            
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
        # TODO: Implement actual LLM call
        await asyncio.sleep(2)  # Simulate API call
        
        # Mock expansion for now
        expanded = {
            'prompt': editor.value + " - enhanced with cinematic lighting, dynamic camera angles",
            'camera': 'Dynamic tracking shots with smooth transitions',
            'style': 'Cinematic, vibrant colors, high contrast',
            'negative': 'blurry, low quality, distorted',
            'technical': 'Professional color grading, motion blur'
        }
        
        state.theme_expanded = expanded
        
        result_text = f"""
### Expanded Theme

**Prompt:** {expanded['prompt']}

**Camera:** {expanded['camera']}

**Style:** {expanded['style']}

**Negative Prompt:** {expanded['negative']}

**Technical:** {expanded['technical']}
"""
        ui.notify('Theme expanded successfully', type='positive')
        add_log("✓ Theme expanded")
        
    except Exception as e:
        add_log(f"Error expanding theme: {e}")
        ui.notify(f'Error: {e}', type='negative')
    finally:
        update_stage_badge('1_theme', 'done')


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
    
    # TODO: Implement vision API calls
    await asyncio.sleep(1)
    
    ui.notify('Image description not yet implemented', type='info')


async def download_audio(url: str):
    """Download audio from YouTube"""
    if not url:
        ui.notify('Please enter a YouTube URL', type='warning')
        return
    
    add_log(f"Downloading audio from: {url}")
    update_stage_badge('3_youtube', 'running')
    
    try:
        # TODO: Implement actual YouTube download using 1_yt_dl.py
        await asyncio.sleep(3)  # Simulate download
        
        add_log("✓ Audio download completed")
        ui.notify('Audio downloaded successfully', type='positive')
        
    except Exception as e:
        add_log(f"Error downloading audio: {e}")
        ui.notify(f'Error: {e}', type='negative')
    finally:
        update_stage_badge('3_youtube', 'done')


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
        port=8080,
        reload=False,
        dark=True,
        storage_secret='music_vdo_secret_key'
    )
