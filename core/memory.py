"""
Memory management utilities for freeing VRAM and system memory
"""
import gc
import logging

logger = logging.getLogger(__name__)


def free_memory(comfy_client=None):
    """
    Free memory on both ComfyUI server and local system
    
    Args:
        comfy_client: Optional ComfyClient instance to call /free endpoint
    """
    # 1. Tell ComfyUI to unload models and free VRAM
    if comfy_client is not None:
        try:
            comfy_client.free_memory()
        except Exception as e:
            logger.error(f"Failed to free ComfyUI memory: {e}")
    
    # 2. Local Python cleanup
    gc.collect()
    
    # 3. Try to clear CUDA cache if torch is available
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("CUDA cache cleared")
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to clear CUDA cache: {e}")
    
    logger.info("Memory cleanup completed")
