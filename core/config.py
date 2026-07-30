"""
Configuration loader and validator for configure.json
"""
import json
import os
from pathlib import Path
from typing import Any, Dict


class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config_path = Path(__file__).parent.parent / "configure.json"
        self.config: Dict[str, Any] = {}
        self.load()
        self._initialized = True
    
    def load(self) -> None:
        """Load configuration from configure.json"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self._validate()
        self._ensure_paths()
    
    def _validate(self) -> None:
        """Validate required configuration keys"""
        required_sections = ['llm', 'comfyui', 'paths']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
    
    def _ensure_paths(self) -> None:
        """Ensure all configured directories exist"""
        paths = self.config.get('paths', {})
        root = Path(paths.get('root', '.'))
        
        for key, path_name in paths.items():
            if key == 'root':
                continue
            path = root / path_name if not Path(path_name).is_absolute() else Path(path_name)
            path.mkdir(parents=True, exist_ok=True)
    
    def get(self, *keys, default=None) -> Any:
        """Get nested configuration value using dot notation"""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    @property
    def llm(self) -> Dict[str, Any]:
        return self.config.get('llm', {})
    
    @property
    def comfyui(self) -> Dict[str, Any]:
        return self.config.get('comfyui', {})
    
    @property
    def paths(self) -> Dict[str, str]:
        return self.config.get('paths', {})
    
    @property
    def rvc(self) -> Dict[str, Any]:
        return self.config.get('rvc', {})
    
    @property
    def segment(self) -> Dict[str, Any]:
        return self.config.get('segment', {})
    
    @property
    def video(self) -> Dict[str, Any]:
        return self.config.get('video', {})
    
    def get_path(self, key: str) -> Path:
        """Get a Path object for a configured directory"""
        paths = self.paths
        root = Path(paths.get('root', '.'))
        path_name = paths.get(key, key)
        return root / path_name if not Path(path_name).is_absolute() else Path(path_name)


# Global config instance
config = Config()
