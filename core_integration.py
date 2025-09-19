"""
EchoScan Core Integration Module

This module provides robust integration utilities for the EchoScan pipeline including:
- Input normalization for all modalities
- Unified module execution schema  
- Error handling and logging
- Scoring and decision labeling
- Advisory flag collection
- Output structuring
- Dry-run/test mode support
"""

import logging
import json
import traceback
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('EchoScan.CoreIntegration')

class EchoScanResult:
    """Standardized result schema for all EchoScan operations."""
    
    def __init__(self, 
                 module_name: str,
                 input_data: str = None,
                 success: bool = True,
                 dry_run: bool = False):
        self.module_name = module_name
        self.input_data = input_data[:100] + "..." if input_data and len(input_data) > 100 else input_data
        self.success = success
        self.dry_run = dry_run
        self.results = {}
        self.errors = []
        self.warnings = []
        self.advisory_flags = []
        self.echo_score_modifier = 0.0
        self.echo_score_penalty = 0.0
        self.source_classification = "Unknown"
        self.metadata = {}
        
    def add_result(self, key: str, value: Any):
        """Add a result field."""
        self.results[key] = value
        
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(f"{self.module_name}: {error}")
        self.success = False
        logger.error(f"{self.module_name}: {error}")
        
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(f"{self.module_name}: {warning}")
        logger.warning(f"{self.module_name}: {warning}")
        
    def add_advisory_flag(self, flag: str):
        """Add an advisory flag."""
        self.advisory_flags.append(f"{self.module_name.upper()}: {flag}")
        
    def set_score_modifier(self, modifier: float, penalty: float = 0.0):
        """Set score modifier and penalty."""
        self.echo_score_modifier = modifier
        self.echo_score_penalty = penalty
        
    def set_source_classification(self, classification: str):
        """Set source classification."""
        self.source_classification = classification
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result_dict = {
            "module": self.module_name,
            "success": self.success,
            "dry_run": self.dry_run,
            **self.results
        }
        
        if self.input_data:
            result_dict["input"] = self.input_data
            
        if self.errors:
            result_dict["errors"] = self.errors
            
        if self.warnings:
            result_dict["warnings"] = self.warnings
            
        if self.advisory_flags:
            result_dict["advisory_flags"] = self.advisory_flags
            
        if self.echo_score_modifier != 0.0:
            result_dict["echo_score_modifier"] = self.echo_score_modifier
            
        if self.echo_score_penalty != 0.0:
            result_dict["echo_score_penalty"] = self.echo_score_penalty
            
        if self.source_classification != "Unknown":
            result_dict["source_classification"] = self.source_classification
            
        if self.metadata:
            result_dict["metadata"] = self.metadata
            
        return result_dict


class InputNormalizer:
    """Handles input normalization for all supported modalities."""
    
    SUPPORTED_MODALITIES = ["text", "image", "audio", "video"]
    
    @staticmethod
    def normalize_input(input_data: Union[str, bytes, Path], 
                       modality: str = "text", 
                       dry_run: bool = False) -> EchoScanResult:
        """
        Normalize input data for processing.
        
        Args:
            input_data: Input data (string, file path, or bytes)
            modality: Type of input ("text", "image", "audio", "video")
            dry_run: If True, perform validation without full processing
            
        Returns:
            EchoScanResult with normalized input
        """
        result = EchoScanResult("InputNormalizer", dry_run=dry_run)
        
        try:
            if modality not in InputNormalizer.SUPPORTED_MODALITIES:
                result.add_error(f"Unsupported modality: {modality}")
                return result
                
            if dry_run:
                result.add_result("normalized_input", "[DRY RUN - Input would be processed]")
                result.add_result("modality", modality)
                result.add_result("input_type", type(input_data).__name__)
                return result
                
            # Handle different input types
            if isinstance(input_data, (str, Path)):
                input_path = Path(input_data)
                if input_path.exists() and input_path.is_file():
                    # File input
                    try:
                        if modality == "text":
                            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                                normalized = f.read()
                        else:
                            with open(input_path, 'rb') as f:
                                normalized = f.read()
                        result.add_result("input_source", "file")
                        result.add_result("file_path", str(input_path))
                    except Exception as e:
                        result.add_error(f"Failed to read file {input_path}: {e}")
                        return result
                else:
                    # Direct string input
                    if modality == "text":
                        normalized = str(input_data)
                    else:
                        result.add_error(f"Non-text modality requires file input, got: {type(input_data)}")
                        return result
                    result.add_result("input_source", "direct")
            elif isinstance(input_data, bytes):
                if modality == "text":
                    try:
                        normalized = input_data.decode('utf-8', errors='ignore')
                    except Exception as e:
                        result.add_error(f"Failed to decode bytes as UTF-8: {e}")
                        return result
                else:
                    normalized = input_data
                result.add_result("input_source", "bytes")
            else:
                result.add_error(f"Unsupported input type: {type(input_data)}")
                return result
                
            # Validate normalized input
            if modality == "text" and isinstance(normalized, str):
                if not normalized.strip():
                    result.add_warning("Empty or whitespace-only input")
                    
                if len(normalized) > 1000000:  # 1MB limit for text
                    result.add_warning(f"Large input detected: {len(normalized)} characters")
                    
            result.add_result("normalized_input", normalized)
            result.add_result("modality", modality)
            result.add_result("input_length", len(normalized) if isinstance(normalized, (str, bytes)) else "N/A")
            
        except Exception as e:
            result.add_error(f"Unexpected error in input normalization: {e}")
            logger.exception(f"Input normalization failed for {modality}")
            
        return result


