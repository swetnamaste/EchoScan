"""
EchoScan Main Pipeline Module

Implements the main EchoScan pipeline using the core integration utilities.
This module orchestrates all detector modules and provides the main entry points.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

# Import core integration utilities
from core_integration import (
    InputNormalizer, 
    ModuleExecutor, 
    ScoreCalculator, 
    AdvisoryFlagCollector,
    OutputStructurer,
    EchoScanResult,
    compute_advisory_flags  # For backward compatibility
)

# Import detector modules
try:
    import detectors.sbsm as sbsm
    import detectors.delta_s as delta_s
    import detectors.echosense as echosense
    import detectors.mimetic_drift as mimetic_drift
    import detectors.obelisk as obelisk
    import detectors.glyph as glyph
    import detectors.stuttergate as stuttergate
    import detectors.pulseadapt as pulseadapt
    import detectors.voicecradle as voicecradle
    import detectors.motif as motif
    import detectors.echostamp as echostamp
    import detectors.ai_drift as ai_drift
    import detectors.foldback as foldback
    import detectors.nsnl as nsnl
    import detectors.echoarc as echoarc
    import detectors.collapseglyph as collapseglyph
    import detectors.ecc_core as ecc_core
    import detectors.echocradle as echocradle
except ImportError as e:
    logging.warning(f"Some detector modules could not be imported: {e}")

# Import EchoVerifier
try:
    import echoverifier
except ImportError:
    echoverifier = None

# Configure logging
logger = logging.getLogger('EchoScan.Pipeline')


def get_available_detectors() -> Dict[str, Any]:
    """Get list of available detector modules with their run functions."""
    detectors = {}
    
    # Core detectors
    detector_modules = [
        ('sbsm', sbsm),
        ('delta_s', delta_s), 
        ('echosense', echosense),
        ('mimetic_drift', mimetic_drift),
        ('obelisk', obelisk),
        ('glyph', glyph),
        ('stuttergate', stuttergate),
        ('pulseadapt', pulseadapt),
        ('voicecradle', voicecradle),
        ('motif', motif),
        ('echostamp', echostamp),
        ('ai_drift', ai_drift),
        ('foldback', foldback),
        ('nsnl', nsnl),
        ('echoarc', echoarc),
        ('collapseglyph', collapseglyph),
        ('ecc_core', ecc_core),
        ('echocradle', echocradle)
    ]
    
    for name, module in detector_modules:
        try:
            if hasattr(module, 'run'):
                detectors[name] = module.run
                logger.debug(f"Loaded detector: {name}")
        except Exception as e:
            logger.warning(f"Failed to load detector {name}: {e}")
    
    return detectors


def run_pipeline(input_source: Union[str, Path], 
                input_type: str = "text",
                dry_run: bool = False,
                selected_detectors: Optional[List[str]] = None,
                include_echoverifier: bool = True) -> Dict[str, Any]:
    """
    Run the complete EchoScan pipeline.
    
    Args:
        input_source: Input data (string content, file path, etc.)
        input_type: Type of input ("text", "image", "audio", "video")
        dry_run: If True, perform validation without full processing
        selected_detectors: List of specific detectors to run (None = all available)
        include_echoverifier: Whether to include EchoVerifier analysis
        
    Returns:
        Structured pipeline results
    """
    logger.info(f"Starting EchoScan pipeline - Input type: {input_type}, Dry run: {dry_run}")
    
    # Step 1: Input normalization
    try:
        normalization_result = InputNormalizer.normalize_input(
            input_source, input_type, dry_run
        )
        
        if not normalization_result.success:
            return OutputStructurer.structure_output(
                str(input_source),
                input_type,
                {"input_normalizer": normalization_result},
                {"final_score": 0.0, "decision_label": "Error"},
                {"critical": normalization_result.errors, "warning": [], "info": [], "all": normalization_result.errors},
                dry_run
            )
            
        normalized_input = normalization_result.results.get("normalized_input", "")
        
    except Exception as e:
        logger.exception("Failed to normalize input")
        error_result = EchoScanResult("input_normalizer")
        error_result.add_error(f"Input normalization failed: {e}")
        
        return OutputStructurer.structure_output(
            str(input_source),
            input_type,
            {"input_normalizer": error_result},
            {"final_score": 0.0, "decision_label": "Error"},
            {"critical": [f"Input normalization failed: {e}"], "warning": [], "info": [], "all": [f"Input normalization failed: {e}"]},
            dry_run
        )
    
    # Step 2: Get available detectors
    available_detectors = get_available_detectors()
    
    if selected_detectors:
        # Use only selected detectors
        detectors_to_run = {name: func for name, func in available_detectors.items() 
                           if name in selected_detectors}
        missing = set(selected_detectors) - set(available_detectors.keys())
        if missing:
            logger.warning(f"Requested detectors not available: {missing}")
    else:
        # Use all available detectors
        detectors_to_run = available_detectors
    
    logger.info(f"Running {len(detectors_to_run)} detectors: {list(detectors_to_run.keys())}")
    
    # Step 3: Execute detectors
    executor = ModuleExecutor(dry_run=dry_run)
    module_results = {"input_normalizer": normalization_result}
    
    for detector_name, detector_func in detectors_to_run.items():
        try:
            result = executor.execute_module(
                detector_name, 
                detector_func, 
                normalized_input
            )
            module_results[detector_name] = result
            
        except Exception as e:
            logger.exception(f"Detector {detector_name} failed unexpectedly")
            error_result = EchoScanResult(detector_name)
            error_result.add_error(f"Unexpected failure: {e}")
            module_results[detector_name] = error_result
    
    # Step 4: Run EchoVerifier if requested and available
    if include_echoverifier and echoverifier and not dry_run:
        try:
            logger.info("Running EchoVerifier analysis")
            ev_result = echoverifier.run(normalized_input, mode="verify")
            
            # Convert EchoVerifier result to EchoScanResult format
            echo_result = EchoScanResult("echoverifier", normalized_input)
            if isinstance(ev_result, dict):
                for key, value in ev_result.items():
                    echo_result.add_result(key, value)
                    
                # Extract standard fields from EchoVerifier
                verdict = ev_result.get("verdict", "Unknown")
                if verdict == "Hallucination":
                    echo_result.add_advisory_flag("Hallucination detected")
                    echo_result.set_source_classification("AI-Generated")
                    echo_result.set_score_modifier(0.0, -20.0)
                elif verdict == "Plausible":
                    echo_result.add_advisory_flag("Content classified as plausible")
                    echo_result.set_source_classification("Questionable")
                    echo_result.set_score_modifier(0.0, -5.0)
                elif verdict == "Authentic":
                    echo_result.add_advisory_flag("Content verified as authentic")
                    echo_result.set_source_classification("Human-Generated")
                    echo_result.set_score_modifier(10.0, 0.0)
            else:
                echo_result.add_warning("EchoVerifier returned non-dict result")
                echo_result.add_result("raw_result", ev_result)
                
            module_results["echoverifier"] = echo_result
            
        except Exception as e:
            logger.exception("EchoVerifier analysis failed")
            error_result = EchoScanResult("echoverifier")
            error_result.add_error(f"EchoVerifier failed: {e}")
            module_results["echoverifier"] = error_result
    elif include_echoverifier and dry_run:
        # Dry run for EchoVerifier
        dry_result = EchoScanResult("echoverifier", dry_run=True)
        dry_result.add_result("status", "DRY RUN - EchoVerifier would be executed")
        module_results["echoverifier"] = dry_result
    
    # Step 5: Calculate scores
    try:
        score_data = ScoreCalculator.calculate_echo_score(module_results)
        logger.info(f"Echo Score calculated: {score_data['final_score']} ({score_data['decision_label']})")
    except Exception as e:
        logger.exception("Score calculation failed")
        score_data = {
            "final_score": 0.0,
            "decision_label": "Error",
            "error": f"Score calculation failed: {e}"
        }
    
    # Step 6: Collect advisory flags
    try:
        advisory_flags = AdvisoryFlagCollector.collect_flags(module_results)
        logger.info(f"Collected {len(advisory_flags['all'])} advisory flags")
    except Exception as e:
        logger.exception("Advisory flag collection failed")
        advisory_flags = {
            "critical": [f"Flag collection failed: {e}"],
            "warning": [],
            "info": [],
            "all": [f"Flag collection failed: {e}"]
        }
    
    # Step 7: Structure output
    try:
        execution_metadata = {
            "detectors_available": len(available_detectors),
            "detectors_executed": len(detectors_to_run),
            "execution_log": executor.get_execution_log(),
            "echoverifier_included": include_echoverifier
        }
        
        final_output = OutputStructurer.structure_output(
            normalized_input,
            input_type,
            module_results,
            score_data,
            advisory_flags,
            dry_run,
            execution_metadata
        )
        
        logger.info("Pipeline execution completed successfully")
        return final_output
        
    except Exception as e:
        logger.exception("Output structuring failed")
        # Fallback to basic output structure
        return {
            "error": "Output structuring failed",
            "details": str(e),
            "partial_results": {
                "score_data": score_data,
                "advisory_flags": advisory_flags,
                "module_count": len(module_results)
            }
        }


def run_single_detector(detector_name: str, 
                       input_data: str, 
                       dry_run: bool = False) -> Dict[str, Any]:
    """
    Run a single detector module.
    
    Args:
        detector_name: Name of the detector to run
        input_data: Input data for the detector
        dry_run: Whether to perform a dry run
        
    Returns:
        Detector results
    """
    available_detectors = get_available_detectors()
    
    if detector_name not in available_detectors:
        return {
            "error": f"Detector '{detector_name}' not available",
            "available_detectors": list(available_detectors.keys())
        }
    
    executor = ModuleExecutor(dry_run=dry_run)
    result = executor.execute_module(
        detector_name,
        available_detectors[detector_name],
        input_data
    )
    
    return result.to_dict()


# Legacy function for backward compatibility
def compute_advisory_flags(results):
    """
    Legacy function maintained for backward compatibility.
    Uses the new AdvisoryFlagCollector internally.
    """
    return compute_advisory_flags(results)