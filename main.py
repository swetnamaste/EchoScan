import os
import sys
import json
import importlib
import logging
from typing import Dict, List, Any, Optional

# Import our new utilities
from error_report import error_reporter
from config_hot_reload import config_manager
from validation import ValidationUtility

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize validation utility with error reporter
validator = ValidationUtility(error_reporter)


def discover_detectors(detector_dir="detectors"):
    """Dynamically discover and load detector modules."""
    detectors = {}
    
    if not os.path.isdir(detector_dir):
        error_reporter.log_error("PipelineError", f"Detector directory not found: {detector_dir}")
        return detectors
    
    try:
        for filename in os.listdir(detector_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    # Import detector module
                    module_path = f"{detector_dir}.{module_name}"
                    detector_module = importlib.import_module(module_path)
                    
                    if hasattr(detector_module, 'run'):
                        detectors[module_name] = detector_module
                        logger.info(f"Loaded detector: {module_name}")
                    else:
                        error_reporter.log_warning(
                            f"Detector {module_name} missing 'run' function",
                            {"module": module_name}
                        )
                        
                except Exception as e:
                    error_reporter.log_error(
                        "DetectorLoadError",
                        f"Failed to load detector {module_name}: {str(e)}",
                        {"module": module_name, "error": str(e)}
                    )
    except Exception as e:
        error_reporter.log_error(
            "PipelineError", 
            f"Error discovering detectors: {str(e)}",
            {"detector_dir": detector_dir}
        )
    
    return detectors


def run_detectors(input_data: str, detectors: Dict) -> Dict[str, Any]:
    """Run all discovered detectors on input data."""
    results = {}
    
    for detector_name, detector_module in detectors.items():
        try:
            logger.info(f"Running detector: {detector_name}")
            result = detector_module.run(input_data)
            
            # Validate detector output
            if validator.validate_detector_output(result, detector_name):
                results[detector_name] = result
                logger.info(f"Detector {detector_name} completed successfully")
            else:
                error_reporter.log_validation_error(
                    f"Detector {detector_name} output validation failed",
                    {"detector": detector_name, "output": result}
                )
                # Include result but mark as invalid
                results[detector_name] = {"error": "validation_failed", "raw_output": result}
                
        except Exception as e:
            error_reporter.log_error(
                "DetectorError",
                f"Detector {detector_name} failed: {str(e)}",
                {"detector": detector_name, "input_length": len(input_data)}
            )
            results[detector_name] = {"error": str(e)}
    
    return results


def run_echoverifier(input_data: str) -> Dict[str, Any]:
    """Run EchoVerifier with validation."""
    try:
        import echoverifier
        logger.info("Running EchoVerifier")
        
        result = echoverifier.run(input_data, mode="verify")
        
        # Validate EchoVerifier output
        if validator.validate_echoverifier_output(result):
            logger.info("EchoVerifier completed successfully")
            return result
        else:
            error_reporter.log_validation_error(
                "EchoVerifier output validation failed",
                {"output": result}
            )
            # Return result but mark validation failure
            result["validation_error"] = "schema_validation_failed"
            return result
            
    except ImportError:
        error_reporter.log_error(
            "PipelineError",
            "EchoVerifier module not available"
        )
        return {"error": "echoverifier_not_available"}
    except Exception as e:
        error_reporter.log_error(
            "EchoVerifierError",
            f"EchoVerifier failed: {str(e)}",
            {"input_length": len(input_data)}
        )
        return {"error": str(e)}


def calculate_echo_score(results: Dict[str, Any]) -> float:
    """Calculate overall EchoScore using configurable weights."""
    try:
        base_score = 50.0  # Base score
        
        # Get penalty thresholds from config
        penalty_config = config_manager.get_penalty_thresholds()
        
        # Apply detector penalties/modifiers
        for module_name, module_result in results.items():
            if isinstance(module_result, dict):
                penalty = module_result.get("echo_score_penalty", 0)
                modifier = module_result.get("echo_score_modifier", 0)
                
                base_score += penalty + modifier
        
        # Apply EchoVerifier score influence
        if "echoverifier" in results:
            ev_result = results["echoverifier"]
            if isinstance(ev_result, dict):
                echo_sense = ev_result.get("echo_sense", 0.5)
                # Convert EchoSense (0-1) to score influence (-20 to +20)
                score_influence = (echo_sense - 0.5) * 40
                base_score += score_influence
        
        # Clamp score to valid range
        return max(0.0, min(100.0, base_score))
        
    except Exception as e:
        error_reporter.log_error(
            "ScoreCalculationError",
            f"Failed to calculate echo score: {str(e)}",
            {"results_keys": list(results.keys()) if results else None}
        )
        return 50.0  # Default score on error


def determine_overall_decision(echo_score: float, results: Dict[str, Any]) -> str:
    """Determine overall pipeline decision based on score and results."""
    try:
        # Get verdict thresholds from config
        thresholds = config_manager.get_verdict_thresholds()
        
        # Check for critical errors
        has_critical_errors = False
        for module_result in results.values():
            if isinstance(module_result, dict) and "error" in module_result:
                has_critical_errors = True
                break
        
        if has_critical_errors:
            return "Error"
        
        # Check EchoVerifier verdict if available
        if "echoverifier" in results:
            ev_result = results["echoverifier"]
            if isinstance(ev_result, dict):
                verdict = ev_result.get("verdict")
                if verdict == "Hallucination":
                    return "Synthetic"
                elif verdict == "Authentic" and echo_score >= thresholds["authentic_min"] * 100:
                    return "Authentic"
        
        # Score-based decision
        if echo_score >= thresholds["authentic_min"] * 100:
            return "Authentic"
        elif echo_score >= thresholds["plausible_min"] * 100:
            return "Plausible"
        else:
            return "Questionable"
            
    except Exception as e:
        error_reporter.log_error(
            "DecisionError",
            f"Failed to determine decision: {str(e)}",
            {"echo_score": echo_score}
        )
        return "Error"


def compute_advisory_flags(results):
    """
    Refined advisory flag computation with comprehensive flag collection and categorization.
    
    Collects and categorizes flags from all modules into:
    - Critical flags (require immediate attention)
    - Warning flags (suspicious patterns)
    - Info flags (general observations)
    """
    critical_flags = []
    warning_flags = []
    info_flags = []
    
    # Get penalty thresholds from config
    try:
        penalty_config = config_manager.get_penalty_thresholds()
    except Exception as e:
        error_reporter.log_error(
            "ConfigError",
            f"Failed to get penalty config for advisory flags: {str(e)}"
        )
        penalty_config = {"severe_penalty": -10, "moderate_penalty": -5, "bonus_modifier": 5}
    
    for module_name, module_result in results.items():
        if isinstance(module_result, dict):
            # Direct advisory flags from modules
            if "advisory_flag" in module_result:
                flag = module_result["advisory_flag"]
                # Categorize flags based on content
                if any(keyword in flag.lower() for keyword in ["synthetic", "extreme", "suspicious", "anomaly"]):
                    critical_flags.append(flag)
                elif any(keyword in flag.lower() for keyword in ["borderline", "elevated", "questionable"]):
                    warning_flags.append(flag)
                else:
                    info_flags.append(flag)
            
            # Generate flags based on module results
            source_class = module_result.get("source_classification")
            if source_class == "AI-Generated":
                critical_flags.append(f"{module_name.upper()}: AI-generated content detected")
            elif source_class == "Questionable":
                warning_flags.append(f"{module_name.upper()}: Content authenticity questioned")
            
            # Check for significant penalties or modifiers
            penalty = module_result.get("echo_score_penalty", 0)
            modifier = module_result.get("echo_score_modifier", 0)
            
            if penalty <= penalty_config["severe_penalty"]:
                critical_flags.append(f"{module_name.upper()}: Severe authenticity penalty applied")
            elif penalty <= penalty_config["moderate_penalty"]:
                warning_flags.append(f"{module_name.upper()}: Moderate authenticity penalty applied")
            elif modifier >= penalty_config["bonus_modifier"]:
                info_flags.append(f"{module_name.upper()}: Authenticity bonus applied")
    
    # Special handling for EchoVerifier results
    if "echoverifier" in results:
        ev_result = results["echoverifier"]
        if isinstance(ev_result, dict):
            verdict = ev_result.get("verdict")
            if verdict == "Hallucination":
                critical_flags.append("ECHOVERIFIER: Hallucination detected")
            elif verdict == "Plausible":
                warning_flags.append("ECHOVERIFIER: Content classified as plausible")
            elif verdict == "Authentic":
                info_flags.append("ECHOVERIFIER: Content verified as authentic")
            
            # Check vault permission
            vault_perm = ev_result.get("vault_permission", False)
            if not vault_perm:
                warning_flags.append("ECHOVERIFIER: Vault access denied")
    
    # Combine flags in priority order: Critical -> Warning -> Info
    all_flags = critical_flags + warning_flags + info_flags
    
    # Remove duplicates while preserving order
    seen = set()
    unique_flags = []
    for flag in all_flags:
        if flag not in seen:
            unique_flags.append(flag)
            seen.add(flag)
    
    return unique_flags


def run_pipeline(input_data: str, input_type: str = "text") -> Dict[str, Any]:
    """
    Main EchoScan pipeline that integrates all components with validation and error reporting.
    
    Args:
        input_data: Input text to process or file path
        input_type: Type of input (text, file)
    
    Returns:
        Complete pipeline results with validation
    """
    try:
        logger.info(f"Starting EchoScan pipeline for {input_type} input")
        
        # Handle file input
        if input_type == "file" or (input_type == "text" and os.path.isfile(input_data)):
            try:
                with open(input_data, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                logger.info(f"Loaded content from file: {input_data}")
            except Exception as e:
                error_reporter.log_error(
                    "FileError",
                    f"Failed to read input file: {str(e)}",
                    {"file_path": input_data}
                )
                return {
                    "error": f"Failed to read input file: {str(e)}",
                    "EchoScore": 0.0,
                    "Decision": "Error", 
                    "AdvisoryFlags": ["PIPELINE: File read error"],
                    "FullResults": {}
                }
        else:
            text_content = input_data
        
        if not text_content.strip():
            error_reporter.log_error("PipelineError", "Empty input provided")
            return {
                "error": "Empty input provided",
                "EchoScore": 0.0,
                "Decision": "Error",
                "AdvisoryFlags": ["PIPELINE: Empty input provided"],
                "FullResults": {}
            }
        
        # Initialize results
        full_results = {}
        
        # Step 1: Run all detectors
        logger.info("Discovering and running detectors")
        detectors = discover_detectors()
        detector_results = run_detectors(text_content, detectors)
        full_results.update(detector_results)
        
        # Step 2: Run EchoVerifier
        logger.info("Running EchoVerifier")
        echoverifier_result = run_echoverifier(text_content)
        full_results["echoverifier"] = echoverifier_result
        
        # Step 3: Calculate overall score
        logger.info("Calculating EchoScore")
        echo_score = calculate_echo_score(full_results)
        
        # Step 4: Determine overall decision
        logger.info("Determining overall decision")
        decision = determine_overall_decision(echo_score, full_results)
        
        # Step 5: Compute advisory flags
        logger.info("Computing advisory flags")
        advisory_flags = compute_advisory_flags(full_results)
        
        # Step 6: Compile final results
        pipeline_result = {
            "EchoScore": echo_score,
            "Decision": decision,  # Changed from "Decision Label" to match schema
            "AdvisoryFlags": advisory_flags,
            "FullResults": full_results
        }
        
        # Step 7: Validate pipeline output
        logger.info("Validating pipeline output")
        if not validator.validate_pipeline_output(pipeline_result):
            error_reporter.log_validation_error(
                "Pipeline output validation failed",
                {"result_keys": list(pipeline_result.keys())}
            )
            # Add validation warning but return results
            pipeline_result["validation_warning"] = "Pipeline output validation failed"
        
        logger.info("EchoScan pipeline completed successfully")
        return pipeline_result
        
    except Exception as e:
        error_reporter.log_error(
            "PipelineError",
            f"Pipeline execution failed: {str(e)}",
            {"input_type": input_type, "input_length": len(input_data) if isinstance(input_data, str) else None}
        )
        return {
            "error": f"Pipeline execution failed: {str(e)}",
            "EchoScore": 0.0,
            "Decision": "Error",  # Changed from "Decision Label"
            "AdvisoryFlags": ["PIPELINE: Execution error occurred"],
            "FullResults": {}
        }