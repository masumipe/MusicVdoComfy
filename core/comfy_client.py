"""
Unified ComfyUI HTTP client for starting, queuing, polling, and managing ComfyUI server
"""
import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ComfyClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        python_exe: str = "",
        main_py: str = "",
        args: List[str] = None,
        poll_interval: float = 10.0,
        timeout: float = 1200.0,
        startup_wait: float = 60.0
    ):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.python_exe = python_exe
        self.main_py = main_py
        self.args = args or []
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.startup_wait = startup_wait
        self.server_process: Optional[subprocess.Popen] = None
        self.client_id = "music_vdo_comfy_client"
    
    @property
    def is_running(self) -> bool:
        """Check if server process is running"""
        if self.server_process is None:
            return False
        return self.server_process.poll() is None
    
    def is_online(self) -> bool:
        """Check if ComfyUI server is responding"""
        try:
            response = requests.get(f"{self.base_url}/system_stats", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def start_server(self) -> bool:
        """Start ComfyUI server as a background process"""
        if self.is_online():
            logger.info("ComfyUI server already online")
            return True
        
        if not self.python_exe or not self.main_py:
            logger.warning("Python executable or main.py not configured")
            return False
        
        cmd = [self.python_exe, self.main_py] + self.args
        
        try:
            # Start hidden on Windows
            creationflags = 0
            if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                creationflags = subprocess.CREATE_NO_WINDOW
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            
            logger.info(f"Starting ComfyUI server with PID {self.server_process.pid}")
            
            # Wait for server to be ready
            start_time = time.time()
            while time.time() - start_time < self.startup_wait:
                if self.is_online():
                    logger.info("ComfyUI server is now online")
                    return True
                time.sleep(2)
            
            logger.error("ComfyUI server failed to start within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start ComfyUI server: {e}")
            return False
    
    def stop_server(self) -> None:
        """Stop ComfyUI server"""
        if self.server_process and self.is_running:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
            logger.info("ComfyUI server stopped")
    
    def upload_file(self, file_path: str, file_type: str = "image") -> Optional[str]:
        """Upload file to ComfyUI and return server filename"""
        url = f"{self.base_url}/upload/{file_type}"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'image': (Path(file_path).name, f)}
                if file_type == "audio":
                    files = {'audio': (Path(file_path).name, f)}
                
                response = requests.post(url, files=files, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if file_type == "image":
                        return data.get('name') or data.get('filename')
                    else:
                        return data.get('filename') or data.get('name')
                else:
                    logger.error(f"Upload failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return None
        
        return None
    
    def queue(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Submit workflow to ComfyUI queue"""
        url = f"{self.base_url}/prompt"
        
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                prompt_id = data.get('prompt_id')
                logger.info(f"Queued workflow with prompt_id: {prompt_id}")
                return prompt_id
            else:
                logger.error(f"Queue failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Queue error: {e}")
            return None
        
        return None
    
    def wait(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Wait for workflow completion by polling /history"""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                response = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=10)
                
                if response.status_code == 200:
                    history = response.json()
                    
                    if prompt_id in history:
                        result = history[prompt_id]
                        
                        # Check for errors
                        if 'error' in result or 'exception' in result:
                            logger.error(f"Workflow error: {result.get('error', 'Unknown error')}")
                            return None
                        
                        # Check for outputs
                        if 'outputs' in result:
                            logger.info(f"Workflow completed successfully")
                            return result['outputs']
                
                # Also check queue status
                queue_response = requests.get(f"{self.base_url}/queue", timeout=5)
                if queue_response.status_code == 200:
                    queue_data = queue_response.json()
                    running = queue_data.get('queue_running', [])
                    pending = queue_data.get('queue_pending', [])
                    
                    # Check if our prompt is still in queue
                    our_prompt_still_there = any(
                        item.get('prompt_id') == prompt_id 
                        for item in running + pending
                    )
                    
                    if not our_prompt_still_there and prompt_id not in history:
                        logger.warning("Prompt disappeared from queue without completing")
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
            
            time.sleep(self.poll_interval)
        
        logger.error(f"Workflow timed out after {self.timeout} seconds")
        return None
    
    def fetch_outputs(self, outputs: Dict[str, Any], save_dir: Path) -> List[Path]:
        """Download output files from ComfyUI"""
        saved_files = []
        
        for node_id, node_outputs in outputs.items():
            for output_type, output_data in node_outputs.items():
                if output_type == 'images':
                    for img_info in output_data:
                        if isinstance(img_info, dict):
                            filename = img_info.get('filename')
                            subfolder = img_info.get('subfolder', '')
                            img_type = img_info.get('type', 'output')
                            
                            if filename:
                                try:
                                    url = f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                                    response = requests.get(url, timeout=30)
                                    
                                    if response.status_code == 200:
                                        save_path = save_dir / filename
                                        save_path.parent.mkdir(parents=True, exist_ok=True)
                                        
                                        with open(save_path, 'wb') as f:
                                            f.write(response.content)
                                        
                                        saved_files.append(save_path)
                                        logger.info(f"Saved image: {save_path}")
                                    
                                except Exception as e:
                                    logger.error(f"Failed to download image: {e}")
                
                elif output_type == 'gifs' or output_type == 'videos':
                    for vid_info in output_data:
                        if isinstance(vid_info, dict):
                            filename = vid_info.get('filename')
                            subfolder = vid_info.get('subfolder', '')
                            vid_type = vid_info.get('type', 'output')
                            
                            if filename:
                                try:
                                    url = f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={vid_type}"
                                    response = requests.get(url, timeout=60)
                                    
                                    if response.status_code == 200:
                                        save_path = save_dir / filename
                                        save_path.parent.mkdir(parents=True, exist_ok=True)
                                        
                                        with open(save_path, 'wb') as f:
                                            f.write(response.content)
                                        
                                        saved_files.append(save_path)
                                        logger.info(f"Saved video: {save_path}")
                                    
                                except Exception as e:
                                    logger.error(f"Failed to download video: {e}")
        
        return saved_files
    
    def free_memory(self) -> bool:
        """Tell ComfyUI to free VRAM and unload models"""
        url = f"{self.base_url}/free"
        
        try:
            response = requests.post(
                url,
                json={"unload_models": True, "free_memory": True},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("ComfyUI memory freed")
                return True
            else:
                logger.warning(f"Free memory failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Free memory error: {e}")
            return False
    
    def get_queue(self) -> Dict[str, Any]:
        """Get current queue status"""
        try:
            response = requests.get(f"{self.base_url}/queue", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Get queue error: {e}")
        return {}
    
    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get history for a specific prompt"""
        try:
            response = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Get history error: {e}")
        return {}
