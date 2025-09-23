#!/usr/bin/env python3
"""
EchoScan Main Pipeline Module
Orchestrates the full EchoScan pipeline with multiple detection modules.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import echoverifier
import sbsh_module
from typing import Dict, Any, Union


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
            
            if penalty <= -10:
                critical_flags.append(f"{module_name.upper()}: Severe authenticity penalty applied")
            elif penalty <= -5:
                warning_flags.append(f"{module_name.upper()}: Moderate authenticity penalty applied")
            elif modifier >= 5:
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


def run_pipeline(input_file: str, input_type: str = "text") -> Dict[str, Any]:
    """
    Run the full EchoScan pipeline on input data.
    
    Args:
        input_file: Path to input file or direct input string
        input_type: Type of input (text, image, audio, video)
    
    Returns:
        Dictionary containing pipeline results including EchoScore, Decision Label, and full results
    """
    try:
        # Read input data
        if os.path.isfile(input_file):
            with open(input_file, 'r', encoding='utf-8') as f:
                input_data = f.read()
        else:
            input_data = input_file  # Treat as direct input string
        
        # Run core detection modules
        results = {}
        
        # Run EchoVerifier (main authenticity analysis)
        try:
            echo_result = echoverifier.run(input_data, mode="verify")
            results["echoverifier"] = echo_result
        except Exception as e:
            results["echoverifier"] = {"error": str(e), "echo_score_penalty": -10}
        
        # Run SBSH symbolic hash if available
        try:
            if hasattr(sbsh_module, 'sbsh_hash'):
                sbsh_result = sbsh_module.sbsh_hash(input_data)
                results["sbsh"] = sbsh_result
        except Exception as e:
            results["sbsh"] = {"error": str(e), "echo_score_penalty": -2}
        
        # Calculate overall EchoScore
        base_score = 50  # Base authenticity score
        echo_score = base_score
        
        # Apply scoring from modules
        for module_name, module_result in results.items():
            if isinstance(module_result, dict):
                penalty = module_result.get("echo_score_penalty", 0)
                modifier = module_result.get("echo_score_modifier", 0)
                echo_score += penalty + modifier
                
                # EchoVerifier specific scoring
                if module_name == "echoverifier" and "echo_sense" in module_result:
                    echo_sense = module_result["echo_sense"]
                    echo_score += (echo_sense - 0.5) * 20  # Scale echo_sense to score
        
        # Clamp score to valid range
        echo_score = max(0, min(100, echo_score))
        
        # Determine decision label based on score and results
        if echo_score >= 75:
            decision_label = "Authentic"
        elif echo_score >= 50:
            decision_label = "Plausible"
        elif echo_score >= 25:
            decision_label = "Questionable"
        else:
            decision_label = "Suspicious"
        
        # Check for specific verdicts that override score-based decisions
        if "echoverifier" in results and isinstance(results["echoverifier"], dict):
            verdict = results["echoverifier"].get("verdict")
            if verdict == "Hallucination":
                decision_label = "Hallucination"
            elif verdict in ["Authentic", "Plausible"]:
                decision_label = verdict
        
        # Compute advisory flags
        advisory_flags = compute_advisory_flags(results)
        
        # Build final result
        pipeline_result = {
            "EchoScore": round(echo_score, 2),
            "Decision Label": decision_label,
            "Advisory Flags": advisory_flags,
            "FullResults": results,
            "InputType": input_type,
            "ProcessedLength": len(input_data),
            "Status": "completed"
        }
        
        return pipeline_result
        
    except Exception as e:
        return {
            "EchoScore": 0,
            "Decision Label": "Error",
            "Advisory Flags": [f"PIPELINE_ERROR: {str(e)}"],
            "FullResults": {},
            "InputType": input_type,
            "ProcessedLength": 0,
            "Status": "error",
            "Error": str(e)
        }