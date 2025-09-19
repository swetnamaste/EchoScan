"""
Context Drift Vectors - SBSM ∆S drift measurement across text blocks
Measures semantic authenticity by tracking drift patterns across paragraphs/blocks.
"""

import re
from typing import Dict, List, Any, Tuple
from . import sbsm


def segment_text_into_blocks(text: str, min_block_size: int = 50) -> List[str]:
    """
    Segment text into logical blocks (paragraphs/sentences).
    
    Args:
        text: Input text to segment
        min_block_size: Minimum characters per block
        
    Returns:
        List of text blocks
    """
    # Split by double newlines (paragraphs) first
    paragraphs = re.split(r'\n\s*\n', text.strip())
    blocks = []
    
    for paragraph in paragraphs:
        if len(paragraph) >= min_block_size:
            blocks.append(paragraph.strip())
        elif blocks:
            # Merge short paragraphs with previous block
            blocks[-1] += " " + paragraph.strip()
        else:
            # First block is short, keep it anyway
            blocks.append(paragraph.strip())
    
    # If no paragraph breaks, split by sentences for longer texts
    if len(blocks) == 1 and len(text) > min_block_size * 2:
        sentences = re.split(r'[.!?]+\s+', text)
        blocks = []
        current_block = ""
        
        for sentence in sentences:
            if len(current_block + sentence) < min_block_size:
                current_block += sentence + ". "
            else:
                if current_block:
                    blocks.append(current_block.strip())
                current_block = sentence + ". "
        
        if current_block:
            blocks.append(current_block.strip())
    
    return [block for block in blocks if block.strip()]


def calculate_drift_vectors(blocks: List[str]) -> Dict[str, Any]:
    """
    Calculate SBSM drift vectors for each block and measure drift patterns.
    
    Args:
        blocks: List of text blocks to analyze
        
    Returns:
        Dict containing drift analysis results
    """
    if not blocks:
        return {
            "block_count": 0,
            "drift_vectors": [],
            "drift_progression": [],
            "drift_variance": 0.0,
            "drift_consistency": 1.0,
            "anomaly_score": 0.0
        }
    
    block_results = []
    drift_values = []
    
    # Analyze each block with SBSM
    for i, block in enumerate(blocks):
        try:
            result = sbsm.sbsm_matrix(block)
            drift_value = result.get("global_drift", 0.0)
            
            block_results.append({
                "block_index": i,
                "block_length": len(block),
                "block_preview": block[:50] + "..." if len(block) > 50 else block,
                "sbsm_drift": drift_value,
                "sbsm_status": result.get("status", "Unknown"),
                "stability_ratio": result.get("stability_ratio", 0.0)
            })
            drift_values.append(drift_value)
            
        except Exception as e:
            # Handle blocks that might cause SBSM issues
            block_results.append({
                "block_index": i,
                "block_length": len(block),
                "block_preview": block[:50] + "..." if len(block) > 50 else block,
                "sbsm_drift": 0.0,
                "sbsm_status": f"Error: {str(e)}",
                "stability_ratio": 0.0
            })
            drift_values.append(0.0)
    
    # Calculate drift progression and variance
    drift_progression = []
    if len(drift_values) > 1:
        for i in range(1, len(drift_values)):
            drift_change = abs(drift_values[i] - drift_values[i-1])
            drift_progression.append(drift_change)
    
    # Calculate drift statistics
    if drift_values:
        mean_drift = sum(drift_values) / len(drift_values)
        drift_variance = sum((d - mean_drift) ** 2 for d in drift_values) / len(drift_values)
        
        # Consistency metric: lower variance suggests more consistent (potentially synthetic) content
        max_possible_variance = mean_drift ** 2  # Theoretical maximum variance
        drift_consistency = 1.0 - (drift_variance / max(max_possible_variance, 0.001))
        drift_consistency = max(0.0, min(1.0, drift_consistency))
        
        # Anomaly score: very low variance or extreme values indicate potential issues
        anomaly_score = 0.0
        if drift_variance < 0.001:  # Too consistent
            anomaly_score += 0.5
        if any(d > 10.0 for d in drift_values):  # Extreme drift values
            anomaly_score += 0.3
        if any(d < 0.001 for d in drift_values):  # Suspiciously low drift
            anomaly_score += 0.2
            
    else:
        mean_drift = 0.0
        drift_variance = 0.0
        drift_consistency = 1.0
        anomaly_score = 1.0  # No data is anomalous
    
    return {
        "block_count": len(blocks),
        "drift_vectors": block_results,
        "drift_progression": drift_progression,
        "mean_drift": round(mean_drift, 6),
        "drift_variance": round(drift_variance, 6),
        "drift_consistency": round(drift_consistency, 6),
        "anomaly_score": round(anomaly_score, 6),
        "drift_range": {
            "min": round(min(drift_values), 6) if drift_values else 0.0,
            "max": round(max(drift_values), 6) if drift_values else 0.0
        }
    }


def run(input_string: str) -> Dict[str, Any]:
    """
    Interface function for the EchoScan pipeline.
    
    Args:
        input_string: Input string to analyze for context drift
        
    Returns:
        Dict containing context drift analysis results
    """
    # Segment text into blocks
    blocks = segment_text_into_blocks(input_string)
    
    # Calculate drift vectors
    drift_analysis = calculate_drift_vectors(blocks)
    
    # Determine authenticity implications
    anomaly_score = drift_analysis["anomaly_score"]
    drift_consistency = drift_analysis["drift_consistency"]
    
    # Generate classification and modifiers
    if anomaly_score > 0.7:
        source_classification = "AI-Generated"
        echo_score_penalty = -12.0
        advisory_flag = "CONTEXT_DRIFT: High anomaly score detected"
    elif anomaly_score > 0.4:
        source_classification = "Questionable"
        echo_score_penalty = -6.0
        advisory_flag = "CONTEXT_DRIFT: Moderate anomaly patterns"
    elif drift_consistency > 0.9:
        source_classification = "Questionable"
        echo_score_penalty = -3.0
        advisory_flag = "CONTEXT_DRIFT: Suspiciously consistent drift patterns"
    else:
        source_classification = "Human-Generated"
        echo_score_modifier = 2.0
        echo_score_penalty = 0.0
        advisory_flag = None
    
    # Compile results for pipeline integration
    result = {
        "detector": "context_drift",
        "source_classification": source_classification,
        "echo_score_penalty": echo_score_penalty if "echo_score_penalty" in locals() else 0.0,
        "echo_score_modifier": locals().get("echo_score_modifier", 0.0),
        **drift_analysis
    }
    
    if advisory_flag:
        result["advisory_flag"] = advisory_flag
        
    return result