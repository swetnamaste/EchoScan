"""Enhanced Delta S drift test detector module with dynamic thresholds and context-aware penalties."""

import math
import numpy as np
from typing import Dict, Any, Optional


def calculate_dynamic_baseline(input_string: str, context_modules: Optional[Dict] = None) -> Dict[str, float]:
    """Calculate dynamic baseline penalty based on context from other modules."""
    
    # Base penalty calculation
    base_penalty = 0.1
    
    # Context-aware adjustments
    drift_variance = 1.0
    ancestry_depth = 3.0  # Default moderate depth
    
    if context_modules:
        # Get ancestry depth from context
        if "ancestry_depth" in context_modules:
            ancestry_depth = max(1.0, float(context_modules["ancestry_depth"]))
        
        # Get variance estimate from input characteristics
        char_diversity = len(set(input_string)) / max(1, len(input_string))
        drift_variance = max(0.1, char_diversity * 2)  # Higher diversity = higher expected variance
        
        # Module agreement factor
        module_agreement = context_modules.get("module_agreement", 0.5)
        if module_agreement > 0.8:  # High agreement across modules
            base_penalty *= 1.2  # Increase penalty weight when modules agree
        elif module_agreement < 0.3:  # Low agreement
            base_penalty *= 0.8  # Reduce penalty weight when modules disagree
    
    # Dynamic scaling formula: penalty = base_penalty × (drift_variance / ancestry_depth)
    scaling_factor = drift_variance / ancestry_depth
    dynamic_penalty = base_penalty * scaling_factor
    
    return {
        "base_penalty": base_penalty,
        "drift_variance": drift_variance,
        "ancestry_depth": ancestry_depth,
        "scaling_factor": scaling_factor,
        "dynamic_penalty": dynamic_penalty
    }


def calculate_enhanced_delta_s(input_string: str) -> Dict[str, float]:
    """Calculate enhanced delta S with multiple window sizes and statistical analysis."""
    
    if not input_string:
        return {
            "delta_s": 0.0,
            "variance": 0.0,
            "stability_score": 1.0,
            "anomaly_flags": []
        }
    
    # Convert to ASCII values
    ascii_vals = [ord(c) for c in input_string]
    
    # Calculate delta S for multiple window sizes
    window_sizes = [3, 5, 10, 15, 20]
    window_deltas = {}
    
    for window_size in window_sizes:
        if len(ascii_vals) >= window_size:
            deltas = []
            for i in range(len(ascii_vals) - window_size + 1):
                window = ascii_vals[i:i + window_size]
                window_delta = sum(abs(window[j] - window[j-1]) for j in range(1, len(window)))
                window_delta /= (len(window) - 1)  # Normalize by window size
                deltas.append(window_delta)
            window_deltas[window_size] = deltas
    
    # Calculate overall delta S as weighted average
    if window_deltas:
        all_deltas = []
        for window_size, deltas in window_deltas.items():
            # Weight larger windows more heavily
            weight = math.log(window_size + 1)
            all_deltas.extend([delta * weight for delta in deltas])
        
        overall_delta_s = np.mean(all_deltas)
        delta_variance = np.var(all_deltas)
        
        # Calculate stability score (lower variance = more stable)
        stability_score = max(0.0, 1.0 - (delta_variance / max(1.0, overall_delta_s ** 2)))
    else:
        overall_delta_s = abs(hash(input_string)) % 1000 / 100000.0  # Fallback
        delta_variance = 0.0
        stability_score = 1.0
    
    # Detect anomaly patterns
    anomaly_flags = []
    if overall_delta_s < 0.001:
        anomaly_flags.append("suspicious_uniformity")
    elif overall_delta_s > 0.1:
        anomaly_flags.append("extreme_drift")
    
    if delta_variance > overall_delta_s * 2:
        anomaly_flags.append("high_variance")
    elif delta_variance < overall_delta_s * 0.1:
        anomaly_flags.append("low_variance")
    
    return {
        "delta_s": overall_delta_s,
        "variance": delta_variance,
        "stability_score": stability_score,
        "anomaly_flags": anomaly_flags,
        "window_analysis": {size: np.mean(deltas) for size, deltas in window_deltas.items()}
    }


