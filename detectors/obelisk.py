"""Obelisk Detector Module

Updated to use standardized EchoScan schema and error handling.
Analyzes symmetry patterns and entropy characteristics.
"""

import numpy as np
from typing import Dict, Any


def run(stream: str, **kwargs) -> Dict[str, Any]:
    """
    Run Obelisk symmetry and entropy analysis.
    
    Args:
        stream: Input text stream to analyze
        **kwargs: Additional arguments (sbsm_result, delta_s_result, etc.)
        
    Returns:
        Standardized result dictionary
    """
    result = {
        "detector": "obelisk",
        "success": True,
        "echo_score_modifier": 0.0,
        "source_classification": "Unknown"
    }
    
    try:
        # Handle empty input
        if not stream or len(stream) == 0:
            result.update({
                "symmetry_score": 0.0,
                "entropy": 0.0,
                "verdict": "No data",
                "warning": "Empty input provided"
            })
            return result
        
        # Symmetry check (mirror about center)
        half = len(stream) // 2
        symmetry_score = 0.0
        
        if half > 0:
            left = stream[:half]
            right = stream[-half:][::-1]  # Reverse the right half
            matches = sum(1 for i in range(half) if left[i] == right[i])
            symmetry_score = matches / half
        
        # Entropy calculation
        try:
            ascii_vals = np.array([ord(c) for c in stream])
            unique_chars = set(stream)
            
            if len(unique_chars) == 0:
                entropy = 0.0
            else:
                # Calculate character probabilities
                probs = []
                for ch in unique_chars:
                    count = stream.count(ch)
                    if count > 0:
                        probs.append(count / len(stream))
                
                # Calculate Shannon entropy
                entropy = 0.0
                for p in probs:
                    if p > 0:
                        entropy -= p * np.log2(p)
                
        except Exception as e:
            result["warning"] = f"Entropy calculation error: {e}"
            entropy = 0.0
        
        # Determine verdict and classification based on symmetry and entropy
        if symmetry_score > 0.7:
            verdict = "High symmetry"
            source_classification = "AI-Generated"  # Perfect symmetry suggests artificial generation
            advisory_flag = "Unusual symmetry pattern detected"
            score_modifier = -0.3
        elif symmetry_score > 0.3:
            verdict = "Moderate symmetry"
            source_classification = "Questionable"
            advisory_flag = "Elevated symmetry detected"
            score_modifier = -0.1
        else:
            verdict = "Natural asymmetry"
            source_classification = "Human-Generated"
            advisory_flag = None
            score_modifier = 0.1
        
        # Adjust based on entropy (very low entropy suggests artificial content)
        if entropy < 1.0:
            if advisory_flag:
                advisory_flag += " + Low entropy"
            else:
                advisory_flag = "Low entropy detected"
            score_modifier -= 0.2
        elif entropy > 4.0:
            score_modifier += 0.1  # High entropy bonus
        
        # Combined score calculation
        combined_score = (symmetry_score * 0.7) + (1 / (1 + entropy)) * 0.3
        
        result.update({
            "symmetry_score": round(symmetry_score, 6),
            "entropy": round(entropy, 6),
            "combined_score": round(combined_score, 6),
            "verdict": verdict,
            "echo_score_modifier": round(score_modifier, 3),
            "source_classification": source_classification,
            "analysis": {
                "text_length": len(stream),
                "unique_chars": len(unique_chars) if 'unique_chars' in locals() else 0,
                "mirror_half_size": half
            }
        })
        
        if advisory_flag:
            result["advisory_flag"] = advisory_flag
            
    except Exception as e:
        result.update({
            "error": f"Obelisk analysis failed: {e}",
            "success": False,
            "symmetry_score": 0.0,
            "entropy": 0.0,
            "verdict": "Analysis failed"
        })
    
    return result