class ModuleExecutor:
    """Unified module execution with error handling and result standardization."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.execution_log = []
        
    def execute_module(self, 
                      module_name: str, 
                      module_func: callable, 
                      input_data: str,
                      **kwargs) -> EchoScanResult:
        """
        Execute a detector module with standardized error handling.
        
        Args:
            module_name: Name of the module
            module_func: Module function to execute
            input_data: Input data for the module
            **kwargs: Additional arguments for the module
            
        Returns:
            EchoScanResult with execution results
        """
        result = EchoScanResult(module_name, input_data, dry_run=self.dry_run)
        
        try:
            if self.dry_run:
                result.add_result("status", "DRY RUN - Module would be executed")
                result.add_result("function", str(module_func))
                result.add_result("kwargs", kwargs)
                self.execution_log.append(f"DRY RUN: {module_name}")
                return result
                
            logger.info(f"Executing module: {module_name}")
            
            # Execute the module function
            module_result = module_func(input_data, **kwargs)
            
            if isinstance(module_result, dict):
                # Standardize the result
                for key, value in module_result.items():
                    result.add_result(key, value)
                    
                # Extract standard fields
                if "echo_score_modifier" in module_result:
                    result.echo_score_modifier = module_result["echo_score_modifier"]
                    
                if "echo_score_penalty" in module_result:
                    result.echo_score_penalty = module_result["echo_score_penalty"]
                    
                if "source_classification" in module_result:
                    result.source_classification = module_result["source_classification"]
                    
                if "advisory_flag" in module_result:
                    result.add_advisory_flag(module_result["advisory_flag"])
                    
            else:
                result.add_result("raw_result", module_result)
                result.add_warning("Module returned non-dict result")
                
            self.execution_log.append(f"SUCCESS: {module_name}")
            logger.info(f"Module {module_name} executed successfully")
            
        except Exception as e:
            result.add_error(f"Execution failed: {e}")
            self.execution_log.append(f"FAILED: {module_name} - {e}")
            logger.exception(f"Module {module_name} execution failed")
            
        return result
        
    def get_execution_log(self) -> List[str]:
        """Get the execution log."""
        return self.execution_log.copy()


class ScoreCalculator:
    """Handles echo score calculation and decision labeling."""
    
    @staticmethod
    def calculate_echo_score(module_results: Dict[str, EchoScanResult], 
                           base_score: float = 50.0) -> Dict[str, Any]:
        """
        Calculate the overall Echo Score from module results.
        
        Args:
            module_results: Dictionary of module results
            base_score: Base score to start from (default: 50.0)
            
        Returns:
            Dictionary containing score breakdown and decision
        """
        score_breakdown = {
            "base_score": base_score,
            "modifiers": {},
            "penalties": {},
            "total_modifier": 0.0,
            "total_penalty": 0.0,
            "final_score": base_score
        }
        
        total_modifier = 0.0
        total_penalty = 0.0
        
        for module_name, result in module_results.items():
            if isinstance(result, EchoScanResult):
                if result.echo_score_modifier != 0.0:
                    score_breakdown["modifiers"][module_name] = result.echo_score_modifier
                    total_modifier += result.echo_score_modifier
                    
                if result.echo_score_penalty != 0.0:
                    score_breakdown["penalties"][module_name] = result.echo_score_penalty
                    total_penalty += result.echo_score_penalty
                    
        score_breakdown["total_modifier"] = total_modifier
        score_breakdown["total_penalty"] = total_penalty
        score_breakdown["final_score"] = max(0.0, base_score + total_modifier + total_penalty)
        
        # Determine decision label
        final_score = score_breakdown["final_score"]
        if final_score >= 70.0:
            decision = "Authentic"
        elif final_score >= 40.0:
            decision = "Questionable"
        else:
            decision = "Likely Synthetic"
            
        score_breakdown["decision_label"] = decision
        
        return score_breakdown


class AdvisoryFlagCollector:
    """Collects and categorizes advisory flags from all modules."""
    
    FLAG_CATEGORIES = {
        "critical": ["synthetic", "hallucination", "extreme", "suspicious", "anomaly", "severe"],
        "warning": ["borderline", "elevated", "questionable", "moderate", "plausible"],
        "info": ["authentic", "bonus", "verified", "normal"]
    }
    
    @staticmethod
    def collect_flags(module_results: Dict[str, EchoScanResult]) -> Dict[str, List[str]]:
        """
        Collect and categorize advisory flags from module results.
        
        Args:
            module_results: Dictionary of module results
            
        Returns:
            Dictionary with categorized flags
        """
        categorized_flags = {
            "critical": [],
            "warning": [],
            "info": [],
            "all": []
        }
        
        for module_name, result in module_results.items():
            if isinstance(result, EchoScanResult):
                for flag in result.advisory_flags:
                    categorized_flags["all"].append(flag)
                    
                    # Categorize flag
                    flag_lower = flag.lower()
                    categorized = False
                    
                    for category, keywords in AdvisoryFlagCollector.FLAG_CATEGORIES.items():
                        if any(keyword in flag_lower for keyword in keywords):
                            categorized_flags[category].append(flag)
                            categorized = True
                            break
                            
                    if not categorized:
                        categorized_flags["info"].append(flag)
                        
                # Generate flags based on source classification
                if result.source_classification == "AI-Generated":
                    flag = f"{module_name.upper()}: AI-generated content detected"
                    categorized_flags["critical"].append(flag)
                    categorized_flags["all"].append(flag)
                elif result.source_classification == "Questionable":
                    flag = f"{module_name.upper()}: Content authenticity questioned"
                    categorized_flags["warning"].append(flag)
                    categorized_flags["all"].append(flag)
                elif result.source_classification == "Human-Generated":
                    flag = f"{module_name.upper()}: Human-generated content verified"
                    categorized_flags["info"].append(flag)
                    categorized_flags["all"].append(flag)
                    
        # Remove duplicates while preserving order
        for category in categorized_flags:
            seen = set()
            unique_flags = []
            for flag in categorized_flags[category]:
                if flag not in seen:
                    unique_flags.append(flag)
                    seen.add(flag)
            categorized_flags[category] = unique_flags
            
        return categorized_flags


class OutputStructurer:
    """Structures final output in standardized format."""
    
    @staticmethod
    def structure_output(input_data: str,
                        modality: str,
                        module_results: Dict[str, EchoScanResult],
                        score_data: Dict[str, Any],
                        advisory_flags: Dict[str, List[str]],
                        dry_run: bool = False,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Structure the final output in standardized format.
        
        Args:
            input_data: Original input data
            modality: Input modality
            module_results: Results from all modules
            score_data: Score calculation data
            advisory_flags: Categorized advisory flags
            dry_run: Whether this was a dry run
            metadata: Additional metadata
            
        Returns:
            Structured output dictionary
        """
        output = {
            "EchoScan": {
                "version": "1.0.0",
                "input": {
                    "data": input_data[:100] + "..." if len(input_data) > 100 else input_data,
                    "modality": modality,
                    "length": len(input_data)
                },
                "execution": {
                    "dry_run": dry_run,
                    "modules_executed": list(module_results.keys()),
                    "successful_modules": [name for name, result in module_results.items() 
                                        if isinstance(result, EchoScanResult) and result.success],
                    "failed_modules": [name for name, result in module_results.items() 
                                     if isinstance(result, EchoScanResult) and not result.success]
                },
                "scoring": score_data,
                "decision": score_data.get("decision_label", "Unknown"),
                "advisory_flags": advisory_flags,
                "results": {}
            }
        }
        
        # Add individual module results
        for module_name, result in module_results.items():
            if isinstance(result, EchoScanResult):
                output["EchoScan"]["results"][module_name] = result.to_dict()
                
        # Add metadata if provided
        if metadata:
            output["EchoScan"]["metadata"] = metadata
            
        # Add summary statistics
        output["EchoScan"]["summary"] = {
            "echo_score": score_data.get("final_score", 0.0),
            "decision_label": score_data.get("decision_label", "Unknown"),
            "total_flags": len(advisory_flags.get("all", [])),
            "critical_flags": len(advisory_flags.get("critical", [])),
            "warning_flags": len(advisory_flags.get("warning", [])),
            "modules_successful": len(output["EchoScan"]["execution"]["successful_modules"]),
            "modules_failed": len(output["EchoScan"]["execution"]["failed_modules"])
        }
        
        return output


# Convenience function for backward compatibility
def compute_advisory_flags(results: Dict[str, Any]) -> List[str]:
    """
    Legacy function for computing advisory flags.
    Maintained for backward compatibility.
    """
    # Convert legacy results to EchoScanResult format
    echo_results = {}
    for module_name, result in results.items():
        if isinstance(result, dict):
            echo_result = EchoScanResult(module_name)
            echo_result.results = result
            
            # Extract standard fields
            if "advisory_flag" in result:
                echo_result.add_advisory_flag(result["advisory_flag"])
            if "source_classification" in result:
                echo_result.source_classification = result["source_classification"]
            if "echo_score_modifier" in result:
                echo_result.echo_score_modifier = result["echo_score_modifier"]
            if "echo_score_penalty" in result:
                echo_result.echo_score_penalty = result["echo_score_penalty"]
                
            echo_results[module_name] = echo_result
            
    # Use new flag collector
    flags = AdvisoryFlagCollector.collect_flags(echo_results)
    return flags.get("all", [])