def assess_synthetic_likelihood(delta_analysis: Dict, baseline: Dict, input_string: str) -> Dict[str, Any]:
    """Assess likelihood of synthetic content using enhanced thresholds."""
    
    delta_s = delta_analysis["delta_s"]
    variance = delta_analysis["variance"]
    stability = delta_analysis["stability_score"]
    anomaly_flags = delta_analysis["anomaly_flags"]
    
    # Dynamic threshold calculation
    base_threshold = 0.02  # Base threshold for authenticity
    dynamic_penalty = baseline["dynamic_penalty"]
    
    # Adjust threshold based on content characteristics
    adjusted_threshold = base_threshold * (1 + dynamic_penalty)
    
    # Synthetic likelihood assessment
    synthetic_score = 0.0
    confidence_factors = []
    
    # Delta S factor
    if delta_s > adjusted_threshold:
        delta_factor = min(1.0, (delta_s - adjusted_threshold) / adjusted_threshold)
        synthetic_score += delta_factor * 0.4
        confidence_factors.append(f"high_delta_s:{delta_factor:.3f}")
    
    # Variance factor
    if "high_variance" in anomaly_flags:
        variance_factor = min(1.0, variance / max(0.001, delta_s))
        synthetic_score += variance_factor * 0.2
        confidence_factors.append(f"high_variance:{variance_factor:.3f}")
    elif "low_variance" in anomaly_flags:
        synthetic_score += 0.3  # Suspiciously low variance
        confidence_factors.append("suspiciously_uniform")
    
    # Stability factor
    if stability < 0.3:
        instability_factor = 1.0 - stability
        synthetic_score += instability_factor * 0.2
        confidence_factors.append(f"instability:{instability_factor:.3f}")
    
    # Extreme cases
    if "suspicious_uniformity" in anomaly_flags:
        synthetic_score += 0.5
        confidence_factors.append("suspicious_uniformity")
    elif "extreme_drift" in anomaly_flags:
        synthetic_score += 0.4
        confidence_factors.append("extreme_drift")
    
    # Content-length adjustment
    length_factor = 1.0
    if len(input_string) < 10:
        length_factor = 1.5  # Higher penalty for very short content
    elif len(input_string) > 1000:
        length_factor = 0.8  # Lower penalty for longer content
    
    final_synthetic_score = min(1.0, synthetic_score * length_factor)
    
    # Determine classification
    if final_synthetic_score > 0.7:
        classification = "highly_synthetic"
    elif final_synthetic_score > 0.4:
        classification = "possibly_synthetic"
    elif final_synthetic_score > 0.2:
        classification = "questionable"
    else:
        classification = "likely_authentic"
    
    return {
        "synthetic_likelihood": round(final_synthetic_score, 3),
        "classification": classification,
        "confidence_factors": confidence_factors,
        "adjusted_threshold": adjusted_threshold,
        "length_adjustment": length_factor
    }


def run(input_string: str, context_modules: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Enhanced delta S drift test with dynamic scaling and context-aware penalties.
    
    Args:
        input_string: Input text to analyze
        context_modules: Optional context from other analysis modules
    
    Returns:
        Dict containing enhanced delta S analysis results
    """
    
    if not input_string:
        return {
            "detector": "delta_s_enhanced",
            "delta_s": 0.0,
            "drift_score": 0.0,
            "echo_score_modifier": 0.0,
            "synthetic_assessment": {"classification": "insufficient_data"},
            "dynamic_baseline": {"dynamic_penalty": 0.1}
        }
    
    # Calculate dynamic baseline with context awareness
    baseline = calculate_dynamic_baseline(input_string, context_modules)
    
    # Enhanced delta S calculation
    delta_analysis = calculate_enhanced_delta_s(input_string)
    
    # Assess synthetic likelihood
    synthetic_assessment = assess_synthetic_likelihood(delta_analysis, baseline, input_string)
    
    # Calculate echo score modifier based on synthetic likelihood
    synthetic_score = synthetic_assessment["synthetic_likelihood"]
    
    if synthetic_score > 0.7:
        echo_modifier = -synthetic_score * 15  # Strong penalty
    elif synthetic_score > 0.4:
        echo_modifier = -synthetic_score * 10  # Moderate penalty  
    elif synthetic_score > 0.2:
        echo_modifier = -synthetic_score * 5   # Mild penalty
    else:
        echo_modifier = synthetic_score * 2     # Small bonus for clearly authentic content
    
    return {
        "detector": "delta_s_enhanced",
        "delta_s": round(delta_analysis["delta_s"], 6),
        "drift_score": round(delta_analysis["delta_s"], 6),
        "echo_score_modifier": round(echo_modifier, 2),
        "variance": round(delta_analysis["variance"], 6),
        "stability_score": round(delta_analysis["stability_score"], 3),
        "anomaly_flags": delta_analysis["anomaly_flags"],
        "synthetic_assessment": synthetic_assessment,
        "dynamic_baseline": baseline,
        "window_analysis": delta_analysis["window_analysis"]
    }