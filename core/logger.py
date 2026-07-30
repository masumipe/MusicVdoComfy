"""
Structured logging for pipeline stages and errors
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StageLogger:
    """Logger for pipeline stages with file output"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main logger
        self.logger = logging.getLogger('music_vdo_comfy')
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler for all logs
        all_log_file = self.log_dir / "pipeline.log"
        file_handler = logging.FileHandler(all_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str) -> None:
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        self.logger.critical(message)
    
    def stage_start(self, stage_name: str) -> None:
        self.logger.info(f"{'='*60}")
        self.logger.info(f"STAGE START: {stage_name}")
        self.logger.info(f"{'='*60}")
    
    def stage_complete(self, stage_name: str, success: bool = True) -> None:
        status = "COMPLETED" if success else "FAILED"
        self.logger.info(f"STAGE {status}: {stage_name}")
    
    def log_error_dump(self, error_data: Dict[str, Any], prompt_id: str = "") -> Path:
        """Save detailed error information to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"error_{prompt_id}_{timestamp}.json" if prompt_id else f"error_{timestamp}.json"
        error_file = self.log_dir / filename
        
        try:
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, default=str)
            self.logger.info(f"Error details saved to: {error_file}")
            return error_file
        except Exception as e:
            self.logger.error(f"Failed to save error dump: {e}")
            return None
    
    def get_log_tail(self, lines: int = 50) -> str:
        """Get last N lines from the log file"""
        log_file = self.log_dir / "pipeline.log"
        
        if not log_file.exists():
            return ""
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            self.logger.error(f"Failed to read log tail: {e}")
            return ""


# Global logger instance
def get_logger(log_dir: Optional[Path] = None) -> StageLogger:
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    
    return StageLogger(log_dir)
