"""AI Drift Detector Module

Updated to use standardized EchoScan schema and error handling.
Analyzes drift patterns across bases 6-9 to detect AI-generated content.
"""

import numpy as np
from typing import Dict, Any


def run(stream: str, **kwargs) -> Dict[str, Any]:
    """
    Run AI drift detection analysis.
    
    Args:
        stream: Input text stream to analyze
        **kwargs: Additional arguments (delta_s_result, sbsm_result, etc.)
        
    Returns:
        Standardized result dictionary
    """
    result = {
        "detector": "ai_drift",
        "success": True,
        "echo_score_modifier": 0.0,
        "source_classification": "Unknown"
    }
    
    try:
        # Handle empty input
        if not stream or len(stream) == 0:
            result.update({
                "drift_variance": 0.0,
                "verdict": "No data",
                "warning": "Empty input provided",
                "echo_score_modifier": 0.0,
                "source_classification": "Unknown"
            })
            return result
        
        # Convert to ASCII values
        ascii_vals = np.array([ord(c) for c in stream])
        
        # Digit sum function for different bases
        def digit_sum(n, base):
            return sum(int(d) for d in np.base_repr(n, base))
        
        # Calculate drift profiles across bases 6-9
        drift_profiles = []
        for base in [6, 7, 8, 9]:
            try:
                profile = [digit_sum(v, base) for v in ascii_vals]
                drift_profiles.append(profile)
            except Exception as e:
                # Handle individual base calculation errors
                result["warning"] = f"Base {base} calculation failed: {e}"
                continue
        
        if not drift_profiles:
            result.update({
                "drift_variance": 0.0,
                "verdict": "Calculation failed",
                "error": "All base calculations failed",
                "success": False
            })
            return result
        
        # Calculate variance of differences
        variances = []
        for profile in drift_profiles:
            if len(profile) > 1:
                diff_profile = np.diff(profile)
                variances.append(np.var(diff_profile))
            else:
                variances.append(0.0)
        
        # Calculate mean drift variance
        drift_var = float(np.mean(variances)) if variances else 0.0
        
        # Determine verdict based on variance
        # High variance indicates unstable human-like stream
        # Low variance (flat drift) indicates synthetic AI filler
        if drift_var < 0.10:
            verdict = "AI-like drift"
            source_classification = "AI-Generated"
            score_modifier = -0.5  # Penalty for AI-like patterns
            advisory_flag = "Low drift variance suggests AI-generated content"
        elif drift_var < 0.25:
            verdict = "Borderline drift"
            source_classification = "Questionable" 
            score_modifier = -0.2
            advisory_flag = "Borderline drift variance detected"
        else:
            verdict = "Human-like drift"
            source_classification = "Human-Generated"
            score_modifier = 0.3  # Bonus for human-like patterns
            advisory_flag = None
        
        result.update({
            "drift_variance": round(drift_var, 6),
            "verdict": verdict,
            "base_profiles_count": len(drift_profiles),
            "echo_score_modifier": score_modifier,
            "source_classification": source_classification
        })
        
        if advisory_flag:
            result["advisory_flag"] = advisory_flag
        
    except Exception as e:
        result.update({
            "error": f"AI drift analysis failed: {e}",
            "success": False,
            "drift_variance": 0.0,
            "verdict": "Analysis failed"
        })
    
    return result