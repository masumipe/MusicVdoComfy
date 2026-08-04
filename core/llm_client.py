"""
LLM Client for prompt enhancement, image description, image generation, and video generation
Supports Ollama (qwen3.5:9b), OpenAI-compatible APIs, and cloud providers
Including Alibaba Cloud Model Studio (Qwen3.5-397B-A17B, Wanx, Wan)
"""
import json
import logging
import os
import time
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
import tempfile
import shutil

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client supporting multiple providers"""
    
    def __init__(
        self,
        provider: str = "ollama",
        base_url: str = "http://localhost:11434",
        api_key: str = "",
        model: str = "qwen3.5:9b",
        vision_model: str = "qwen3.5:9b",
        image_model: str = "wanx2.1-turbo-i2v",
        video_model: str = "wan2.1-t2v-14b",
        max_tokens: int = 800,
        temperature: float = 0.7,
        timeout: int = 120
    ):
        self.provider = provider
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.vision_model = vision_model
        self.image_model = image_model
        self.video_model = video_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.temp_dir = Path(tempfile.mkdtemp(prefix="music_vdo_api_"))
        
        # Handle API key with environment variable support
        self.api_key = self._resolve_api_key(api_key, provider)
        
        # Headers for API calls
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def _resolve_api_key(self, api_key: str, provider: str) -> str:
        """
        Resolve API key from provided value or environment variable
        
        For Alibaba Cloud provider, checks ALIBABA_API_KEY environment variable
        """
        # If API key is provided directly, use it
        if api_key and api_key.strip():
            return api_key.strip()
        
        # Check for provider-specific environment variables
        provider_lower = provider.lower()
        
        if provider_lower == "alibaba":
            env_key = os.environ.get("ALIBABA_API_KEY", "").strip()
            if env_key:
                logger.info("API key loaded from ALIBABA_API_KEY environment variable")
                return env_key
        
        # Add support for other providers here if needed
        # elif provider_lower == "openai":
        #     return os.environ.get("OPENAI_API_KEY", "").strip()
        
        return ""
    
    def _get_image_generation_url(self) -> str:
        """Get appropriate image generation API URL"""
        if self._is_ollama():
            return f"{self.base_url}/v1/images/generations"
        else:
            # Alibaba Cloud Wanx image generation endpoint
            return f"{self.base_url}/wanx/v1/image-generation"
    
    def _get_video_generation_url(self) -> str:
        """Get appropriate video generation API URL"""
        if self._is_ollama():
            return f"{self.base_url}/v1/video/generations"
        else:
            # Alibaba Cloud Wan video generation endpoint
            return f"{self.base_url}/wan/v1/video-generation"
    
    def _is_ollama(self) -> bool:
        """Check if using Ollama provider"""
        return self.provider.lower() == "ollama"
    
    def _get_chat_url(self) -> str:
        """Get appropriate chat completion URL"""
        if self._is_ollama():
            return f"{self.base_url}/v1/chat/completions"
        else:
            return f"{self.base_url}/chat/completions"
    
    def _get_vision_url(self) -> str:
        """Get appropriate vision API URL"""
        if self._is_ollama():
            return f"{self.base_url}/v1/chat/completions"
        else:
            return f"{self.base_url}/chat/completions"
    
    def cleanup_temp(self):
        """Clean up temporary directory"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            self.temp_dir = Path(tempfile.mkdtemp(prefix="music_vdo_api_"))
        except Exception as e:
            logger.error(f"Failed to cleanup temp dir: {e}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Send chat completion request
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Override model name
            system_prompt: Optional system prompt to prepend
            
        Returns:
            Response text or None on error
        """
        url = self._get_chat_url()
        use_model = model or self.model
        
        # Build messages with optional system prompt
        final_messages = []
        if system_prompt:
            final_messages.append({"role": "system", "content": system_prompt})
        final_messages.extend(messages)
        
        payload = {
            "model": use_model,
            "messages": final_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info(f"LLM response received ({len(content)} chars)")
                return content
            else:
                logger.error(f"LLM API error ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return None
    
    def enhance_prompt(self, theme: str, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Enhance a theme/prompt using LLM
        
        Args:
            theme: Base theme description
            context: Optional additional context
            
        Returns:
            Dict with enhanced prompt, camera, style, negative, technical details
        """
        system_prompt = """You are an expert AI video generation assistant. 
        Your task is to expand brief themes into detailed, production-ready prompts for music video generation.
        Always provide structured output with the following sections:
        - Enhanced Prompt: Detailed visual description
        - Camera Directions: Camera movements, angles, transitions
        - Style & Atmosphere: Lighting, color grading, mood
        - Negative Prompt: What to avoid
        - Technical Notes: Frame rate, resolution, special techniques"""
        
        user_message = f"Expand this theme for a music video:\n\n{theme}"
        if context:
            user_message += f"\n\nAdditional context: {context}"
        
        response = self.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt
        )
        
        if not response:
            return None
        
        # Parse response into structured format
        result = {
            "original": theme,
            "enhanced_prompt": response,
            "camera": "Dynamic camera movements with smooth transitions",
            "style": "Cinematic quality with professional lighting",
            "negative": "blurry, low quality, distorted, deformed",
            "technical": "High resolution, 25fps, professional color grading"
        }
        
        # Try to extract sections from response
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            if 'prompt' in line_lower and ':' in line:
                current_section = 'enhanced_prompt'
            elif 'camera' in line_lower and ':' in line:
                current_section = 'camera'
            elif 'style' in line_lower and ':' in line:
                current_section = 'style'
            elif 'negative' in line_lower and ':' in line:
                current_section = 'negative'
            elif 'technical' in line_lower and ':' in line:
                current_section = 'technical'
            elif current_section:
                result[current_section] = result.get(current_section, '') + ' ' + line.strip()
        
        logger.info("Prompt enhancement completed")
        return result
    
    def describe_image(self, image_path: str, question: Optional[str] = None) -> Optional[str]:
        """
        Describe an image using vision-capable model
        
        Args:
            image_path: Path to image file
            question: Optional specific question about the image
            
        Returns:
            Image description or answer to question
        """
        image_file = Path(image_path)
        if not image_file.exists():
            logger.error(f"Image not found: {image_path}")
            return None
        
        # Encode image to base64
        import base64
        try:
            with open(image_file, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Determine MIME type
            mime_type = "image/jpeg" if image_file.suffix.lower() in ['.jpg', '.jpeg'] else "image/png"
            
            # Build vision request
            question_text = question or "Describe this image in detail, focusing on visual elements, composition, lighting, and subject matter."
            
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    }
                ]
            }]
            
            url = self._get_vision_url()
            payload = {
                "model": self.vision_model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info(f"Image description received ({len(content)} chars)")
                return content
            else:
                logger.error(f"Vision API error ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Image description error: {e}")
            return None
    
    def suggest_api_changes(
        self,
        current_workflow: Dict[str, Any],
        goal: str,
        constraints: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest changes to ComfyUI workflow JSON based on goals
        
        Args:
            current_workflow: Current workflow dictionary
            goal: What the user wants to achieve
            constraints: Optional constraints or requirements
            
        Returns:
            Suggested workflow modifications
        """
        system_prompt = """You are a ComfyUI workflow optimization expert.
        Analyze the provided workflow JSON and suggest improvements to achieve the stated goal.
        Return your suggestions as a JSON object with:
        - "changes": List of specific node modifications
        - "additions": New nodes to add
        - "removals": Nodes to remove
        - "explanation": Brief explanation of changes"""
        
        workflow_json = json.dumps(current_workflow, indent=2)[:8000]  # Truncate if too long
        
        user_message = f"""Current workflow:
{workflow_json}

Goal: {goal}"""
        
        if constraints:
            user_message += f"\n\nConstraints: {constraints}"
        
        response = self.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt
        )
        
        if not response:
            return None
        
        # Try to parse response as JSON
        try:
            # Look for JSON block in response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        
        # Return as text suggestion
        return {
            "suggestions": response,
            "explanation": "Manual review recommended"
        }
    
    def modify_workflow_in_temp(
        self,
        workflow_path: str,
        modifications: Dict[str, Any]
    ) -> Optional[Path]:
        """
        Apply modifications to workflow JSON and save to temp folder
        
        Args:
            workflow_path: Path to original workflow JSON
            modifications: Dictionary of modifications to apply
            
        Returns:
            Path to modified workflow in temp directory
        """
        try:
            # Load original workflow
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            # Apply modifications (deep merge)
            def deep_merge(base, updates):
                result = base.copy()
                for key, value in updates.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result
            
            modified_workflow = deep_merge(workflow, modifications)
            
            # Save to temp directory
            original_name = Path(workflow_path).name
            temp_path = self.temp_dir / f"modified_{original_name}"
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(modified_workflow, f, indent=2)
            
            logger.info(f"Modified workflow saved to: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to modify workflow: {e}")
            return None
    
    def generate_pose_instructions(
        self,
        source_description: str,
        target_pose: str,
        additional_info: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate detailed instructions for pose-to-image transformation
        
        Args:
            source_description: Description of source image
            target_pose: Target pose description
            additional_info: Additional user instructions
            
        Returns:
            Detailed generation instructions
        """
        system_prompt = """You are an expert in AI image generation and pose transfer.
        Provide detailed technical instructions for transforming a source image to match a target pose.
        Include guidance on:
        - Pose alignment and proportions
        - Lighting consistency
        - Background handling
        - Artifact prevention"""
        
        user_message = f"""Source image: {source_description}
Target pose: {target_pose}"""
        
        if additional_info:
            user_message += f"\n\nAdditional requirements: {additional_info}"
        
        response = self.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt
        )
        
        if response:
            logger.info("Pose instructions generated")
        return response
    
    def generate_video_instructions(
        self,
        image_description: str,
        motion_type: str,
        camera_angles: int,
        camera_degrees: List[float],
        additional_instruction: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate instructions for image-to-video generation
        
        Args:
            image_description: Description of the source image
            motion_type: Type of motion (pan, zoom, rotate, etc.)
            camera_angles: Number of camera views
            camera_degrees: List of camera angle degrees
            additional_instruction: Additional user instructions
            
        Returns:
            Detailed video generation instructions
        """
        system_prompt = """You are an expert in AI video generation from images.
        Provide detailed instructions for creating smooth, cinematic videos from static images.
        Include guidance on:
        - Camera movement paths
        - Motion smoothing
        - Temporal consistency
        - Frame interpolation
        - Artifact prevention"""
        
        angles_str = ", ".join([f"{d}°" for d in camera_degrees])
        user_message = f"""Image: {image_description}
Motion type: {motion_type}
Camera views: {camera_angles}
Camera angles: {angles_str}"""
        
        if additional_instruction:
            user_message += f"\n\nAdditional instructions: {additional_instruction}"
        
        response = self.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt
        )
        
        if response:
            logger.info("Video instructions generated")
        return response
    
    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: str = "1024x1024",
        output_path: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Generate image using Alibaba Cloud Wanx or other providers
        
        Args:
            prompt: Text prompt for image generation
            negative_prompt: What to avoid in the generated image
            size: Image size (e.g., "1024x1024", "720x1280")
            output_path: Optional path to save the generated image
            **kwargs: Additional parameters for specific providers
            
        Returns:
            Dict with 'image_path', 'prompt', 'model' keys or None on error
        """
        if not self.api_key and not self._is_ollama():
            logger.error("API key required for image generation")
            return None
        
        url = self._get_image_generation_url()
        
        # Parse size
        width, height = map(int, size.split('x'))
        
        # Build request payload based on provider
        if self._is_ollama():
            payload = {
                "model": self.image_model,
                "prompt": prompt,
                "negative_prompt": negative_prompt or "",
                "width": width,
                "height": height,
                "steps": kwargs.get('steps', 30),
                "cfg_scale": kwargs.get('cfg_scale', 7.0),
            }
        else:
            # Alibaba Cloud Wanx format
            payload = {
                "model": self.image_model,
                "prompt": prompt,
                "negative_prompt": negative_prompt or "",
                "size": size,
                "n": 1,
                "style": kwargs.get('style', '<auto>'),
            }
            
            # Add optional parameters
            if 'seed' in kwargs:
                payload['seed'] = kwargs['seed']
            if 'num_inference_steps' in kwargs:
                payload['num_inference_steps'] = kwargs['num_inference_steps']
        
        try:
            logger.info(f"Generating image with model: {self.image_model}")
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout * 2  # Image generation takes longer
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract image URL/data from response
                image_data = None
                if 'data' in data and len(data['data']) > 0:
                    if 'url' in data['data'][0]:
                        # Download image from URL
                        image_url = data['data'][0]['url']
                        img_response = requests.get(image_url, timeout=30)
                        if img_response.status_code == 200:
                            image_data = img_response.content
                    elif 'b64_json' in data['data'][0]:
                        # Base64 encoded image
                        image_data = base64.b64decode(data['data'][0]['b64_json'])
                
                if image_data:
                    # Save to file
                    if output_path:
                        output_file = Path(output_path)
                    else:
                        output_file = self.temp_dir / f"generated_{int(time.time())}.png"
                    
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, 'wb') as f:
                        f.write(image_data)
                    
                    logger.info(f"Image saved to: {output_file}")
                    return {
                        'image_path': str(output_file),
                        'prompt': prompt,
                        'model': self.image_model,
                        'size': size
                    }
                else:
                    logger.error("No image data in response")
                    return None
            else:
                logger.error(f"Image generation API error ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None
    
    def generate_video(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        duration: int = 5,
        resolution: str = "720p",
        output_path: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Generate video using Alibaba Cloud Wan or other providers
        
        Args:
            prompt: Text prompt for video generation
            image_path: Optional input image for image-to-video
            negative_prompt: What to avoid in the generated video
            duration: Video duration in seconds
            resolution: Video resolution (e.g., "720p", "1080p")
            output_path: Optional path to save the generated video
            **kwargs: Additional parameters for specific providers
            
        Returns:
            Dict with 'video_path', 'prompt', 'model' keys or None on error
        """
        if not self.api_key and not self._is_ollama():
            logger.error("API key required for video generation")
            return None
        
        url = self._get_video_generation_url()
        
        # Build request payload based on provider
        if self._is_ollama():
            payload = {
                "model": self.video_model,
                "prompt": prompt,
                "negative_prompt": negative_prompt or "",
                "duration": duration,
                "resolution": resolution,
            }
            if image_path:
                # Encode and send image
                with open(image_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                payload['image'] = image_data
        else:
            # Alibaba Cloud Wan video generation format
            payload = {
                "model": self.video_model,
                "prompt": prompt,
                "negative_prompt": negative_prompt or "",
                "duration": duration,
                "resolution": resolution,
            }
            
            # Add image for image-to-video
            if image_path:
                with open(image_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                payload['image'] = image_data
            
            # Add optional parameters
            if 'seed' in kwargs:
                payload['seed'] = kwargs['seed']
            if 'guidance_scale' in kwargs:
                payload['guidance_scale'] = kwargs['guidance_scale']
        
        try:
            logger.info(f"Starting video generation with model: {self.video_model}")
            
            # Submit video generation task
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30  # Initial submission timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Video generation submission error ({response.status_code}): {response.text}")
                return None
            
            data = response.json()
            task_id = data.get('task_id') or data.get('id')
            
            if not task_id:
                logger.error("No task_id in video generation response")
                return None
            
            logger.info(f"Video generation task submitted: {task_id}")
            
            # Poll for completion (Alibaba Cloud uses async task processing)
            status_url = f"{url}/{task_id}" if not self._is_ollama() else f"{url}/status/{task_id}"
            max_wait_time = kwargs.get('max_wait_time', 600)  # Default 10 minutes
            poll_interval = kwargs.get('poll_interval', 10)  # Check every 10 seconds
            
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                time.sleep(poll_interval)
                
                status_response = requests.get(
                    status_url,
                    headers=self.headers,
                    timeout=30
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status', '').lower()
                    
                    if status in ['completed', 'succeeded', 'success']:
                        # Video ready, download it
                        video_url = status_data.get('output', {}).get('video_url') or \
                                   status_data.get('results', {}).get('video', {}).get('url')
                        
                        if video_url:
                            logger.info(f"Downloading generated video from: {video_url}")
                            video_response = requests.get(video_url, timeout=120)
                            
                            if video_response.status_code == 200:
                                # Save video file
                                if output_path:
                                    video_file = Path(output_path)
                                else:
                                    video_file = self.temp_dir / f"generated_{int(time.time())}.mp4"
                                
                                video_file.parent.mkdir(parents=True, exist_ok=True)
                                with open(video_file, 'wb') as f:
                                    f.write(video_response.content)
                                
                                logger.info(f"Video saved to: {video_file}")
                                return {
                                    'video_path': str(video_file),
                                    'prompt': prompt,
                                    'model': self.video_model,
                                    'duration': duration,
                                    'resolution': resolution
                                }
                        break
                    elif status in ['failed', 'error', 'cancelled']:
                        logger.error(f"Video generation failed: {status_data.get('message', 'Unknown error')}")
                        return None
                    # else: still processing
                    
            logger.error("Video generation timed out")
            return None
            
        except Exception as e:
            logger.error(f"Video generation error: {e}")
            return None
    
    def check_health(self) -> bool:
        """Check if LLM service is available"""
        try:
            if self._is_ollama():
                # Check Ollama health
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            else:
                # Check OpenAI-compatible API
                response = requests.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=5
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """List available models from the provider"""
        try:
            if self._is_ollama():
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return [model.get('name', '') for model in data.get('models', [])]
            else:
                response = requests.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    return [model.get('id', '') for model in data.get('data', [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []


# Global LLM client instance (will be initialized from config)
llm_client: Optional[LLMClient] = None


def init_llm_from_config(config_dict: Dict[str, Any]) -> LLMClient:
    """Initialize LLM client from configuration dictionary"""
    global llm_client
    
    llm_config = config_dict.get('llm', {})
    
    # Use connection_timeout if available, otherwise fall back to timeout
    timeout = llm_config.get('connection_timeout', llm_config.get('timeout', 120))
    
    llm_client = LLMClient(
        provider=llm_config.get('provider', 'ollama'),
        base_url=llm_config.get('base_url', 'http://localhost:11434'),
        api_key=llm_config.get('api_key', ''),
        model=llm_config.get('theme_model', 'qwen3.5:9b'),
        vision_model=llm_config.get('vision_model', 'qwen3.5:9b'),
        image_model=llm_config.get('image_model', 'wanx2.1-turbo-i2v'),
        video_model=llm_config.get('video_model', 'wan2.1-t2v-14b'),
        max_tokens=llm_config.get('max_tokens', 800),
        temperature=llm_config.get('temperature', 0.7),
        timeout=timeout
    )
    
    logger.info(f"LLM client initialized: {llm_client.provider} @ {llm_client.base_url} (timeout={timeout}s)")
    return llm_client


def get_llm_client() -> Optional[LLMClient]:
    """Get the global LLM client instance"""
    return llm_client
