#!/usr/bin/env python3
"""
Detector Registry System for EchoScan
Provides dynamic loading and management of detectors based on registry.json
"""

import json
import importlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DetectorRegistry:
    """Dynamic detector registry with plug-and-play support."""
    
    def __init__(self, registry_path: Optional[str] = None):
        """Initialize the detector registry."""
        if registry_path is None:
            registry_path = Path(__file__).parent / "registry.json"
        
        self.registry_path = Path(registry_path)
        self.detectors = {}
        self.symbolic_detectors = {}
        self.experimental_detectors = {}
        self.loaded_modules = {}
        
        # Load registry configuration
        self.load_registry()
        
        # Auto-discover and load enabled detectors
        if self.registry_config.get("registry_meta", {}).get("auto_discovery", True):
            self.auto_load_detectors()
    
    def load_registry(self):
        """Load detector registry from JSON file."""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.registry_config = json.load(f)
            logger.info(f"✅ Loaded detector registry from {self.registry_path}")
        except FileNotFoundError:
            logger.error(f"❌ Registry file not found: {self.registry_path}")
            self.registry_config = {"detectors": {}, "symbolic_detectors": {}, "experimental_detectors": {}}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in registry file: {e}")
            self.registry_config = {"detectors": {}, "symbolic_detectors": {}, "experimental_detectors": {}}
    
    def auto_load_detectors(self):
        """Automatically load all enabled detectors from registry."""
        # Load standard detectors
        for name, config in self.registry_config.get("detectors", {}).items():
            if config.get("enabled", False):
                self.load_detector(name, config, "detectors")
        
        # Load symbolic detectors
        for name, config in self.registry_config.get("symbolic_detectors", {}).items():
            if config.get("enabled", False):
                self.load_detector(name, config, "symbolic_detectors")
        
        # Load experimental detectors
        for name, config in self.registry_config.get("experimental_detectors", {}).items():
            if config.get("enabled", False):
                self.load_detector(name, config, "experimental_detectors")
        
        logger.info(f"✅ Registry loaded: {len(self.detectors)} standard, "
                   f"{len(self.symbolic_detectors)} symbolic, "
                   f"{len(self.experimental_detectors)} experimental detectors")
    
    def load_detector(self, name: str, config: Dict[str, Any], category: str):
        """Load a single detector based on its configuration."""
        try:
            # Check dependencies
            if not self.check_dependencies(config.get("dependencies", [])):
                logger.warning(f"⚠️ Skipping {name}: dependencies not met")
                return False
            
            # Import module
            module_name = config["module"]
            class_name = config.get("class", None)
            
            try:
                module = importlib.import_module(module_name)
                self.loaded_modules[module_name] = module
            except ImportError as e:
                logger.warning(f"⚠️ Cannot import {module_name} for {name}: {e}")
                return False
            
            # Get detector class if specified
            detector_class = None
            if class_name:
                try:
                    detector_class = getattr(module, class_name)
                except AttributeError:
                    logger.warning(f"⚠️ Class {class_name} not found in {module_name}")
                    detector_class = None
            
            # Store in appropriate category
            detector_info = {
                "name": name,
                "config": config,
                "module": module,
                "class": detector_class,
                "description": config.get("description", "No description")
            }
            
            if category == "detectors":
                self.detectors[name] = detector_info
            elif category == "symbolic_detectors":
                self.symbolic_detectors[name] = detector_info
            elif category == "experimental_detectors":
                self.experimental_detectors[name] = detector_info
            
            logger.info(f"✅ Loaded {category} detector: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load detector {name}: {e}")
            return False
    
    def check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if all dependencies are available."""
        for dep in dependencies:
            if dep not in self.detectors and dep not in self.symbolic_detectors:
                return False
        return True
    
    def get_detector(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a detector by name from any category."""
        return (self.detectors.get(name) or 
                self.symbolic_detectors.get(name) or 
                self.experimental_detectors.get(name))
    
    def list_detectors(self, category: str = "all") -> Dict[str, List[str]]:
        """List available detectors by category."""
        if category == "all":
            return {
                "detectors": list(self.detectors.keys()),
                "symbolic_detectors": list(self.symbolic_detectors.keys()),
                "experimental_detectors": list(self.experimental_detectors.keys())
            }
        elif category == "detectors":
            return {"detectors": list(self.detectors.keys())}
        elif category == "symbolic_detectors":
            return {"symbolic_detectors": list(self.symbolic_detectors.keys())}
        elif category == "experimental_detectors":
            return {"experimental_detectors": list(self.experimental_detectors.keys())}
        else:
            return {}
    
    def register_new_detector(self, name: str, config: Dict[str, Any], category: str = "detectors"):
        """Register a new detector dynamically."""
        if category not in ["detectors", "symbolic_detectors", "experimental_detectors"]:
            raise ValueError(f"Invalid category: {category}")
        
        # Add to registry config
        self.registry_config.setdefault(category, {})[name] = config
        
        # Load the detector
        success = self.load_detector(name, config, category)
        
        if success:
            # Save updated registry
            self.save_registry()
            logger.info(f"✅ Registered and loaded new {category} detector: {name}")
        
        return success
    
    def save_registry(self):
        """Save current registry state to file."""
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry_config, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved registry to {self.registry_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save registry: {e}")
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get registry metadata and statistics."""
        return {
            "registry_path": str(self.registry_path),
            "version": self.registry_config.get("registry_meta", {}).get("version", "unknown"),
            "detector_counts": {
                "standard": len(self.detectors),
                "symbolic": len(self.symbolic_detectors), 
                "experimental": len(self.experimental_detectors),
                "total": len(self.detectors) + len(self.symbolic_detectors) + len(self.experimental_detectors)
            },
            "loaded_modules": list(self.loaded_modules.keys())
        }
    
    def run_detector(self, name: str, input_data: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Run a specific detector by name."""
        detector_info = self.get_detector(name)
        if not detector_info:
            logger.error(f"❌ Detector {name} not found")
            return None
        
        try:
            module = detector_info["module"]
            
            # Try different invocation methods
            if hasattr(module, 'run'):
                return module.run(input_data, **kwargs)
            elif detector_info["class"]:
                # Instantiate class and call run method
                detector_instance = detector_info["class"]()
                if hasattr(detector_instance, 'run'):
                    return detector_instance.run(input_data, **kwargs)
                elif hasattr(detector_instance, 'analyze'):
                    return detector_instance.analyze(input_data, **kwargs)
            
            logger.warning(f"⚠️ No suitable run method found for {name}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error running detector {name}: {e}")
            return None


# Global registry instance
detector_registry = DetectorRegistry()


def get_registry() -> DetectorRegistry:
    """Get the global detector registry instance."""
    return detector_registry


def reload_registry():
    """Reload the detector registry from file."""
    global detector_registry
    detector_registry = DetectorRegistry()
    return detector_registry


def register_detector(name: str, module_path: str, class_name: str = None, 
                     category: str = "detectors", description: str = "", 
                     dependencies: List[str] = None, **kwargs):
    """Convenience function to register a new detector."""
    config = {
        "module": module_path,
        "class": class_name,
        "enabled": True,
        "description": description,
        "dependencies": dependencies or []
    }
    config.update(kwargs)
    
    return detector_registry.register_new_detector(name, config, category)


if __name__ == "__main__":
    # CLI interface for registry management
    import argparse
    
    parser = argparse.ArgumentParser(description="EchoScan Detector Registry Manager")
    parser.add_argument("--list", action="store_true", help="List all detectors")
    parser.add_argument("--info", action="store_true", help="Show registry info")
    parser.add_argument("--reload", action="store_true", help="Reload registry")
    parser.add_argument("--test", type=str, help="Test a specific detector")
    
    args = parser.parse_args()
    
    if args.list:
        detectors = detector_registry.list_detectors()
        print("📋 Registered Detectors:")
        for category, names in detectors.items():
            print(f"  {category}: {', '.join(names)}")
    
    elif args.info:
        info = detector_registry.get_registry_info()
        print("ℹ️ Registry Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    elif args.reload:
        reload_registry()
        print("🔄 Registry reloaded")
    
    elif args.test:
        result = detector_registry.run_detector(args.test, "test input")
        print(f"🧪 Test result for {args.test}: {result}")
    
    else:
        parser.print_help()