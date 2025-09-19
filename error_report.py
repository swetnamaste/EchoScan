"""
Centralized error reporting utility for EchoScan pipeline.
Logs all errors, validation failures, and config issues to a centralized error log 
with timestamps and detailed context.
"""

import json
import logging
import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ErrorReporter:
    """Centralized error reporter with structured logging and context tracking."""
    
    def __init__(self, log_dir: Optional[str] = None, log_level: int = logging.ERROR):
        self.log_dir = log_dir or self._get_default_log_dir()
        self.lock = threading.RLock()
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup main error logger
        self.error_logger = self._setup_error_logger(log_level)
        
        # Setup validation error logger
        self.validation_logger = self._setup_validation_logger(log_level)
        
        # Setup config error logger  
        self.config_logger = self._setup_config_logger(log_level)
        
        # Error counters
        self.error_counts = {
            'validation': 0,
            'config': 0,
            'pipeline': 0,
            'general': 0
        }
        
        # Recent errors cache for diagnostics
        self.recent_errors = []
        self.max_recent_errors = 100
    
    def _get_default_log_dir(self) -> str:
        """Get default log directory."""
        base_dir = Path(__file__).parent
        return str(base_dir / "logs")
    
    def _setup_error_logger(self, log_level: int) -> logging.Logger:
        """Setup main error logger with file and console handlers."""
        logger = logging.getLogger('echoscan.errors')
        logger.setLevel(log_level)
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # File handler for error log
        error_log_path = os.path.join(self.log_dir, 'echoscan_errors.log')
        file_handler = logging.FileHandler(error_log_path)
        file_handler.setLevel(log_level)
        
        # Console handler for critical errors
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.CRITICAL)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_validation_logger(self, log_level: int) -> logging.Logger:
        """Setup validation-specific error logger."""
        logger = logging.getLogger('echoscan.validation.errors')
        logger.setLevel(log_level)
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        validation_log_path = os.path.join(self.log_dir, 'validation_errors.log')
        file_handler = logging.FileHandler(validation_log_path)
        file_handler.setLevel(log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - VALIDATION - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _setup_config_logger(self, log_level: int) -> logging.Logger:
        """Setup config-specific error logger."""
        logger = logging.getLogger('echoscan.config.errors')
        logger.setLevel(log_level)
        
        # Clear existing handlers  
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        config_log_path = os.path.join(self.log_dir, 'config_errors.log')
        file_handler = logging.FileHandler(config_log_path)
        file_handler.setLevel(log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - CONFIG - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def log_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None,
                  exc_info: Optional[Exception] = None):
        """Log error with structured context and categorization."""
        with self.lock:
            timestamp = datetime.now().isoformat()
            
            # Create error record
            error_record = {
                'timestamp': timestamp,
                'error_type': error_type,
                'message': message,
                'context': context or {},
                'exception': None,
                'traceback': None
            }
            
            # Add exception details if provided
            if exc_info:
                error_record['exception'] = str(exc_info)
                error_record['traceback'] = traceback.format_exception(
                    type(exc_info), exc_info, exc_info.__traceback__
                )
            elif sys.exc_info()[0] is not None:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error_record['exception'] = str(exc_value)
                error_record['traceback'] = traceback.format_exception(
                    exc_type, exc_value, exc_traceback
                )
            
            # Update error counters
            category = self._categorize_error(error_type)
            self.error_counts[category] += 1
            
            # Add to recent errors cache
            self.recent_errors.append(error_record)
            if len(self.recent_errors) > self.max_recent_errors:
                self.recent_errors.pop(0)
            
            # Log to appropriate logger
            formatted_message = self._format_error_message(error_record)
            
            if category == 'validation':
                self.validation_logger.error(formatted_message)
            elif category == 'config':
                self.config_logger.error(formatted_message)
            else:
                self.error_logger.error(formatted_message)
            
            # Log critical errors to console
            if error_type in ['ValidationError', 'ConfigError', 'PipelineError']:
                self.error_logger.critical(f"CRITICAL: {formatted_message}")
    
    def _categorize_error(self, error_type: str) -> str:
        """Categorize error type for counting and routing."""
        if 'validation' in error_type.lower():
            return 'validation'
        elif 'config' in error_type.lower():
            return 'config'  
        elif 'pipeline' in error_type.lower():
            return 'pipeline'
        else:
            return 'general'
    
    def _format_error_message(self, error_record: Dict[str, Any]) -> str:
        """Format error record for logging."""
        base_msg = f"[{error_record['error_type']}] {error_record['message']}"
        
        if error_record['context']:
            context_str = json.dumps(error_record['context'], indent=None, default=str)
            base_msg += f" | Context: {context_str}"
        
        if error_record['exception']:
            base_msg += f" | Exception: {error_record['exception']}"
            
        return base_msg
    
    def log_validation_error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log validation-specific error."""
        self.log_error("ValidationError", message, context)
    
    def log_config_error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log configuration-specific error."""
        self.log_error("ConfigError", message, context)
    
    def log_pipeline_error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log pipeline-specific error."""  
        self.log_error("PipelineError", message, context)
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        with self.lock:
            formatted_msg = f"WARNING: {message}"
            if context:
                formatted_msg += f" | Context: {json.dumps(context, default=str)}"
            self.error_logger.warning(formatted_msg)
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log informational message."""
        with self.lock:
            formatted_msg = message
            if context:
                formatted_msg += f" | Context: {json.dumps(context, default=str)}"
            self.error_logger.info(formatted_msg)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of logged errors."""
        with self.lock:
            return {
                'total_errors': sum(self.error_counts.values()),
                'error_counts': self.error_counts.copy(),
                'recent_error_count': len(self.recent_errors),
                'log_directory': self.log_dir
            }
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors for diagnostics."""
        with self.lock:
            return self.recent_errors[-limit:] if self.recent_errors else []
    
    def clear_error_counts(self):
        """Clear error counters (for testing/reset)."""
        with self.lock:
            self.error_counts = {key: 0 for key in self.error_counts}
            self.recent_errors.clear()
    
    def create_error_report(self, filepath: Optional[str] = None) -> str:
        """Create comprehensive error report."""
        with self.lock:
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'summary': self.get_error_summary(),
                'recent_errors': self.get_recent_errors(50),
                'log_files': {
                    'main_errors': os.path.join(self.log_dir, 'echoscan_errors.log'),
                    'validation_errors': os.path.join(self.log_dir, 'validation_errors.log'),
                    'config_errors': os.path.join(self.log_dir, 'config_errors.log')
                }
            }
            
            if filepath:
                with open(filepath, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
                return filepath
            else:
                return json.dumps(report_data, indent=2, default=str)


# Global error reporter instance
error_reporter = ErrorReporter()


def log_error(error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
    """Convenience function to log errors to global reporter."""
    error_reporter.log_error(error_type, message, context)


def log_validation_error(message: str, context: Optional[Dict[str, Any]] = None):
    """Convenience function to log validation errors."""
    error_reporter.log_validation_error(message, context)


def log_config_error(message: str, context: Optional[Dict[str, Any]] = None):
    """Convenience function to log config errors."""
    error_reporter.log_config_error(message, context)


def log_pipeline_error(message: str, context: Optional[Dict[str, Any]] = None):
    """Convenience function to log pipeline errors."""
    error_reporter.log_pipeline_error(message, context)