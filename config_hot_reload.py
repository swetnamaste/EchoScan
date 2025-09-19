"""
Configuration hot-reload manager for EchoScan scoring weights.
Watches scoring_config.json for changes and automatically reloads configuration.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging for config management
config_logger = logging.getLogger('echoscan.config')


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for config file changes."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('scoring_config.json'):
            config_logger.info(f"Config file modified: {event.src_path}")
            self.config_manager.reload_config()


class ConfigManager:
    """Configuration manager with hot-reload capability for scoring weights."""
    
    def __init__(self, config_path: Optional[str] = None, error_reporter=None):
        self.error_reporter = error_reporter
        self.config_path = config_path or self._get_default_config_path()
        self.config_data = {}
        self.observers = []
        self.callbacks = []
        self.lock = threading.RLock()
        self.last_modified = 0
        
        # Load initial configuration
        self.load_config()
        
        # Start file watching
        self.start_watching()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        base_dir = Path(__file__).parent
        return str(base_dir / "config" / "scoring_config.json")
    
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if not os.path.exists(self.config_path):
                self._create_default_config()
            
            with open(self.config_path, 'r') as f:
                new_config = json.load(f)
            
            with self.lock:
                self.config_data = new_config
                self.last_modified = os.path.getmtime(self.config_path)
            
            config_logger.info(f"Configuration loaded from {self.config_path}")
            self._notify_callbacks()
            return True
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            error_msg = f"Failed to load config from {self.config_path}: {e}"
            config_logger.error(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ConfigError", error_msg, 
                                            {"config_path": self.config_path})
            return False
        except Exception as e:
            error_msg = f"Unexpected error loading config: {e}"
            config_logger.error(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ConfigError", error_msg,
                                            {"config_path": self.config_path})
            return False
    
    def _create_default_config(self):
        """Create default configuration if none exists."""
        default_config = {
            "echosense_weights": {
                "delta_component": 0.3,
                "fold_component": 0.3,
                "glyph_component": 0.2,
                "ancestry_component": 0.2
            },
            "verdict_thresholds": {
                "authentic_min": 0.8,
                "plausible_min": 0.5,
                "hallucination_max": 0.5
            },
            "penalty_thresholds": {
                "severe_penalty": -10,
                "moderate_penalty": -5,
                "bonus_modifier": 5
            },
            "vault_access": {
                "min_echo_sense": 0.7,
                "min_ancestry_depth": 2
            }
        }
        
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        config_logger.info(f"Created default config at {self.config_path}")
    
    def reload_config(self):
        """Reload configuration from file."""
        try:
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime <= self.last_modified:
                return  # No changes
                
            self.load_config()
            config_logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            error_msg = f"Failed to reload config: {e}"
            config_logger.error(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ConfigReloadError", error_msg,
                                            {"config_path": self.config_path})
    
    def start_watching(self):
        """Start watching config file for changes."""
        try:
            observer = Observer()
            handler = ConfigFileHandler(self)
            config_dir = os.path.dirname(self.config_path)
            
            observer.schedule(handler, config_dir, recursive=False)
            observer.start()
            self.observers.append(observer)
            
            config_logger.info(f"Started watching config directory: {config_dir}")
            
        except Exception as e:
            error_msg = f"Failed to start config file watching: {e}"
            config_logger.error(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ConfigWatchError", error_msg,
                                            {"config_path": self.config_path})
    
    def stop_watching(self):
        """Stop watching config file for changes."""
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers.clear()
        config_logger.info("Stopped config file watching")
    
    def get_echosense_weights(self) -> Dict[str, float]:
        """Get EchoSense scoring weights."""
        with self.lock:
            return self.config_data.get("echosense_weights", {
                "delta_component": 0.3,
                "fold_component": 0.3,
                "glyph_component": 0.2,
                "ancestry_component": 0.2
            }).copy()
    
    def get_verdict_thresholds(self) -> Dict[str, float]:
        """Get verdict determination thresholds."""
        with self.lock:
            return self.config_data.get("verdict_thresholds", {
                "authentic_min": 0.8,
                "plausible_min": 0.5,
                "hallucination_max": 0.5
            }).copy()
    
    def get_penalty_thresholds(self) -> Dict[str, float]:
        """Get penalty/modifier thresholds."""
        with self.lock:
            return self.config_data.get("penalty_thresholds", {
                "severe_penalty": -10,
                "moderate_penalty": -5,
                "bonus_modifier": 5
            }).copy()
    
    def get_vault_access_config(self) -> Dict[str, Any]:
        """Get vault access configuration."""
        with self.lock:
            return self.config_data.get("vault_access", {
                "min_echo_sense": 0.7,
                "min_ancestry_depth": 2
            }).copy()
    
    def get_config(self, key: str, default=None) -> Any:
        """Get specific configuration value."""
        with self.lock:
            return self.config_data.get(key, default)
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get complete configuration."""
        with self.lock:
            return self.config_data.copy()
    
    def add_callback(self, callback: Callable):
        """Add callback to be notified of config changes."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove config change callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of config changes."""
        for callback in self.callbacks:
            try:
                callback(self.config_data)
            except Exception as e:
                config_logger.error(f"Config callback error: {e}")
    
    def __del__(self):
        """Cleanup file watching on destruction."""
        self.stop_watching()


# Global config manager instance
config_manager = ConfigManager()


def get_scoring_weights() -> Dict[str, float]:
    """Convenience function to get current scoring weights."""
    return config_manager.get_echosense_weights()


def get_config_value(key: str, default=None) -> Any:
    """Convenience function to get config value."""
    return config_manager.get_config(key, default)


def reload_config():
    """Convenience function to manually reload configuration."""
    config_manager.reload_config()